#!/usr/bin/env python3
"""Move post-referenced /public images to /assets/img and rewrite links."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote


POSTS_DIR = Path('_posts')
PUBLIC_PREFIX = '/public/'
ASSETS_PREFIX = '/assets/img/'
IMAGE_EXTENSIONS = (
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.webp',
    '.svg',
    '.bmp',
    '.tif',
    '.tiff',
)

IMAGE_PATH_RE = re.compile(
    r'(?P<path>/public/[^\s\]\)"\'<>]+'
    r'(?:\.jpg|\.jpeg|\.png|\.gif|\.webp|\.svg|\.bmp|\.tif|\.tiff))'
    r'(?P<query>\?[^)\]\s"\'<>]*)?',
    re.IGNORECASE,
)


def post_files() -> list[Path]:
    return sorted(POSTS_DIR.glob('*.md'))


def source_path(public_url: str) -> Path:
    return Path(unquote(public_url.lstrip('/')))


def destination_url(public_url: str) -> str:
    return ASSETS_PREFIX + public_url[len(PUBLIC_PREFIX):]


def destination_path(public_url: str) -> Path:
    return Path(destination_url(public_url).lstrip('/'))


def collect_references() -> dict[str, int]:
    references: dict[str, int] = {}
    for post in post_files():
        text = post.read_text(encoding='utf-8')
        for match in IMAGE_PATH_RE.finditer(text):
            public_url = match.group('path')
            if public_url.lower().endswith(IMAGE_EXTENSIONS):
                references[public_url] = references.get(public_url, 0) + 1
    return references


def ensure_no_conflicts(public_urls: list[str]) -> None:
    missing: list[str] = []
    conflicts: list[str] = []
    for public_url in public_urls:
        src = source_path(public_url)
        dst = destination_path(public_url)
        if not src.is_file():
            missing.append(str(src))
        if dst.exists() and src.resolve() != dst.resolve():
            conflicts.append(str(dst))

    if missing:
        raise SystemExit(
            'Missing source image files:\n' + '\n'.join(missing[:50])
        )
    if conflicts:
        raise SystemExit(
            'Destination files already exist:\n' + '\n'.join(conflicts[:50])
        )


def rewrite_posts() -> tuple[int, int, int]:
    changed_posts = 0
    rewritten_targets = 0
    removed_queries = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal rewritten_targets, removed_queries

        public_url = match.group('path')
        query = match.group('query')
        rewritten_targets += 1
        if query:
            removed_queries += 1
        return destination_url(public_url)

    for post in post_files():
        text = post.read_text(encoding='utf-8')
        new_text = IMAGE_PATH_RE.sub(replace, text)
        if new_text != text:
            post.write_text(new_text, encoding='utf-8')
            changed_posts += 1

    return changed_posts, rewritten_targets, removed_queries


def is_tracked(path: Path) -> bool:
    result = subprocess.run(
        ['git', 'ls-files', '--error-unmatch', str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def move_image(public_url: str) -> None:
    src = source_path(public_url)
    dst = destination_path(public_url)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if is_tracked(src):
        subprocess.run(['git', 'mv', str(src), str(dst)], check=True)
    else:
        shutil.move(str(src), str(dst))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--apply',
        action='store_true',
        help='rewrite posts and move image files',
    )
    args = parser.parse_args()

    references = collect_references()
    public_urls = sorted(references)
    ensure_no_conflicts(public_urls)

    query_references = 0
    for post in post_files():
        text = post.read_text(encoding='utf-8')
        for match in IMAGE_PATH_RE.finditer(text):
            if match.group('query'):
                query_references += 1

    print(f'unique_public_images={len(public_urls)}')
    print(f'public_image_references={sum(references.values())}')
    print(f'public_image_references_with_query={query_references}')

    if not args.apply:
        print('dry_run=true')
        return

    changed_posts, rewritten_targets, removed_queries = rewrite_posts()
    for public_url in public_urls:
        move_image(public_url)

    print('dry_run=false')
    print(f'changed_posts={changed_posts}')
    print(f'rewritten_targets={rewritten_targets}')
    print(f'removed_queries={removed_queries}')
    print(f'moved_images={len(public_urls)}')


if __name__ == '__main__':
    main()
