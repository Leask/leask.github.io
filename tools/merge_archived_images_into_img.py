#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVED_DIR = ROOT / 'assets' / 'archived'
IMG_DIR = ROOT / 'assets' / 'img'
IMAGE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.bmp',
    '.tif',
    '.tiff',
    '.webp',
    '.mpo',
}


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def remove_empty_dirs(root: Path) -> int:
    removed = 0
    for path in sorted(root.rglob('*'), reverse=True):
        if not path.is_dir():
            continue
        try:
            path.rmdir()
        except OSError:
            continue
        removed += 1
    return removed


def main() -> int:
    counts: Counter[str] = Counter()
    moved: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []

    for source in sorted(ARCHIVED_DIR.rglob('*')):
        if not source.is_file():
            continue
        if source.name == '.DS_Store':
            source.unlink()
            counts['deleted_ds_store'] += 1
            continue
        if not is_image(source):
            counts['non_image_kept'] += 1
            continue

        rel = source.relative_to(ARCHIVED_DIR)
        target = IMG_DIR / rel
        if target.exists():
            skipped.append((rel.as_posix(), target.relative_to(ROOT).as_posix()))
            counts['skipped_existing'] += 1
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        source.rename(target)
        moved.append((rel.as_posix(), target.relative_to(ROOT).as_posix()))
        counts['moved_images'] += 1

    counts['removed_empty_dirs'] = remove_empty_dirs(ARCHIVED_DIR)

    print(f"moved_images {counts['moved_images']}")
    print(f"skipped_existing {counts['skipped_existing']}")
    print(f"non_image_kept {counts['non_image_kept']}")
    print(f"deleted_ds_store {counts['deleted_ds_store']}")
    print(f"removed_empty_dirs {counts['removed_empty_dirs']}")

    if moved:
        print('\nfirst_moved')
        for source, target in moved[:40]:
            print(f'{source} -> {target}')

    if skipped:
        print('\nfirst_skipped')
        for source, target in skipped[:40]:
            print(f'{source} -> {target}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
