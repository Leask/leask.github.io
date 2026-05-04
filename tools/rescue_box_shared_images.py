#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from PIL import Image, UnidentifiedImageError


REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / '_posts'
ASSETS_DIR = REPO_ROOT / 'assets' / 'img'

BOX_URL_RE = re.compile(
    r'https?://(?:www\.)?(?:box\.net|app\.box\.com)/'
    r'(?:lite/(?:image|thumb)/[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)?|'
    r'lite/[A-Za-z0-9]+|public/[A-Za-z0-9]+|shared/[A-Za-z0-9]+|'
    r's/[A-Za-z0-9]+)'
)
TOKEN_RE = re.compile(
    r'(?:/lite/(?:image|thumb)/|/lite/|/public/|/shared/|/s/)'
    r'([A-Za-z0-9]+)'
)
IMAGE_EXTENSIONS = {
    'bmp',
    'gif',
    'jpeg',
    'jpg',
    'png',
    'tif',
    'tiff',
    'webp',
}
RENDERABLE_EXTENSIONS = {'gif', 'jpeg', 'jpg', 'png', 'webp'}
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/136.0.0.0 Safari/537.36'
)


@dataclass(frozen=True)
class Occurrence:
    post_path: Path
    url: str


@dataclass(frozen=True)
class SharedImage:
    token: str
    item_id: str
    name: str
    extension: str
    sha1: str
    download_url: str


def fetch_url_bytes(url: str) -> tuple[int, dict[str, str], bytes]:
    request = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(request, timeout=120) as response:
            status = response.getcode()
            headers = {k.lower(): v for k, v in response.headers.items()}
            return status, headers, response.read()
    except HTTPError as exc:
        return exc.code, dict(exc.headers.items()), exc.read()
    except URLError as exc:
        raise RuntimeError(f'Failed to fetch {url}: {exc}') from exc


def fetch_url_text(url: str) -> tuple[int, str]:
    status, headers, body = fetch_url_bytes(url)
    charset = 'utf-8'
    content_type = headers.get('content-type', '')
    match = re.search(r'charset=([A-Za-z0-9_-]+)', content_type)
    if match:
        charset = match.group(1)
    return status, body.decode(charset, errors='replace')


def json_unescape(value: str) -> str:
    return json.loads(f'"{value}"')


def parse_shared_image(token: str) -> SharedImage | None:
    status, html = fetch_url_text(f'https://app.box.com/s/{token}')
    if status != 200:
        return None

    marker = '"preview_metadata":{'
    start = html.find(marker)
    if start == -1:
        return None

    snippet = html[start:start + 5000]

    item_match = re.search(r'"id":"(\d+)"', snippet)
    name_match = re.search(r'"name":"([^"]+)"', snippet)
    ext_match = re.search(r'"extension":"([^"]+)"', snippet)
    sha_match = re.search(r'"sha1":"([0-9a-f]{40})"', snippet)
    can_download = '"can_download":true' in snippet

    if (
        not item_match
        or not name_match
        or not ext_match
        or not sha_match
        or not can_download
    ):
        return None

    item_id = item_match.group(1)
    name = json_unescape(name_match.group(1))
    extension = ext_match.group(1).lower()
    if extension not in IMAGE_EXTENSIONS:
        return None

    return SharedImage(
        token=token,
        item_id=item_id,
        name=name,
        extension=extension,
        sha1=sha_match.group(1),
        download_url=(
            'https://app.box.com/index.php?rm=box_download_shared_file'
            f'&shared_name={token}&file_id=f_{item_id}'
        ),
    )


def verify_image_bytes(data: bytes) -> tuple[str, tuple[int, int]]:
    try:
        image = Image.open(BytesIO(data))
        image.load()
        return image.format or 'UNKNOWN', image.size
    except UnidentifiedImageError as exc:
        raise RuntimeError('Downloaded file is not a valid image.') from exc


def slugify_stem(name: str) -> str:
    stem = Path(name).stem
    normalized = unicodedata.normalize('NFKD', stem)
    ascii_only = normalized.encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^A-Za-z0-9]+', '-', ascii_only).strip('-').lower()
    return slug or 'box-image'


def post_year_month(post_path: Path) -> tuple[str, str]:
    match = re.match(r'(\d{4})-(\d{2})-\d{2}-', post_path.name)
    if not match:
        raise RuntimeError(f'Unexpected post filename: {post_path.name}')
    return match.group(1), match.group(2)


def repo_relative_url(path: Path) -> str:
    return '/' + path.relative_to(REPO_ROOT).as_posix()


def build_original_path(shared: SharedImage, post_path: Path) -> Path:
    year, month = post_year_month(post_path)
    directory = ASSETS_DIR / year / month
    filename = (
        f'{slugify_stem(shared.name)}-box-{shared.token}.'
        f'{shared.extension}'
    )
    return directory / filename


