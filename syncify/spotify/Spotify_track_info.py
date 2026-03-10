"""
Spotify_track_info.py
---------------------
Lightweight helpers for working with Spotify track / playlist URLs and for
extracting metadata for a single Spotify track.

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
    track_id: str = ""
    track_title: str = ""
    artist_title: str = ""
    track_image_url: str = ""


def is_spotify_link(url: str) -> bool:
    """Return True if *url* is a Spotify track or playlist URL."""
    return bool(re.match(TRACK_REGEX, url) or re.match(PLAYLIST_REGEX, url))


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


def get_track(url: str) -> TrackDetails:
    """
    Fetch track metadata from a Spotify track URL.

    Args:
        url: Full Spotify track URL (e.g. https://open.spotify.com/track/...).

    Returns:
        TrackDetails with track_id, track_title, artist_title, track_image_url.
    """
    driver = _build_chrome_driver()
    details = TrackDetails(spotify_url=url)

    # Try to extract the track ID directly from the URL using TRACK_REGEX.
    match = re.match(TRACK_REGEX, url)
    if match:
        details.track_id = match.group(1)

    try:
        wait = WebDriverWait(driver, 30)

        # ── Step 1: Spotify page ──────────────────────────────────────────
        driver.get(url)
        track_name_el = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'span[data-testid="entityTitle"]')
            )
        )
        track_artist_el = driver.find_element(
            By.CSS_SELECTOR, 'a[data-testid="creator-link"]'
        )
        # Try to grab the main track artwork image from the header section.
        # Avoid relying on the dynamic class name (e.g. "fNnrSm2k2IonbI9c");
        # instead, use the stable "contentSpacing" class and Spotify image URL.
        try:
            track_img_el = driver.find_element(
                By.CSS_SELECTOR,
                "div.contentSpacing img[loading='lazy'][src^='https://i.scdn.co/image/']",
            )
            details.track_image_url = track_img_el.get_attribute("src") or ""
        except Exception:
            # Image URL is optional; keep it empty if not found.
            details.track_image_url = ""

        details.track_title = track_name_el.text.strip()
        details.artist_title = track_artist_el.text.strip()
        LOG.debug(
            "Spotify track: '%s' by '%s'", details.track_title, details.artist_title
        )

    except Exception as exc:
        LOG.debug("Error in get_track: %s", exc)
    finally:
        driver.quit()

    return details