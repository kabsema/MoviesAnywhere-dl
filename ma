#!/usr/bin/env python3
"""
Movies Anywhere Downloader

Simple workflow:
1. Play movie in Firefox with WidevineProxy2 enabled
2. Export logs from WidevineProxy2
3. Run: ma "Movie Name"

The script reads ~/Downloads/logs.json by default
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def find_tool(name):
    """Find tool in common locations"""
    paths = [
        f"/usr/local/bin/{name}",
        f"/usr/bin/{name}",
        os.path.expanduser(f"~/VT-PR/linux_binaries/{name}"),
        os.path.expanduser(f"~/.local/bin/{name}"),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return name


def sanitize_filename(name):
    """Remove invalid characters from filename"""
    # Remove invalid chars
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace multiple spaces with single
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def parse_logs(logs_path):
    """Parse WidevineProxy2 logs.json"""
    print(f"[*] Reading: {logs_path}")

    with open(logs_path, 'r') as f:
        logs = json.load(f)

    # Get the most recent entry (usually only one)
    for pssh_key, data in logs.items():
        keys = {}
        manifest_url = None

        # Extract keys
        for key_data in data.get('keys', []):
            kid = key_data.get('kid', '')
            key = key_data.get('k', '')
            if kid and key:
                keys[kid] = key

        # Extract manifest URL
        for manifest in data.get('manifests', []):
            if manifest.get('type') == 'DASH':
                manifest_url = manifest.get('url')
                break

        if keys and manifest_url:
            return manifest_url, keys

    return None, None


def download(movie_name, manifest_url, keys, base_dir="~/Downloads/Movies"):
    """Download movie with all tracks"""

    # Expand paths
    base_dir = os.path.expanduser(base_dir)

    # Create movie folder
    safe_name = sanitize_filename(movie_name)
    movie_dir = os.path.join(base_dir, safe_name)
    os.makedirs(movie_dir, exist_ok=True)

    print("=" * 60)
    print(f"  MOVIES ANYWHERE DOWNLOADER")
    print("=" * 60)
    print(f"  Movie: {movie_name}")
    print(f"  Output: {movie_dir}")
    print(f"  Keys: {len(keys)}")
    for kid, key in keys.items():
        print(f"    {kid}:{key}")
    print("=" * 60)

    # Find tools
    n_m3u8dl = find_tool("N_m3u8DL-RE")
    mp4decrypt = find_tool("mp4decrypt")

    # Build command
    cmd = [
        n_m3u8dl,
        manifest_url,
        "--save-name", safe_name,
        "--save-dir", movie_dir,
        "--auto-select",
        "--decryption-binary-path", mp4decrypt,
        "-H", "Referer: https://moviesanywhere.com/",
        "-H", "Origin: https://moviesanywhere.com",
        "-M", "format=mkv",
    ]

    # Add keys
    for kid, key in keys.items():
        cmd.extend(["--key", f"{kid}:{key}"])

    print(f"\n[*] Starting download...")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ''):
            print(line, end='')

        process.wait()

        if process.returncode == 0:
            # Find output file
            for f in Path(movie_dir).glob(f"{safe_name}*"):
                if f.suffix in ['.mkv', '.mp4']:
                    print(f"\n{'=' * 60}")
                    print(f"  SUCCESS!")
                    print(f"{'=' * 60}")
                    print(f"  Output: {f}")
                    print(f"{'=' * 60}")
                    return str(f)

        print(f"\n[!] Download may have completed - check {movie_dir}")
        return movie_dir

    except Exception as e:
        print(f"[!] Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Movies Anywhere Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
WORKFLOW:
  1. Install WidevineProxy2 extension in Firefox
  2. Load your CDM (.wvd file) in the extension
  3. Enable the extension and play your movie
  4. Click "Export Logs" in the extension
  5. Run: ma "Movie Name"

EXAMPLES:
  ma "The Sound of Music"
  ma "Shutter Island" --logs ~/Downloads/logs.json
  ma "My Movie" --dir ~/Videos/Movies
        """
    )

    parser.add_argument('name', help='Movie name (shown when video is paused)')
    parser.add_argument('--logs', '-l', default='~/Downloads/logs.json',
                        help='WidevineProxy2 logs.json (default: ~/Downloads/logs.json)')
    parser.add_argument('--dir', '-d', default='~/Downloads/Movies',
                        help='Base output directory (default: ~/Downloads/Movies)')

    args = parser.parse_args()

    # Expand paths
    logs_path = os.path.expanduser(args.logs)

    # Check logs file exists
    if not os.path.exists(logs_path):
        print(f"[!] Logs file not found: {logs_path}")
        print(f"[!] Make sure to export logs from WidevineProxy2 first")
        return 1

    # Parse logs
    manifest_url, keys = parse_logs(logs_path)

    if not manifest_url or not keys:
        print("[!] Could not find manifest URL or keys in logs")
        print("[!] Make sure you played the movie with WidevineProxy2 enabled")
        return 1

    # Download
    result = download(args.name, manifest_url, keys, args.dir)

    return 0 if result else 1


if __name__ == '__main__':
    sys.exit(main())
