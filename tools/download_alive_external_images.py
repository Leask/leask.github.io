#!/usr/bin/env python3
"""Download reachable external post images and rewrite posts to local assets."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import mimetypes
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image


POSTS_DIR = Path('_posts')
ASSETS_PREFIX = '/assets/img/'
IMAGE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.webp',
    '.svg',
    '.bmp',
    '.tif',
    '.tiff',
}
CONTENT_TYPE_EXTENSIONS = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
    'image/bmp': '.bmp',
    'image/tiff': '.tiff',
}
IMAGE_MAGIC_EXTENSIONS = (
    (b'\xff\xd8\xff', '.jpg'),
    (b'\x89PNG\r\n\x1a\n', '.png'),
    (b'GIF87a', '.gif'),
    (b'GIF89a', '.gif'),
    (b'RIFF', '.webp'),
    (b'<svg', '.svg'),
    (b'<?xml', '.svg'),
)

MARKDOWN_IMAGE_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)', re.M)
MARKDOWN_LINK_RE = re.compile(r'(!?\[[^\]]*\]\()([^)]+)(\))', re.M)
HTML_ATTR_RE = re.compile(
    r'(<(?:img|a)\b[^>]*\b(?:src|href)=["\'])([^"\']+)(["\'][^>]*>)',
    re.I,
)
FENCE_RE = re.compile(r'^```.*?^```', re.M | re.S)
SAFE_NAME_RE = re.compile(r'[^a-z0-9._-]+')


@dataclass(frozen=True)
class ImageReference:
    post: Path
    url: str


@dataclass
class DownloadResult:
    url: str
    ok: bool
    local_url: str = ''
    status: int = 0
    content_type: str = ''
    error: str = ''
    bytes_written: int = 0


def split_fenced(text: str) -> list[tuple[bool, str]]:
    parts: list[tuple[bool, str]] = []
    pos = 0
    for match in FENCE_RE.finditer(text):
        if match.start() > pos:
            parts.append((False, text[pos:match.start()]))
        parts.append((True, match.group(0)))
        pos = match.end()
    if pos < len(text):
        parts.append((False, text[pos:]))
    return parts


def first_markdown_target(raw: str) -> tuple[str, str]:
    content = raw.strip()
    if content.startswith('<'):
        end = content.find('>')
        if end != -1:
            return content[1:end], content[end + 1:]
    match = re.match(r'(\S+)(.*)\Z', content, re.S)
    if not match:
        return '', ''
    return match.group(1).strip('"\''), match.group(2)


def is_external(url: str) -> bool:
    return url.startswith(('http://', 'https://'))


def collect_image_references() -> list[ImageReference]:
    references: list[ImageReference] = []
    for post in sorted(POSTS_DIR.glob('*.md')):
        text = post.read_text(encoding='utf-8')
        for is_code, segment in split_fenced(text):
            if is_code:
                continue
            for match in MARKDOWN_IMAGE_RE.finditer(segment):
                url, _rest = first_markdown_target(match.group(1))
                if is_external(url):
                    references.append(ImageReference(post=post, url=url))
            for match in re.finditer(
                r'<img\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>',
                segment,
                re.I,
            ):
                url = match.group(1).strip()
                if is_external(url):
                    references.append(ImageReference(post=post, url=url))
    return references


def post_year_month(post: Path) -> tuple[str, str]:
    match = re.match(r'(\d{4})-(\d{2})-\d{2}-', post.name)
    if not match:
        return 'unknown', 'unknown'
    return match.group(1), match.group(2)


def image_extension(url: str, content_type: str, data: bytes) -> str:
    path = urllib.parse.urlparse(url).path
    ext = Path(urllib.parse.unquote(path)).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        if ext == '.jpeg':
            return '.jpg'
        return ext

    if content_type in CONTENT_TYPE_EXTENSIONS:
        return CONTENT_TYPE_EXTENSIONS[content_type]

    head = data.lstrip()[:16]
    for magic, magic_ext in IMAGE_MAGIC_EXTENSIONS:
        if head.startswith(magic):
            return magic_ext

    guessed = mimetypes.guess_extension(content_type)
    if guessed:
        return guessed
    return '.img'


def safe_slug(value: str) -> str:
    slug = SAFE_NAME_RE.sub('-', value.lower()).strip('-._')
    slug = re.sub(r'-{2,}', '-', slug)
    return slug[:60] or 'image'


def local_asset_url(reference: ImageReference, content_type: str, data: bytes) -> str:
    year, month = post_year_month(reference.post)
    parsed = urllib.parse.urlparse(reference.url)
    host = safe_slug(parsed.netloc or 'external')
    basename = Path(urllib.parse.unquote(parsed.path)).name
    stem = safe_slug(Path(basename).stem) if basename else 'image'
    digest = hashlib.sha1(reference.url.encode('utf-8')).hexdigest()[:10]
    ext = image_extension(reference.url, content_type, data)
    filename = f'{stem}-{host}-{digest}{ext}'
    return f'{ASSETS_PREFIX}{year}/{month}/{filename}'


def image_validation_error(data: bytes, content_type: str) -> str:
    stripped = data.lstrip()
    lower_head = stripped[:64].lower()
    if lower_head.startswith((b'data:image', b'<!doctype', b'<html')):
        return 'text_image_or_html'

    magic_match = any(
        stripped.startswith(magic) for magic, _ext in IMAGE_MAGIC_EXTENSIONS
    )
    if not magic_match:
        return 'unknown_image_magic'

    if content_type == 'image/svg+xml':
        return ''

    try:
        image = Image.open(BytesIO(data))
        image.verify()
        image = Image.open(BytesIO(data))
        width, height = image.size
    except Exception as exc:  # noqa: BLE001 - validation should report type
        return f'image_decode_failed:{type(exc).__name__}'

    if width <= 1 and height <= 1:
        return 'one_pixel_placeholder'
    return ''


def download_url(reference: ImageReference) -> DownloadResult:
    parsed = urllib.parse.urlparse(reference.url)
    referer = parsed._replace(
        path='/',
        params='',
        query='',
        fragment='',
    ).geturl()
    request = urllib.request.Request(
        reference.url,
        headers={
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0 Safari/537.36'
            ),
            'Accept': (
                'image/avif,image/webp,image/apng,image/svg+xml,'
                'image/*,*/*;q=0.8'
            ),
            'Referer': referer,
        },
        method='GET',
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            status = response.getcode() or 0
            content_type = (
                response.headers.get('content-type', '')
                .split(';', 1)[0]
                .lower()
            )
            data = response.read()
    except urllib.error.HTTPError as exc:
        return DownloadResult(
            url=reference.url,
            ok=False,
            status=exc.code,
            content_type=exc.headers.get('content-type', '').split(';', 1)[0],
            error=f'HTTP {exc.code}',
        )
    except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError) as exc:
        reason = getattr(exc, 'reason', exc)
        error = reason if isinstance(reason, str) else type(reason).__name__
        return DownloadResult(url=reference.url, ok=False, error=str(error)[:120])
    except Exception as exc:  # noqa: BLE001 - migration diagnostic
        return DownloadResult(url=reference.url, ok=False, error=type(exc).__name__)

    validation_error = image_validation_error(data, content_type)
    if not (200 <= status < 400) or validation_error:
        return DownloadResult(
            url=reference.url,
            ok=False,
            status=status,
            content_type=content_type,
            error=validation_error or 'bad_status',
        )

    local_url = local_asset_url(reference, content_type, data)
    destination = Path(local_url.lstrip('/'))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)

    return DownloadResult(
        url=reference.url,
        ok=True,
        local_url=local_url,
        status=status,
        content_type=content_type,
        bytes_written=len(data),
    )


def rewrite_markdown_content(content: str, replacements: dict[str, str]) -> str:
    target, rest = first_markdown_target(content)
    if target not in replacements:
        return content
    return replacements[target] + rest


def rewrite_posts(replacements: dict[str, str]) -> tuple[int, int]:
    changed_posts = 0
    rewritten_targets = 0

    def replace_link(match: re.Match[str]) -> str:
        nonlocal rewritten_targets
        new_content = rewrite_markdown_content(match.group(2), replacements)
        if new_content != match.group(2):
            rewritten_targets += 1
        return match.group(1) + new_content + match.group(3)

    def replace_html_attr(match: re.Match[str]) -> str:
        nonlocal rewritten_targets
        url = match.group(2)
        if url not in replacements:
            return match.group(0)
        rewritten_targets += 1
        return match.group(1) + replacements[url] + match.group(3)

    for post in sorted(POSTS_DIR.glob('*.md')):
        text = post.read_text(encoding='utf-8')
        parts: list[str] = []
        for is_code, segment in split_fenced(text):
            if is_code:
                parts.append(segment)
                continue
            segment = MARKDOWN_LINK_RE.sub(replace_link, segment)
            segment = HTML_ATTR_RE.sub(replace_html_attr, segment)
            parts.append(segment)
        new_text = ''.join(parts)
        if new_text != text:
            post.write_text(new_text, encoding='utf-8')
            changed_posts += 1

    return changed_posts, rewritten_targets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--apply',
        action='store_true',
        help='download reachable images and rewrite posts',
    )
    args = parser.parse_args()

    references = collect_image_references()
    first_reference: dict[str, ImageReference] = {}
    occurrences: dict[str, int] = {}
    for reference in references:
        first_reference.setdefault(reference.url, reference)
        occurrences[reference.url] = occurrences.get(reference.url, 0) + 1

    print(f'external_image_refs={len(references)}')
    print(f'unique_external_images={len(first_reference)}')

    if not args.apply:
        print('dry_run=true')
        return

    results: list[DownloadResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as executor:
        futures = [
            executor.submit(download_url, reference)
            for reference in first_reference.values()
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    replacements = {
        result.url: result.local_url
        for result in results
        if result.ok and result.local_url
    }
    changed_posts, rewritten_targets = rewrite_posts(replacements)

    alive_refs = sum(occurrences[url] for url in replacements)
    failed = [result for result in results if not result.ok]
    print('dry_run=false')
    print(f'downloaded_unique_images={len(replacements)}')
    print(f'downloaded_image_refs={alive_refs}')
    print(f'failed_unique_images={len(failed)}')
    print(f'changed_posts={changed_posts}')
    print(f'rewritten_targets={rewritten_targets}')
    print(
        'downloaded_bytes='
        + str(sum(result.bytes_written for result in results if result.ok))
    )


if __name__ == '__main__':
    main()
