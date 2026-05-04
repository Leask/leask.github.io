#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import re
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import yaml
from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / '_posts'
ASSETS_IMG_DIR = ROOT / 'assets' / 'img'
REPORT_DIR = ROOT / 'reports' / 'dead_image_asset_match'
MODEL_NAME = 'clip-ViT-B-32'
IMAGE_EXTENSIONS = {
    '.jpg',
    '.jpeg',
    '.png',
    '.gif',
    '.webp',
    '.svg',
    '.bmp',
    '.tif',
    '.tiff',
    '.mpo',
}
IMAGE_MAGIC_EXTENSIONS = (
    (b'\xff\xd8\xff', '.jpg'),
    (b'\x89PNG\r\n\x1a\n', '.png'),
    (b'GIF87a', '.gif'),
    (b'GIF89a', '.gif'),
    (b'RIFF', '.webp'),
    (b'<svg', '.svg'),
    (b'<?xml', '.svg'),
)
FENCE_RE = re.compile(r'^```.*?^```', re.M | re.S)
MD_IMAGE_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)', re.M)
HTML_IMG_RE = re.compile(
    r'<img\b[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>',
    re.I,
)
LOCAL_ASSET_RE = re.compile(r'(/assets/img/[^)\s\'"]+)')
MD_LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
HTML_TAG_RE = re.compile(r'<[^>]+>')
RAW_URL_RE = re.compile(r'https?://\S+')
SAFE_TOKEN_RE = re.compile(r'[^0-9a-z]+', re.I)
WHITESPACE_RE = re.compile(r'\s+')
FRONT_MATTER_RE = re.compile(r'\A---\n(.*?)\n---\n?', re.S)
SENTENCE_BREAK_RE = re.compile(r'[\r\n]+')
GENERIC_TOKENS = {
    'bmp',
    'gif',
    'img',
    'image',
    'images',
    'index',
    'jpeg',
    'jpg',
    'logo',
    'photo',
    'photos',
    'pic',
    'pics',
    'picture',
    'pictures',
    'png',
    'screen',
    'screenshot',
    'snapshot',
    'thumb',
    'tif',
    'tiff',
}
ImageFile.LOAD_TRUNCATED_IMAGES = True


@dataclass(frozen=True)
class CandidateImage:
    rel_path: str
    abs_path: str
    year: str
    month: str
    stem: str
    width: int
    height: int
    pixels: int
    file_size: int


@dataclass(frozen=True)
class ExternalImageOccurrence:
    occurrence_id: str
    post_name: str
    post_path: str
    title: str
    url: str
    alt_text: str
    line_number: int
    start: int
    end: int
    body: str


@dataclass(frozen=True)
class UrlStatus:
    ok: bool
    status: int
    content_type: str
    error: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Match dead external post images to unused assets/img candidates '
            'with CLIP text-image embeddings.'
        ),
    )
    parser.add_argument(
        '--report-dir',
        type=Path,
        default=REPORT_DIR,
        help='Directory for generated reports and caches.',
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Embedding batch size.',
    )
    parser.add_argument(
        '--concurrency',
        type=int,
        default=20,
        help='Parallel URL checks.',
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of candidates to keep per dead occurrence.',
    )
    parser.add_argument(
        '--report-limit',
        type=int,
        default=120,
        help='Max promising rows to render into HTML/Markdown.',
    )
    parser.add_argument(
        '--reuse-status-cache',
        action='store_true',
        help='Reuse existing URL status cache when present.',
    )
    parser.add_argument(
        '--match-profile',
        choices=('strict', 'relaxed'),
        default='strict',
        help='Candidate filtering profile for promising matches.',
    )
    return parser.parse_args()


def split_fenced_offsets(text: str) -> list[tuple[bool, int, str]]:
    parts: list[tuple[bool, int, str]] = []
    pos = 0
    for match in FENCE_RE.finditer(text):
        if match.start() > pos:
            parts.append((False, pos, text[pos:match.start()]))
        parts.append((True, match.start(), match.group(0)))
        pos = match.end()
    if pos < len(text):
        parts.append((False, pos, text[pos:]))
    return parts


