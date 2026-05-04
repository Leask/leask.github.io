#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / '_posts'
PLACEHOLDER = 'LEASK_CODE_BLOCK_PLACEHOLDER_'
UNWRAP_TAGS = [
    'font',
    'span',
    'div',
    'center',
    'table',
    'tbody',
    'thead',
    'tfoot',
    'tr',
    'td',
    'th',
]


@dataclass
class ConvertedPost:
    source: Path
    target: Path
    content: str
    links: list[str]
    images: list[str]


def split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        return '', text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            return ''.join(lines[: index + 1]), ''.join(lines[index + 1 :])

    return '', text


def clean_code(raw: str, include_script_tag: bool = False) -> str:
    raw = re.sub(r'^\s*<code\b[^>]*>', '', raw, flags=re.I)
    raw = re.sub(r'</code>\s*$', '', raw, flags=re.I)
    raw = re.sub(r"(?<!['\"])<br\s*/?\s*>", '\n', raw, flags=re.I)
    raw = re.sub(r'</?p\b[^>]*>', '', raw, flags=re.I)
    raw = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', raw, flags=re.I | re.S)
    raw = re.sub(
        r'</?(font|span|em|strong|b|i)\b[^>]*>',
        '',
        raw,
        flags=re.I,
    )
    raw = html.unescape(raw).replace('\xa0', ' ')
    raw = raw.replace('\r\n', '\n').replace('\r', '\n')
    raw = '\n'.join(line.rstrip() for line in raw.splitlines())
    raw = re.sub(r'\n[ \t]*\n+', '\n', raw)
    raw = raw.strip('\n')

    if include_script_tag and raw:
        raw = f'<script>\n{raw}\n</script>'

    return f'```\n{raw}\n```'


def protect_code_blocks(body: str) -> tuple[str, list[str]]:
    blocks: list[str] = []

    def replace_pre(match: re.Match[str]) -> str:
        blocks.append(clean_code(match.group(2)))
        return f'\n\n<p>{PLACEHOLDER}{len(blocks) - 1}</p>\n\n'

    def replace_script(match: re.Match[str]) -> str:
        blocks.append(clean_code(match.group(2), include_script_tag=True))
        return f'\n\n<p>{PLACEHOLDER}{len(blocks) - 1}</p>\n\n'

    body = re.sub(r'<pre\b([^>]*)>(.*?)</pre>', replace_pre, body, flags=re.I | re.S)
    body = re.sub(
        r'<script\b([^>]*)>(.*?)</script>',
        replace_script,
        body,
        flags=re.I | re.S,
    )
    return body, blocks


def extract_urls(body: str) -> tuple[list[str], list[str]]:
    body, _blocks = protect_code_blocks(body)
    soup = BeautifulSoup(body, 'html.parser')
    links = [
        normalize_url(tag.get('href', ''))
        for tag in soup.find_all('a')
        if tag.get('href') and (tag.get_text(strip=True) or tag.find('img'))
    ]
    images = [
        normalize_url(tag.get('src', ''))
        for tag in soup.find_all('img')
        if tag.get('src')
    ]
    return links, images


def normalize_url(value: str) -> str:
    return html.unescape(value).replace('\xa0', ' ').strip()


def normalize_html_body(body: str) -> tuple[str, list[str]]:
    body = body.replace('&nbsp;', ' ').replace('\xa0', ' ')
    body, blocks = protect_code_blocks(body)
    soup = BeautifulSoup(body, 'html.parser')

    for tag in soup(['style']):
        tag.decompose()

    for tag in soup.find_all(UNWRAP_TAGS):
        tag.unwrap()

    return str(soup), blocks


