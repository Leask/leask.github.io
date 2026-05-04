#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = REPO_ROOT / '_posts'

TOKEN_TO_NAME = {
    '12dzbxqhdl': 'Far Away From Home.mp3',
    '1bp1xgjo49': 'Spring_Memory.part3.rar',
    '5ztbfrkf4x': '偶然遇见(荃主题曲).mp3',
    '787v5aons8': '4008_onffline.scpt',
    '8816rp351b': 'iSync_Siemens_Plus_v2.3.1.dmg',
    'a1rph9ln67': 'Zhen Shou Ai Qing.mp3',
    'fvfh57d0e2': 'SX1_RU06_LSK_UNLOCK.part1.rar',
    'haqemtlxhh': 'Spring_Memory.part1.rar',
    'hi6xl35uk0': 'SX1_RU06_LSK_UNLOCK.part2.rar',
    'ifp60mar57': 'Moonlight Shadow.mp3',
    'junjze9kla': 'How Can I Not Love You.mp3',
    'ki5smdhyot': 'iPhone_Leask.zip',
    'l37jab3mvs': 'FrontRow Enabler 1.3.1.dmg',
    'qg9ro73ja4': 'Spring_Memory.part2.rar',
    'r89rv1rgp1': 'Lost Without You.zip',
    'ts2vjxdn1o': 'Spring_Memory.part5.rar',
    'v1pvg4hllx': 'Aperture_1.5k_Leask.dmg',
    'xuif6udrzx': 'Spring_Memory.part4.rar',
    'y83rn3arj3': 'iPod_Box_Design.zip',
}


def modern_url(token: str) -> str:
    return f'https://app.box.com/s/{token}'


def replace_preview_link(text: str, token: str, name: str) -> str:
    url = modern_url(token)
    pattern = re.compile(
        r'\[!\[\]\(http://www\.box\.net/lite/'
        rf'(?:image|thumb)/{re.escape(token)}(?:\.[^)]+)?\)\]'
        rf'\(http://www\.box\.net/lite/{re.escape(token)}\)'
    )
    return pattern.sub(f'[{name}]({url})', text)


def replace_exact_markdown_links(text: str, token: str) -> str:
    url = modern_url(token)
    variants = [
        f'http://www.box.net/public/{token}',
        f'http://www.box.net/shared/{token}',
        f'http://www.boxcn.net/shared/{token}',
        f'http://www.box.net/lite/{token}',
    ]
    for old in variants:
        text = text.replace(f'[{old}]({old})', f'[{url}]({url})')
        text = text.replace(
            f'[{old}]({old} "{old}")',
            f'[{url}]({url} "{url}")',
        )
        text = text.replace(
            f'[{old}]({old} "http://www.box.net/shared/{token}")',
            f'[{url}]({url} "{url}")',
        )
    return text


def replace_modern_url_links_with_name(text: str, token: str, name: str) -> str:
    url = modern_url(token)
    text = text.replace(f'[{url}]({url})', f'[{name}]({url})')
    text = text.replace(f'[{url}]({url} "{url}")', f'[{name}]({url})')
    return text


def replace_plain_urls(text: str, token: str) -> str:
    url = modern_url(token)
    variants = [
        f'http://www.box.net/public/{token}',
        f'http://www.box.net/shared/{token}',
        f'http://www.boxcn.net/shared/{token}',
        f'http://www.box.net/lite/{token}',
    ]
    for old in variants:
        text = text.replace(old, url)
    return text


def replace_bare_url_lines(text: str, token: str, name: str) -> str:
    url = modern_url(token)
    pattern = re.compile(
        rf'^(?P<indent>\s*){re.escape(url)}(?P<trailing>\s*)$',
        re.MULTILINE,
    )
    return pattern.sub(
        lambda m: f'{m.group("indent")}[{name}]({url}){m.group("trailing")}',
        text,
    )


def main() -> int:
    changed = 0
    for post_path in sorted(POSTS_DIR.glob('*.md')):
        original = post_path.read_text(encoding='utf-8')
        updated = original
        for token, name in TOKEN_TO_NAME.items():
            updated = replace_preview_link(updated, token, name)
            updated = replace_exact_markdown_links(updated, token)
            updated = replace_plain_urls(updated, token)
            updated = replace_modern_url_links_with_name(updated, token, name)
            updated = replace_bare_url_lines(updated, token, name)
        if updated != original:
            post_path.write_text(updated, encoding='utf-8')
            changed += 1

    print(
        json.dumps(
            {
                'changed_posts': changed,
                'tokens': len(TOKEN_TO_NAME),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