def first_markdown_target(raw: str) -> tuple[str, str]:
    content = raw.strip()
    if content.startswith('<'):
        end = content.find('>')
        if end != -1:
            return content[1:end], content[end + 1 :]
    match = re.match(r'(\S+)(.*)\Z', content, re.S)
    if not match:
        return '', ''
    return match.group(1).strip('"\''), match.group(2)


def parse_post(post_path: Path) -> tuple[dict[str, object], str]:
    text = post_path.read_text(encoding='utf-8', errors='ignore')
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    front_matter = yaml.safe_load(match.group(1)) or {}
    body = text[match.end() :]
    return front_matter, body


def collect_used_asset_refs() -> set[str]:
    refs: set[str] = set()
    for post_path in POSTS_DIR.glob('*.md'):
        text = post_path.read_text(encoding='utf-8', errors='ignore')
        for ref in LOCAL_ASSET_RE.findall(text):
            refs.add(ref.split('?', 1)[0])
    return refs


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def collect_unused_images() -> tuple[list[CandidateImage], list[dict[str, str]]]:
    used_refs = collect_used_asset_refs()
    records: list[CandidateImage] = []
    bad_files: list[dict[str, str]] = []
    for path in sorted(ASSETS_IMG_DIR.rglob('*')):
        if not path.is_file() or not is_image_file(path):
            continue
        rel_path = '/' + str(path.relative_to(ROOT)).replace('\\', '/')
        if rel_path in used_refs:
            continue
        parts = path.relative_to(ASSETS_IMG_DIR).parts
        year = parts[0] if len(parts) >= 1 else '0000'
        month = parts[1] if len(parts) >= 2 else '00'
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image)
                width, height = image.size
        except (OSError, UnidentifiedImageError) as exc:
            bad_files.append(
                {
                    'rel_path': rel_path,
                    'error': type(exc).__name__,
                },
            )
            continue
        records.append(
            CandidateImage(
                rel_path=rel_path,
                abs_path=str(path),
                year=year,
                month=month,
                stem=path.stem,
                width=width,
                height=height,
                pixels=width * height,
                file_size=path.stat().st_size,
            ),
        )
    return records, bad_files


def clean_markdown_text(text: str) -> str:
    text = MD_IMAGE_RE.sub(lambda match: f' {match.group(1)} ', text)
    text = MD_LINK_RE.sub(lambda match: f' {match.group(1)} ', text)
    text = HTML_TAG_RE.sub(' ', text)
    text = RAW_URL_RE.sub(' ', text)
    text = html.unescape(text)
    text = SENTENCE_BREAK_RE.sub(' ', text)
    text = WHITESPACE_RE.sub(' ', text)
    return text.strip()


def extract_context(body: str, start: int, end: int) -> str:
    prev_break = body.rfind('\n\n', 0, start)
    prev_prev_break = body.rfind('\n\n', 0, max(prev_break, 0))
    next_break = body.find('\n\n', end)
    next_next_break = body.find('\n\n', next_break + 2) if next_break != -1 else -1
    begin = 0 if prev_prev_break == -1 else prev_prev_break + 2
    finish = len(body) if next_next_break == -1 else next_next_break
    snippet = body[begin:finish]
    return clean_markdown_text(snippet)


def token_set(value: str) -> set[str]:
    tokens: set[str] = set()
    for token in SAFE_TOKEN_RE.sub(' ', value.lower()).split():
        if token in GENERIC_TOKENS:
            continue
        if token.isdigit() and len(token) < 5:
            continue
        if len(token) < 3 and not any(char.isdigit() for char in token):
            continue
        tokens.add(token)
    return tokens


