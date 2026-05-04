#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image, ImageFile

from clean_posts_html_to_md import convert_body


ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT = Path(__file__).resolve().parents[1]
TUMBLR_HTML_DIR = ROOT / 'tumblr/posts/html'
TUMBLR_MEDIA_DIR = ROOT / 'tumblr/media'
POSTS_DIR = ROOT / '_posts'
ASSETS_DIR = ROOT / 'assets/img'
TIMEZONE = ZoneInfo('America/Toronto')
MONTHS = {
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'May': 5,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12,
}
TIMESTAMP_RE = re.compile(
    r'^\s*([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th),\s+(\d{4})\s+'
    r'(\d{1,2}):(\d{2})(am|pm)\s*$'
)
MEDIA_NAME_RE = re.compile(r'^(?P<post_id>\d+)(?:_(?P<index>\d+))?$')
SPACE_RE = re.compile(r'\s+')
SLUG_RE = re.compile(r'[^a-z0-9]+')
EXCERPT_TRIM_RE = re.compile(r'\s+')
CJK_RE = re.compile(r'[\u3400-\u9fff]')


@dataclass(frozen=True)
class MediaFile:
    path: Path
    width: int
    height: int
    index: int

    @property
    def dims(self) -> tuple[int, int]:
        return (self.width, self.height)


@dataclass
class ConvertedTumblrPost:
    post_id: str
    source: Path
    target: Path
    asset_copies: list[tuple[Path, Path]]
    content: str
    title: str
    tags: list[str]
    image_count: int


def yaml_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def normalize_space(value: str) -> str:
    return SPACE_RE.sub(' ', value).strip()


def parse_timestamp(raw: str) -> datetime:
    match = TIMESTAMP_RE.match(raw)
    if not match:
        raise ValueError(f'unsupported timestamp: {raw!r}')
    month_name, day, year, hour, minute, meridiem = match.groups()
    hour_num = int(hour)
    if meridiem == 'pm' and hour_num != 12:
        hour_num += 12
    if meridiem == 'am' and hour_num == 12:
        hour_num = 0
    return datetime(
        int(year),
        MONTHS[month_name],
        int(day),
        hour_num,
        int(minute),
        tzinfo=TIMEZONE,
    )


def media_sort_key(path: Path) -> tuple[int, str]:
    match = MEDIA_NAME_RE.match(path.stem)
    if match and match.group('index') is not None:
        return (int(match.group('index')), path.name)
    return (0, path.name)


def media_index(path: Path) -> int:
    match = MEDIA_NAME_RE.match(path.stem)
    if match and match.group('index') is not None:
        return int(match.group('index'))
    return 0


def media_files_for_post(post_id: str) -> list[MediaFile]:
    files = sorted(TUMBLR_MEDIA_DIR.glob(f'{post_id}*'), key=media_sort_key)
    result: list[MediaFile] = []
    for path in files:
        if not path.is_file():
            continue
        with Image.open(path) as image:
            width, height = image.size
        result.append(
            MediaFile(
                path=path,
                width=width,
                height=height,
                index=media_index(path),
            )
        )
    return result


def asset_url_and_path(post_dt: datetime, media: MediaFile) -> tuple[str, Path]:
    rel = Path(f'{post_dt.year:04d}') / f'{post_dt.month:02d}' / media.path.name
    url = '/' + str((Path('assets/img') / rel).as_posix())
    return url, ASSETS_DIR / rel


def stable_copy_target(post_dt: datetime, media: MediaFile) -> Path:
    _url, path = asset_url_and_path(post_dt, media)
    return path


def ensure_copy_target(dest: Path, source: Path) -> Path:
    if not dest.exists():
        return dest
    if hashlib.sha256(dest.read_bytes()).digest() == hashlib.sha256(
        source.read_bytes()
    ).digest():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    for index in range(1, 1000):
        candidate = dest.with_name(f'{stem}-tumblr-{index}{suffix}')
        if not candidate.exists():
            return candidate
        if hashlib.sha256(candidate.read_bytes()).digest() == hashlib.sha256(
            source.read_bytes()
        ).digest():
            return candidate
    raise RuntimeError(f'cannot resolve asset collision for {dest.as_posix()}')


