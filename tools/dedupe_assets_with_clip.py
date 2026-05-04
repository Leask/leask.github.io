#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / '_posts'
DEFAULT_IMAGE_ROOTS = [
    ROOT / 'assets' / 'img',
    ROOT / 'assets' / 'archived',
]
REPORT_DIR = ROOT / 'reports' / 'asset_image_dedupe'
MODEL_NAME = 'clip-ViT-B-32'
MANUAL_EXCLUDED_PAIRS = {
    frozenset(
        (
            'assets/img/2011/12/14312141458.jpg',
            'assets/img/2011/12/13975561811.jpg',
        ),
    ),
    frozenset(
        (
            'assets/img/2010/09/picture11.png',
            'assets/img/2010/09/picture12.png',
        ),
    ),
}
ORIGINAL_HINT_RE = re.compile(
    r'原圖|原图|full\s*size|fullsize|原大|点击看大图|點擊看大圖|看大圖|看大图|大圖|大图',
    re.I,
)
LOCAL_ASSET_RE = re.compile(r'\((/assets/(?:img|archived)/[^)\s]+)')
SIZE_SUFFIX_RE = re.compile(r'[-_](?:\d{2,5}x\d{2,5}|thumb[a-z0-9]*)$', re.I)
PUNCT_RE = re.compile(r'[^a-z0-9]+')
EXACT_GROUP_MAX = 12
REVIEW_CLUSTER_MAX = 120
NN_COUNT = 10


@dataclass
class ImageRecord:
    path: str
    rel_path: str
    root_kind: str
    extension: str
    file_size: int
    width: int
    height: int
    pixels: int
    sha256: str
    dhash: str
    stem_key: str
    referenced_posts: list[str]
    referenced_count: int
    original_hint_posts: list[str]


@dataclass
class ClusterMember:
    path: str
    rel_path: str
    root_kind: str
    width: int
    height: int
    file_size: int
    extension: str
    referenced_count: int
    original_hint_posts: list[str]
    quality_rank: list[float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Visual dedupe candidate discovery for assets images.',
    )
    parser.add_argument(
        '--report-dir',
        type=Path,
        default=REPORT_DIR,
        help='Directory for JSON and HTML outputs.',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=REVIEW_CLUSTER_MAX,
        help='Maximum review clusters to render in the HTML report.',
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Embedding batch size.',
    )
    parser.add_argument(
        '--apply-safe',
        action='store_true',
        help='Apply safe no-markdown-change dedupe actions.',
    )
    parser.add_argument(
        '--apply-reviewed-internal',
        action='store_true',
        help='Apply reviewed img-to-img merges and rewrite post refs.',
    )
    return parser.parse_args()


