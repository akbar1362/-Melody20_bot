import os
import re
from urllib.parse import urlparse


def is_spotify_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in ("open.spotify.com", "spotify.com")


def is_soundcloud_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in (
        "soundcloud.com",
        "m.soundcloud.com",
        "on.soundcloud.com",
    )


def extract_spotify_id(url: str) -> tuple[str, str]:
    match = re.search(r"spotify\.com/(track|album|playlist)/([a-zA-Z0-9]+)", url)
    if match:
        return match.group(1), match.group(2)
    return None, None


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = name.strip()
    return name[:200] if len(name) > 200 else name


def format_duration(ms: int) -> str:
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def cleanup_file(filepath: str):
    if os.path.exists(filepath):
        os.remove(filepath)
