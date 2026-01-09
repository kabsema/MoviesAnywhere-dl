#!/usr/bin/env python3
"""
Movies Anywhere Downloader by Jwheet
Downloads movies using WidevineProxy2 logs.json

Usage:
    movies-anywhere ~/Downloads/logs.json
    movies-anywhere ~/Downloads/logs.json "Movie Name"
"""

import argparse

BANNER = r"""
                                        ==
                                      =======
                                   ===========
                                     =============         *===
                                 ================       %*+====+
                                   =============     %%#+%======
                                     ==========+++++  %%*==========
                                  =============++++    %%=========
                                   ===========+++++#####=========
                                     =========++++  ####============
                                   ==============++++###==========
                                   %============++++***=========
                                 +#%%+==========++*****============
                                  +**%#========+++=#***+=========
                                  ==*+#========+++=##***========
                           +== +++===+#%+======++==*****=======
                           ===+++++===========+*====****=====+
                         ====================+++=====##*=++++===
                        =========+++=========++========+++++=====
                          ====+===+==+====+==++=====+%%*++++======
                         =+=======+=+++==+===++======++++++======
                           ======+====*==*===++=====+++++++=======
                           +=========+*%*+==+++=====++++++======
                             ========+*##*==+++=====++++++++++*
                              +==++==+=*#*==+++=====++++++==++++
                                =====***#+==+++===++++++++++++
                                  ===+#%*===++++=   +++++++++
                                  ====+%*==+=+==      ++++
                                  ====+ *==+=+==     +===
                                   ====+*==+=+==     ====
                                   ====+*==+=+=     ====
                                   ==+==#==++==    =====
                                   ==+==*==++==    ====
                                    ==*=*===+==   =====
                                    #***#======%%@====
                                    %*%%###############
                                     *=*#===+== ==+==
                                      ==%===*==#==+==
                                      *=%========++=
                                      %+*==+=+==++==
                                      %%%*+++%**####%
                                       +*########*==
                                       =**==+#==++=
                                       =++==+*=====
                                       =====++=====
                                       =====++=====
                                       ============
                                       ======+=====
                                       ======++====
                                        ==+==++====
                                        ==*==++===
                                        == == ++==
                          ____.       .__                   __
                         |    |_  _  _|  |__   ____   _____/  |_
                         |    \ \/ \/ /  |  \_/ __ \_/ __ \   __\
                     /\__|    |\     /|   Y  \  ___/\  ___/|  |
                     \________| \/\_/ |___|  /\___  >\___  >__|
                                       \/     \/     \/
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime


class MADownloader:
    """Movies Anywhere downloader using WidevineProxy2 extracted keys"""

    TOOL_PATHS = [
        "/usr/local/bin",
        "/usr/bin",
        os.path.expanduser("~/VT-PR/linux_binaries"),
        os.path.expanduser("~/.local/bin"),
    ]

    def __init__(self, output_dir="downloads"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.n_m3u8dl_re = self._find_tool("N_m3u8DL-RE")
        self.mp4decrypt = self._find_tool("mp4decrypt")
        self.ffmpeg = self._find_tool("ffmpeg")
        self.ffprobe = self._find_tool("ffprobe")

    def _find_tool(self, name):
        """Find tool in common locations"""
        for base in self.TOOL_PATHS:
            path = os.path.join(base, name)
            if os.path.exists(path):
                return path
        return name

    def _run_cmd(self, cmd, capture=True):
        """Run command and return result"""
        return subprocess.run(cmd, capture_output=capture, text=True)

    def _filter_duplicate_subs(self, mkv_path):
        """Remove duplicate subtitle tracks, keeping only the largest per language"""
        print("\n[Filter] Analyzing subtitle tracks...")

        # Get subtitle track info
        result = self._run_cmd([
            self.ffprobe, "-v", "error", "-select_streams", "s",
            "-show_entries", "stream=index:stream_tags=language",
            "-of", "json", mkv_path
        ])

        if result.returncode != 0:
            print("[Filter] Could not analyze tracks")
            return mkv_path

        streams = json.loads(result.stdout).get('streams', [])
        if len(streams) <= 1:
            print(f"[Filter] Only {len(streams)} subtitle track(s), no filtering needed")
            return mkv_path

        # Extract each subtitle to measure actual size
        sub_info = []
        for stream in streams:
            idx = stream['index']
            lang = stream.get('tags', {}).get('language', 'und')
            temp_sub = f"/tmp/sub_check_{idx}.srt"

            self._run_cmd([
                self.ffmpeg, "-y", "-v", "error", "-i", mkv_path,
                "-map", f"0:{idx}", temp_sub
            ])

            size = os.path.getsize(temp_sub) if os.path.exists(temp_sub) else 0
            sub_info.append({'index': idx, 'lang': lang, 'size': size})

            if os.path.exists(temp_sub):
                os.remove(temp_sub)

        # Group by language and keep largest per language
        lang_tracks = {}
        for sub in sub_info:
            lang_tracks.setdefault(sub['lang'], []).append(sub)

        keep_indices = set()
        for lang, tracks in lang_tracks.items():
            tracks.sort(key=lambda x: x['size'], reverse=True)
            keep_indices.add(tracks[0]['index'])

            if len(tracks) == 1:
                print(f"[Filter] {lang}: keeping ({tracks[0]['size']} bytes)")
            else:
                print(f"[Filter] {lang}: keeping largest ({tracks[0]['size']} bytes), removing ({tracks[1]['size']} bytes)")

        if len(keep_indices) == len(streams):
            print("[Filter] No duplicate tracks to remove")
            return mkv_path

        # Remux with only selected subtitle tracks
        print(f"[Filter] Remuxing to remove {len(streams) - len(keep_indices)} duplicate track(s)...")
        temp_output = mkv_path.replace('.mkv', '.FILTERED.mkv')

        cmd = [self.ffmpeg, "-y", "-v", "warning", "-i", mkv_path, "-map", "0:v", "-map", "0:a"]
        for idx in sorted(keep_indices):
            cmd.extend(["-map", f"0:{idx}"])
        cmd.extend(["-c", "copy", temp_output])

        if self._run_cmd(cmd).returncode == 0 and os.path.exists(temp_output):
            os.remove(mkv_path)
            os.rename(temp_output, mkv_path)
            print("[Filter] Done - removed duplicate subtitle tracks")
        else:
            print("[Filter] Remux failed, keeping original")
            if os.path.exists(temp_output):
                os.remove(temp_output)

        return mkv_path

    def parse_logs(self, logs_path):
        """Parse WidevineProxy2 logs.json to extract manifest URL and keys"""
        print(f"[Parser] Reading: {logs_path}")

        with open(logs_path, 'r') as f:
            logs = json.load(f)

        results = []
        for data in logs.values():
            keys = {k['kid']: k['k'] for k in data.get('keys', []) if k.get('kid') and k.get('k')}
            manifest_url = next(
                (m['url'] for m in data.get('manifests', []) if m.get('type') == 'DASH'),
                None
            )
            if keys and manifest_url:
                results.append({'keys': keys, 'manifest_url': manifest_url})

        print(f"[Parser] Found {len(results)} entries with keys and manifest")
        return results

    def download(self, manifest_url, keys, output_name):
        """Download movie with all tracks"""
        print(BANNER)
        print("=" * 60)
        print("  MOVIES ANYWHERE DOWNLOADER - by Jwheet")
        print("=" * 60)
        print(f"  Movie:  {output_name}")
        print(f"  Video:  Best quality")
        print(f"  Audio:  All languages")
        print(f"  Subs:   All languages (duplicates filtered)")
        print("=" * 60)
        print(f"[Info] Manifest: {manifest_url[:80]}...")
        print(f"[Info] Keys: {len(keys)}")
        for kid, key in keys.items():
            print(f"  {kid}:{key}")

        cmd = [
            self.n_m3u8dl_re, manifest_url,
            "--save-name", output_name,
            "--save-dir", self.output_dir,
            "--decryption-binary-path", self.mp4decrypt,
            "--ffmpeg-binary-path", self.ffmpeg,
            "-H", "Referer: https://moviesanywhere.com/",
            "-H", "Origin: https://moviesanywhere.com",
            "-M", "format=mkv:muxer=ffmpeg",
            "--log-level", "INFO",
            "-sv", "best", "-sa", "all", "-ss", "all",
        ]
        for kid, key in keys.items():
            cmd.extend(["--key", f"{kid}:{key}"])

        print("\n[Download] Starting...")

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
            process.wait()

            if process.returncode != 0:
                print(f"\n[Download] Failed with code {process.returncode}")
                return None

            # Handle output file naming
            final_path = os.path.join(self.output_dir, f"{output_name}.mkv")
            mux_path = os.path.join(self.output_dir, f"{output_name}.MUX.mkv")

            if os.path.exists(mux_path):
                if os.path.exists(final_path):
                    os.remove(final_path)
                os.rename(mux_path, final_path)

            if not os.path.exists(final_path):
                print("\n[Download] Completed but output file not found")
                return None

            self._filter_duplicate_subs(final_path)
            print(f"\n[Download] SUCCESS: {final_path}")
            return final_path

        except Exception as e:
            print(f"[Download] Error: {e}")
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Movies Anywhere Downloader',
        epilog="Usage: movies-anywhere ~/Downloads/logs.json \"Movie Name\""
    )
    parser.add_argument('logs', help='WidevineProxy2 logs.json file')
    parser.add_argument('name', nargs='?', help='Movie name (optional)')
    parser.add_argument('--dir', '-d', default='~/Downloads/Movies', help='Output directory')

    args = parser.parse_args()
    logs_path = os.path.expanduser(args.logs)
    base_dir = os.path.expanduser(args.dir)

    if not os.path.exists(logs_path):
        print(f"[!] Logs file not found: {logs_path}")
        return 1

    downloader = MADownloader(output_dir=base_dir)
    entries = downloader.parse_logs(logs_path)

    if not entries:
        print("[!] No valid entries found in logs")
        return 1

    # Generate safe filename
    if args.name:
        safe_name = re.sub(r'[<>:"/\\|?*]', '', args.name)
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    else:
        safe_name = f"Movie_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create movie folder and download
    movie_dir = os.path.join(base_dir, safe_name)
    os.makedirs(movie_dir, exist_ok=True)
    downloader.output_dir = movie_dir

    result = downloader.download(entries[0]['manifest_url'], entries[0]['keys'], safe_name)

    if result:
        print(f"\n{'=' * 60}")
        print(f"  SUCCESS: {result}")
        print(f"{'=' * 60}")
        return 0

    print("\n[!] FAILED")
    return 1


if __name__ == '__main__':
    sys.exit(main())