def is_image_path(path: Path) -> bool:
    return path.suffix.lower() in {
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def compute_dhash(path: Path) -> str:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        gray = image.convert('L').resize((9, 8))
        pixels = np.asarray(gray, dtype=np.int16)
    diff = pixels[:, 1:] > pixels[:, :-1]
    value = 0
    for bit in diff.flatten():
        value = (value << 1) | int(bit)
    return f'{value:016x}'


def grayscale_mae_64(left_path: str, right_path: str) -> float:
    def load(path: str) -> np.ndarray:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert('L').resize((64, 64))
            return np.asarray(image, dtype=np.float32)

    left = load(left_path)
    right = load(right_path)
    return float(np.mean(np.abs(left - right)))


def dhash_distance(left: str, right: str) -> int:
    return int(int(left, 16) ^ int(right, 16)).bit_count()


def stem_key(path: Path) -> str:
    value = path.stem.lower()
    value = SIZE_SUFFIX_RE.sub('', value)
    value = PUNCT_RE.sub('', value)
    return value


def collect_post_refs() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    asset_to_posts: dict[str, list[str]] = defaultdict(list)
    asset_to_original_posts: dict[str, list[str]] = defaultdict(list)
    for post_path in POSTS_DIR.glob('*.md'):
        text = post_path.read_text(encoding='utf-8', errors='ignore')
        refs = sorted(set(LOCAL_ASSET_RE.findall(text)))
        if not refs:
            continue
        has_original_hint = bool(ORIGINAL_HINT_RE.search(text))
        for ref in refs:
            asset_to_posts[ref].append(post_path.name)
            if has_original_hint:
                asset_to_original_posts[ref].append(post_path.name)
    return asset_to_posts, asset_to_original_posts


def collect_images() -> tuple[list[ImageRecord], list[dict[str, str]]]:
    asset_to_posts, asset_to_original_posts = collect_post_refs()
    records: list[ImageRecord] = []
    bad_files: list[dict[str, str]] = []
    for root in DEFAULT_IMAGE_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob('*')):
            if not path.is_file() or not is_image_path(path):
                continue
            rel_path = str(path.relative_to(ROOT)).replace('\\', '/')
            asset_ref = f'/{rel_path}'
            try:
                with Image.open(path) as image:
                    image = ImageOps.exif_transpose(image)
                    width, height = image.size
            except (UnidentifiedImageError, OSError) as exc:
                bad_files.append(
                    {
                        'path': rel_path,
                        'error': type(exc).__name__,
                    },
                )
                continue
            records.append(
                ImageRecord(
                    path=str(path),
                    rel_path=rel_path,
                    root_kind='img' if '/assets/img/' in asset_ref else 'archived',
                    extension=path.suffix.lower(),
                    file_size=path.stat().st_size,
                    width=width,
                    height=height,
                    pixels=width * height,
                    sha256=sha256_file(path),
                    dhash=compute_dhash(path),
                    stem_key=stem_key(path),
                    referenced_posts=sorted(asset_to_posts.get(asset_ref, [])),
                    referenced_count=len(asset_to_posts.get(asset_ref, [])),
                    original_hint_posts=sorted(
                        asset_to_original_posts.get(asset_ref, []),
                    ),
                ),
            )
    return records, bad_files


def image_iter(paths: Iterable[str]) -> Iterable[Image.Image]:
    for path in paths:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert('RGB')
            yield image.copy()


