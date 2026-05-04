#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFile, ImageOps


ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT_ARCHIVE_DIR = Path('archive')
ASSET_DIR = Path('assets/img')
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

EXTRA_EXT_RE = re.compile(r'\.(png|jpg|jpeg|gif|bmp|tif|tiff)$', re.I)
SIZE_SUFFIX_RE = re.compile(r'-(\d+)x(\d+)$')
THUMB_SUFFIX_RE = re.compile(r'(_thumb[0-9a-z]+|5b[0-9a-z]+)$', re.I)
NONWORD_RE = re.compile(r'[^0-9a-z\u4e00-\u9fff]+', re.I)


@dataclass(frozen=True)
class ImageInfo:
    path: Path
    loose_key: str
    family: str
    width: int
    height: int
    file_size: int
    sha256: str
    ahash: int
    norm64: np.ndarray

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def quality_key(self) -> tuple[int, int]:
        return (self.area, self.file_size)

    @property
    def dims(self) -> tuple[int, int]:
        return (self.width, self.height)


@dataclass(frozen=True)
class CandidateMatch:
    archive: ImageInfo
    asset: ImageInfo
    hash_distance: int
    ratio: float
    mae: float


@dataclass
class Result:
    archive_images_before: int = 0
    exact_sha_duplicates_removed: int = 0
    accepted_duplicate_archive_files: int = 0
    asset_paths_touched: int = 0
    assets_replaced_from_archive: int = 0
    archive_duplicates_removed: int = 0
    unresolved_candidates: int = 0
    remaining_archive_images: int = 0


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def normalize_loose_key(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = EXTRA_EXT_RE.sub('', stem)
    stem = SIZE_SUFFIX_RE.sub('', stem)
    stem = THUMB_SUFFIX_RE.sub('', stem)
    stem = stem.replace('+', '')
    stem = NONWORD_RE.sub('', stem)
    return stem


def format_family(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {'.jpg', '.jpeg'}:
        return 'jpeg'
    if ext in {'.tif', '.tiff'}:
        return 'tiff'
    return ext.lstrip('.')


def sha256_for(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def open_image(path: Path) -> Image.Image:
    image = Image.open(path)
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass
    return image


def read_dimensions(path: Path) -> tuple[int, int]:
    with open_image(path) as image:
        return image.size


def average_hash(path: Path) -> int:
    with open_image(path) as image:
        image = image.convert('L').resize((8, 8))
        pixels = list(image.getdata())
        average = sum(pixels) / len(pixels)
        bits = ''.join('1' if pixel >= average else '0' for pixel in pixels)
        return int(bits, 2)


def normalized_grayscale(path: Path) -> np.ndarray:
    with open_image(path) as image:
        image = image.convert('L').resize((64, 64))
        return np.asarray(image, dtype=np.float32)


def hash_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


def dimension_ratio(left: tuple[int, int], right: tuple[int, int]) -> float:
    return max(
        left[0] / right[0],
        right[0] / left[0],
        left[1] / right[1],
        right[1] / left[1],
    )


def build_info(path: Path) -> ImageInfo:
    width, height = read_dimensions(path)
    return ImageInfo(
        path=path,
        loose_key=normalize_loose_key(path.name),
        family=format_family(path),
        width=width,
        height=height,
        file_size=path.stat().st_size,
        sha256=sha256_for(path),
        ahash=average_hash(path),
        norm64=normalized_grayscale(path),
    )


def mean_abs_difference(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.abs(left - right)))


def collect_assets() -> list[ImageInfo]:
    return [
        build_info(path)
        for path in sorted(ASSET_DIR.rglob('*'))
        if is_image(path)
    ]


def collect_archive() -> list[ImageInfo]:
    return [
        build_info(path)
        for path in sorted(ROOT_ARCHIVE_DIR.iterdir())
        if is_image(path)
    ]


def choose_best_by_quality(candidates: list[ImageInfo]) -> ImageInfo:
    return max(candidates, key=lambda info: info.quality_key)


def copy_archive_to_asset(archive: ImageInfo, asset: ImageInfo, apply: bool) -> None:
    if not apply:
        return
    temp_path = asset.path.with_suffix(asset.path.suffix + '.tmp')
    shutil.copy2(archive.path, temp_path)
    temp_path.replace(asset.path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='write changes')
    parser.add_argument(
        '--threshold',
        type=int,
        default=7,
        help='max average-hash Hamming distance for same-key duplicate',
    )
    parser.add_argument(
        '--cross-name-threshold',
        type=int,
        default=1,
        help='max average-hash Hamming distance for cross-name duplicate',
    )
    parser.add_argument(
        '--cross-name-mae',
        type=float,
        default=5.0,
        help='max normalized grayscale MAE for cross-name duplicate',
    )
    args = parser.parse_args()

    assets = collect_assets()
    archive_images = collect_archive()

    assets_by_key: dict[str, list[ImageInfo]] = defaultdict(list)
    assets_by_sha: dict[str, list[ImageInfo]] = defaultdict(list)
    assets_by_path = {info.path: info for info in assets}
    asset_keys = {info.loose_key for info in assets}

    for asset in assets:
        assets_by_key[asset.loose_key].append(asset)
        assets_by_sha[asset.sha256].append(asset)

    result = Result(archive_images_before=len(archive_images))
    exact_sha_archive_paths: set[Path] = set()
    grouped_matches: dict[Path, list[CandidateMatch]] = defaultdict(list)
    unresolved_archive_paths: set[Path] = set()
    matched_archive_paths: set[Path] = set()

    for archive in archive_images:
        if archive.sha256 in assets_by_sha:
            exact_sha_archive_paths.add(archive.path)
            continue

        candidates = assets_by_key.get(archive.loose_key, [])
        if not candidates:
            continue

        ranked: list[tuple[int, int, float, Path, ImageInfo]] = []
        for asset in candidates:
            distance = hash_distance(archive.ahash, asset.ahash)
            family_penalty = 0 if archive.family == asset.family else 1
            ratio = dimension_ratio(archive.dims, asset.dims)
            ranked.append(
                (distance, family_penalty, ratio, asset.path, asset),
            )
        ranked.sort()
        distance, _, ratio, _, best_asset = ranked[0]
        if distance > args.threshold:
            continue

        grouped_matches[best_asset.path].append(
            CandidateMatch(
                archive=archive,
                asset=best_asset,
                hash_distance=distance,
                ratio=ratio,
                mae=mean_abs_difference(archive.norm64, best_asset.norm64),
            ),
        )
        matched_archive_paths.add(archive.path)

    for archive in archive_images:
        if archive.path in exact_sha_archive_paths:
            continue
        if archive.loose_key in asset_keys:
            continue
        if archive.path in matched_archive_paths:
            continue

        best_cross_name: tuple[float, int, float, str, ImageInfo] | None = None
        for asset in assets:
            if archive.family != asset.family:
                continue
            ratio = dimension_ratio(archive.dims, asset.dims)
            if ratio > 6.0:
                continue
            distance = hash_distance(archive.ahash, asset.ahash)
            if distance > args.cross_name_threshold:
                continue
            mae = mean_abs_difference(archive.norm64, asset.norm64)
            if mae > args.cross_name_mae:
                continue
            candidate = (mae, distance, ratio, asset.path.as_posix(), asset)
            if best_cross_name is None or candidate < best_cross_name:
                best_cross_name = candidate

        if best_cross_name is None:
            continue

        mae, distance, ratio, _, best_asset = best_cross_name
        grouped_matches[best_asset.path].append(
            CandidateMatch(
                archive=archive,
                asset=best_asset,
                hash_distance=distance,
                ratio=ratio,
                mae=mae,
            ),
        )
        matched_archive_paths.add(archive.path)

    result.exact_sha_duplicates_removed = len(exact_sha_archive_paths)
    result.accepted_duplicate_archive_files = (
        sum(len(matches) for matches in grouped_matches.values())
        + len(exact_sha_archive_paths)
    )
    result.asset_paths_touched = len(grouped_matches)

    archive_paths_to_delete: set[Path] = set(exact_sha_archive_paths)

    for asset_path, matches in grouped_matches.items():
        asset = assets_by_path[asset_path]
        compatible = [
            match.archive
            for match in matches
            if match.archive.family == asset.family
        ]

        incompatible = [
            match.archive
            for match in matches
            if match.archive.family != asset.family
        ]
        unresolved_archive_paths.update(info.path for info in incompatible)

        if not compatible:
            continue

        best_candidate = choose_best_by_quality([asset] + compatible)
        if best_candidate.path != asset.path:
            copy_archive_to_asset(best_candidate, asset, args.apply)
            result.assets_replaced_from_archive += 1

        archive_paths_to_delete.update(info.path for info in compatible)

    if args.apply:
        for path in sorted(archive_paths_to_delete):
            if path.exists():
                path.unlink()

    result.archive_duplicates_removed = len(archive_paths_to_delete)
    result.unresolved_candidates = len(unresolved_archive_paths)

    remaining_archive_images = [
        path
        for path in sorted(ROOT_ARCHIVE_DIR.iterdir())
        if is_image(path)
        and path not in archive_paths_to_delete
    ]
    result.remaining_archive_images = len(remaining_archive_images)

    print(f'archive_images_before {result.archive_images_before}')
    print(f'exact_sha_duplicates_removed {result.exact_sha_duplicates_removed}')
    print(
        'accepted_duplicate_archive_files '
        f'{result.accepted_duplicate_archive_files}'
    )
    print(f'asset_paths_touched {result.asset_paths_touched}')
    print(f'assets_replaced_from_archive {result.assets_replaced_from_archive}')
    print(f'archive_duplicates_removed {result.archive_duplicates_removed}')
    print(f'unresolved_candidates {result.unresolved_candidates}')
    print(f'remaining_archive_images {result.remaining_archive_images}')
    print(f'apply {int(args.apply)}')

    if remaining_archive_images:
        print('remaining_archive_sample')
        for path in remaining_archive_images[:120]:
            print(path.as_posix())


if __name__ == '__main__':
    main()
