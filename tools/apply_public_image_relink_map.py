#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = REPO_ROOT / 'tools' / 'public_image_relink_map.json'


def load_map() -> dict:
    return json.loads(MAP_PATH.read_text(encoding='utf-8'))


LINKED_IMAGE_RE = re.compile(
    r'\[!\[(?P<alt>[^\]]*)\]\('
    r'(?P<img_url><[^>]+>|[^)\s]+)'
    r'(?:\s+"(?P<img_title>[^"]*)")?\)\]'
    r'\((?P<link_url><[^>]+>|[^)\s]+)(?:\s+"[^"]*")?\)'
)
IMAGE_RE = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\('
    r'(?P<img_url><[^>]+>|[^)\s]+)'
    r'(?:\s+"(?P<img_title>[^"]*)")?\)'
)


def normalize_url(url: str) -> str:
    if url.startswith('<') and url.endswith('>'):
        return url[1:-1]
    return url


def build_image_markdown(alt: str, replacement_url: str, title: str | None) -> str:
    if title:
        return f'![{alt}]({replacement_url} "{title}")'
    return f'![{alt}]({replacement_url})'


def transform_line(
    line: str,
    match_substrings: list[str],
    replacement_url: str,
) -> tuple[str, int]:
    updated = line
    replacements = 0

    def linked_replacer(match: re.Match[str]) -> str:
        nonlocal replacements
        img_url = normalize_url(match.group('img_url'))
        link_url = normalize_url(match.group('link_url'))
        if not any(token in img_url or token in link_url for token in match_substrings):
            return match.group(0)
        replacements += 1
        return build_image_markdown(
            alt=match.group('alt'),
            replacement_url=replacement_url,
            title=match.group('img_title'),
        )

    updated = LINKED_IMAGE_RE.sub(linked_replacer, updated)

    def image_replacer(match: re.Match[str]) -> str:
        nonlocal replacements
        img_url = normalize_url(match.group('img_url'))
        if not any(token in img_url for token in match_substrings):
            return match.group(0)
        replacements += 1
        return build_image_markdown(
            alt=match.group('alt'),
            replacement_url=replacement_url,
            title=match.group('img_title'),
        )

    updated = IMAGE_RE.sub(image_replacer, updated)
    return updated, replacements


def ensure_target_file(source: Path, target: Path, apply_changes: bool) -> str:
    if target.exists():
        return 'target_exists'
    if not source.exists():
        return 'source_missing'
    if apply_changes:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    return 'moved' if apply_changes else 'planned_move'


def process_entry(entry: dict, apply_changes: bool) -> dict:
    post_path = REPO_ROOT / entry['post']
    source_path = REPO_ROOT / entry['source_public_path']
    target_path = REPO_ROOT / entry['target_asset_path']

    lines = post_path.read_text(encoding='utf-8').splitlines(keepends=True)
    index = entry['line'] - 1
    original_line = lines[index]
    updated_line, replacements = transform_line(
        original_line,
        entry['match_substrings'],
        entry['replacement_url'],
    )

    file_result = ensure_target_file(source_path, target_path, apply_changes)

    line_changed = original_line != updated_line
    if apply_changes and line_changed:
        lines[index] = updated_line
        post_path.write_text(''.join(lines), encoding='utf-8')

    return {
        'id': entry['id'],
        'post': entry['post'],
        'line': entry['line'],
        'file_result': file_result,
        'url_replacements': replacements,
        'line_changed': line_changed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Move files and replace URLs in posts.',
    )
    args = parser.parse_args()

    mapping = load_map()
    results = [
        process_entry(entry, apply_changes=args.apply)
        for entry in mapping['entries']
    ]
    print(
        json.dumps(
            {
                'apply': args.apply,
                'entries': len(results),
                'results': results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