def embed_images(
    model: SentenceTransformer,
    records: list[ImageRecord],
    batch_size: int,
) -> np.ndarray:
    embeddings: list[np.ndarray] = []
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        images = list(image_iter(record.path for record in batch))
        vectors = model.encode(
            images,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embeddings.append(vectors.astype(np.float32))
    return np.vstack(embeddings)


def aspect_delta(left: ImageRecord, right: ImageRecord) -> float:
    left_ratio = left.width / left.height
    right_ratio = right.width / right.height
    return abs(left_ratio - right_ratio) / max(left_ratio, right_ratio)


def pixel_ratio(left: ImageRecord, right: ImageRecord) -> float:
    return min(left.pixels, right.pixels) / max(left.pixels, right.pixels)


def same_original_post(left: ImageRecord, right: ImageRecord) -> bool:
    return bool(set(left.original_hint_posts) & set(right.original_hint_posts))


def same_referenced_post(left: ImageRecord, right: ImageRecord) -> bool:
    return bool(set(left.referenced_posts) & set(right.referenced_posts))


def is_candidate_pair(
    left: ImageRecord,
    right: ImageRecord,
    cosine_sim: float,
    hash_distance: int,
) -> tuple[bool, str]:
    aspect = aspect_delta(left, right)
    ratio = pixel_ratio(left, right)
    same_stem = bool(left.stem_key) and left.stem_key == right.stem_key
    exact = left.sha256 == right.sha256
    if exact:
        return True, 'exact'
    if same_original_post(left, right):
        return False, 'keep_original_pair'
    if hash_distance <= 4 and aspect <= 0.04 and (
        same_stem or cosine_sim >= 0.94
    ):
        return True, 'dhash'
    if cosine_sim >= 0.995 and aspect <= 0.05:
        return True, 'clip_very_high'
    if cosine_sim >= 0.989 and hash_distance <= 10 and aspect <= 0.08:
        return True, 'clip_hash'
    if same_stem and cosine_sim >= 0.98 and ratio >= 0.35 and aspect <= 0.15:
        return True, 'stem_clip'
    return False, ''


def quality_rank(record: ImageRecord) -> list[float]:
    lossless = 1 if record.extension in {'.png', '.tif', '.tiff'} else 0
    return [
        float(record.pixels),
        float(min(record.width, record.height)),
        float(lossless),
        float(record.file_size),
    ]


def group_exact_duplicates(records: list[ImageRecord]) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        groups[record.sha256].append(index)
    return [indices for indices in groups.values() if len(indices) > 1]


def build_neighbor_pairs(
    records: list[ImageRecord],
    embeddings: np.ndarray,
) -> tuple[list[dict[str, object]], list[list[int]]]:
    neighbors = min(len(records), NN_COUNT + 1)
    nn = NearestNeighbors(metric='cosine', n_neighbors=neighbors)
    nn.fit(embeddings)
    distances, indices = nn.kneighbors(embeddings)
    pair_map: dict[tuple[int, int], dict[str, object]] = {}
    for left_index, neighbor_list in enumerate(indices):
        for rank, right_index in enumerate(neighbor_list[1:], start=1):
            if right_index <= left_index:
                continue
            left = records[left_index]
            right = records[right_index]
            cosine_sim = float(1 - distances[left_index][rank])
            hash_distance = dhash_distance(left.dhash, right.dhash)
            if frozenset((left.rel_path, right.rel_path)) in MANUAL_EXCLUDED_PAIRS:
                continue
            candidate, reason = is_candidate_pair(
                left,
                right,
                cosine_sim,
                hash_distance,
            )
            if not candidate:
                continue
            mae_64 = grayscale_mae_64(left.path, right.path)
            if (
                left.width == right.width
                and left.height == right.height
                and mae_64 > 4.0
            ):
                continue
            pair_map[(left_index, right_index)] = {
                'left': int(left_index),
                'right': int(right_index),
                'cosine_similarity': round(cosine_sim, 6),
                'dhash_distance': int(hash_distance),
                'aspect_delta': round(aspect_delta(left, right), 6),
                'pixel_ratio': round(pixel_ratio(left, right), 6),
                'mae_64': round(mae_64, 4),
                'reason': reason,
            }
    parent = list(range(len(records)))

    def find(node: int) -> int:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for pair in pair_map.values():
        union(int(pair['left']), int(pair['right']))

    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        components[find(index)].append(index)
    clusters = [group for group in components.values() if len(group) > 1]
    pairs = sorted(
        pair_map.values(),
        key=lambda item: (
            item['reason'] != 'exact',
            -float(item['cosine_similarity']),
            item['dhash_distance'],
        ),
    )
    return pairs, clusters


def cluster_member(record: ImageRecord) -> ClusterMember:
    return ClusterMember(
        path=record.path,
        rel_path=record.rel_path,
        root_kind=record.root_kind,
        width=record.width,
        height=record.height,
        file_size=record.file_size,
        extension=record.extension,
        referenced_count=record.referenced_count,
        original_hint_posts=record.original_hint_posts,
        quality_rank=quality_rank(record),
    )


def summarize_cluster(records: list[ImageRecord], indices: list[int]) -> dict[str, object]:
    members = [records[index] for index in indices]
    members.sort(key=quality_rank, reverse=True)
    winner = members[0]
    touches_img = any(member.root_kind == 'img' for member in members)
    has_original_keep = any(member.original_hint_posts for member in members)
    same_post_refs = False
    post_ref_counts: Counter[str] = Counter()
    for member in members:
        post_ref_counts.update(member.referenced_posts)
    same_post_refs = any(count > 1 for count in post_ref_counts.values())
    referenced_members = [member for member in members if member.referenced_count]
    if same_post_refs or (has_original_keep and len(referenced_members) > 1):
        action = 'keep_variants'
    elif touches_img:
        action = 'review_merge_into_img'
    else:
        action = 'archived_only'
    return {
        'winner': winner.rel_path,
        'action': action,
        'members': [asdict(cluster_member(member)) for member in members],
        'max_pixels': winner.pixels,
    }


def file_url(path: str) -> str:
    return Path(path).resolve().as_uri()


def render_report(
    report_dir: Path,
    clusters: list[dict[str, object]],
    exact_groups: list[dict[str, object]],
    summary: dict[str, object],
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    html_path = report_dir / 'index.html'
    sections: list[str] = []
    for title, items in (
        ('Exact duplicates', exact_groups),
        ('Review clusters', clusters),
    ):
        cards: list[str] = []
        for cluster in items:
            members_html: list[str] = []
            for member in cluster['members']:
                label = (
                    f"{member['rel_path']}<br>"
                    f"{member['width']}x{member['height']} | "
                    f"{member['file_size']} bytes | "
                    f"refs {member['referenced_count']}"
                )
                if member['original_hint_posts']:
                    label += '<br><strong>keep original/full-size pair</strong>'
                members_html.append(
                    '<figure>'
                    f"<img src=\"{html.escape(file_url(str(ROOT / member['rel_path'])))}\" "
                    'loading="lazy">'
                    f'<figcaption>{label}</figcaption>'
                    '</figure>',
                )
            cards.append(
                '<section class="cluster">'
                f"<h3>{html.escape(cluster['winner'])}</h3>"
                f"<p>action: {html.escape(cluster['action'])}</p>"
                '<div class="grid">'
                + ''.join(members_html)
                + '</div></section>',
            )
        sections.append(
            f'<h2>{html.escape(title)}</h2>' + ''.join(cards or ['<p>None.</p>']),
        )
    summary_list = ''.join(
        f'<li>{html.escape(str(key))}: {html.escape(str(value))}</li>'
        for key, value in summary.items()
    )
    html_text = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Asset image dedupe report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, sans-serif;
      margin: 24px;
      line-height: 1.4;
      color: #111827;
      background: #f9fafb;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 16px;
      align-items: start;
    }}
    .cluster {{
      margin: 20px 0 32px;
      padding: 16px;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      background: white;
    }}
    figure {{
      margin: 0;
      padding: 12px;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      background: #f8fafc;
    }}
    img {{
      display: block;
      width: 100%;
      max-height: 260px;
      object-fit: contain;
      background: #e5e7eb;
    }}
    figcaption {{
      margin-top: 8px;
      font-size: 12px;
      word-break: break-word;
    }}
    ul {{
      padding-left: 20px;
    }}
  </style>
