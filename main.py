"""
Syncify - Spotify track and playlist metadata library.

Use as a library:
    from syncify import get_track, get_playlist, get_likes
    from syncify import TrackDetails, PlaylistDetails, LikesDetails

    track    = get_track("https://open.spotify.com/track/...")
    playlist = get_playlist("https://open.spotify.com/playlist/...")
    likes    = get_likes()          # opens browser, waits for Spotify login

Use as CLI:
    python main.py <url> [url ...]
    python -m syncify <url> [url ...]
    python -m syncify --track <url>
    python -m syncify --playlist <url>
    python -m syncify --likes
    python -m syncify --likes --login-timeout 180
"""

from syncify.spotify.Spotify_playlist_info import PlaylistDetails, get_playlist
from syncify.spotify.Spotify_track_info import TrackDetails, get_track
from syncify.spotify.Spotify_likes_info import LikesDetails, get_likes

__all__ = [
    "get_track", "get_playlist", "get_likes",
    "TrackDetails", "PlaylistDetails", "LikesDetails",
]

if __name__ == "__main__":
    import sys
    from syncify.__main__ import main
    sys.exit(main())