def tag_host_label(url: str) -> str:
    host = (urlparse(url).netloc or '').lower().strip()
    host = host.removeprefix('www.')
    if 'instagram.com' in host or 'instagr.am' in host:
        return 'Instagram'
    if 'youtube.com' in host or 'youtu.be' in host:
        return 'YouTube'
    if host == 'path.com':
        return 'Path'
    if host == 'github.com':
        return 'GitHub'
    if host == 'twitter.com' or host == 'x.com':
        return 'X'
    if not host:
        return 'Link'
    return host.split('.', 1)[0].capitalize()


def is_empty_anchor(anchor: Tag) -> bool:
    return not anchor.get_text(strip=True) and not anchor.find('img')


def is_generated_anchor(anchor: Tag) -> bool:
    return anchor.get('data-import-generated-label') == '1'


def should_embed_all_local_media(soup: BeautifulSoup, local_media: list[MediaFile]) -> bool:
    if not local_media:
        return False
    body = soup.body
    if body is None:
        return False
    empty_links = [
        anchor
        for anchor in body.find_all('a')
        if anchor.get('href')
        and is_empty_anchor(anchor)
        and not anchor.find_parent(class_='npf_link')
        and anchor.find_parent(id='footer') is None
    ]
    if empty_links:
        return True
    if body.select_one('.npf_link'):
        return False
    return True


def unwrap_image_links(body: Tag) -> None:
    for anchor in list(body.find_all('a')):
        if anchor.find_parent(id='footer') is not None:
            continue
        children = [child for child in anchor.children if not is_blank_node(child)]
        if len(children) != 1:
            continue
        child = children[0]
        if isinstance(child, Tag) and child.name == 'img':
            anchor.replace_with(child)


def is_blank_node(node: object) -> bool:
    return isinstance(node, NavigableString) and not node.strip()


def replace_embeds_with_links(soup: BeautifulSoup, body: Tag) -> None:
    for figure in list(body.find_all('figure')):
        iframe = figure.find('iframe')
        if iframe is None and 'tmblr-embed' not in (figure.get('class') or []):
            continue
        url = figure.get('data-url') or (iframe.get('src') if iframe else '')
        if not url:
            figure.decompose()
            continue
        label = tag_host_label(url)
        replacement = soup.new_tag('p')
        link = soup.new_tag('a', href=url)
        link.string = label
        replacement.append(link)
        figure.replace_with(replacement)

    for iframe in list(body.find_all('iframe')):
        url = iframe.get('src', '')
        if not url:
            iframe.decompose()
            continue
        label = tag_host_label(url)
        replacement = soup.new_tag('p')
        link = soup.new_tag('a', href=url)
        link.string = label
        replacement.append(link)
        iframe.replace_with(replacement)


def normalize_anchors(body: Tag) -> None:
    for anchor in body.find_all('a'):
        if anchor.find_parent(id='footer') is not None:
            continue
        href = (anchor.get('href') or '').strip()
        if not href:
            continue
        anchor['href'] = href
        if is_empty_anchor(anchor):
            anchor.clear()
            anchor.string = tag_host_label(href)
            anchor['data-import-generated-label'] = '1'


