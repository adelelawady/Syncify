"""Shared Spotify URL helpers."""

import re
from urllib.parse import urlparse
from typing import Optional

_ID = r"([a-zA-Z0-9]+)"
TRACK_REGEX = rf"^https?://open\.spotify\.com/track/{_ID}/?$"
PLAYLIST_REGEX = rf"^https?://open\.spotify\.com/playlist/{_ID}/?$"


def canonicalize_spotify_url(url: str) -> str:
    """
    Strip query/fragment and normalize for matching.

    Spotify links often include tracking params like '?si=...'.
    """
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return url.strip()
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def get_link_type(url: str) -> Optional[str]:
    """Return 'Track', 'Playlist', or None for invalid URLs."""
    canonical = canonicalize_spotify_url(url)
    if re.match(TRACK_REGEX, canonical):
        return "Track"
    if re.match(PLAYLIST_REGEX, canonical):
        return "Playlist"
    return None


def is_valid_link(url: str) -> bool:
    """Return True if url is a valid Spotify track or playlist URL."""
    return get_link_type(url) is not None
