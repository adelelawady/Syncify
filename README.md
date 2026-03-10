# Syncify

A Python library to fetch Spotify track and playlist metadata. Use it as a library in your code or from the command line.

## Features

- **Track details** – Get title, artist, cover image, and track ID from any Spotify track URL
- **Playlist details** – Get playlist title, cover image, and all track URLs from any Spotify playlist URL
- **Simple API** – Two main functions: `get_track()` and `get_playlist()`
- **CLI** – Run from the terminal with URLs or flags

## Installation

```bash
pip install .
```

Or from source:

```bash
git clone <repo-url>
cd Syncify
pip install -e .
```

### Requirements

- Python 3.10+
- Chrome (for Selenium headless scraping)

## Usage

### As a library

```python
from syncify import get_track, get_playlist, TrackDetails, PlaylistDetails

# Get track details
track = get_track("https://open.spotify.com/track/5nJ4Zzqc2UjwSaIcv7bGjx")
print(track.track_title)      # Song title
print(track.artist_title)     # Artist name
print(track.track_image_url)  # Cover art URL
print(track.track_id)        # Spotify track ID

# Get playlist details
playlist = get_playlist("https://open.spotify.com/playlist/5YOevUTnavVClJ0hAslu0N")
print(playlist.title)        # Playlist name
print(playlist.track_urls)   # List of track URLs
print(playlist.playlist_image_url)  # Cover image URL
```

### As a CLI

```bash
# Auto-detect URL type (track or playlist)
python -m syncify https://open.spotify.com/track/5nJ4Zzqc2UjwSaIcv7bGjx
python -m syncify https://open.spotify.com/playlist/5YOevUTnavVClJ0hAslu0N

# Explicit type
python -m syncify --track https://open.spotify.com/track/...
python -m syncify --playlist https://open.spotify.com/playlist/...

# Multiple URLs
python -m syncify <url1> <url2> <url3>
```

After installation, use the `syncify` command directly:

```bash
syncify https://open.spotify.com/track/...
```

## API Reference

### `get_track(url: str) -> TrackDetails`

Fetches metadata for a Spotify track.

| Field           | Type  | Description                    |
|-----------------|-------|--------------------------------|
| `spotify_url`   | str   | Original Spotify URL           |
| `track_id`      | str   | Spotify track ID               |
| `track_title`   | str   | Song title                     |
| `artist_title`  | str   | Artist name                    |
| `track_image_url` | str | Cover art URL                  |

### `get_playlist(url: str) -> PlaylistDetails`

Fetches metadata for a Spotify playlist.

| Field               | Type  | Description              |
|---------------------|-------|--------------------------|
| `playlist_url`      | str   | Original Spotify URL     |
| `playlist_id`       | str   | Spotify playlist ID      |
| `title`             | str   | Playlist name            |
| `playlist_image_url`| str   | Cover image URL          |
| `track_urls`        | list  | List of track URLs       |

## License

MIT
