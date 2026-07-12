import os
import json
import subprocess
import glob
import re
import time
from config import DOWNLOAD_PATH


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
                if result.returncode == 0:
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
                        return tracks
                time.sleep(1)
            except Exception as e:
                print(f"Search attempt {attempt+1} failed: {e}")
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

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
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
                                "url": data.get("webpage_url") or data.get("url"),
                            })
                        except:
                            continue
                return tracks
        except Exception as e:
            print(f"SoundCloud search failed: {e}")

        return []

    def download_with_progress(self, url: str, output_name: str, progress_callback=None) -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, output_name)
        return self._download_yt_dlp(url, output_name, progress_callback)

    def _download_yt_dlp(self, url: str, output_name: str, progress_callback=None) -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, output_name)

        is_youtube = "youtube.com" in url or "youtu.be" in url

        base_cmd = [
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
        ]

        if is_youtube:
            clients = ["mediaconnect", "android", "tv_embedded"]
        else:
            clients = [None]

        for client in clients:
            cmd = list(base_cmd)
            if client:
                cmd.extend(["--extractor-args", f"youtube:player_client={client}"])
            cmd.append(url)

            for attempt in range(2):
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )

                    for line in iter(process.stdout.readline, ''):
                        if not line:
                            break
                        line = line.strip()

                        if "%" in line:
                            try:
                                match = re.search(r'(\d+\.?\d*)%', line)
                                if match:
                                    percent = float(match.group(1))
                                    if progress_callback:
                                        progress_callback(percent)
                            except:
                                pass

                    process.wait(timeout=300)

                    if process.returncode == 0:
                        mp3_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.mp3"))
                        if mp3_files:
                            return mp3_files[0]

                        for ext in ['*.webm', '*.m4a', '*.opus']:
                            files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}{ext}"))
                            for f in files:
                                new_name = f.rsplit('.', 1)[0] + '.mp3'
                                try:
                                    os.rename(f, new_name)
                                    return new_name
                                except:
                                    pass

                    time.sleep(2)

                except Exception as e:
                    print(f"yt-dlp attempt {attempt+1} (client={client}) error: {e}")
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