def clip_query_text(occurrence: ExternalImageOccurrence) -> str:
    context = extract_context(
        occurrence.body,
        occurrence.start,
        occurrence.end,
    )
    basename = Path(urllib.parse.unquote(
        urllib.parse.urlparse(occurrence.url).path,
    )).stem
    parts = [
        occurrence.title.strip(),
        occurrence.alt_text.strip(),
        basename.replace('_', ' ').replace('-', ' '),
        context,
    ]
    merged = ' '.join(part for part in parts if part)
    merged = WHITESPACE_RE.sub(' ', merged).strip()
    words = merged.split()
    if len(words) > 72:
        merged = ' '.join(words[:72])
    return merged


def collect_external_occurrences() -> list[ExternalImageOccurrence]:
    occurrences: list[ExternalImageOccurrence] = []
    for post_path in sorted(POSTS_DIR.glob('*.md')):
        front_matter, body = parse_post(post_path)
        title = str(front_matter.get('title') or post_path.stem)
        line_offsets = [0]
        for match in re.finditer(r'\n', body):
            line_offsets.append(match.end())
        image_index = 0
        for is_code, base_offset, segment in split_fenced_offsets(body):
            if is_code:
                continue
            for match in MD_IMAGE_RE.finditer(segment):
                url, _rest = first_markdown_target(match.group(2))
                if not url.startswith(('http://', 'https://')):
                    continue
                start = base_offset + match.start()
                line_number = body.count('\n', 0, start) + 1
                occurrences.append(
                    ExternalImageOccurrence(
                        occurrence_id=f'{post_path.name}::md::{image_index}',
                        post_name=post_path.name,
                        post_path=str(post_path),
                        title=title,
                        url=url,
                        alt_text=match.group(1).strip(),
                        line_number=line_number,
                        start=start,
                        end=base_offset + match.end(),
                        body=body,
                    ),
                )
                image_index += 1
            for match in HTML_IMG_RE.finditer(segment):
                url = match.group(1).strip()
                if not url.startswith(('http://', 'https://')):
                    continue
                start = base_offset + match.start()
                line_number = body.count('\n', 0, start) + 1
                occurrences.append(
                    ExternalImageOccurrence(
                        occurrence_id=f'{post_path.name}::html::{image_index}',
                        post_name=post_path.name,
                        post_path=str(post_path),
                        title=title,
                        url=url,
                        alt_text='',
                        line_number=line_number,
                        start=start,
                        end=base_offset + match.end(),
                        body=body,
                    ),
                )
                image_index += 1
    return occurrences


def image_validation_error(data: bytes, content_type: str) -> str:
    stripped = data.lstrip()
    lower_head = stripped[:64].lower()
    if lower_head.startswith((b'data:image', b'<!doctype', b'<html')):
        return 'text_image_or_html'

    magic_match = any(
        stripped.startswith(magic) for magic, _ext in IMAGE_MAGIC_EXTENSIONS
    )
    if not magic_match and content_type != 'image/svg+xml':
        return 'unknown_image_magic'

    if content_type == 'image/svg+xml':
        return ''

    try:
        image = Image.open(io_bytes(data))
        image.verify()
        image = Image.open(io_bytes(data))
        width, height = image.size
    except Exception as exc:  # noqa: BLE001
        return f'image_decode_failed:{type(exc).__name__}'

    if width <= 1 and height <= 1:
        return 'one_pixel_placeholder'
    return ''


def io_bytes(data: bytes):
    from io import BytesIO

    return BytesIO(data)


