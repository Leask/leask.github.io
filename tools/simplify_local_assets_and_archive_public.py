#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


POSTS_DIR = Path('_posts')
PUBLIC_DIR = Path('public')
ARCHIVE_DIR = Path('assets/archived')

ASSET_IMAGE_PREFIX = '/assets/img/'
PUBLIC_PREFIX = '/public/'
ARCHIVE_PREFIX = '/assets/archived/'

TEXT_EXTENSIONS = {
    '.html',
    '.htm',
    '.md',
    '.txt',
    '.xml',
    '.css',
    '.js',
}

NESTED_LOCAL_IMAGE_RE = re.compile(
    r'\[!\[(?P<alt>[^\]]*)\]\('
    r'(?P<inner_url>/assets/img/[^\s\)"]+)'
    r'(?P<inner_meta>\s+"[^"]*")?'
    r'\)\]\('
    r'(?P<outer_url>/assets/img/[^\s\)"]+)'
    r'(?P<outer_meta>\s+"[^"]*")?'
    r'\)'
)

PUBLIC_URL_RE = re.compile(r'/public/[^\s\)\"\'<>]+')

ARCHIVE_TEXT_REWRITES = {
    Path('2011/09/overflowScrolling.html'): [
        (
            'http://www.leaskh.com/wp-content/uploads/2011/07/'
            'qingyuan_city_09_06_181.jpg',
            '/assets/img/2011/07/qingyuan_city_09_06_181.jpg',
        ),
    ],
}


@dataclass
class Result:
    posts_changed: int = 0
    linked_images_simplified: int = 0
    public_urls_rewritten: int = 0
    moved_files: int = 0
    removed_ds_store: int = 0
    archived_files_rewritten: int = 0
    removed_empty_dirs: int = 0


def extract_title(meta: str | None) -> str | None:
    if not meta:
        return None
    match = re.fullmatch(r'\s+"([^"]*)"', meta)
    if not match:
        return None
    title = match.group(1)
    return title or None


def render_image(alt: str, url: str, title: str | None) -> str:
    if title is None:
        return f'![{alt}]({url})'
    return f'![{alt}]({url} "{title}")'


def simplify_nested_local_images(text: str) -> tuple[str, int]:
    replacements = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal replacements
        replacements += 1
        alt = match.group('alt')
        final_url = match.group('outer_url')
        title = (
            extract_title(match.group('inner_meta'))
            or extract_title(match.group('outer_meta'))
        )
        return render_image(alt, final_url, title)

    return NESTED_LOCAL_IMAGE_RE.sub(replace, text), replacements


def rewrite_public_urls(text: str) -> tuple[str, int]:
    matches = list(PUBLIC_URL_RE.finditer(text))
    if not matches:
        return text, 0
    return text.replace(PUBLIC_PREFIX, ARCHIVE_PREFIX), len(matches)


def update_posts(apply: bool, result: Result) -> None:
    for post_path in sorted(POSTS_DIR.glob('*.md')):
        original = post_path.read_text(encoding='utf-8')
        updated, simplified = simplify_nested_local_images(original)
        updated, public_rewrites = rewrite_public_urls(updated)

        if updated == original:
            continue

        result.posts_changed += 1
        result.linked_images_simplified += simplified
        result.public_urls_rewritten += public_rewrites

        if apply:
            post_path.write_text(updated, encoding='utf-8')


def move_public_tree(apply: bool, result: Result) -> None:
    if not PUBLIC_DIR.exists():
        return

    for source_path in sorted(PUBLIC_DIR.rglob('*')):
        if not source_path.is_file():
            continue

        if source_path.name == '.DS_Store':
            result.removed_ds_store += 1
            if apply:
                source_path.unlink()
            continue

        relative_path = source_path.relative_to(PUBLIC_DIR)
        target_path = ARCHIVE_DIR / relative_path
        result.moved_files += 1

        if apply:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                raise FileExistsError(f'target already exists: {target_path}')
            shutil.move(str(source_path), str(target_path))


def rewrite_archived_files(apply: bool, result: Result) -> None:
    for relative_path, replacements in ARCHIVE_TEXT_REWRITES.items():
        archive_path = ARCHIVE_DIR / relative_path
        if not archive_path.exists():
            continue
        if archive_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        original = archive_path.read_text(encoding='utf-8')
        updated = original
        change_count = 0
        for old, new in replacements:
            if old in updated:
                updated = updated.replace(old, new)
                change_count += 1

        if updated == original:
            continue

        result.archived_files_rewritten += change_count
        if apply:
            archive_path.write_text(updated, encoding='utf-8')


def remove_empty_directories(apply: bool, result: Result) -> None:
    if not PUBLIC_DIR.exists():
        return

    directories = sorted(
        (path for path in PUBLIC_DIR.rglob('*') if path.is_dir()),
        reverse=True,
    )
    for directory in directories:
        if any(directory.iterdir()):
            continue
        result.removed_empty_dirs += 1
        if apply:
            directory.rmdir()

    if PUBLIC_DIR.exists() and not any(PUBLIC_DIR.iterdir()):
        result.removed_empty_dirs += 1
        if apply:
            PUBLIC_DIR.rmdir()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--apply',
        action='store_true',
        help='write changes to disk',
    )
    args = parser.parse_args()

    result = Result()
    update_posts(apply=args.apply, result=result)
    move_public_tree(apply=args.apply, result=result)
    rewrite_archived_files(apply=args.apply, result=result)
    remove_empty_directories(apply=args.apply, result=result)

    print(f'posts_changed {result.posts_changed}')
    print(f'linked_images_simplified {result.linked_images_simplified}')
    print(f'public_urls_rewritten {result.public_urls_rewritten}')
    print(f'moved_files {result.moved_files}')
    print(f'removed_ds_store {result.removed_ds_store}')
    print(f'archived_files_rewritten {result.archived_files_rewritten}')
    print(f'removed_empty_dirs {result.removed_empty_dirs}')
    print(f'apply {int(args.apply)}')


if __name__ == '__main__':
    main()
