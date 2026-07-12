import os
import json
import subprocess
import glob
import re
import tempfile
from config import DOWNLOAD_PATH


class MusicService:
    def __init__(self):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    def search(self, query: str, limit: int = 10) -> list[dict]:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--dump-json",
            "--no-warnings",
            f"ytsearch{limit}:{query}",
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
                                "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                                "thumbnail": data.get("thumbnail", ""),
                            })
                        except json.JSONDecodeError:
                            continue
                return tracks
        except Exception as e:
            print(f"Search error: {e}")

        return []

    def download_with_progress(self, url: str, output_name: str, progress_callback=None) -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, output_name)

        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "-o", f"{output_path}.%(ext)s",
            "--no-playlist",
            "--newline",
            "--no-check-certificates",
            "--extractor-args", "youtube:skip=hls,use_ssl=True",
            url,
        ]

        try:
            print(f"Starting download: {url}")
            print(f"Command: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            output_lines = []
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                line = line.strip()
                output_lines.append(line)
                print(f"yt-dlp: {line}")

                if "%" in line:
                    try:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            percent = float(match.group(1))
                            if progress_callback:
                                progress_callback(percent)
                    except Exception as e:
                        pass

            process.wait(timeout=300)

            print(f"Process return code: {process.returncode}")

            if process.returncode == 0:
                mp3_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.mp3"))
                if mp3_files:
                    print(f"Found MP3: {mp3_files[0]}")
                    return mp3_files[0]

                webm_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.webm"))
                for f in webm_files:
                    new_name = f.rsplit('.', 1)[0] + '.mp3'
                    try:
                        os.rename(f, new_name)
                        print(f"Renamed to: {new_name}")
                        return new_name
                    except:
                        pass

                m4a_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*.m4a"))
                for f in m4a_files:
                    new_name = f.rsplit('.', 1)[0] + '.mp3'
                    try:
                        os.rename(f, new_name)
                        print(f"Renamed to: {new_name}")
                        return new_name
                    except:
                        pass

                all_files = glob.glob(os.path.join(DOWNLOAD_PATH, f"{output_name}*"))
                print(f"All matching files: {all_files}")

            else:
                error_msg = "\n".join(output_lines[-5:]) if output_lines else "Unknown error"
                print(f"Download failed: {error_msg}")

        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except:
                pass
            print("Download timeout")
        except Exception as e:
            print(f"Download error: {e}")

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
