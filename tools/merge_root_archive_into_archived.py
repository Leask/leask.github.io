#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import ExifTags, Image, ImageFile


ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT_ARCHIVE_DIR = Path('archive')
ARCHIVED_DIR = Path('assets/archived')

EXIF_TAGS = {value: key for key, value in ExifTags.TAGS.items()}
DATE_TAG_IDS = [
    EXIF_TAGS.get('DateTimeOriginal'),
    EXIF_TAGS.get('DateTimeDigitized'),
    EXIF_TAGS.get('DateTime'),
]

FOUR_DIGIT_DATE_PATTERNS = [
    re.compile(r'(?<!\d)(20\d{2})[-_](\d{1,2})[-_](\d{1,2})(?!\d)'),
    re.compile(r'(?<!\d)(19\d{2})[-_](\d{1,2})[-_](\d{1,2})(?!\d)'),
    re.compile(r'(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)'),
    re.compile(r'(?<!\d)(19\d{2})(\d{2})(\d{2})(?!\d)'),
]
TWO_DIGIT_DATE_PATTERN = re.compile(r'(?<!\d)(\d{2})-(\d{2})-(\d{2})(?!\d)')


@dataclass(frozen=True)
class DateChoice:
    folder: str
    source: str
    datetime_value: datetime | None


def parse_exif_date(raw_value: object) -> datetime | None:
    if not raw_value:
        return None
    if isinstance(raw_value, bytes):
        try:
            raw_value = raw_value.decode('utf-8', 'ignore')
        except Exception:
            return None
    value = str(raw_value).strip().replace('\x00', '')
    for fmt in ('%Y:%m:%d %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def pick_exif_date(path: Path) -> datetime | None:
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            for tag_id in DATE_TAG_IDS:
                if tag_id and tag_id in exif:
                    parsed = parse_exif_date(exif.get(tag_id))
                    if parsed:
                        return parsed
    except Exception:
        return None
    return None


def valid_date(year: int, month: int, day: int) -> datetime | None:
    try:
        return datetime(year, month, day)
    except ValueError:
        return None


def pick_filename_date(path: Path) -> datetime | None:
    name = path.name
    for pattern in FOUR_DIGIT_DATE_PATTERNS:
        match = pattern.search(name)
        if not match:
            continue
        year, month, day = (int(part) for part in match.groups())
        parsed = valid_date(year, month, day)
        if parsed:
            return parsed

    match = TWO_DIGIT_DATE_PATTERN.search(name)
    if not match:
        return None

    yy, month, day = (int(part) for part in match.groups())
    year = 2000 + yy if yy <= 30 else 1900 + yy
    return valid_date(year, month, day)


def choose_date(path: Path) -> DateChoice:
    exif_date = pick_exif_date(path)
    if exif_date:
        return DateChoice(
            folder=f'{exif_date.year:04d}/{exif_date.month:02d}',
            source='exif',
            datetime_value=exif_date,
        )

    filename_date = pick_filename_date(path)
    if filename_date:
        return DateChoice(
            folder=f'{filename_date.year:04d}/{filename_date.month:02d}',
            source='filename',
            datetime_value=filename_date,
        )

    return DateChoice(folder='undated', source='undated', datetime_value=None)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='move files')
    args = parser.parse_args()

    if not ROOT_ARCHIVE_DIR.exists():
        print('archive_exists 0')
        print('files_seen 0')
        print('apply', int(args.apply))
        return

    files = sorted(path for path in ROOT_ARCHIVE_DIR.iterdir() if path.is_file())
    counts_by_source: Counter[str] = Counter()
    counts_by_folder: Counter[str] = Counter()
    planned_moves: list[tuple[Path, Path, DateChoice]] = []

    for source_path in files:
        date_choice = choose_date(source_path)
        destination_dir = ARCHIVED_DIR / date_choice.folder
        destination_path = destination_dir / source_path.name
        if destination_path.exists():
            raise FileExistsError(
                f'destination already exists: {destination_path.as_posix()}'
            )
        planned_moves.append((source_path, destination_path, date_choice))
        counts_by_source[date_choice.source] += 1
        counts_by_folder[date_choice.folder] += 1

    if args.apply:
        for source_path, destination_path, _ in planned_moves:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source_path.as_posix(), destination_path.as_posix())
        try:
            ROOT_ARCHIVE_DIR.rmdir()
        except OSError:
            pass

    print('archive_exists', int(ROOT_ARCHIVE_DIR.exists()))
    print('files_seen', len(files))
    print('planned_moves', len(planned_moves))
    print('apply', int(args.apply))
    print('date_sources')
    for source, count in sorted(counts_by_source.items()):
        print(source, count)
    print('folder_distribution')
    for folder, count in sorted(counts_by_folder.items()):
        print(folder, count)
    print('sample_moves')
    for source_path, destination_path, date_choice in planned_moves[:40]:
        print(
            f'{source_path.as_posix()} -> {destination_path.as_posix()} '
            f'[{date_choice.source}]'
        )


if __name__ == '__main__':
    main()
