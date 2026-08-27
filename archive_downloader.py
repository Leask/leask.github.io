#!/usr/bin/env python3
'''
Archive.org Borrowed Book Downloader
Downloads pages of borrowed books from archive.org and merges them into a PDF.
'''

import argparse
import concurrent.futures
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request

try:
    from PIL import Image
except ImportError:
    print('Error: "Pillow" library is required to compile images to PDF.')
    print('Please install it using: pip install Pillow')
    sys.exit(1)


def parse_identifier(url_or_id):
    '''Extracts the Archive.org identifier from a URL or returns it if it is an ID.'''
    pattern = r'(?:archive\.org/details/|archive\.org/embed/)([^/]+)'
    match = re.search(pattern, url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()


def fetch_metadata(identifier):
    '''Fetches book metadata from Archive.org metadata API.'''
    url = f'https://archive.org/metadata/{identifier}'
    print(f'Fetching metadata for {identifier}...')
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if not data or 'metadata' not in data:
                print('Error: Could not retrieve valid metadata.')
                sys.exit(1)
            return data
    except Exception as e:
        print(f'Error fetching metadata: {e}')
        sys.exit(1)


def download_page(page_num, server, dir_path, identifier, scale, cookie, user_agent, temp_dir):
    '''Downloads a single page image from Archive.org using system curl.'''
    out_file = os.path.join(temp_dir, f'{page_num:04d}.jpg')
    url = (
        f'https://{server}/BookReader/BookReaderImages.php'
        f'?id={identifier}'
        f'&itemPath={dir_path}'
        f'&server={server}'
        f'&page=n{page_num}.jpg'
        f'&scale={scale}'
    )

    import subprocess
    cmd = [
        'curl', '-s', '-L', url,
        '-H', f'User-Agent: {user_agent}',
        '-H', f'Cookie: {cookie}',
        '-H', f'Referer: https://archive.org/details/{identifier}/mode/2up',
        '-H', 'Accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        '-H', 'Accept-Language: en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh-TW;q=0.5,zh;q=0.4',
        '-H', 'Sec-Ch-Ua: "Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        '-H', 'Sec-Ch-Ua-Mobile: ?0',
        '-H', 'Sec-Ch-Ua-Platform: "macOS"',
        '-H', 'Sec-Fetch-Dest: image',
        '-H', 'Sec-Fetch-Mode: no-cors',
        '-H', 'Sec-Fetch-Site: same-origin',
        '-o', out_file
    ]

    try:
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0:
            if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                # Check if the downloaded file is HTML error page
                with open(out_file, 'rb') as f:
                    header = f.read(200)
                    if b'<!DOCTYPE html>' in header or b'<html' in header:
                        error_body = header + f.read(1000)
                        try:
                            error_text = error_body.decode('utf-8', errors='ignore')
                        except Exception:
                            error_text = str(error_body)
                        title_match = re.search(r'<title>(.*?)</title>', error_text, re.IGNORECASE)
                        title_str = title_match.group(1) if title_match else 'HTML Error Page'
                        print(f'\nError downloading page {page_num}: Server returned HTML page: "{title_str}"')
                        return page_num, False
                return page_num, True
            else:
                print(f'\nError downloading page {page_num}: Output file is empty or missing.')
                return page_num, False
        else:
            stderr_str = res.stderr.decode('utf-8', errors='ignore')
            print(f'\nError downloading page {page_num}: curl failed (code {res.returncode}). Stderr: {stderr_str}')
            return page_num, False
    except Exception as e:
        print(f'\nError downloading page {page_num} exception: {e}')
        return page_num, False


def check_page_exists(page_num, server, dir_path, identifier, scale, cookie, user_agent):
    '''Checks if a specific page exists using system curl.'''
    url = (
        f'https://{server}/BookReader/BookReaderImages.php'
        f'?id={identifier}'
        f'&itemPath={dir_path}'
        f'&server={server}'
        f'&page=n{page_num}.jpg'
        f'&scale={scale}'
    )
    import subprocess
    cmd = [
        'curl', '-s', '-I', url,
        '-H', f'User-Agent: {user_agent}',
        '-H', f'Cookie: {cookie}',
        '-H', f'Referer: https://archive.org/details/{identifier}/mode/2up',
        '-H', 'Sec-Ch-Ua: "Not;A=Brand";v="8", "Chromium";v="150", "Google Chrome";v="150"',
        '-H', 'Sec-Ch-Ua-Mobile: ?0',
        '-H', 'Sec-Ch-Ua-Platform: "macOS"',
        '-H', 'Sec-Fetch-Dest: image',
        '-H', 'Sec-Fetch-Mode: no-cors',
        '-H', 'Sec-Fetch-Site: same-origin'
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            is_valid = '200' in res.stdout or '302' in res.stdout
            if not is_valid:
                print(f'\nDebug check_page_exists({page_num}) failed. Output:\n{res.stdout}\nError:\n{res.stderr}')
            return is_valid
        else:
            print(f'\nDebug check_page_exists({page_num}) failed. curl return code: {res.returncode}')
        return False
    except Exception as e:
        print(f'\nDebug check_page_exists({page_num}) exception: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Download Archive.org borrowed book as PDF'
    )
    parser.add_argument(
        'url_or_id',
        help='URL of the book or the book identifier'
    )
    parser.add_argument(
        '--cookie', required=True,
        help='Your Archive.org Cookie header string'
    )
    parser.add_argument(
        '--user-agent',
        default='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
        help='Your browser User-Agent header string'
    )
    parser.add_argument(
        '--scale', type=int, default=4,
        help='Image scale quality (default: 4, higher is better quality)'
    )
    parser.add_argument(
        '--threads', type=int, default=5,
        help='Number of concurrent download threads (default: 5)'
    )
    parser.add_argument(
        '--output',
        help='Output PDF file path'
    )

    args = parser.parse_args()

    identifier = parse_identifier(args.url_or_id)
    metadata = fetch_metadata(identifier)

    server = metadata.get('server')
    dir_path = metadata.get('dir')
    title = metadata.get('metadata', {}).get('title', identifier)
    # Clean title for filename
    clean_title = re.sub(r'[\\/*?:"<>|]', '_', title)

    # Determine image count
    image_count = int(metadata.get('metadata', {}).get('imagecount', 0))
    if not image_count:
        for f in metadata.get('files', []):
            if f.get('name', '').endswith('_jp2.zip'):
                image_count = int(f.get('filecount', 0))
                break

    if not image_count:
        print('Error: Could not determine the number of pages.')
        image_count = int(input('Please enter total pages manually: '))

    print(f'Book Title: {title}')
    print(f'Total Pages: {image_count}')
    print(f'Server: {server}')
    print(f'Directory: {dir_path}')

    # Check whether the pages start at 0000 or 0001
    print('Detecting page numbering sequence...')
    start_page = 0
    if not check_page_exists(0, server, dir_path, identifier, args.scale, args.cookie, args.user_agent):
        if check_page_exists(1, server, dir_path, identifier, args.scale, args.cookie, args.user_agent):
            start_page = 1
            print('Detected sequence starting at 0001.')
        else:
            print('Warning: Could not access page 0 or page 1. Your cookie may be invalid or expired.')
            confirm = input('Do you want to continue anyway? (y/n): ')
            if confirm.lower() != 'y':
                sys.exit(1)
    else:
        print('Detected sequence starting at 0000.')

    pages_to_download = list(range(start_page, start_page + image_count))

    # Output file
    output_pdf = args.output if args.output else f'{clean_title}.pdf'

    # Create temporary directory for page images
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f'Downloading pages to temporary directory {temp_dir}...')
        downloaded_count = 0
        failed_pages = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
            futures = {
                executor.submit(
                    download_page, p, server, dir_path, identifier,
                    args.scale, args.cookie, args.user_agent, temp_dir
                ): p for p in pages_to_download
            }

            for future in concurrent.futures.as_completed(futures):
                page_num, success = future.result()
                if success:
                    downloaded_count += 1
                else:
                    failed_pages.append(page_num)

                # Simple progress indicator
                percent = (downloaded_count + len(failed_pages)) / len(pages_to_download) * 100
                sys.stdout.write(
                    f'\rProgress: {downloaded_count + len(failed_pages)}/{len(pages_to_download)} '
                    f'({percent:.1f}%) | Success: {downloaded_count} | Failed: {len(failed_pages)}'
                )
                sys.stdout.flush()

        print('\nDownload process finished.')
        if failed_pages:
            print(f'Failed to download pages: {sorted(failed_pages)}')
            retry = input('Would you like to retry downloading failed pages? (y/n): ')
            if retry.lower() == 'y':
                # Retry failed pages
                print('Retrying failed pages...')
                with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                    retry_futures = {
                        executor.submit(
                            download_page, p, server, dir_path, identifier,
                            args.scale, args.cookie, args.user_agent, temp_dir
                        ): p for p in failed_pages
                    }
                    for future in concurrent.futures.as_completed(retry_futures):
                        p, success = future.result()
                        if success:
                            failed_pages.remove(p)
                            downloaded_count += 1

                print(f'Final Success Count: {downloaded_count}/{len(pages_to_download)}')

        if downloaded_count == 0:
            print('Error: No pages were successfully downloaded. PDF was not created.')
            sys.exit(1)

        # Get list of downloaded images and sort them
        images_files = sorted([
            os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
            if f.endswith('.jpg')
        ])

        print(f'Converting {len(images_files)} images to PDF...')
        try:
            pil_images = []
            for img_file in images_files:
                img = Image.open(img_file)
                # Convert to RGB mode if not already (PDF doesn't support RGBA/L sometimes)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                pil_images.append(img)

            if pil_images:
                pil_images[0].save(
                    output_pdf,
                    'PDF',
                    resolution=100.0,
                    save_all=True,
                    append_images=pil_images[1:]
                )
                print(f'Success! PDF saved to: {os.path.abspath(output_pdf)}')
            else:
                print('Error: No images found to convert.')
        except Exception as e:
            print(f'Error compiling PDF: {e}')


if __name__ == '__main__':
    main()
