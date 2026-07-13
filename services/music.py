import os
import json
import subprocess
import glob
import re
import time
import requests
from config import DOWNLOAD_PATH, COBALT_API_URL


class MusicService:
    def __init__(self):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    def search(self, query: str, limit: int = 8) -> list[dict]:
        tracks = self._search_soundcloud(query, limit)
        if tracks:
            print(f"[SEARCH] Found {len(tracks)} SoundCloud results")
            return tracks

        print("[SEARCH] SoundCloud empty, trying YouTube")
        tracks = self._search_youtube(query, limit)
        if tracks:
            print(f"[SEARCH] Found {len(tracks)} YouTube results")
        return tracks

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
                        return tracks
                else:
                    print(f"[SC_SEARCH] stderr: {result.stderr[:200]}")
                time.sleep(1)
            except Exception as e:
                print(f"[SC_SEARCH] error: {e}")
                time.sleep(2)

        return []

    def _search_youtube(self, query: str, limit: int = 8) -> list[dict]:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            "--no-check-certificates",
            "--force-ipv4",
            f"ytsearch{limit}:{query}",
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
                                tracks.append({
                                    "id": data.get("id"),
                                    "title": data.get("title", "ناشناس"),
                                    "artist": data.get("uploader", "ناشناس"),
                                    "duration": int(duration),
                                    "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                                    "source": "youtube",
                                })
                            except:
                                continue
                    if tracks:
                        return tracks
                else:
                    print(f"[YT_SEARCH] stderr: {result.stderr[:200]}")
                time.sleep(1)
            except Exception as e:
                print(f"[YT_SEARCH] error: {e}")
                time.sleep(2)

        return []

    def download_with_progress(self, url: str, output_name: str, progress_callback=None) -> str | None:
        print(f"[DOWNLOAD] URL: {url}")
        print(f"[DOWNLOAD] Name: {output_name}")

        is_soundcloud = "soundcloud.com" in url or "api.soundcloud.com" in url
        is_youtube = "youtube.com" in url or "youtu.be" in url

        if is_soundcloud:
            print("[DOWNLOAD] Trying SoundCloud...")
            filepath = self._download_soundcloud(url, output_name, progress_callback)
            if filepath:
                print(f"[DOWNLOAD] SoundCloud OK: {filepath}")
                return filepath
            print("[DOWNLOAD] SoundCloud failed")

        if is_youtube:
            print("[DOWNLOAD] Trying cobalt...")
            filepath = self._download_cobalt(url, output_name, progress_callback)
            if filepath:
                print(f"[DOWNLOAD] Cobalt OK: {filepath}")
                return filepath
            print("[DOWNLOAD] Cobalt failed")

        print("[DOWNLOAD] Trying yt-dlp fallback...")
        filepath = self._download_yt_dlp(url, output_name, progress_callback)
        if filepath:
            print(f"[DOWNLOAD] yt-dlp OK: {filepath}")
            return filepath

        print("[DOWNLOAD] ALL METHODS FAILED")
        return None

    def _download_soundcloud(self, url: str, output_name: str, progress_callback=None) -> str | None:
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
            "--no-overwrites",
            url,
        ]

        try:
            if progress_callback:
                progress_callback(5)

            print(f"[SC_DL] Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            print(f"[SC_DL] Return code: {result.returncode}")
            print(f"[SC_DL] stdout: {result.stdout[-300:]}")
            print(f"[SC_DL] stderr: {result.stderr[-300:]}")

            if progress_callback:
                progress_callback(90)

            if result.returncode == 0:
                mp3_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.mp3"))
                if mp3_files:
                    filepath = mp3_files[0]
                    size = os.path.getsize(filepath)
                    print(f"[SC_DL] Found: {filepath} ({size} bytes)")
                    if progress_callback:
                        progress_callback(100)
                    return filepath

                print("[SC_DL] No MP3 file found after download")

        except subprocess.TimeoutExpired:
            print("[SC_DL] TIMEOUT after 300s")
        except Exception as e:
            print(f"[SC_DL] Exception: {e}")

        return None

    def _download_cobalt(self, url: str, output_name: str, progress_callback=None) -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, f"{output_name}.mp3")

        try:
            if progress_callback:
                progress_callback(5)

            print(f"[COBALT] API: {COBALT_API_URL}")
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            payload = {
                "url": url,
                "downloadMode": "audio",
                "audioFormat": "mp3",
            }

            response = requests.post(COBALT_API_URL, json=payload, headers=headers, timeout=30)
            print(f"[COBALT] Status: {response.status_code}")
            print(f"[COBALT] Body: {response.text[:200]}")

            if response.status_code == 200:
                data = response.json()
                if "url" in data:
                    download_url = data["url"]
                    if progress_callback:
                        progress_callback(20)

                    audio_response = requests.get(download_url, stream=True, timeout=300)
                    print(f"[COBALT] Download status: {audio_response.status_code}")

                    if audio_response.status_code == 200:
                        total_size = int(audio_response.headers.get("content-length", 0))
                        downloaded = 0

                        with open(output_path, "wb") as f:
                            for chunk in audio_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0 and progress_callback:
                                        percent = 20 + (downloaded / total_size) * 80
                                        progress_callback(min(percent, 95))

                        file_size = os.path.getsize(output_path)
                        print(f"[COBALT] Saved: {output_path} ({file_size} bytes)")

                        if file_size > 1000:
                            if progress_callback:
                                progress_callback(100)
                            return output_path

        except Exception as e:
            print(f"[COBALT] Exception: {e}")

        return None

    def _download_yt_dlp(self, url: str, output_name: str, progress_callback=None) -> str | None:
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
            "--retries", "3",
            "--force-ipv4",
            "--geo-bypass",
            url,
        ]

        for attempt in range(2):
            try:
                print(f"[YTDLP] Attempt {attempt+1}: {url}")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                print(f"[YTDLP] Return code: {result.returncode}")
                print(f"[YTDLP] stderr: {result.stderr[-300:]}")

                if result.returncode == 0:
                    mp3_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.mp3"))
                    if mp3_files:
                        return mp3_files[0]

                time.sleep(2)

            except subprocess.TimeoutExpired:
                print(f"[YTDLP] TIMEOUT attempt {attempt+1}")
            except Exception as e:
                print(f"[YTDLP] Exception: {e}")
                time.sleep(2)

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