def save_original_image(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)


def build_preview_path(original_path: Path) -> Path:
    return original_path.with_name(f'{original_path.stem}-preview.jpg')


def save_preview_image(preview_path: Path, data: bytes) -> None:
    image = Image.open(BytesIO(data))
    if image.mode not in {'RGB', 'L'}:
        image = image.convert('RGB')
    elif image.mode == 'L':
        image = image.convert('RGB')
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(preview_path, format='JPEG', quality=92)


def collect_occurrences() -> dict[str, list[Occurrence]]:
    occurrences: dict[str, list[Occurrence]] = {}
    for post_path in sorted(POSTS_DIR.glob('*.md')):
        text = post_path.read_text(encoding='utf-8')
        for url in BOX_URL_RE.findall(text):
            token_match = TOKEN_RE.search(url)
            if not token_match:
                continue
            token = token_match.group(1)
            occurrences.setdefault(token, []).append(
                Occurrence(post_path=post_path, url=url)
            )
    return occurrences


def replace_urls(
    text: str,
    shared: SharedImage,
    original_url: str,
    preview_url: str | None,
) -> str:
    def replacement(url: str) -> str:
        if preview_url and (
            '/lite/image/' in url or '/lite/thumb/' in url
        ):
            return preview_url
        return original_url

    urls = sorted(
        {
            match
            for match in BOX_URL_RE.findall(text)
            if TOKEN_RE.search(match)
            and TOKEN_RE.search(match).group(1) == shared.token
        },
        key=len,
        reverse=True,
    )
    for url in urls:
        text = text.replace(url, replacement(url))
    return text


def download_and_verify(shared: SharedImage) -> tuple[bytes, str, tuple[int, int]]:
    status, headers, data = fetch_url_bytes(shared.download_url)
    if status != 200:
        raise RuntimeError(
            f'Box download failed for {shared.token}: HTTP {status}'
        )
    digest = hashlib.sha1(data).hexdigest()
    if digest != shared.sha1:
        raise RuntimeError(
            f'SHA1 mismatch for {shared.token}: {digest} != {shared.sha1}'
        )
    if not headers.get('content-type', '').startswith('image/'):
        raise RuntimeError(
            f'Unexpected content type for {shared.token}: '
            f'{headers.get("content-type", "")}'
        )
    image_format, size = verify_image_bytes(data)
    return data, image_format, size


def process(apply_changes: bool) -> int:
    occurrences = collect_occurrences()
    changed_posts: dict[Path, str] = {}
    downloaded = 0
    rescued: list[dict[str, object]] = []
    unresolved: list[str] = []
    previews = 0

    for token in sorted(occurrences):
        shared = parse_shared_image(token)
        if shared is None:
            unresolved.append(token)
            continue

        data, image_format, size = download_and_verify(shared)
        first_post = sorted(
            occurrence.post_path for occurrence in occurrences[token]
        )[0]
        original_path = build_original_path(shared, first_post)
        original_url = repo_relative_url(original_path)
        preview_url = None
        if shared.extension not in RENDERABLE_EXTENSIONS:
            preview_path = build_preview_path(original_path)
            preview_url = repo_relative_url(preview_path)
            previews += 1
            if apply_changes:
                save_preview_image(preview_path, data)
        if apply_changes:
            save_original_image(original_path, data)

        for occurrence in occurrences[token]:
            if occurrence.post_path not in changed_posts:
                changed_posts[occurrence.post_path] = (
                    occurrence.post_path.read_text(encoding='utf-8')
                )
            changed_posts[occurrence.post_path] = replace_urls(
                changed_posts[occurrence.post_path],
                shared,
                original_url,
                preview_url,
            )

        downloaded += 1
        rescued.append(
            {
                'token': token,
                'file_id': shared.item_id,
                'name': shared.name,
                'asset': original_url,
                'preview': preview_url,
                'format': image_format,
                'size': list(size),
                'refs': len(occurrences[token]),
            }
        )

    rewritten_posts = 0
    if apply_changes:
        for post_path, new_text in changed_posts.items():
            current = post_path.read_text(encoding='utf-8')
            if current == new_text:
                continue
            post_path.write_text(new_text, encoding='utf-8')
            rewritten_posts += 1

    print(
        json.dumps(
            {
                'rescued_images': downloaded,
                'rewritten_posts': rewritten_posts if apply_changes else 0,
                'created_previews': previews,
                'rescued': rescued,
                'unresolved_tokens': unresolved,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Write updated Markdown and downloaded image files.',
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    return process(apply_changes=args.apply)


if __name__ == '__main__':
    raise SystemExit(main())