</head>
<body>
  <h1>Asset image dedupe report</h1>
  <ul>{summary_list}</ul>
  {''.join(sections)}
</body>
</html>
'''
    html_path.write_text(html_text, encoding='utf-8')


def safe_sync_file(src: Path, dst: Path) -> None:
    dst.write_bytes(src.read_bytes())


def apply_safe_actions(clusters: list[dict[str, object]]) -> dict[str, int]:
    results: Counter[str] = Counter()
    for cluster in clusters:
        action = cluster['action']
        members = cluster['members']
        winner = members[0]
        root_kinds = {member['root_kind'] for member in members}
        if action == 'keep_variants':
            results['kept_variants'] += 1
            continue
        if action == 'review_merge_into_img':
            if root_kinds == {'img'}:
                referenced_members = [
                    member for member in members if member['referenced_count']
                ]
                if len(referenced_members) == 1:
                    winner_path = ROOT / winner['rel_path']
                    for member in members[1:]:
                        if member['referenced_count']:
                            results['skipped_referenced_img'] += 1
                            continue
                        (ROOT / member['rel_path']).unlink()
                        results['deleted_img_derivatives'] += 1
                    continue
                results['skipped_img_only_clusters'] += 1
                continue
            if root_kinds == {'archived'}:
                winner_path = ROOT / winner['rel_path']
                for member in members[1:]:
                    if member['referenced_count']:
                        results['skipped_referenced_archived'] += 1
                        continue
                    (ROOT / member['rel_path']).unlink()
                    results['deleted_archived_duplicates'] += 1
                continue
            if root_kinds == {'img', 'archived'}:
                img_members = [member for member in members if member['root_kind'] == 'img']
                archived_members = [
                    member for member in members if member['root_kind'] == 'archived'
                ]
                if winner['root_kind'] == 'img':
                    for member in archived_members:
                        if member['referenced_count']:
                            results['skipped_referenced_archived'] += 1
                            continue
                        (ROOT / member['rel_path']).unlink()
                        results['deleted_archived_duplicates'] += 1
                    continue
                if (
                    winner['root_kind'] == 'archived'
                    and len(img_members) == 1
                    and winner['extension'] == img_members[0]['extension']
                ):
                    winner_path = ROOT / winner['rel_path']
                    img_path = ROOT / img_members[0]['rel_path']
                    safe_sync_file(winner_path, img_path)
                    results['promoted_archived_over_img'] += 1
                    for member in archived_members:
                        if member['referenced_count']:
                            results['skipped_referenced_archived'] += 1
                            continue
                        (ROOT / member['rel_path']).unlink()
                        results['deleted_archived_duplicates'] += 1
                    continue
                results['skipped_complex_cross_root_clusters'] += 1
                continue
        if action == 'archived_only':
            for member in members[1:]:
                if member['referenced_count']:
                    results['skipped_referenced_archived'] += 1
                    continue
                (ROOT / member['rel_path']).unlink()
                results['deleted_archived_duplicates'] += 1
            continue
        results['skipped_unknown_actions'] += 1
    return dict(results)


def apply_reviewed_internal_merges(clusters: list[dict[str, object]]) -> dict[str, int]:
    results: Counter[str] = Counter()
    replacements: dict[str, str] = {}
    for cluster in clusters:
        if cluster['action'] != 'review_merge_into_img':
            continue
        members = cluster['members']
        if {member['root_kind'] for member in members} != {'img'}:
            continue
        winner = members[0]
        winner_ref = '/' + winner['rel_path']
        for loser in members[1:]:
            loser_ref = '/' + loser['rel_path']
            replacements[loser_ref] = winner_ref

    touched_posts = 0
    for post_path in POSTS_DIR.glob('*.md'):
        text = post_path.read_text(encoding='utf-8', errors='ignore')
        updated = text
        for loser_ref, winner_ref in replacements.items():
            updated = updated.replace(loser_ref, winner_ref)
        if updated != text:
            post_path.write_text(updated, encoding='utf-8')
            touched_posts += 1
    results['updated_posts'] = touched_posts

    for loser_ref, winner_ref in replacements.items():
        loser_path = ROOT / loser_ref.lstrip('/')
        if not loser_path.exists():
            continue
        still_referenced = False
        for post_path in POSTS_DIR.glob('*.md'):
            text = post_path.read_text(encoding='utf-8', errors='ignore')
            if loser_ref in text:
                still_referenced = True
                break
        if still_referenced:
            results['skipped_still_referenced'] += 1
            continue
        loser_path.unlink()
        results['deleted_internal_duplicates'] += 1
    return dict(results)


def main() -> int:
    args = parse_args()
    records, bad_files = collect_images()
    model = SentenceTransformer(MODEL_NAME)
    embeddings = embed_images(model, records, batch_size=args.batch_size)
    exact_indices = group_exact_duplicates(records)
    pairs, cluster_indices = build_neighbor_pairs(records, embeddings)

    exact_groups: list[dict[str, object]] = []
    for indices in exact_indices[:EXACT_GROUP_MAX]:
        exact_groups.append(
            {
                'winner': records[indices[0]].rel_path,
                'action': 'exact_duplicate',
                'members': [
                    asdict(cluster_member(records[index]))
                    for index in sorted(
                        indices,
                        key=lambda item: quality_rank(records[item]),
                        reverse=True,
                    )
                ],
            },
        )

    review_clusters = sorted(
        (summarize_cluster(records, indices) for indices in cluster_indices),
        key=lambda item: (
            item['action'] == 'keep_variants',
            -int(item['max_pixels']),
            -len(item['members']),
        ),
    )[: args.limit]

    report_dir = args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / 'inventory.json').write_text(
        json.dumps(
            {
                'records': [asdict(record) for record in records],
                'bad_files': bad_files,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    (report_dir / 'pairs.json').write_text(
        json.dumps(pairs, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    (report_dir / 'clusters.json').write_text(
        json.dumps(
            {
                'exact_groups': exact_groups,
                'review_clusters': review_clusters,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    summary = {
        'model': MODEL_NAME,
        'images_scanned': len(records),
        'bad_files': len(bad_files),
        'exact_duplicate_groups': len(exact_indices),
        'candidate_pairs': len(pairs),
        'candidate_clusters': len(cluster_indices),
        'rendered_clusters': len(review_clusters),
        'posts_with_original_hint': sum(
            1 for record in records if record.original_hint_posts
        ),
    }
    (report_dir / 'summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    render_report(report_dir, review_clusters, exact_groups, summary)
    if args.apply_safe:
        summary['apply_safe'] = apply_safe_actions(review_clusters)
    if args.apply_reviewed_internal:
        summary['apply_reviewed_internal'] = apply_reviewed_internal_merges(
            review_clusters,
        )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