def check_external_url(url: str) -> UrlStatus:
    parsed = urllib.parse.urlparse(url)
    referer = parsed._replace(
        path='/',
        params='',
        query='',
        fragment='',
    ).geturl()
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0 Safari/537.36'
            ),
            'Accept': (
                'image/avif,image/webp,image/apng,image/svg+xml,'
                'image/*,*/*;q=0.8'
            ),
            'Referer': referer,
        },
        method='GET',
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            status = response.getcode() or 0
            content_type = (
                response.headers.get('content-type', '')
                .split(';', 1)[0]
                .lower()
            )
            data = response.read()
    except urllib.error.HTTPError as exc:
        return UrlStatus(
            ok=False,
            status=exc.code,
            content_type=exc.headers.get('content-type', '').split(';', 1)[0],
            error=f'HTTP {exc.code}',
        )
    except (urllib.error.URLError, TimeoutError, socket.timeout, ssl.SSLError) as exc:
        reason = getattr(exc, 'reason', exc)
        error = reason if isinstance(reason, str) else type(reason).__name__
        return UrlStatus(ok=False, status=0, content_type='', error=str(error)[:120])
    except Exception as exc:  # noqa: BLE001
        return UrlStatus(
            ok=False,
            status=0,
            content_type='',
            error=type(exc).__name__,
        )

    if not (200 <= status < 400):
        return UrlStatus(
            ok=False,
            status=status,
            content_type=content_type,
            error='bad_status',
        )

    validation_error = image_validation_error(data, content_type)
    if validation_error:
        return UrlStatus(
            ok=False,
            status=status,
            content_type=content_type,
            error=validation_error,
        )

    return UrlStatus(
        ok=True,
        status=status,
        content_type=content_type,
        error='',
    )


def load_status_cache(path: Path) -> dict[str, UrlStatus]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding='utf-8'))
    return {url: UrlStatus(**payload) for url, payload in raw.items()}


