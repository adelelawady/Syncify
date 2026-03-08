"""
youtube.py
----------
Utilities for resolving Spotify tracks to YouTube and downloading them
as MP3 files. This module is responsible for YouTube / download concerns,
while `spotify/Spotify_track_info.py` is kept as a Spotify-only helper.
"""

import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC

from syncify.spotify.Spotify_track_info import (
    is_spotify_link,
    extract_youtube_video_id,
    is_valid_youtube_url,
    grape_youtube_video_id_from_spotify_url,
)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
LOG = logging.getLogger("YouTubeDownloader")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class TrackInfo:
    """Holds metadata for a downloaded track."""

    spotify_url: str
    youtube_video_id: str = ""
    youtube_url: str = ""
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: str = ""
    year: str = ""
    duration_seconds: int = 0
    output_path: str = ""


# ---------------------------------------------------------------------------
# Audio metadata extraction
# ---------------------------------------------------------------------------
def extract_track_metadata(mp3_path: str, youtube_url: str) -> dict:
    """
    Read ID3 tags from the downloaded MP3 and return a metadata dict.
    Falls back to empty strings if a tag is missing.
    """
    metadata = {
        "title": "",
        "artist": "",
        "album": "",
        "genre": "",
        "year": "",
        "duration_seconds": 0,
    }

    path = Path(mp3_path)
    if not path.exists():
        raise FileNotFoundError(f"MP3 file not found: {mp3_path}")

    try:
        audio = MP3(mp3_path)
        metadata["duration_seconds"] = int(audio.info.length)

        tags = ID3(mp3_path)
        metadata["title"] = str(tags.get("TIT2", ""))
        metadata["artist"] = str(tags.get("TPE1", ""))
        metadata["album"] = str(tags.get("TALB", ""))
        metadata["genre"] = str(tags.get("TCON", ""))
        metadata["year"] = str(tags.get("TDRC", ""))
    except Exception as exc:
        LOG.debug("Could not read ID3 tags: %s", exc)

    return metadata