def rewrite_and_match_images(
    soup: BeautifulSoup,
    post_dt: datetime,
    local_media: list[MediaFile],
) -> tuple[list[tuple[Path, Path]], int]:
    body = soup.body
    if body is None:
        return [], 0

    copies: list[tuple[Path, Path]] = []
    used: set[Path] = set()
    img_tags = body.find_all('img')

    if not img_tags and should_embed_all_local_media(soup, local_media):
        insert_before = next(
            (child for child in body.contents if not is_blank_node(child)),
            None,
        )
        for media in local_media:
            url, target = asset_url_and_path(post_dt, media)
            final_target = ensure_copy_target(target, media.path)
            copies.append((media.path, final_target))
            used.add(media.path)
            wrapper = soup.new_tag('p')
            tag = soup.new_tag(
                'img',
                src='/' + str(final_target.relative_to(ROOT).as_posix()),
            )
            wrapper.append(tag)
            if insert_before is None:
                body.append(wrapper)
            else:
                insert_before.insert_before(wrapper)
        return copies, len(local_media)

    for img in img_tags:
        src = (img.get('src') or '').strip()
        media: MediaFile | None = None

        if src.startswith('../../media/'):
            candidate = (TUMBLR_HTML_DIR / src).resolve()
            for item in local_media:
                if item.path.resolve() == candidate:
                    media = item
                    break
        else:
            width = img.get('data-orig-width')
            height = img.get('data-orig-height')
            if width and height:
                dims = (int(width), int(height))
                for item in local_media:
                    if item.path in used:
                        continue
                    if item.dims == dims:
                        media = item
                        break

        if media is None:
            continue

        url, target = asset_url_and_path(post_dt, media)
        final_target = ensure_copy_target(target, media.path)
        copies.append((media.path, final_target))
        used.add(media.path)

        img.attrs.clear()
        img['src'] = '/' + str(final_target.relative_to(ROOT).as_posix())

    return copies, len(used)


def remove_footer_and_empty_titles(soup: BeautifulSoup) -> None:
    for footer in soup.select('#footer'):
        footer.decompose()
    for heading in list(soup.find_all('h1')):
        if not heading.get_text(' ', strip=True):
            heading.decompose()


def remove_all_h1(body: Tag) -> None:
    for heading in list(body.find_all('h1')):
        heading.decompose()


def first_title_from_h1(soup: BeautifulSoup) -> str:
    for heading in soup.find_all('h1'):
        text = normalize_space(heading.get_text(' ', strip=True))
        if text:
            return text
    return ''


def first_excerpt_text(body: Tag | None) -> str:
    if body is None:
        return ''
    for tag in body.find_all(['p', 'blockquote', 'h2', 'h3', 'li']):
        if tag.find_parent(id='footer') is not None:
            continue
        if tag.name == 'p':
            anchors = tag.find_all('a')
            if anchors and all(is_generated_anchor(anchor) for anchor in anchors):
                text = normalize_space(tag.get_text(' ', strip=True))
                labels = ' '.join(anchor.get_text(' ', strip=True) for anchor in anchors)
                if text == labels:
                    continue
        text = normalize_space(tag.get_text(' ', strip=True))
        if text:
            return text
    return ''


def derive_fallback_title(body: Tag | None, image_count: int) -> str:
    if body is not None:
        for anchor in body.find_all('a'):
            if is_generated_anchor(anchor):
                label = normalize_space(anchor.get_text(' ', strip=True))
                if label:
                    return f'{label} Photo' if image_count else f'{label} Link'
    if image_count:
        return 'Photo'
    return 'Tumblr Post'


def title_for_post(soup: BeautifulSoup, image_count: int) -> str:
    title = first_title_from_h1(soup)
    if title:
        return title
    excerpt = first_excerpt_text(soup.body)
    if excerpt:
        if len(excerpt) > 80:
            excerpt = excerpt[:77].rstrip() + '...'
        return excerpt
    return derive_fallback_title(soup.body, image_count)


def slugify(value: str) -> str:
    ascii_value = (
        unicodedata.normalize('NFKD', value)
        .encode('ascii', 'ignore')
        .decode('ascii')
        .lower()
    )
    slug = SLUG_RE.sub('-', ascii_value).strip('-')
    slug = re.sub(r'-{2,}', '-', slug)
    return slug[:60]


def build_target_path(post_dt: datetime, title: str, post_id: str) -> Path:
    slug = slugify(title)
    if CJK_RE.search(title) and len(slug) < 8:
        slug = ''
    stem = f'{post_dt:%Y-%m-%d}-{slug}-tumblr-{post_id}' if slug else f'{post_dt:%Y-%m-%d}-tumblr-{post_id}'
    return POSTS_DIR / f'{stem}.md'


