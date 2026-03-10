"""Shared Spotify URL helpers."""

import re
from typing import Optional

TRACK_REGEX = r"^https://open\.spotify\.com/track/([a-zA-Z0-9]+)$"
PLAYLIST_REGEX = r"^https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)$"


def get_link_type(url: str) -> Optional[str]:
    """Return 'Track', 'Playlist', or None for invalid URLs."""
    if re.match(TRACK_REGEX, url):
        return "Track"
    if re.match(PLAYLIST_REGEX, url):
        return "Playlist"
    return None


def is_valid_link(url: str) -> bool:
    """Return True if url is a valid Spotify track or playlist URL."""
    return get_link_type(url) is not None
