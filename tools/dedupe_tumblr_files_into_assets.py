#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFile, ImageOps


ImageFile.LOAD_TRUNCATED_IMAGES = True

TUMBLR_DIR = Path('tumblr_files')
ASSET_DIR = Path('assets/img')
ARCHIVED_DIR = Path('assets/archived')
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


@dataclass(frozen=True)
class ImageInfo:
    path: Path
    family: str
    width: int
    height: int
    file_size: int
    sha256: str
    ahash: int
    dhash: int
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
    source: ImageInfo
    target: ImageInfo
    target_kind: str
    ahash_distance: int
    dhash_distance: int
    ratio: float
    mae: float

    @property
    def sort_key(self) -> tuple[int, int, float, float, int]:
        kind_penalty = 0 if self.target_kind == 'assets_img' else 1
        return (
            self.ahash_distance,
            self.dhash_distance,
            self.mae,
            self.ratio,
            kind_penalty,
        )


@dataclass
class Result:
    tumblr_images_before: int = 0
    assets_img_matches: int = 0
    assets_img_replaced: int = 0
    assets_archived_matches: int = 0
    assets_archived_replaced: int = 0
    tumblr_internal_groups_removed: int = 0
    tumblr_removed_total: int = 0
    unresolved_better_sources: int = 0
    tumblr_images_remaining: int = 0


def is_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


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
        pixels = np.asarray(image, dtype=np.float32).reshape(-1).tolist()
        average = sum(pixels) / len(pixels)
        bits = ''.join('1' if pixel >= average else '0' for pixel in pixels)
        return int(bits, 2)


def difference_hash(path: Path) -> int:
    with open_image(path) as image:
        image = image.convert('L').resize((9, 8))
        pixels = np.asarray(image, dtype=np.int16)
        bits = ''.join(
            '1' if pixels[row, col] >= pixels[row, col + 1] else '0'
            for row in range(8)
            for col in range(8)
        )
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


def mean_abs_difference(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(np.abs(left - right)))


def build_info(path: Path) -> ImageInfo:
    width, height = read_dimensions(path)
    return ImageInfo(
        path=path,
        family=format_family(path),
        width=width,
        height=height,
        file_size=path.stat().st_size,
        sha256=sha256_for(path),
        ahash=average_hash(path),
        dhash=difference_hash(path),
        norm64=normalized_grayscale(path),
    )


def collect_images(root: Path) -> list[ImageInfo]:
    return [build_info(path) for path in sorted(root.rglob('*')) if is_image(path)]


def can_replace_content(source: ImageInfo, target: ImageInfo) -> bool:
    return source.family == target.family


def replace_target_with_source(
    source: ImageInfo,
    target: ImageInfo,
    apply: bool,
) -> bool:
    if not can_replace_content(source, target):
        return False
    if apply:
        temp_path = target.path.with_suffix(target.path.suffix + '.tmp')
        shutil.copy2(source.path, temp_path)
        temp_path.replace(target.path)
    return True


def remove_source(source: ImageInfo, apply: bool) -> None:
    if apply:
        source.path.unlink()


def find_best_external_match(
    source: ImageInfo,
    target_kind: str,
    targets: list[ImageInfo],
    max_ahash: int,
    max_dhash: int,
    max_mae: float,
    max_ratio: float,
) -> CandidateMatch | None:
    best: CandidateMatch | None = None
    for target in targets:
        ratio = dimension_ratio(source.dims, target.dims)
        if ratio > max_ratio:
            continue
        ahash_distance = hash_distance(source.ahash, target.ahash)
        if ahash_distance > max_ahash:
            continue
        dhash_distance = hash_distance(source.dhash, target.dhash)
        if dhash_distance > max_dhash:
            continue
        mae = mean_abs_difference(source.norm64, target.norm64)
        if mae > max_mae:
            continue
        match = CandidateMatch(
            source=source,
            target=target,
            target_kind=target_kind,
            ahash_distance=ahash_distance,
            dhash_distance=dhash_distance,
            ratio=ratio,
            mae=mae,
        )
        if best is None or match.sort_key < best.sort_key:
            best = match
    return best


def classify_targets(
    sources: list[ImageInfo],
    assets_img: list[ImageInfo],
    assets_archived: list[ImageInfo],
    max_ahash: int,
    max_dhash: int,
    max_mae: float,
    max_ratio: float,
) -> dict[Path, CandidateMatch]:
    matches: dict[Path, CandidateMatch] = {}
    for source in sources:
        best: CandidateMatch | None = None
        for target_kind, targets in (
            ('assets_img', assets_img),
            ('assets_archived', assets_archived),
        ):
            match = find_best_external_match(
                source=source,
                target_kind=target_kind,
                targets=targets,
                max_ahash=max_ahash,
                max_dhash=max_dhash,
                max_mae=max_mae,
                max_ratio=max_ratio,
            )
            if match is None:
                continue
            if best is None or match.sort_key < best.sort_key:
                best = match
        if best is not None:
            matches[source.path] = best
    return matches


