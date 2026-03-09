"""Syncify entry point."""

from syncify.spotify.Spotify_playlist_info import SpotifyPlaylistInfo
from syncify.spotify.Spotify_track_info import (
    TrackDetails,
    get_spotify_link_type,
    grape_youtube_video_id_from_spotify_url,
)


# Default test playlist URL (your Iraqi playlist)
TEST_PLAYLIST_URLS = [
    "https://open.spotify.com/playlist/5YOevUTnavVClJ0hAslu0N","https://open.spotify.com/track/5nJ4Zzqc2UjwSaIcv7bGjx"
]


def fetch_playlist_details(playlist_url: str):
    """
    Fetch Spotify playlist title and track URLs using SpotifyPlaylistInfo.
    ChromeDriver is managed automatically via webdriver-manager.

    Args:
        playlist_url: Full Spotify playlist URL (e.g. https://open.spotify.com/playlist/...).  # noqa: E501

    Returns:
        PlaylistDetails with .title and .track_urls.
    """
    info = SpotifyPlaylistInfo()
    return info.get_playlist_details(playlist_url)


def test_track_information(spotify_track_url: str) -> None:
    """
    Simple helper to test information gathering for a single Spotify track.

    It resolves the Spotify track URL to a TrackDetails model that includes:
    - the original Spotify URL
    - the detected track title and artist
    - the first matching YouTube video ID and full URL (when available)
    """
    if get_spotify_link_type(spotify_track_url) != "Track":
        raise ValueError("URL must be a Spotify track URL.")

    details: TrackDetails = grape_youtube_video_id_from_spotify_url(spotify_track_url)

    # Example usage of the TrackDetails model:
    print("Spotify track details:")
    print(f"  Spotify URL      : {details.spotify_url or '(empty)'}")
    print(f"  Track title      : {details.track_title or '(empty)'}")
    print(f"  Artist           : {details.artist_title or '(empty)'}")
    print(f"  YouTube video ID : {details.youtube_video_id or '(empty)'}")
    print(f"  YouTube URL      : {details.youtube_url or '(empty)'}")

    if not details.youtube_video_id:
        print("Could not resolve a YouTube video ID for this track.")


def run_for_urls(urls: list[str]) -> None:
    """
    For each given URL, detect its type and print information.

        - For playlist URLs: fetch playlist title and all track URLs (PlaylistDetails).
        - For track URLs: resolve and print TrackDetails for the first matching YouTube video.
    """
    for index, url in enumerate(urls, start=1):
        link_type = get_spotify_link_type(url)

        print("=" * 80)
        print(f"[{index}] URL: {url}")
        print(f"Type: {link_type}")

        if link_type == "Playlist":
            details = fetch_playlist_details(url)

            # Example usage of the PlaylistDetails model:
            print("Playlist details:")
            print(f"  Playlist title  : {details.title or '(empty)'}")
            print(f"  Number of tracks: {len(details.track_urls)}")
            print("  Track URLs:")
            for i, track_url in enumerate(details.track_urls, 1):
                print(f"    {i:>3}. {track_url}")

        elif link_type == "Track":
            test_track_information(url)

        else:
            print("Provided URL is not a valid Spotify track or playlist URL.")


if __name__ == "__main__":
    import sys

    # If user passes URLs on the command line, use those.
    # Otherwise, fall back to the built-in test playlist URL(s).
    if len(sys.argv) > 1:
        input_urls = sys.argv[1:]
    else:
        input_urls = TEST_PLAYLIST_URLS

    run_for_urls(input_urls)