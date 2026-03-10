"""Syncify - Spotify track and playlist metadata library."""

from syncify.spotify.Spotify_playlist_info import PlaylistDetails, get_playlist
from syncify.spotify.Spotify_track_info import TrackDetails, get_track

__all__ = ["get_track", "get_playlist", "TrackDetails", "PlaylistDetails"]
