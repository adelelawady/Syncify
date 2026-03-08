"""Syncify entry point."""

from syncify.spotify.Spotify_playlist_info import SpotifyPlaylistInfo
from syncify.spotify.Spotify_track_info import (
    get_spotify_link_type,
    grape_youtube_video_id_from_spotify_url,
)


def fetch_playlist_details(playlist_url: str):
    """
    Fetch Spotify playlist title and track URLs using SpotifyPlaylistInfo.
    ChromeDriver is managed automatically via webdriver-manager.

    Args:
        playlist_url: Full Spotify playlist URL (e.g. https://open.spotify.com/playlist/...).

    Returns:
        PlaylistDetails with .title and .track_urls.
    """
    info = SpotifyPlaylistInfo()
    return info.get_playlist_details(playlist_url)


def test_track_information(spotify_track_url: str) -> None:
    """
    Simple helper to test information gathering for a single Spotify track.

    It resolves the Spotify track URL to the first matching YouTube video ID
    (no downloading involved).
    """
    if get_spotify_link_type(spotify_track_url) != "Track":
        raise ValueError("URL must be a Spotify track URL.")

    video_id = grape_youtube_video_id_from_spotify_url(spotify_track_url)
    if not video_id:
        print("Could not resolve a YouTube video ID for this track.")
        return

    print(f"Resolved YouTube video ID: {video_id}")
    print(f"YouTube URL: https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python main.py <spotify_playlist_or_track_url>")
        sys.exit(1)

    url = sys.argv[1]
    link_type = get_spotify_link_type(url)

    if link_type == "Playlist":
        print(f"Fetching playlist details for: {url}")
        details = fetch_playlist_details(url)
        print(f"Playlist: {details.title}")
        print(f"Tracks:   {len(details.track_urls)}")
        for i, track_url in enumerate(details.track_urls, 1):
            print(f"  {i:>3}. {track_url}")
    elif link_type == "Track":
        print(f"Testing track information gathering for: {url}")
        test_track_information(url)
    else:
        print("Provided URL is not a valid Spotify track or playlist URL.")
        sys.exit(1)