def save_status_cache(path: Path, statuses: dict[str, UrlStatus]) -> None:
    serialized = {url: asdict(status) for url, status in statuses.items()}
    path.write_text(
        json.dumps(serialized, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def check_url_statuses(
    urls: list[str],
    cache_path: Path,
    concurrency: int,
    reuse_cache: bool,
) -> dict[str, UrlStatus]:
    statuses = load_status_cache(cache_path) if reuse_cache else {}
    pending = [url for url in urls if url not in statuses]
    if pending:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=concurrency,
        ) as executor:
            futures = {
                executor.submit(check_external_url, url): url for url in pending
            }
            for future in concurrent.futures.as_completed(futures):
                url = futures[future]
                statuses[url] = future.result()
        save_status_cache(cache_path, statuses)
    return statuses


def image_iter(paths: Iterable[str]):
    for path in paths:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert('RGB')
            yield image.copy()


def embed_images(
    model: SentenceTransformer,
    images: list[CandidateImage],
    batch_size: int,
) -> np.ndarray:
    embeddings: list[np.ndarray] = []
    for start in range(0, len(images), batch_size):
        batch = images[start : start + batch_size]
        vectors = model.encode(
            list(image_iter(item.abs_path for item in batch)),
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embeddings.append(vectors.astype(np.float32))
    return np.vstack(embeddings)


def embed_texts(
    model: SentenceTransformer,
    texts: list[str],
    batch_size: int,
) -> np.ndarray:
    return model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    ).astype(np.float32)


def post_year_month(post_name: str) -> tuple[str, str]:
    match = re.match(r'(\d{4})-(\d{2})-\d{2}-', post_name)
    if not match:
        return '0000', '00'
    return match.group(1), match.group(2)


def overlap_bonus(
    occurrence: ExternalImageOccurrence,
    image: CandidateImage,
) -> tuple[float, list[str]]:
    reasons: list[str] = []
    post_year, post_month = post_year_month(occurrence.post_name)
    bonus = 0.0
    if image.year == post_year and image.month == post_month:
        bonus += 0.035
        reasons.append('same_year_month')
    elif image.year == post_year and image.year != '0000':
        bonus += 0.015
        reasons.append('same_year')

    url_stem = Path(urllib.parse.unquote(
        urllib.parse.urlparse(occurrence.url).path,
    )).stem
    query_tokens = (
        token_set(occurrence.title)
        | token_set(occurrence.alt_text)
        | token_set(url_stem)
    )
    image_tokens = token_set(image.stem)
    common = sorted(query_tokens & image_tokens)
    if common:
        token_bonus = min(0.03, 0.01 * len(common))
        bonus += token_bonus
        reasons.append('token:' + ','.join(common[:4]))
    return bonus, reasons


def rank_candidates(
    occurrence: ExternalImageOccurrence,
    text_vector: np.ndarray,
    images: list[CandidateImage],
    image_vectors: np.ndarray,
    top_k: int,
) -> list[dict[str, object]]:
    cosine_scores = image_vectors @ text_vector
    top_indices = np.argsort(cosine_scores)[::-1][:top_k]
    ranked: list[dict[str, object]] = []
    for index in top_indices:
        image = images[int(index)]
        clip_score = float(cosine_scores[int(index)])
        bonus, reasons = overlap_bonus(occurrence, image)
        ranked.append(
            {
                'rel_path': image.rel_path,
                'width': image.width,
                'height': image.height,
                'pixels': image.pixels,
                'file_size': image.file_size,
                'clip_score': round(clip_score, 5),
                'heuristic_bonus': round(bonus, 5),
                'final_score': round(clip_score + bonus, 5),
                'reasons': reasons,
            },
        )
    ranked.sort(key=lambda item: item['final_score'], reverse=True)
    return ranked


def promising_rank(
    ranked: list[dict[str, object]],
) -> tuple[float, float, float]:
    top1 = float(ranked[0]['final_score']) if ranked else 0.0
    top2 = float(ranked[1]['final_score']) if len(ranked) > 1 else 0.0
    margin = top1 - top2
    heuristic = float(ranked[0]['heuristic_bonus']) if ranked else 0.0
    return top1, margin, heuristic


def is_promising_match(
    ranked: list[dict[str, object]],
    profile: str,
) -> bool:
    top1, margin, heuristic = promising_rank(ranked)
    if not ranked:
        return False
    reasons = ranked[0]['reasons']
    has_token_reason = any(
        isinstance(reason, str) and reason.startswith('token:')
        for reason in reasons
    )
    same_year_month = 'same_year_month' in reasons
    same_year = 'same_year' in reasons
    if profile == 'strict':
        if has_token_reason and same_year_month and top1 >= 0.21:
            return True
        if has_token_reason and top1 >= 0.24:
            return True
        if same_year_month and top1 >= 0.34 and margin >= 0.012:
            return True
        if same_year and top1 >= 0.36 and margin >= 0.02:
            return True
        if top1 >= 0.42 and margin >= 0.03:
            return True
        return False

    if has_token_reason and same_year_month and top1 >= 0.18:
        return True
    if has_token_reason and same_year and top1 >= 0.2:
        return True
    if has_token_reason and top1 >= 0.22:
        return True
    if same_year_month and top1 >= 0.3 and margin >= 0.008:
        return True
    if same_year and top1 >= 0.32 and margin >= 0.012:
        return True
    if top1 >= 0.38 and margin >= 0.02:
        return True
    return False


def html_escape(value: str) -> str:
    return html.escape(value, quote=True)


def render_html(
    report_dir: Path,
    report_rows: list[dict[str, object]],
    summary: dict[str, object],
) -> None:
    rows_html: list[str] = []
    for row in report_rows:
        candidates_html: list[str] = []
        for candidate in row['candidates']:
            reasons = ', '.join(candidate['reasons']) or 'clip_only'
            candidates_html.append(
                '\n'.join(
                    [
                        "<div class='candidate'>",
                        (
                            f"<img src='../../{html_escape(candidate['rel_path'].lstrip('/'))}' "
                            f"alt='{html_escape(candidate['rel_path'])}'>"
                        ),
                        (
                            f"<div class='candidate-path'>"
                            f"{html_escape(candidate['rel_path'])}</div>"
                        ),
                        (
                            "<div class='candidate-meta'>"
                            f"final {candidate['final_score']:.3f} | "
                            f"clip {candidate['clip_score']:.3f} | "
                            f"bonus {candidate['heuristic_bonus']:.3f}"
                            '</div>'
                        ),
                        (
                            "<div class='candidate-meta'>"
                            f"{html_escape(reasons)}"
                            '</div>'
                        ),
                        '</div>',
                    ],
                )
            )
        rows_html.append(
            '\n'.join(
                [
                    '<tr>',
                    (
                        "<td class='post-cell'>"
                        f"<div class='post-title'>{html_escape(row['title'])}</div>"
                        f"<div class='post-file'>{html_escape(row['post_name'])}"
                        f":{row['line_number']}</div>"
                        f"<div class='post-url'>{html_escape(row['url'])}</div>"
                        f"<div class='post-status'>"
                        f"{html_escape(row['status_error'])}"
                        '</div>'
                        '</td>'
                    ),
                    (
                        "<td class='query-cell'>"
                        f"<div class='query-text'>{html_escape(row['query_text'])}</div>"
                        '</td>'
                    ),
                    (
                        "<td class='candidate-cell'>"
                        + ''.join(candidates_html)
                        + '</td>'
                    ),
                    '</tr>',
                ],
            )
        )

    html_text = '\n'.join(
        [
            '<!doctype html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<title>Dead Image Asset Match Report</title>',
            '<style>',
            'body { background: #111; color: #f3f3f3; font: 14px/1.5 Inter, system-ui, sans-serif; margin: 24px; }',
            'h1, h2 { margin: 0 0 12px; }',
            '.summary { color: #bbb; margin-bottom: 24px; }',
            'table { width: 100%; border-collapse: collapse; }',
            'th, td { border-top: 1px solid #2a2a2a; vertical-align: top; padding: 16px 12px; }',
            'th { color: #9f9f9f; font-weight: 600; text-align: left; }',
            '.post-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; }',
            '.post-file, .post-url, .post-status, .candidate-meta, .candidate-path { color: #9f9f9f; font-size: 12px; word-break: break-word; }',
            '.query-text { max-width: 44ch; white-space: normal; }',
            '.candidate { display: inline-block; width: 220px; margin: 0 12px 16px 0; }',
            '.candidate img { width: 220px; height: 160px; object-fit: cover; display: block; background: #222; margin-bottom: 8px; }',
            'a { color: #8bb7ff; }',
            '</style>',
            '</head>',
            '<body>',
            '<h1>Dead Image to Unused Asset Match Report</h1>',
            (
                "<div class='summary'>"
                f"Model: {html_escape(str(summary['model']))} | "
                f"Profile: {html_escape(str(summary['match_profile']))} | "
                f"Unused local images: {summary['unused_images']} | "
                f"Dead external refs: {summary['dead_occurrences']} | "
                f"Rendered promising rows: {summary['promising_rendered']}"
                '</div>'
            ),
            '<table>',
            '<thead><tr><th>Dead image ref</th><th>Query text</th><th>Top candidates</th></tr></thead>',
            '<tbody>',
            ''.join(rows_html),
            '</tbody>',
            '</table>',
            '</body>',
            '</html>',
        ],
    )
    (report_dir / 'index.html').write_text(html_text, encoding='utf-8')


def render_markdown(
    report_dir: Path,
    report_rows: list[dict[str, object]],
    summary: dict[str, object],
) -> None:
    lines = [
        '# Dead Image to Unused Asset Match Report',
        '',
        f"- Model: `{summary['model']}`",
        f"- Match profile: `{summary['match_profile']}`",
        f"- Unused local images: `{summary['unused_images']}`",
        f"- Dead external refs: `{summary['dead_occurrences']}`",
        f"- Rendered promising rows: `{summary['promising_rendered']}`",
        '',
        '| Post | Dead URL | Top candidate | Score | Notes |',
        '| --- | --- | --- | --- | --- |',
    ]
    for row in report_rows:
        top = row['candidates'][0]
        notes = ', '.join(top['reasons']) or 'clip_only'
        lines.append(
            '| '
            f"`{row['post_name']}:{row['line_number']}` | "
            f"`{row['url']}` | "
            f"`{top['rel_path']}` | "
            f"`{top['final_score']:.3f}` | "
            f'{notes} |'
        )
    (report_dir / 'report.md').write_text(
        '\n'.join(lines) + '\n',
        encoding='utf-8',
    )


def main() -> int:
    args = parse_args()
    report_dir = args.report_dir
    report_dir.mkdir(parents=True, exist_ok=True)

    unused_images, bad_unused_images = collect_unused_images()
    occurrences = collect_external_occurrences()
    unique_urls = sorted({item.url for item in occurrences})
    status_cache_path = report_dir / 'url_status_cache.json'
    statuses = check_url_statuses(
        unique_urls,
        cache_path=status_cache_path,
        concurrency=args.concurrency,
        reuse_cache=args.reuse_status_cache,
    )

    dead_occurrences = [
        occurrence for occurrence in occurrences if not statuses[occurrence.url].ok
    ]
    dead_occurrences.sort(key=lambda item: (item.post_name, item.line_number, item.url))

    model = SentenceTransformer(MODEL_NAME)
    image_vectors = embed_images(model, unused_images, batch_size=args.batch_size)
    queries = [clip_query_text(item) for item in dead_occurrences]
    text_vectors = embed_texts(model, queries, batch_size=args.batch_size)

    all_ranked_rows: list[dict[str, object]] = []
    for occurrence, query_text, text_vector in zip(
        dead_occurrences,
        queries,
        text_vectors,
        strict=True,
    ):
        ranked = rank_candidates(
            occurrence,
            text_vector,
            unused_images,
            image_vectors,
            top_k=args.top_k,
        )
        all_ranked_rows.append(
            {
                'occurrence_id': occurrence.occurrence_id,
                'post_name': occurrence.post_name,
                'post_path': occurrence.post_path,
                'title': occurrence.title,
                'line_number': occurrence.line_number,
                'url': occurrence.url,
                'status_error': statuses[occurrence.url].error,
                'status_code': statuses[occurrence.url].status,
                'query_text': query_text,
                'candidates': ranked,
            }
        )

    all_ranked_rows.sort(
        key=lambda item: promising_rank(item['candidates']),
        reverse=True,
    )
    promising_rows = [
        item
        for item in all_ranked_rows
        if is_promising_match(item['candidates'], args.match_profile)
    ][: args.report_limit]

    summary = {
        'model': MODEL_NAME,
        'match_profile': args.match_profile,
        'unused_images': len(unused_images),
        'bad_unused_images': len(bad_unused_images),
        'external_occurrences': len(occurrences),
        'dead_occurrences': len(dead_occurrences),
        'dead_posts': len({item.post_name for item in dead_occurrences}),
        'unique_dead_urls': len({item.url for item in dead_occurrences}),
        'promising_total': len(
            [
                item
                for item in all_ranked_rows
                if is_promising_match(item['candidates'], args.match_profile)
            ]
        ),
        'promising_rendered': len(promising_rows),
    }

    (report_dir / 'summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    (report_dir / 'unused_images.json').write_text(
        json.dumps([asdict(item) for item in unused_images], ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    (report_dir / 'bad_unused_images.json').write_text(
        json.dumps(bad_unused_images, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    (report_dir / 'dead_occurrences.json').write_text(
        json.dumps(
            [
                {
                    'occurrence_id': item.occurrence_id,
                    'post_name': item.post_name,
                    'post_path': item.post_path,
                    'title': item.title,
                    'line_number': item.line_number,
                    'url': item.url,
                    'status': asdict(statuses[item.url]),
                    'query_text': clip_query_text(item),
                }
                for item in dead_occurrences
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding='utf-8',
    )
    (report_dir / 'all_ranked_matches.json').write_text(
        json.dumps(all_ranked_rows, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    (report_dir / 'promising_matches.json').write_text(
        json.dumps(promising_rows, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    render_markdown(report_dir, promising_rows, summary)
    render_html(report_dir, promising_rows, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
