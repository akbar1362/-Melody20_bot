import os
import subprocess
import json
import re
from config import DOWNLOAD_PATH
from utils.helpers import sanitize_filename, cleanup_file


class ConverterService:
    def __init__(self):
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)

    def download_from_youtube(self, search_query: str, output_filename: str) -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, output_filename)

        cmd = [
            "yt-dlp",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "320K",
            "--output", f"{output_path}.%(ext)s",
            "--no-playlist",
            f"ytsearch1:{search_query}",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return f"{output_path}.mp3"
        except subprocess.TimeoutExpired:
            pass

        return None

    def download_soundcloud(self, url: str, output_filename: str) -> str | None:
        output_path = os.path.join(DOWNLOAD_PATH, output_filename)

        cmd = [
            "scdl",
            "--path", DOWNLOAD_PATH,
            "--name", output_filename,
            "--onlymp3",
            "--no-art",
            f"--url={url}",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                possible_files = [
                    f for f in os.listdir(DOWNLOAD_PATH)
                    if f.startswith(output_filename) and f.endswith(".mp3")
                ]
                if possible_files:
                    return os.path.join(DOWNLOAD_PATH, possible_files[0])
        except subprocess.TimeoutExpired:
            pass

        return None

    def add_metadata(self, filepath: str, title: str, artist: str, album_art_path: str = None) -> bool:
        if not os.path.exists(filepath):
            return False

        cmd = ["ffmpeg", "-i", filepath, "-y"]

        if album_art_path and os.path.exists(album_art_path):
            cmd.extend(["-i", album_art_path])
            cmd.extend([
                "-map", "0:a", "-map", "1:v",
                "-c:v", "copy",
                "-id3v2_version", "3",
                "-metadata", f"title={title}",
                "-metadata", f"artist={artist}",
            ])
        else:
            cmd.extend([
                "-id3v2_version", "3",
                "-metadata", f"title={title}",
                "-metadata", f"artist={artist}",
            ])

        temp_output = filepath + ".tmp"
        cmd.append(temp_output)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                cleanup_file(filepath)
                os.rename(temp_output, filepath)
                return True
        except Exception:
            pass

        cleanup_file(temp_output)
        return False

    def search_youtube(self, query: str) -> str | None:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "id",
            "--playlist-items", "1",
            f"ytsearch1:{query}",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            pass

        return None