# ---------------------------------------------------------------------------
# yt-dlp download
# ---------------------------------------------------------------------------
def download_youtube_video_as_mp3(
    video_url: str,
    video_id: str,
    output_dir: str,
    ytdlp_path: str = "yt-dlp",
    ffmpeg_path: str = "ffmpeg",
    progress_callback=None,
) -> str:
    """
    Download a YouTube video as MP3 using yt-dlp.

    Args:
        video_url:        Full YouTube watch URL.
        video_id:         YouTube video ID (used for naming).
        output_dir:       Directory where the file will be saved.
        ytdlp_path:       Path to yt-dlp binary (default: system PATH).
        ffmpeg_path:      Path to ffmpeg binary (default: system PATH).
        progress_callback: Optional callable(line: str) for progress updates.

    Returns:
        Full path to the downloaded MP3 file.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, f"{video_id}.%(ext)s")

    cmd = [
        ytdlp_path,
        "-x",
        "--audio-format",
        "mp3",
        "--ffmpeg-location",
        ffmpeg_path,
        "-o",
        output_template,
        video_url,
    ]

    LOG.debug("Running: %s", " ".join(cmd))

    progress_pattern = re.compile(r"[a-zA-Z0-9@.]+")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    for line in process.stdout:
        line = line.rstrip()
        LOG.debug(line)

        if progress_callback:
            progress_callback(line)

        # Parse progress line: [download]   0.0% of 3.75MiB at 495KiB/s ETA 00:07
        if "[download]" in line and "ETA" in line:
            tokens = progress_pattern.findall(line)
            try:
                percentage = tokens[1]
                filesize = tokens[3]
                speed = tokens[5]
                eta = f"{tokens[8]}:{tokens[9]}"
                LOG.debug(
                    "Progress: %s%% | Size: %s | Speed: %s | ETA: %s",
                    percentage,
                    filesize,
                    speed,
                    eta,
                )
            except IndexError:
                pass

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(
            f"yt-dlp exited with code {process.returncode} for URL: {video_url}"
        )

    mp3_path = os.path.join(output_dir, f"{video_id}.mp3")
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(
            f"Expected MP3 not found after download: {mp3_path}"
        )

    LOG.debug("Download complete: %s", mp3_path)
    return mp3_path


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------
def add_spotify_song(
    spotify_url: str,
    output_dir: str = "downloads",
    ytdlp_path: str = "yt-dlp",
    ffmpeg_path: str = "ffmpeg",
    allow_duplicates: bool = False,
    progress_callback=None,
) -> TrackInfo:
    """
    Full pipeline: Spotify URL → YouTube ID → MP3 download → metadata.

    Args:
        spotify_url:       e.g. "https://open.spotify.com/track/..."
        output_dir:        Root folder for downloads.
        ytdlp_path:        Path/command for yt-dlp.
        ffmpeg_path:       Path/command for ffmpeg.
        allow_duplicates:  If False (default), raises if the output MP3
                           already exists on disk.
        progress_callback: Optional callable(line: str) for yt-dlp output.

    Returns:
        Populated TrackInfo dataclass.
    """
    if not is_spotify_link(spotify_url):
        raise ValueError(f"Not a valid Spotify track/playlist URL: {spotify_url}")

    LOG.debug("Processing Spotify URL: %s", spotify_url)

    # 1) Resolve YouTube video ID via Spotify page + YouTube search
    video_id = grape_youtube_video_id_from_spotify_url(spotify_url)
    if not video_id:
        raise RuntimeError(f"Could not find a YouTube video for: {spotify_url}")

    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    if not is_valid_youtube_url(youtube_url):
        raise ValueError(f"Resolved URL is not a valid YouTube URL: {youtube_url}")

    # 2) Duplicate check
    track_output_dir = os.path.join(output_dir, video_id)
    mp3_path = os.path.join(track_output_dir, f"{video_id}.mp3")

    if not allow_duplicates and os.path.exists(mp3_path):
        LOG.debug("Track already exists, skipping download: %s", mp3_path)
        raise FileExistsError(f"Track already downloaded: {mp3_path}")

    # 3) Download
    mp3_path = download_youtube_video_as_mp3(
        video_url=youtube_url,
        video_id=video_id,
        output_dir=track_output_dir,
        ytdlp_path=ytdlp_path,
        ffmpeg_path=ffmpeg_path,
        progress_callback=progress_callback,
    )

    # 4) Extract metadata
    metadata = extract_track_metadata(mp3_path, youtube_url)

    track = TrackInfo(
        spotify_url=spotify_url,
        youtube_video_id=video_id,
        youtube_url=youtube_url,
        output_path=mp3_path,
        **metadata,
    )

    LOG.debug("TrackInfo: %s", track)
    return track


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Download a Spotify track as MP3 via YouTube."
    )
    parser.add_argument("spotify_url", help="Spotify track URL")
    parser.add_argument(
        "--output-dir", default="downloads", help="Output directory (default: downloads)"
    )
    parser.add_argument(
        "--ytdlp", default="yt-dlp", help="Path to yt-dlp  (default: yt-dlp in PATH)"
    )
    parser.add_argument(
        "--ffmpeg", default="ffmpeg", help="Path to ffmpeg (default: ffmpeg in PATH)"
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Re-download even if the file already exists",
    )
    args = parser.parse_args()

    try:
        track_info = add_spotify_song(
            spotify_url=args.spotify_url,
            output_dir=args.output_dir,
            ytdlp_path=args.ytdlp,
            ffmpeg_path=args.ffmpeg,
            allow_duplicates=args.allow_duplicates,
        )
        print("\nDownload complete!")
        print(f"   Title   : {track_info.title}")
        print(f"   Artist  : {track_info.artist}")
        print(f"   Duration: {track_info.duration_seconds}s")
        print(f"   File    : {track_info.output_path}")
    except FileExistsError as e:
        print(f"{e}")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

