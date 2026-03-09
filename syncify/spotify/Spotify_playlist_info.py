"""
spotify_playlist_info.py
------------------------
Standalone Python library to fetch Spotify playlist/track details.

Dependencies:
    pip install selenium beautifulsoup4 requests webdriver-manager

Usage:
    from spotify_playlist_info import SpotifyPlaylistInfo

    info = SpotifyPlaylistInfo()
    details = info.get_playlist_details("https://open.spotify.com/playlist/...")
    print(details.title)
    print(details.track_urls)
"""

import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------
TRACK_REGEX    = r"^https://open\.spotify\.com/track/([a-zA-Z0-9]+)$"
PLAYLIST_REGEX = r"^https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)$"


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------
@dataclass
class PlaylistDetails:
    """Holds the result of a playlist scrape."""
    # Use empty defaults so missing data is represented by empty fields.
    title: str = ""
    track_urls: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"PlaylistDetails(title={self.title!r}, tracks={len(self.track_urls)})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_spotify_link_type(url: str) -> Optional[str]:
    """Return 'Track', 'Playlist', or None."""
    if re.match(TRACK_REGEX, url):
        return "Track"
    if re.match(PLAYLIST_REGEX, url):
        return "Playlist"
    return None


def is_spotify_link(url: str) -> bool:
    """Return True if *url* is a valid Spotify track or playlist URL."""
    return bool(re.match(TRACK_REGEX, url) or re.match(PLAYLIST_REGEX, url))


def get_song_name_from_url(url: str) -> str:
    """
    Fetch a Spotify track page and extract the song title from the
    og:title meta tag.

    Args:
        url: A Spotify track URL.

    Returns:
        The song title string, or 'Song title not found.' on failure.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tag = soup.find("meta", property="og:title")
    if tag and tag.get("content"):
        return tag["content"]
    return "Song title not found."


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------
class SpotifyPlaylistInfo:
    """
    Scrapes a Spotify playlist page using Selenium (headless Chrome) and
    returns all track URLs along with the playlist title.
    Uses webdriver-manager to manage ChromeDriver automatically.

    Args:
        page_load_timeout:  Seconds to wait for the page to load (default 30).
        scroll_pause:       Seconds to pause between scroll steps (default 2).
        initial_wait:       Seconds to wait after first page load (default 10).
    """

    def __init__(
        self,
        page_load_timeout: int = 30,
        scroll_pause: float = 2.0,
        initial_wait: float = 10.0,
    ) -> None:
        self.page_load_timeout  = page_load_timeout
        self.scroll_pause       = scroll_pause
        self.initial_wait       = initial_wait
        self.playlist_title: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_playlist_details(self, url: str) -> PlaylistDetails:
        """
        Scrape all track URLs and the title from a Spotify playlist page.

        Args:
            url: Full Spotify playlist URL.

        Returns:
            A :class:`PlaylistDetails` instance.

        Raises:
            ValueError: If *url* is not a Spotify playlist link.
            Exception:  On any Selenium / network error.
        """
        if get_spotify_link_type(url) != "Playlist":
            raise ValueError(f"{url!r} is not a Spotify playlist link.")

        driver = self._build_driver()
        links_found: List[str] = []

        try:
            driver.set_page_load_timeout(self.page_load_timeout)
            driver.get(url)
            time.sleep(self.initial_wait)

            # ---- grab playlist title ----
            title_el = driver.find_element(
                By.CSS_SELECTOR, 'span[data-testid="entityTitle"]'
            )
            self.playlist_title = title_el.text

            # ---- scroll and collect track links, accounting for virtualized rows ----
            # The Spotify UI virtualizes the tracklist, so the number of DOM rows can
            # stay roughly constant while the actual songs change as you scroll.
            # To handle this, we:
            #   1) repeatedly scroll to the last visible row
            #   2) on each iteration, collect any new track URLs we see
            #   3) stop when we stop discovering new links for several iterations
            stable_loops = 0
            max_stable_loops = 5
            max_scrolls = 200
            prev_count = 0

            for _ in range(max_scrolls):
                # collect links currently in the DOM
                rows = driver.find_elements(
                    By.CSS_SELECTOR, 'div[data-testid="tracklist-row"]'
                )
                for row in rows:
                    try:
                        anchor = row.find_element(
                            By.CSS_SELECTOR, 'a[data-testid="internal-track-link"]'
                        )
                        href = anchor.get_attribute("href") or ""
                        if is_spotify_link(href) and href not in links_found:
                            links_found.append(href)
                    except Exception:
                        # Some rows may be ads or separators – skip them silently.
                        pass

                current_count = len(links_found)
                if current_count == prev_count:
                    stable_loops += 1
                    if stable_loops >= max_stable_loops:
                        break
                else:
                    stable_loops = 0
                    prev_count = current_count

                # scroll to the last visible row to trigger loading more items
                driver.execute_script(
                    """
                    const rows = document.querySelectorAll("div[data-testid='tracklist-row']");
                    if (rows.length) {
                        rows[rows.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                    """
                )
                time.sleep(self.scroll_pause)

        finally:
            driver.quit()

        return PlaylistDetails(title=self.playlist_title, track_urls=links_found)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _build_driver(self) -> webdriver.Chrome:
        """Construct and return a headless Chrome WebDriver.

        We rely on Selenium Manager to locate a matching ChromeDriver
        for the locally installed Chrome (no webdriver-manager needed).
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--incognito")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
        chrome_options.add_argument("--remote-allow-origins=*")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        # Selenium 4+ will download / locate the correct driver automatically.
        return webdriver.Chrome(options=chrome_options)


# ---------------------------------------------------------------------------
# Quick CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python spotify_playlist_info.py <spotify_playlist_url>")
        sys.exit(1)

    playlist_url = sys.argv[1]
    scraper = SpotifyPlaylistInfo()
    result = scraper.get_playlist_details(playlist_url)

    print(f"Playlist : {result.title}")
    print(f"Tracks   : {len(result.track_urls)}")
    for i, t in enumerate(result.track_urls, 1):
        print(f"  {i:>3}. {t}")