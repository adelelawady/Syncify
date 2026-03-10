<!--
NOTE:
- This README assumes the GitHub repo will be published as: adelelawady/Syncify
- Update REPO_NAME below if you rename the repository.
-->

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/adelelawady/Syncify?style=for-the-badge)
![GitHub forks](https://img.shields.io/github/forks/adelelawady/Syncify?style=for-the-badge)
![License](https://img.shields.io/github/license/adelelawady/Syncify?style=for-the-badge)
![Repo size](https://img.shields.io/github/repo-size/adelelawady/Syncify?style=for-the-badge)
![Last commit](https://img.shields.io/github/last-commit/adelelawady/Syncify?style=for-the-badge)
![Issues](https://img.shields.io/github/issues/adelelawady/Syncify?style=for-the-badge)
![Top language](https://img.shields.io/github/languages/top/adelelawady/Syncify?style=for-the-badge)
![PyPI - Version](https://img.shields.io/pypi/v/syncify-py?style=for-the-badge)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/syncify-py?style=for-the-badge)
![PyPI - Downloads](https://img.shields.io/pypi/dm/syncify-py?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)

</div>

# 🚀 Syncify

**Syncify** is a Python **library + CLI** that fetches **Spotify track and playlist metadata** directly from `open.spotify.com` pages — great for quick metadata lookups, playlist introspection, and tooling where you don’t want to wire up OAuth.

> **Heads up**: Syncify scrapes Spotify’s web UI (via Selenium). Selectors can break if Spotify updates their site.

## ✨ Features

- **Track metadata**: title, artist, cover image URL, and track ID from a track URL
- **Playlist metadata**: playlist title, cover image URL, playlist ID, and **all track URLs**
- **CLI-first**: run `syncify <url>` or `python -m syncify ...`
- **Auto-detect URLs**: mix track + playlist URLs in one command
- **No OAuth setup**: does **not** require Spotify API keys/tokens

## 🧠 How It Works

- **Input**: Spotify track/playlist URLs (`https://open.spotify.com/track/...`, `https://open.spotify.com/playlist/...`)
- **URL detection**: a lightweight regex-based detector determines whether each URL is a Track or Playlist
- **Extraction**:
  - **Tracks**: Selenium loads the page and extracts title/artist/image from page elements
  - **Playlists**: Selenium loads the page, scrolls through the track list, and collects every track link
- **Output**:
  - **Library**: returns dataclasses (`TrackDetails`, `PlaylistDetails`)
  - **CLI**: prints a readable summary plus playlist track URLs

## 🛠 Tech Stack

- **Language**: Python
- **Automation/scraping**: Selenium (headless Chrome)
- **Driver management**: `webdriver-manager` (fallback if Selenium driver resolution fails)
- **HTML parsing (small helper)**: BeautifulSoup4
- **HTTP**: `requests`

## 📦 Installation

### Prerequisites

- **Python**: 3.9+ recommended (packaging allows older, but tested targets are 3.9–3.12)
- **Google Chrome** installed (used by Selenium)

### Install from PyPI (recommended)

```bash
pip install syncify-py
```

Then use:
- **CLI**: `syncify ...`
- **Python import**: `from syncify import ...`

### Install from GitHub (recommended)

```bash
pip install "git+https://github.com/adelelawady/Syncify.git"
```

### Install locally (for development)

```bash
git clone https://github.com/adelelawady/Syncify.git
cd Syncify
pip install -e ".[dev]"
```

### Install from source tree (non-editable)

```bash
pip install .
```

## ⚙️ Configuration

Syncify has **no required environment variables**.

### Runtime requirements

- **Chrome available on PATH / installed normally**
- **Chromedriver** is handled automatically via Selenium’s driver resolution, with a fallback to `webdriver-manager`.

### Troubleshooting

- If Selenium can’t start Chrome:
  - Ensure Chrome is installed and up to date.
  - Try upgrading Selenium and webdriver-manager:

```bash
pip install -U selenium webdriver-manager
```

- If playlist results are incomplete:
  - Spotify’s UI loads tracks lazily; the scraper scrolls, but very large playlists may take longer.

## 🚀 Usage

## **As a library**

```python
from syncify import get_track, get_playlist

track = get_track("https://open.spotify.com/track/5nJ4Zzqc2UjwSaIcv7bGjx")
print(track.track_title, "-", track.artist_title)
print(track.track_image_url)

playlist = get_playlist("https://open.spotify.com/playlist/5YOevUTnavVClJ0hAslu0N")
print(playlist.title)
print("Tracks:", len(playlist.track_urls))
print(playlist.track_urls[:5])
```

## **As a CLI**

After installation, you can use either:

- `syncify ...` (console script), or
- `python -m syncify ...` (module execution)

```bash
# Auto-detect URL type (track or playlist)
syncify https://open.spotify.com/track/5nJ4Zzqc2UjwSaIcv7bGjx
syncify https://open.spotify.com/playlist/5YOevUTnavVClJ0hAslu0N

# Explicit type
syncify --track https://open.spotify.com/track/...
syncify --playlist https://open.spotify.com/playlist/...

# Multiple URLs (mixed types supported)
syncify <url1> <url2> <url3>
```

CLI flags:

```bash
syncify --track <URL>
syncify --playlist <URL>
syncify <URL> [URL ...]
```

## 📡 API Reference

### `get_track(url: str) -> TrackDetails`

Fetch metadata for a Spotify track URL.

| Field | Type | Description |
|---|---:|---|
| `spotify_url` | `str` | Original Spotify URL |
| `track_id` | `str` | Spotify track ID |
| `track_title` | `str` | Song title |
| `artist_title` | `str` | Artist name |
| `track_image_url` | `str` | Cover image URL |

### `get_playlist(url: str) -> PlaylistDetails`

Fetch metadata for a Spotify playlist URL.

| Field | Type | Description |
|---|---:|---|
| `playlist_url` | `str` | Original Spotify URL |
| `playlist_id` | `str` | Spotify playlist ID |
| `title` | `str` | Playlist title |
| `playlist_image_url` | `str` | Cover image URL |
| `track_urls` | `list[str]` | Track URLs in the playlist |

## 📂 Project Structure

```text
Syncify/
├─ syncify/
│  ├─ __init__.py              # Public API exports
│  ├─ __main__.py              # CLI: `python -m syncify` / `syncify`
│  └─ spotify/
│     ├─ Spotify_track_info.py
│     ├─ Spotify_playlist_info.py
│     ├─ utils.py
│     └─ __init__.py
├─ main.py                     # Convenience script wrapper
├─ pyproject.toml              # Modern packaging + dependencies
├─ setup.py                    # Legacy packaging (mirrors pyproject)
├─ requirements.txt            # Dev-friendly requirements list
└─ README.md
```

## 🧪 Development

```bash
git clone https://github.com/adelelawady/Syncify.git
cd Syncify
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"

# Run the CLI against a URL
python -m syncify https://open.spotify.com/track/<id>
```

Suggested checks:

```bash
python -c "from syncify import get_track; print(get_track('https://open.spotify.com/track/<id>').track_title)"
```

## 🤝 Contributing

Contributions are welcome!

- **Bugs/requests**: open an issue with a minimal repro (URL + expected vs actual output)
- **PRs**:
  - Keep changes focused and include a clear description
  - Prefer small, well-scoped improvements to selectors and parsing logic
  - Avoid committing local artifacts (`.venv/`, `build/`, `syncify.egg-info/`)

If you’re adding new scraping logic, please include:
- A sample Spotify URL (track/playlist) that the change targets
- A note about which DOM selectors were relied on and why

## 📜 License

**MIT** (as declared in package metadata).

> Tip: consider adding a top-level `LICENSE` file so GitHub can display the license automatically.

## ⭐ Support

If you find Syncify useful, please **star** the repo — it helps others discover the project and motivates continued maintenance.
