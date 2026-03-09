"""
Spotify_track_info.py
---------------------
Lightweight helpers for working with Spotify track / playlist URLs and for
resolving a Spotify track URL to a YouTube video ID.

This module is **Spotify‑only**: it does not download audio or touch yt-dlp.
Downloading and further processing are handled in a separate `youtube` module.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# Use a module-specific logger and keep external driver logs quiet.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
LOG = logging.getLogger("SpotifyTrackInfo")
logging.getLogger("WDM").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Regex helpers  (ported 1-to-1 from Java)
# ---------------------------------------------------------------------------
YOUTUBE_URL_REGEX = (
    r"^(?:https?://)?(?:www\.|m\.)?(?:youtube\.com/watch\?v=|youtu\.be/)"
    r"([a-zA-Z0-9_-]{11})"
)
YOUTUBE_URL_PATTERN = re.compile(YOUTUBE_URL_REGEX)

TRACK_REGEX = r"^https://open\.spotify\.com/track/([a-zA-Z0-9]+)$"
PLAYLIST_REGEX = r"^https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)$"


# ---------------------------------------------------------------------------
# Data model for track details
# ---------------------------------------------------------------------------
@dataclass
class TrackDetails:
    """
    Holds all gathered information for a single Spotify track.

    All string fields default to the empty string so that missing data
    is represented as empty fields instead of None.
    """

    spotify_url: str = ""
    track_title: str = ""
    artist_title: str = ""
    youtube_video_id: str = ""
    youtube_url: str = ""


def is_spotify_link(url: str) -> bool:
    """Return True if *url* is a Spotify track or playlist URL."""
    return bool(re.match(TRACK_REGEX, url) or re.match(PLAYLIST_REGEX, url))


def get_spotify_link_type(url: str) -> str:
    """Return 'Track', 'Playlist', or 'Invalid' based on the URL contents."""
    if "track" in url:
        return "Track"
    if "playlist" in url:
        return "Playlist"
    return "Invalid"


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Return the 11‑char YouTube video ID from a full URL, or None."""
    match = YOUTUBE_URL_PATTERN.match(url)
    return match.group(1) if match else None


def is_valid_youtube_url(url: str) -> bool:
    """Quick validation that a URL looks like a YouTube watch / short link."""
    return extract_youtube_video_id(url) is not None


# ---------------------------------------------------------------------------
# Selenium-based scraping
# ---------------------------------------------------------------------------
def _build_chrome_driver() -> webdriver.Chrome:
    """
    Create a headless Chrome WebDriver.

    We rely on Selenium Manager to locate a matching ChromeDriver for
    the locally installed Chrome (no webdriver-manager needed).
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--incognito")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    )
    options.add_argument("--remote-allow-origins=*")
    options.add_argument("--disable-dev-shm-usage")

    # Selenium 4+ will download / locate the correct driver automatically.
    return webdriver.Chrome(options=options)


def grape_youtube_video_id_from_spotify_url(spotify_url: str) -> TrackDetails:
    """
    Open the Spotify track page with Selenium, extract track name + artist,
    search YouTube, and return the first non‑ad video ID.

    Mirrors the original Java method: GrapeYoutubeVideoIdFromSpotifyUrl().
    This only discovers the YouTube ID; downloading happens in the
    separate `youtube` module.

    Returns:
        TrackDetails: populated with any information we were able to gather.
        If some values cannot be resolved, those fields remain empty strings.
    """
    driver = _build_chrome_driver()
    details = TrackDetails(spotify_url=spotify_url)

    try:
        wait = WebDriverWait(driver, 30)

        # ── Step 1: Spotify page ──────────────────────────────────────────
        driver.get(spotify_url)
        track_name_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'span[data-testid="entityTitle"]')
            )
        )
        track_artist_el = driver.find_element(
            By.CSS_SELECTOR, 'a[data-testid="creator-link"]'
        )

        details.track_title = track_name_el.text.strip()
        details.artist_title = track_artist_el.text.strip()
        LOG.debug(
            "Spotify track: '%s' by '%s'", details.track_title, details.artist_title
        )

        # ── Step 2: YouTube search ────────────────────────────────────────
        driver.get("https://www.youtube.com/")
        search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "search_query"))
        )
        search_box.send_keys(f"{details.track_title} {details.artist_title}")
        search_box.submit()

        # Wait briefly for results to render
        import time

        time.sleep(3)

        # ── Step 3: First non‑ad result ───────────────────────────────────
        results = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer")
        first_result = None
        for result in results:
            if not result.find_elements(By.CSS_SELECTOR, "ytd-ad-slot-renderer"):
                first_result = result
                break

        if first_result:
            title_element = first_result.find_element(By.ID, "video-title")
            video_url_raw = title_element.get_attribute("href") or ""
            details.youtube_url = video_url_raw
            LOG.debug("Found YouTube URL: %s", video_url_raw)
            details.youtube_video_id = extract_youtube_video_id(video_url_raw) or ""

        LOG.debug("YouTube video ID: %s", details.youtube_video_id)
        LOG.debug("YouTube video URL: %s", details.youtube_url)
        LOG.debug("Spotify URL: %s", details.spotify_url)
        LOG.debug("Track title: %s", details.track_title)
        LOG.debug("Artist: %s", details.artist_title)


    except Exception as exc:
        LOG.debug("Error in grape_youtube_video_id_from_spotify_url: %s", exc)
    finally:
        driver.quit()

    return details