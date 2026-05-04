#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / '_posts'

ALWAYS_REMOVE = {
    'status',
    'published',
    'author_login',
    'author_email',
    'author_url',
    'wordpress_id',
    'wordpress_url',
    'date_gmt',
}
REMOVE_IF_EMPTY = {
    'categories',
    'tags',
    'comments',
}
TOP_LEVEL_KEY_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_-]*:')


@dataclass
class Block:
    key: str
    lines: list[str]


def split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        return '', text

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            return ''.join(lines[1:index]), ''.join(lines[index + 1 :])
        if line.startswith('---'):
            return ''.join(lines[1:index]), line[3:] + ''.join(lines[index + 1 :])

    return '', text


def parse_blocks(front_matter: str) -> list[Block]:
    blocks: list[Block] = []
    current: Block | None = None

    for line in front_matter.splitlines(keepends=True):
        if TOP_LEVEL_KEY_RE.match(line):
            key = line.split(':', 1)[0]
            if current is not None:
                blocks.append(current)
            current = Block(key=key, lines=[line])
        elif current is not None:
            current.lines.append(line)
        else:
            blocks.append(Block(key='', lines=[line]))

    if current is not None:
        blocks.append(current)

    return blocks


def block_is_empty(block: Block) -> bool:
    first = block.lines[0].strip()
    if first.endswith(': []'):
        return True

    if first != f'{block.key}:':
        return False

    for line in block.lines[1:]:
        if line.strip():
            return False
    return True


def compact_blank_lines(lines: list[str]) -> list[str]:
    compacted: list[str] = []
    previous_blank = False

    for line in lines:
        is_blank = not line.strip()
        if is_blank and previous_blank:
            continue
        compacted.append(line)
        previous_blank = is_blank

    while compacted and not compacted[0].strip():
        compacted.pop(0)
    while compacted and not compacted[-1].strip():
        compacted.pop()

    return compacted


def clean_front_matter(front_matter: str) -> str:
    front_matter = restore_orphan_comments(front_matter)
    kept: list[str] = []

    for block in parse_blocks(front_matter):
        if block.key in ALWAYS_REMOVE:
            continue
        if block.key in REMOVE_IF_EMPTY and block_is_empty(block):
            continue
        kept.extend(clean_block_lines(block))

    return ''.join(compact_blank_lines(kept))


def clean_block_lines(block: Block) -> list[str]:
    lines = list(block.lines)
    if block.key != 'comments':
        while lines and not lines[-1].strip():
            lines.pop()
    return lines


def restore_orphan_comments(front_matter: str) -> str:
    lines = front_matter.splitlines(keepends=True)
    restored: list[str] = []
    in_comments = False

    for line in lines:
        if line.startswith('- id:') and not in_comments:
            restored.append('comments:\n')
            in_comments = True
        elif TOP_LEVEL_KEY_RE.match(line):
            in_comments = line.startswith('comments:')

        restored.append(line)

    return ''.join(restored)


def clean_post(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    front_matter, body = split_front_matter(text)
    if not front_matter:
        return False

    cleaned = clean_front_matter(front_matter)
    new_text = f'---\n{cleaned.rstrip(chr(10))}\n---\n{body.lstrip(chr(10))}'
    if new_text == text:
        return False

    path.write_text(new_text, encoding='utf-8')
    return True


def main() -> int:
    changed = 0
    for path in sorted(POSTS_DIR.glob('*.md')):
        if clean_post(path):
            changed += 1

    print(f'cleaned_posts={changed}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