def build_internal_groups(
    sources: list[ImageInfo],
    max_ahash: int,
    max_dhash: int,
    max_mae: float,
    max_ratio: float,
) -> list[list[ImageInfo]]:
    adjacency: dict[Path, set[Path]] = defaultdict(set)
    by_path = {source.path: source for source in sources}

    for index, left in enumerate(sources):
        for right in sources[index + 1:]:
            ratio = dimension_ratio(left.dims, right.dims)
            if ratio > max_ratio:
                continue
            ahash_distance = hash_distance(left.ahash, right.ahash)
            if ahash_distance > max_ahash:
                continue
            dhash_distance = hash_distance(left.dhash, right.dhash)
            if dhash_distance > max_dhash:
                continue
            mae = mean_abs_difference(left.norm64, right.norm64)
            if mae > max_mae:
                continue
            adjacency[left.path].add(right.path)
            adjacency[right.path].add(left.path)

    groups: list[list[ImageInfo]] = []
    seen: set[Path] = set()
    for path in adjacency:
        if path in seen:
            continue
        stack = [path]
        component: list[ImageInfo] = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component.append(by_path[current])
            stack.extend(adjacency[current] - seen)
        if len(component) > 1:
            groups.append(component)
    return groups


def choose_best_by_quality(candidates: list[ImageInfo]) -> ImageInfo:
    return max(candidates, key=lambda info: info.quality_key)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='write changes')
    parser.add_argument(
        '--max-ahash',
        type=int,
        default=4,
        help='max average-hash Hamming distance for near duplicates',
    )
    parser.add_argument(
        '--max-dhash',
        type=int,
        default=6,
        help='max difference-hash Hamming distance for near duplicates',
    )
    parser.add_argument(
        '--max-mae',
        type=float,
        default=4.5,
        help='max normalized grayscale MAE for near duplicates',
    )
    parser.add_argument(
        '--max-ratio',
        type=float,
        default=1.02,
        help='max dimension ratio between duplicate candidates',
    )
    args = parser.parse_args()

    tumblr_images = collect_images(TUMBLR_DIR)
    assets_img = collect_images(ASSET_DIR)
    assets_archived = collect_images(ARCHIVED_DIR)

    result = Result(tumblr_images_before=len(tumblr_images))

    external_matches = classify_targets(
        sources=tumblr_images,
        assets_img=assets_img,
        assets_archived=assets_archived,
        max_ahash=args.max_ahash,
        max_dhash=args.max_dhash,
        max_mae=args.max_mae,
        max_ratio=args.max_ratio,
    )

    kept_for_internal: list[ImageInfo] = []
    replaced_targets: set[Path] = set()

    for source in tumblr_images:
        match = external_matches.get(source.path)
        if match is None:
            kept_for_internal.append(source)
            continue

        if match.target_kind == 'assets_img':
            result.assets_img_matches += 1
        else:
            result.assets_archived_matches += 1

        if source.quality_key > match.target.quality_key:
            replaced = replace_target_with_source(source, match.target, args.apply)
            if replaced:
                replaced_targets.add(match.target.path)
                if match.target_kind == 'assets_img':
                    result.assets_img_replaced += 1
                else:
                    result.assets_archived_replaced += 1
                result.tumblr_removed_total += 1
                remove_source(source, args.apply)
            else:
                result.unresolved_better_sources += 1
                kept_for_internal.append(source)
        else:
            result.tumblr_removed_total += 1
            remove_source(source, args.apply)

    internal_groups = build_internal_groups(
        sources=kept_for_internal,
        max_ahash=args.max_ahash,
        max_dhash=args.max_dhash,
        max_mae=args.max_mae,
        max_ratio=args.max_ratio,
    )
    internal_removed_paths: set[Path] = set()
    for group in internal_groups:
        best = choose_best_by_quality(group)
        removed = [info for info in group if info.path != best.path]
        if not removed:
            continue
        result.tumblr_internal_groups_removed += len(removed)
        result.tumblr_removed_total += len(removed)
        internal_removed_paths.update(info.path for info in removed)
        if args.apply:
            for info in removed:
                info.path.unlink()

    remaining = [
        path for path in sorted(TUMBLR_DIR.glob('*'))
        if is_image(path)
    ]
    result.tumblr_images_remaining = len(remaining)

    print(f'tumblr_images_before {result.tumblr_images_before}')
    print(f'assets_img_matches {result.assets_img_matches}')
    print(f'assets_img_replaced {result.assets_img_replaced}')
    print(f'assets_archived_matches {result.assets_archived_matches}')
    print(f'assets_archived_replaced {result.assets_archived_replaced}')
    print(f'tumblr_internal_groups_removed {result.tumblr_internal_groups_removed}')
    print(f'unresolved_better_sources {result.unresolved_better_sources}')
    print(f'tumblr_removed_total {result.tumblr_removed_total}')
    print(f'tumblr_images_remaining {result.tumblr_images_remaining}')
    print(f'apply {int(args.apply)}')

    if external_matches:
        print('external_matches')
        for source_path, match in sorted(external_matches.items()):
            print(
                f'{source_path.as_posix()} => {match.target_kind}:'
                f'{match.target.path.as_posix()} '
                f'ahash={match.ahash_distance} '
                f'dhash={match.dhash_distance} '
                f'mae={match.mae:.3f} '
                f'ratio={match.ratio:.4f}'
            )

    if internal_groups:
        print('internal_groups')
        for group in internal_groups:
            print('---')
            for info in sorted(group, key=lambda item: item.path.as_posix()):
                print(
                    f'{info.path.as_posix()} '
                    f'{info.width}x{info.height} size={info.file_size}'
                )


if __name__ == '__main__':
    main()