def clean_markdown(markdown: str, code_blocks: list[str]) -> str:
    markdown = re.sub(r'<br\s*/?\s*>', '\n', markdown, flags=re.I)

    for index, block in enumerate(code_blocks):
        markdown = markdown.replace(f'{PLACEHOLDER}{index}', block)

    markdown = markdown.replace('\r\n', '\n').replace('\r', '\n')
    markdown = markdown.replace('\xa0', ' ')
    markdown = re.sub(r'\n[ \t]+\n', '\n\n', markdown)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    markdown = markdown.strip()

    if markdown:
        return f'{markdown}\n'
    return ''


def convert_body(body: str) -> str:
    normalized, code_blocks = normalize_html_body(body)
    markdown = markdownify(
        normalized,
        autolinks=False,
        bullets='-',
        default_title=False,
        escape_asterisks=False,
        escape_underscores=False,
        heading_style='ATX',
        newline_style='spaces',
    )
    return clean_markdown(markdown, code_blocks)


def convert_post(path: Path) -> ConvertedPost:
    text = path.read_text(encoding='utf-8')
    front_matter, body = split_front_matter(text)
    links, images = extract_urls(body)
    markdown = convert_body(body)

    if front_matter:
        content = f'{front_matter.rstrip()}\n\n{markdown}'
    else:
        content = markdown

    return ConvertedPost(
        source=path,
        target=path.with_suffix('.md'),
        content=content,
        links=links,
        images=images,
    )


def strip_fenced_code(markdown: str) -> str:
    return re.sub(r'```.*?```', '', markdown, flags=re.S)


def find_missing_urls(post: ConvertedPost) -> tuple[list[str], list[str]]:
    text = post.content
    missing_links = [url for url in post.links if url and url not in text]
    missing_images = [url for url in post.images if url and url not in text]
    return missing_links, missing_images


def summarize(posts: list[ConvertedPost]) -> int:
    missing_front_matter = [
        post.source
        for post in posts
        if not post.content.startswith('---\n')
    ]
    conflicts = [
        post.target
        for post in posts
        if post.target.exists() and post.target != post.source
    ]
    missing_links: list[tuple[Path, str]] = []
    missing_images: list[tuple[Path, str]] = []
    residual_html: list[Path] = []

    for post in posts:
        links, images = find_missing_urls(post)
        missing_links.extend((post.source, url) for url in links)
        missing_images.extend((post.source, url) for url in images)

        _front_matter, markdown_body = split_front_matter(post.content)
        body = strip_fenced_code(markdown_body)
        if re.search(r'</?[a-zA-Z][^>]*>', body):
            residual_html.append(post.source)

    print(f'HTML posts found: {len(posts)}')
    print(f'Would create Markdown posts: {len(posts)}')
    print(f'Missing front matter: {len(missing_front_matter)}')
    print(f'Target conflicts: {len(conflicts)}')
    print(f'Missing normal links: {len(missing_links)}')
    print(f'Missing normal images: {len(missing_images)}')
    print(f'Residual HTML outside code fences: {len(residual_html)}')

    for label, entries in [
        ('front matter', [(path, '') for path in missing_front_matter]),
        ('conflict', [(path, '') for path in conflicts]),
        ('link', missing_links),
        ('image', missing_images),
        ('html', [(path, '') for path in residual_html]),
    ]:
        for path, value in entries[:10]:
            suffix = f' -> {value}' if value else ''
            print(f'  {label}: {path.relative_to(ROOT)}{suffix}')

    return int(
        bool(missing_front_matter)
        or bool(conflicts)
        or bool(missing_links)
        or bool(missing_images)
    )


def write_posts(posts: list[ConvertedPost]) -> None:
    for post in posts:
        post.target.write_text(post.content, encoding='utf-8')
        if post.target != post.source:
            post.source.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--write',
        action='store_true',
        help='write converted .md files and remove source .html files',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    html_posts = sorted(POSTS_DIR.glob('*.html'))
    posts = [convert_post(path) for path in html_posts]
    status = summarize(posts)

    if status:
        print('Aborted because verification found blocking issues.')
        return status

    if args.write:
        write_posts(posts)
        print('Converted posts written.')
    else:
        print('Dry run only. Pass --write to update files.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
