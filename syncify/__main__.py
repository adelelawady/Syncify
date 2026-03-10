"""CLI entry point for python -m syncify."""

import argparse
import sys

from syncify.spotify.Spotify_playlist_info import PlaylistDetails, get_playlist
from syncify.spotify.Spotify_track_info import TrackDetails, get_track
from syncify.spotify.utils import get_link_type


def _print_track(details: TrackDetails) -> None:
    print("Track:")
    print(f"  URL    : {details.spotify_url or '(empty)'}")
    print(f"  ID     : {details.track_id or '(empty)'}")
    print(f"  Title  : {details.track_title or '(empty)'}")
    print(f"  Artist : {details.artist_title or '(empty)'}")
    print(f"  Image  : {details.track_image_url or '(empty)'}")


def _print_playlist(details: PlaylistDetails) -> None:
    print("Playlist:")
    print(f"  URL    : {details.playlist_url or '(empty)'}")
    print(f"  ID     : {details.playlist_id or '(empty)'}")
    print(f"  Title  : {details.title or '(empty)'}")
    print(f"  Tracks : {len(details.track_urls)}")
    print(f"  Image  : {details.playlist_image_url or '(empty)'}")
    for i, url in enumerate(details.track_urls, 1):
        print(f"    {i:>3}. {url}")


def _run(urls: list[str]) -> int:
    for i, url in enumerate(urls, 1):
        link_type = get_link_type(url)
        print("=" * 60)
        print(f"[{i}] {url}")
        print(f"Type: {link_type or 'Invalid'}")

        if link_type == "Track":
            try:
                _print_track(get_track(url))
            except Exception as e:
                print(f"Error: {e}")
                return 1
        elif link_type == "Playlist":
            try:
                _print_playlist(get_playlist(url))
            except Exception as e:
                print(f"Error: {e}")
                return 1
        else:
            print("Invalid Spotify URL. Use track or playlist links.")
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch Spotify track or playlist details.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--track", metavar="URL", help="Fetch track details")
    group.add_argument("--playlist", metavar="URL", help="Fetch playlist details")
    parser.add_argument("urls", nargs="*", metavar="URL", help="Spotify URLs (auto-detect)")
    args = parser.parse_args()

    if args.track:
        urls = [args.track]
    elif args.playlist:
        urls = [args.playlist]
    elif args.urls:
        urls = args.urls
    else:
        print("Usage: python -m syncify <url> [url ...]")
        print("       python -m syncify --track <url>")
        print("       python -m syncify --playlist <url>")
        return 1
    return _run(urls)


if __name__ == "__main__":
    sys.exit(main())
