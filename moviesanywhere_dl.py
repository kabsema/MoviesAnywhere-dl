#!/usr/bin/env python3
"""
Movies Anywhere Downloader
Downloads movies with all audio tracks and subtitles from Movies Anywhere

Usage:
    python3 moviesanywhere_dl.py <movie_url> --cookies <cookies_file> --cdm <cdm_path>
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from pywidevine.cdm import Cdm
    from pywidevine.device import Device
    from pywidevine.pssh import PSSH
    import requests
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install pywidevine requests selenium")
    sys.exit(1)


class MoviesAnywhereDownloader:
    """Downloads movies from Movies Anywhere with all audio and subtitle tracks"""

    def __init__(self, cdm_path, cookies_path, output_dir="downloads", headless=True):
        self.cdm_path = cdm_path
        self.cookies_path = cookies_path
        self.output_dir = output_dir
        self.headless = headless
        self.driver = None
        self.device = None
        self.cdm = None

        # Tool paths
        self.n_m3u8dl_re = self._find_tool("N_m3u8DL-RE")
        self.mp4decrypt = self._find_tool("mp4decrypt")
        self.ffmpeg = self._find_tool("ffmpeg")

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def _find_tool(self, name):
        """Find tool in common locations"""
        paths = [
            f"/usr/local/bin/{name}",
            f"/usr/bin/{name}",
            f"/home/{os.environ.get('USER')}/VT-PR/linux_binaries/{name}",
            f"/home/{os.environ.get('USER')}/.local/bin/{name}",
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        # Try which
        result = subprocess.run(["which", name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        return name  # Hope it's in PATH

    def load_cdm(self):
        """Load Widevine CDM from file"""
        print(f"[CDM] Loading from: {self.cdm_path}")

        # Check if it's a .wvd file or directory with client_id.bin/private_key.pem
        if self.cdm_path.endswith('.wvd'):
            self.device = Device.load(self.cdm_path)
        elif os.path.isdir(self.cdm_path):
            # Look for .wvd file in directory
            wvd_files = list(Path(self.cdm_path).glob("*.wvd"))
            if wvd_files:
                self.device = Device.load(str(wvd_files[0]))
            else:
                # Try client_id.bin and private_key.pem
                client_id = os.path.join(self.cdm_path, "client_id.bin")
                private_key = os.path.join(self.cdm_path, "private_key.pem")
                if os.path.exists(client_id) and os.path.exists(private_key):
                    from pywidevine.device import DeviceTypes
                    self.device = Device(
                        type_=DeviceTypes.ANDROID,
                        security_level=3,
                        client_id=open(client_id, 'rb').read(),
                        private_key=open(private_key, 'rb').read()
                    )
                else:
                    raise FileNotFoundError(f"No CDM files found in {self.cdm_path}")
        else:
            raise FileNotFoundError(f"CDM path not found: {self.cdm_path}")

        self.cdm = Cdm.from_device(self.device)
        print(f"[CDM] Loaded successfully")

    def setup_browser(self):
        """Setup Chrome browser with cookies"""
        print("[Browser] Setting up Chrome...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Enable performance logging for network capture
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        self.driver = webdriver.Chrome(options=chrome_options)

        # Load cookies
        self._load_cookies()

        print("[Browser] Ready")

    def _load_cookies(self):
        """Load cookies from file"""
        print(f"[Browser] Loading cookies from: {self.cookies_path}")

        # First navigate to the domain
        self.driver.get("https://moviesanywhere.com")
        time.sleep(2)

        with open(self.cookies_path, 'r') as f:
            content = f.read().strip()

        # Try JSON format first
        try:
            cookies = json.loads(content)
            if isinstance(cookies, list):
                for cookie in cookies:
                    try:
                        # Ensure required fields
                        cookie_dict = {
                            'name': cookie.get('name'),
                            'value': cookie.get('value'),
                            'domain': cookie.get('domain', '.moviesanywhere.com'),
                        }
                        if 'path' in cookie:
                            cookie_dict['path'] = cookie['path']
                        if 'secure' in cookie:
                            cookie_dict['secure'] = cookie['secure']
                        self.driver.add_cookie(cookie_dict)
                    except Exception as e:
                        pass
                print(f"[Browser] Loaded {len(cookies)} cookies (JSON format)")
                return
        except json.JSONDecodeError:
            pass

        # Try Netscape format
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                try:
                    cookie = {
                        'name': parts[5],
                        'value': parts[6],
                        'domain': parts[0],
                        'path': parts[2],
                        'secure': parts[3].upper() == 'TRUE',
                    }
                    self.driver.add_cookie(cookie)
                except Exception:
                    pass

        print("[Browser] Loaded cookies (Netscape format)")

    def navigate_to_movie(self, url):
        """Navigate to movie page and start playback"""
        print(f"[Browser] Navigating to: {url}")

        self.driver.get(url)
        time.sleep(3)

        # Click play button if present
        try:
            play_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Play'], button[class*='play'], [class*='PlayButton']"))
            )
            play_button.click()
            print("[Browser] Clicked play button")
            time.sleep(5)
        except TimeoutException:
            print("[Browser] No play button found, video may auto-play")

    def get_available_tracks(self):
        """Get all available audio and subtitle tracks"""
        print("[Browser] Getting available tracks...")

        audio_tracks = []
        subtitle_tracks = []

        # Click settings/options button to reveal track menus
        try:
            # Try multiple selectors for the settings button
            settings_selectors = [
                "i._3TLveGoIBG3bodgcfLy4rn._1hYrlzyr4r2K0pbJgamEWE",
                "button[aria-label*='Settings']",
                "button[aria-label*='Audio']",
                "[class*='settings']",
                "[class*='Settings']",
            ]

            for selector in settings_selectors:
                try:
                    settings_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    settings_btn.click()
                    time.sleep(1)
                    break
                except NoSuchElementException:
                    continue

        except Exception as e:
            print(f"[Browser] Could not find settings button: {e}")

        # Get audio tracks
        try:
            audio_container = self.driver.find_element(By.CSS_SELECTOR, "div._1tKTeGrrcdKzsuwiyVq6rr, [class*='AudioTracks']")
            audio_items = audio_container.find_elements(By.CSS_SELECTOR, "[role='menuitemradio']")

            for item in audio_items:
                track_name = item.text.strip()
                if track_name:
                    audio_tracks.append({
                        'name': track_name,
                        'element': item,
                        'lang': self._extract_lang_code(track_name)
                    })

        except NoSuchElementException:
            print("[Browser] Could not find audio track menu")
            # Try alternative method - get from manifest

        # Get subtitle tracks
        try:
            subtitle_container = self.driver.find_element(By.CSS_SELECTOR, "div._3-NwsFGsJi6SDgsAtChN1N, [class*='Subtitles'], [class*='ClosedCaptions']")
            subtitle_items = subtitle_container.find_elements(By.CSS_SELECTOR, "[role='menuitemradio']")

            for item in subtitle_items:
                track_name = item.text.strip()
                if track_name and track_name.lower() != 'none':
                    subtitle_tracks.append({
                        'name': track_name,
                        'element': item,
                        'lang': self._extract_lang_code(track_name)
                    })

        except NoSuchElementException:
            print("[Browser] Could not find subtitle track menu")

        print(f"[Browser] Found {len(audio_tracks)} audio tracks, {len(subtitle_tracks)} subtitle tracks")

        return audio_tracks, subtitle_tracks

    def _extract_lang_code(self, track_name):
        """Extract language code from track name"""
        lang_map = {
            'english': 'en',
            'spanish': 'es',
            'french': 'fr',
            'german': 'de',
            'italian': 'it',
            'portuguese': 'pt',
            'japanese': 'ja',
            'korean': 'ko',
            'chinese': 'zh',
            'russian': 'ru',
            'arabic': 'ar',
            'hindi': 'hi',
        }

        name_lower = track_name.lower()
        for lang, code in lang_map.items():
            if lang in name_lower:
                return code

        return 'und'  # Unknown

    def capture_manifest_and_keys(self):
        """Capture manifest URL and extract decryption keys from network traffic"""
        print("[Capture] Analyzing network traffic...")

        manifest_url = None
        license_url = None
        pssh_data = None
        keys = {}

        # Get performance logs
        logs = self.driver.get_log('performance')

        for log in logs:
            try:
                message = json.loads(log['message'])
                method = message.get('message', {}).get('method', '')
                params = message.get('message', {}).get('params', {})

                if method == 'Network.requestWillBeSent':
                    url = params.get('request', {}).get('url', '')

                    # Look for manifest
                    if '.mpd' in url or 'manifest' in url.lower():
                        if 'akamaized.net' in url or 'media-ma' in url:
                            manifest_url = url
                            print(f"[Capture] Found manifest: {url[:100]}...")

                    # Look for license server
                    if 'license' in url.lower() or 'widevine' in url.lower():
                        license_url = url

                elif method == 'Network.responseReceived':
                    url = params.get('response', {}).get('url', '')

                    if '.mpd' in url and not manifest_url:
                        manifest_url = url

            except Exception:
                continue

        if manifest_url:
            # Fetch manifest to get PSSH
            print("[Capture] Fetching manifest for PSSH...")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                    'Referer': 'https://moviesanywhere.com/',
                    'Origin': 'https://moviesanywhere.com'
                }
                response = requests.get(manifest_url, headers=headers)

                # Extract PSSH from manifest
                pssh_match = re.search(r'<cenc:pssh[^>]*>([^<]+)</cenc:pssh>', response.text)
                if pssh_match:
                    pssh_data = pssh_match.group(1)
                    print(f"[Capture] Found PSSH: {pssh_data[:50]}...")

                # Also try ContentProtection
                if not pssh_match:
                    pssh_match = re.search(r'pssh["\s:]+([A-Za-z0-9+/=]+)', response.text)
                    if pssh_match:
                        pssh_data = pssh_match.group(1)

            except Exception as e:
                print(f"[Capture] Error fetching manifest: {e}")

        # Get keys using pywidevine if we have PSSH
        if pssh_data and self.cdm:
            keys = self._get_keys_from_pssh(pssh_data, license_url)

        return {
            'manifest_url': manifest_url,
            'license_url': license_url,
            'pssh': pssh_data,
            'keys': keys
        }

    def _get_keys_from_pssh(self, pssh_data, license_url=None):
        """Extract decryption keys using pywidevine"""
        print("[Keys] Extracting keys with pywidevine...")

        keys = {}

        try:
            # Parse PSSH
            pssh = PSSH(pssh_data)

            # Open CDM session
            session_id = self.cdm.open()

            # Generate license challenge
            challenge = self.cdm.get_license_challenge(session_id, pssh)

            # We need to send challenge to license server
            # Movies Anywhere license URL
            if not license_url:
                license_url = "https://wv-keyos.licensekeyserver.com/"

            print(f"[Keys] Sending challenge to license server...")

            # This is a simplified version - actual implementation would need
            # proper headers and authentication from the browser session
            headers = {
                'Content-Type': 'application/octet-stream',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Origin': 'https://moviesanywhere.com',
                'Referer': 'https://moviesanywhere.com/'
            }

            # Note: This simplified version may not work for all content
            # The WidevineProxy2 extension handles this more robustly

        except Exception as e:
            print(f"[Keys] Error extracting keys: {e}")
            print("[Keys] Will try to use keys from WidevineProxy2 logs if available")

        return keys

    def download_track(self, manifest_url, keys, output_name, track_type="video"):
        """Download a single track using N_m3u8DL-RE"""
        print(f"[Download] Downloading {track_type}: {output_name}")

        cmd = [
            self.n_m3u8dl_re,
            manifest_url,
            "--save-name", output_name,
            "--save-dir", self.output_dir,
            "--auto-select",
            "--decryption-binary-path", self.mp4decrypt,
            "-H", "Referer: https://moviesanywhere.com/",
            "-H", "Origin: https://moviesanywhere.com",
        ]

        # Add keys
        for kid, key in keys.items():
            cmd.extend(["--key", f"{kid}:{key}"])

        # Add track selection based on type
        if track_type == "video":
            cmd.extend(["-dv", "false"])  # Don't drop video
        elif track_type == "audio":
            cmd.extend(["-sv", "none"])  # Select no video, just audio

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                print(f"[Download] Completed: {output_name}")
                return True
            else:
                print(f"[Download] Error: {result.stderr[:500]}")
                return False
        except subprocess.TimeoutExpired:
            print(f"[Download] Timeout downloading {output_name}")
            return False

    def mux_tracks(self, video_file, audio_files, subtitle_files, output_file):
        """Mux all tracks into final MKV"""
        print(f"[Mux] Creating final file: {output_file}")

        cmd = [self.ffmpeg, "-y"]

        # Add video
        cmd.extend(["-i", video_file])

        # Add audio files
        for audio in audio_files:
            cmd.extend(["-i", audio])

        # Add subtitle files
        for sub in subtitle_files:
            cmd.extend(["-i", sub])

        # Map all streams
        cmd.extend(["-map", "0:v"])  # Video from first input

        for i in range(len(audio_files)):
            cmd.extend(["-map", f"{i+1}:a"])  # Audio from subsequent inputs

        for i in range(len(subtitle_files)):
            cmd.extend(["-map", f"{i+1+len(audio_files)}:s"])  # Subtitles

        # Copy codecs
        cmd.extend(["-c", "copy"])

        # Output
        cmd.append(output_file)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                print(f"[Mux] Success: {output_file}")
                return True
            else:
                print(f"[Mux] Error: {result.stderr[:500]}")
                return False
        except Exception as e:
            print(f"[Mux] Exception: {e}")
            return False

    def download_movie(self, url, output_name=None):
        """Main method to download a complete movie"""
        print("=" * 60)
        print("Movies Anywhere Downloader")
        print("=" * 60)

        # Load CDM
        self.load_cdm()

        # Setup browser
        self.setup_browser()

        try:
            # Navigate to movie
            self.navigate_to_movie(url)

            # Wait for video to start loading
            time.sleep(5)

            # Capture manifest and keys
            capture_data = self.capture_manifest_and_keys()

            if not capture_data['manifest_url']:
                print("[Error] Could not capture manifest URL")
                print("[Info] Please use WidevineProxy2 extension to get manifest and keys")
                return None

            # Get available tracks
            audio_tracks, subtitle_tracks = self.get_available_tracks()

            # Generate output name if not provided
            if not output_name:
                # Try to get movie title from page
                try:
                    title = self.driver.title.replace(" - Movies Anywhere", "").strip()
                    output_name = re.sub(r'[^\w\s-]', '', title).replace(' ', '_')
                except:
                    output_name = "movie"

            print(f"\n[Info] Output name: {output_name}")
            print(f"[Info] Manifest: {capture_data['manifest_url'][:80]}...")
            print(f"[Info] Keys: {capture_data['keys']}")

            # Return capture data for manual processing if keys weren't extracted
            if not capture_data['keys']:
                print("\n" + "=" * 60)
                print("MANUAL KEY EXTRACTION REQUIRED")
                print("=" * 60)
                print("\nUse WidevineProxy2 extension to extract keys, then run:")
                print(f"\n  python3 moviesanywhere_dl.py --manifest '{capture_data['manifest_url']}' --key 'KID:KEY' --output '{output_name}'")
                print()

            return capture_data

        finally:
            if self.driver:
                self.driver.quit()

    def download_with_keys(self, manifest_url, keys, output_name):
        """Download movie with provided keys (from WidevineProxy2)"""
        print("=" * 60)
        print(f"Downloading: {output_name}")
        print("=" * 60)

        # Parse keys if string
        if isinstance(keys, str):
            keys_dict = {}
            for key_pair in keys.split(','):
                if ':' in key_pair:
                    kid, key = key_pair.strip().split(':')
                    keys_dict[kid] = key
            keys = keys_dict

        print(f"[Info] Manifest: {manifest_url[:80]}...")
        print(f"[Info] Keys: {len(keys)} key(s)")

        # Download with N_m3u8DL-RE
        cmd = [
            self.n_m3u8dl_re,
            manifest_url,
            "--save-name", output_name,
            "--save-dir", self.output_dir,
            "--auto-select",
            "--decryption-binary-path", self.mp4decrypt,
            "-H", "Referer: https://moviesanywhere.com/",
            "-H", "Origin: https://moviesanywhere.com",
            "-M", "format=mkv",
        ]

        # Add keys
        for kid, key in keys.items():
            cmd.extend(["--key", f"{kid}:{key}"])

        print(f"\n[Download] Starting download...")
        print(f"[Download] Command: {' '.join(cmd[:10])}...")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Stream output
            for line in process.stdout:
                print(line, end='')

            process.wait()

            if process.returncode == 0:
                print(f"\n[Download] SUCCESS!")
                # Find output file
                for ext in ['.mkv', '.mp4']:
                    output_path = os.path.join(self.output_dir, f"{output_name}{ext}")
                    if os.path.exists(output_path):
                        print(f"[Download] Output: {output_path}")
                        return output_path
            else:
                print(f"\n[Download] Failed with code {process.returncode}")

        except Exception as e:
            print(f"[Download] Error: {e}")

        return None


def main():
    parser = argparse.ArgumentParser(
        description='Movies Anywhere Downloader - Download movies with all audio and subtitle tracks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Browse mode - captures manifest and keys info
  python3 moviesanywhere_dl.py https://moviesanywhere.com/movie/... --cookies cookies.json --cdm cdm/

  # Direct download with keys from WidevineProxy2
  python3 moviesanywhere_dl.py --manifest 'https://...' --key 'KID:KEY' --output 'MovieName'
        """
    )

    parser.add_argument('url', nargs='?', help='Movies Anywhere movie URL')
    parser.add_argument('--cookies', '-c', default='cookies.json', help='Cookies file (JSON or Netscape format)')
    parser.add_argument('--cdm', default='cdm/', help='Path to CDM (.wvd file or directory)')
    parser.add_argument('--output', '-o', help='Output filename (without extension)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode')
    parser.add_argument('--no-headless', action='store_true', help='Show browser window')

    # Direct download options
    parser.add_argument('--manifest', '-m', help='Manifest URL (from WidevineProxy2)')
    parser.add_argument('--key', '-k', action='append', help='Decryption key(s) in KID:KEY format')

    args = parser.parse_args()

    # Determine headless mode
    headless = not args.no_headless

    # Initialize downloader
    downloader = MoviesAnywhereDownloader(
        cdm_path=args.cdm,
        cookies_path=args.cookies,
        output_dir='downloads',
        headless=headless
    )

    # Direct download mode
    if args.manifest and args.key:
        keys = {}
        for key_pair in args.key:
            if ':' in key_pair:
                kid, key = key_pair.split(':')
                keys[kid.strip()] = key.strip()

        output_name = args.output or 'movie'
        result = downloader.download_with_keys(args.manifest, keys, output_name)

        if result:
            print(f"\n✓ Download complete: {result}")
            return 0
        else:
            print("\n✗ Download failed")
            return 1

    # Browse mode
    elif args.url:
        result = downloader.download_movie(args.url, args.output)

        if result:
            print("\n" + "=" * 60)
            print("Capture complete!")
            print("=" * 60)
            return 0
        else:
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
