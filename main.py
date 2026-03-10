"""
Syncify - Spotify track and playlist metadata library.

Use as a library:
    from syncify import get_track, get_playlist, TrackDetails, PlaylistDetails

    track = get_track("https://open.spotify.com/track/...")
    playlist = get_playlist("https://open.spotify.com/playlist/...")

Use as CLI:
    python main.py <url> [url ...]
    python -m syncify <url> [url ...]
    python -m syncify --track <url>
    python -m syncify --playlist <url>
"""

from syncify.spotify.Spotify_playlist_info import PlaylistDetails, get_playlist
from syncify.spotify.Spotify_track_info import TrackDetails, get_track

__all__ = ["get_track", "get_playlist", "TrackDetails", "PlaylistDetails"]

if __name__ == "__main__":
    import sys
    from syncify.__main__ import main
    sys.exit(main())
