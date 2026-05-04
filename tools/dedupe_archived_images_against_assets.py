#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps


ASSET_DIR = Path('assets/img')
ARCHIVE_DIR = Path('assets/archived')
IMAGE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.webp',
    '.bmp',
    '.tif',
    '.tiff',
}

SIZE_SUFFIX_RE = re.compile(r'-(\d+)x(\d+)$')
THUMB_SUFFIX_RE = re.compile(r'(_thumb[0-9a-z]+|5b[0-9a-z]+)$', re.I)
EXTRA_EXT_RE = re.compile(r'\.(png|jpg|jpeg|gif|bmp|tif|tiff)$', re.I)


@dataclass(frozen=True)
class ImageInfo:
    path: Path
    normalized_name: str
    width: int
    height: int
    file_size: int
    sha256: str

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def quality_key(self) -> tuple[int, int]:
        return (self.area, self.file_size)


@dataclass
class Result:
    archived_images_before: int = 0
    norm_name_duplicates_removed: int = 0
    exact_sha_duplicates_removed: int = 0
    assets_replaced_from_archive: int = 0
    unresolved_better_archive: int = 0
    kept_archived_images: int = 0
    removed_empty_dirs: int = 0


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def normalize_name(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = EXTRA_EXT_RE.sub('', stem)
    stem = SIZE_SUFFIX_RE.sub('', stem)
    stem = THUMB_SUFFIX_RE.sub('', stem)
    stem = re.sub(r'[_\-]+$', '', stem)
    return stem


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read_dimensions(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        return image.size


def build_image_info(path: Path) -> ImageInfo:
    width, height = read_dimensions(path)
    return ImageInfo(
        path=path,
        normalized_name=normalize_name(path.name),
        width=width,
        height=height,
        file_size=path.stat().st_size,
        sha256=sha256_for(path),
    )


def collect_images(root: Path) -> list[ImageInfo]:
    return [build_image_info(path) for path in sorted(root.rglob('*')) if is_image(path)]


def choose_best_asset(candidates: list[ImageInfo]) -> ImageInfo:
    return max(candidates, key=lambda info: info.quality_key)


def remove_file(path: Path, apply: bool) -> None:
    if apply:
        path.unlink()


def replace_asset_with_archive(
    archive_info: ImageInfo,
    asset_info: ImageInfo,
    apply: bool,
) -> bool:
    if archive_info.path.suffix.lower() != asset_info.path.suffix.lower():
        return False
    if apply:
        temp_path = asset_info.path.with_suffix(asset_info.path.suffix + '.tmp')
        shutil.copy2(archive_info.path, temp_path)
        temp_path.replace(asset_info.path)
        archive_info.path.unlink()
    return True


def prune_empty_directories(root: Path, apply: bool) -> int:
    removed = 0
    directories = sorted(
        (path for path in root.rglob('*') if path.is_dir()),
        reverse=True,
    )
    for directory in directories:
        if any(directory.iterdir()):
            continue
        removed += 1
        if apply:
            directory.rmdir()
    return removed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='write changes')
    args = parser.parse_args()

    assets = collect_images(ASSET_DIR)
    archived = collect_images(ARCHIVE_DIR)

    assets_by_name: dict[str, list[ImageInfo]] = defaultdict(list)
    assets_by_sha: dict[str, list[ImageInfo]] = defaultdict(list)
    for asset in assets:
        assets_by_name[asset.normalized_name].append(asset)
        assets_by_sha[asset.sha256].append(asset)

    result = Result(archived_images_before=len(archived))
    removed_archived_paths: set[Path] = set()
    kept_archived_paths: set[Path] = set()

    for archived_info in archived:
        candidates = assets_by_name.get(archived_info.normalized_name, [])
        if candidates:
            best_asset = choose_best_asset(candidates)
            if archived_info.quality_key > best_asset.quality_key:
                if replace_asset_with_archive(archived_info, best_asset, args.apply):
                    result.assets_replaced_from_archive += 1
                    removed_archived_paths.add(archived_info.path)
                else:
                    result.unresolved_better_archive += 1
                    kept_archived_paths.add(archived_info.path)
            else:
                result.norm_name_duplicates_removed += 1
                remove_file(archived_info.path, args.apply)
                removed_archived_paths.add(archived_info.path)
            continue

        if archived_info.sha256 in assets_by_sha:
            result.exact_sha_duplicates_removed += 1
            remove_file(archived_info.path, args.apply)
            removed_archived_paths.add(archived_info.path)
            continue

        kept_archived_paths.add(archived_info.path)

    result.kept_archived_images = len(kept_archived_paths)
    result.removed_empty_dirs = prune_empty_directories(ARCHIVE_DIR, args.apply)

    print(f'archived_images_before {result.archived_images_before}')
    print(f'norm_name_duplicates_removed {result.norm_name_duplicates_removed}')
    print(f'exact_sha_duplicates_removed {result.exact_sha_duplicates_removed}')
    print(f'assets_replaced_from_archive {result.assets_replaced_from_archive}')
    print(f'unresolved_better_archive {result.unresolved_better_archive}')
    print(f'kept_archived_images {result.kept_archived_images}')
    print(f'removed_empty_dirs {result.removed_empty_dirs}')
    print(f'apply {int(args.apply)}')

    if kept_archived_paths:
        print('remaining_archived_images')
        for path in sorted(kept_archived_paths):
            print(path.as_posix())


if __name__ == '__main__':
    main()