def front_matter(title: str, post_dt: datetime, tags: list[str]) -> str:
    lines = [
        '---',
        'layout: post',
        f'title: {yaml_quote(title)}',
        'author: Leask',
        f"date: {yaml_quote(post_dt.strftime('%Y-%m-%d %H:%M:%S %z'))}",
    ]
    if tags:
        lines.append('tags:')
        for tag in tags:
            lines.append(f'- {yaml_quote(tag)}')
    lines.append('---')
    return '\n'.join(lines)


def dedupe_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = normalize_space(tag)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def convert_one(path: Path) -> ConvertedTumblrPost:
    post_id = path.stem
    soup = BeautifulSoup(path.read_text(encoding='utf-8', errors='ignore'), 'html.parser')
    timestamp_tag = soup.select_one('#footer #timestamp')
    if timestamp_tag is None:
        raise ValueError(f'missing timestamp: {path.as_posix()}')
    post_dt = parse_timestamp(timestamp_tag.get_text(' ', strip=True))
    tags = dedupe_tags(
        [span.get_text(' ', strip=True) for span in soup.select('#footer .tag')]
    )
    local_media = media_files_for_post(post_id)

    remove_footer_and_empty_titles(soup)
    body = soup.body
    if body is None:
        raise ValueError(f'missing body: {path.as_posix()}')

    unwrap_image_links(body)
    replace_embeds_with_links(soup, body)
    normalize_anchors(body)
    asset_copies, image_count = rewrite_and_match_images(soup, post_dt, local_media)

    title = title_for_post(soup, image_count)
    remove_all_h1(body)
    markdown = convert_body(str(body)).strip()
    markdown = markdown.replace('<none>', '&lt;none&gt;')
    content = front_matter(title, post_dt, tags)
    if markdown:
        content = f'{content}\n\n{markdown}\n'
    else:
        content = f'{content}\n'

    return ConvertedTumblrPost(
        post_id=post_id,
        source=path,
        target=build_target_path(post_dt, title, post_id),
        asset_copies=asset_copies,
        content=content,
        title=title,
        tags=tags,
        image_count=image_count,
    )


def write_post(post: ConvertedTumblrPost) -> None:
    post.target.parent.mkdir(parents=True, exist_ok=True)
    post.target.write_text(post.content, encoding='utf-8')
    for source, dest in post.asset_copies:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            if hashlib.sha256(dest.read_bytes()).digest() == hashlib.sha256(
                source.read_bytes()
            ).digest():
                continue
        shutil.copy2(source, dest)


def summarize(posts: list[ConvertedTumblrPost]) -> int:
    target_counts = Counter(post.target.name for post in posts)
    duplicate_targets = [name for name, count in target_counts.items() if count > 1]
    residual_html = 0
    total_images = 0
    posts_with_images = 0
    tags_used = 0

    for post in posts:
        total_images += post.image_count
        if post.image_count:
            posts_with_images += 1
        if post.tags:
            tags_used += 1
        body = post.content.split('---\n', 2)[-1]
        if re.search(r'</?[a-zA-Z][^>]*>', body):
            residual_html += 1

    print(f'tumblr_html_posts {len(posts)}')
    print(f'posts_with_images {posts_with_images}')
    print(f'total_embedded_images {total_images}')
    print(f'posts_with_tags {tags_used}')
    print(f'asset_copies {sum(len(post.asset_copies) for post in posts)}')
    print(f'duplicate_targets {len(duplicate_targets)}')
    print(f'residual_html_posts {residual_html}')
    for name in duplicate_targets[:20]:
        print('duplicate_target', name)
    for post in posts[:10]:
        print(
            'sample',
            post.source.name,
            '->',
            post.target.name,
            '|',
            post.title,
            '| images=',
            post.image_count,
        )
    return int(bool(duplicate_targets) or bool(residual_html))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--write',
        action='store_true',
        help='write imported posts and copied assets',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    posts = [convert_one(path) for path in sorted(TUMBLR_HTML_DIR.glob('*.html'))]
    status = summarize(posts)
    if args.write:
        for post in posts:
            write_post(post)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
