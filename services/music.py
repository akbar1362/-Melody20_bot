import os
import json
import subprocess
import glob
import re
import time
import requests
from config import DOWNLOAD_PATH

def get_warp_proxy():
    proxy = os.environ.get("WARP_PROXY", "")
    if proxy:
        print(f"[WARP] Using proxy: {proxy}")
    return proxy

class MusicService:
    def __init__(self):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    def search(self, query: str, limit: int = 8) -> list[dict]:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--force-ipv4",
            f"ytsearch{limit}:{query}",
        ]

        for attempt in range(3):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0 and result.stdout.strip():
                    tracks = []
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            try:
                                data = json.loads(line)
                                duration = data.get("duration", 0) or 0
                                tracks.append({
                                    "id": data.get("id"),
                                    "title": data.get("title", "ناشناس"),
                                    "artist": data.get("uploader", "ناشناس"),
                                    "duration": int(duration),
                                    "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                                })
                            except:
                                continue
                    if tracks:
                        print(f"[SEARCH] Found {len(tracks)} results")
                        return tracks
                time.sleep(1)
            except Exception as e:
                print(f"[SEARCH] attempt {attempt+1} failed: {e}")
                time.sleep(2)

        return self._search_soundcloud(query, limit)

    def _search_soundcloud(self, query: str, limit: int = 8) -> list[dict]:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--force-ipv4",
            f"scsearch{limit}:{query}",
        ]

        for attempt in range(2):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0 and result.stdout.strip():
                    tracks = []
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            try:
                                data = json.loads(line)
                                duration = data.get("duration", 0) or 0
                                webpage_url = data.get("webpage_url") or data.get("url", "")
                                tracks.append({
                                    "id": data.get("id"),
                                    "title": data.get("title", "ناشناس"),
                                    "artist": data.get("uploader", "ناشناس"),
                                    "duration": int(duration),
                                    "url": webpage_url,
                                    "source": "soundcloud",
                                })
                            except:
                                continue
                    if tracks:
                        print(f"[SEARCH] SoundCloud fallback: {len(tracks)} results")
                        return tracks
                time.sleep(1)
            except Exception as e:
                print(f"[SC_SEARCH] error: {e}")
                time.sleep(2)

        return []

    def download_with_progress(self, url: str, output_name: str, progress_callback=None) -> str | None:
        print(f"[DOWNLOAD] URL: {url}")

        is_youtube = "youtube.com" in url or "youtu.be" in url

        if is_youtube:
            clients = ["mediaconnect", "android", "tv_embedded"]
            for client in clients:
                print(f"[DOWNLOAD] Trying YouTube ({client}) with WARP proxy...")
                filepath = self._download_youtube(url, output_name, progress_callback, client)
                if filepath:
                    print(f"[DOWNLOAD] YouTube ({client}) OK!")
                    return filepath
                print(f"[DOWNLOAD] YouTube ({client}) failed, trying next...")

        print(f"[DOWNLOAD] Trying direct yt-dlp (no proxy)...")
        filepath = self._download_yt_dlp_direct(url, output_name, progress_callback)
        if filepath:
            return filepath

        print("[DOWNLOAD] ALL METHODS FAILED")
        return None

    def _download_youtube(self, url: str, output_name: str, progress_callback=None, client="mediaconnect") -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, output_name)

        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "128K",
            "-o", f"{output_path}.%(ext)s",
            "--no-playlist",
            "--newline",
            "--no-check-certificates",
            "--force-ipv4",
            "--retries", "3",
            "--extractor-args", f"youtube:player_client={client}",
            url,
        ]

        proxy = get_warp_proxy()
        if proxy:
            cmd.insert(-1, "--proxy")
            cmd.insert(-1, proxy)

        try:
            if progress_callback:
                progress_callback(5)

            print(f"[YT_DL] Running with proxy: {client}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            print(f"[YT_DL] Return code: {result.returncode}")

            if result.returncode == 0:
                mp3_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.mp3"))
                if mp3_files:
                    filepath = mp3_files[0]
                    size = os.path.getsize(filepath)
                    print(f"[YT_DL] Found: {filepath} ({size} bytes)")
                    if progress_callback:
                        progress_callback(100)
                    return filepath

                for ext in ['*.webm', '*.m4a', '*.opus']:
                    files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}{ext}"))
                    for f in files:
                        new_name = f.rsplit('.', 1)[0] + '.mp3'
                        try:
                            os.rename(f, new_name)
                            return new_name
                        except:
                            pass
            else:
                stderr_short = result.stderr[-200:] if result.stderr else "none"
                print(f"[YT_DL] Failed: {stderr_short}")

        except subprocess.TimeoutExpired:
            print("[YT_DL] TIMEOUT")
        except Exception as e:
            print(f"[YT_DL] Exception: {e}")

        return None

    def _download_yt_dlp_direct(self, url: str, output_name: str, progress_callback=None) -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, output_name)

        is_youtube = "youtube.com" in url or "youtu.be" in url
        is_soundcloud = "soundcloud.com" in url or "api.soundcloud.com" in url

        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "128K",
            "-o", f"{output_path}.%(ext)s",
            "--no-playlist",
            "--newline",
            "--no-check-certificates",
            "--retries", "3",
            "--force-ipv4",
        ]

        if is_youtube:
            cmd.extend(["--extractor-args", "youtube:player_client=mediaconnect"])

        cmd.append(url)

        try:
            if progress_callback:
                progress_callback(5)

            print(f"[DL_DIRECT] Running direct download")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            print(f"[DL_DIRECT] Return code: {result.returncode}")

            if result.returncode == 0:
                mp3_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.mp3"))
                if mp3_files:
                    filepath = mp3_files[0]
                    size = os.path.getsize(filepath)
                    print(f"[DL_DIRECT] Found: {filepath} ({size} bytes)")
                    if progress_callback:
                        progress_callback(100)
                    return filepath

                for ext in ['*.webm', '*.m4a', '*.opus']:
                    files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}{ext}"))
                    for f in files:
                        new_name = f.rsplit('.', 1)[0] + '.mp3'
                        try:
                            os.rename(f, new_name)
                            return new_name
                        except:
                            pass
            else:
                stderr_short = result.stderr[-200:] if result.stderr else "none"
                print(f"[DL_DIRECT] Failed: {stderr_short}")

        except subprocess.TimeoutExpired:
            print("[DL_DIRECT] TIMEOUT")
        except Exception as e:
            print(f"[DL_DIRECT] Exception: {e}")

        return None

    def compress_file(self, filepath: str, max_size_mb: int = 50) -> str | None:
        file_size = os.path.getsize(filepath)
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size <= max_size_bytes:
            return filepath

        compressed_path = filepath.replace('.mp3', '_compressed.mp3')

        bitrate = 128
        if file_size > 100 * 1024 * 1024:
            bitrate = 64
        elif file_size > 70 * 1024 * 1024:
            bitrate = 96

        cmd = [
            "ffmpeg",
            "-i", filepath,
            "-codec:a", "libmp3lame",
            "-b:a", f"{bitrate}k",
            "-y",
            compressed_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                new_size = os.path.getsize(compressed_path)
                if new_size <= max_size_bytes:
                    os.remove(filepath)
                    return compressed_path
                else:
                    os.remove(compressed_path)
        except Exception as e:
            print(f"Compress error: {e}")

        return filepath

    def download(self, url: str, output_name: str) -> str | None:
        return self.download_with_progress(url, output_name)
