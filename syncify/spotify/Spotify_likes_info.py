"""
Spotify_likes_info.py
---------------------
Fetches all tracks from a user's Spotify Liked Songs.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from syncify.spotify.utils import is_valid_link


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
LOG = logging.getLogger("SpotifyLikesInfo")
logging.getLogger("WDM").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

LOGIN_URL  = "https://accounts.spotify.com/en/login?continue=https%3A%2F%2Fopen.spotify.com%2Fcollection%2Ftracks"
LIKES_HOST = "open.spotify.com"
LIKES_PATH = "/collection/tracks"


@dataclass
class LikesDetails:
    playlist_url: str = "https://open.spotify.com/collection/tracks"
    playlist_id: str = "LIKED"
    title: str = "Liked Songs"
    playlist_image_url: str = "https://misc.scdn.co/liked-songs/liked-songs-300.jpg"
    track_urls: List[str] = field(default_factory=list)

    @property
    def total_tracks(self) -> int:
        return len(self.track_urls)

    def __repr__(self) -> str:
        return f"LikesDetails(total_tracks={self.total_tracks}, title ={self.title} , playlist_image_url={self.playlist_image_url})"


def get_likes(login_timeout: int = 120, page_load_timeout: int = 30, scroll_pause: float = 2.0) -> LikesDetails:
    return SpotifyLikesInfo(login_timeout=login_timeout, page_load_timeout=page_load_timeout, scroll_pause=scroll_pause).get_likes()


class SpotifyLikesInfo:

    _POLL_INTERVAL: float = 2.0
    _DUMP_INTERVAL: float = 5.0

    def __init__(self, login_timeout: int = 120, page_load_timeout: int = 30, scroll_pause: float = 2.0) -> None:
        self.login_timeout     = login_timeout
        self.page_load_timeout = page_load_timeout
        self.scroll_pause      = scroll_pause
        self.playlist_title: str = ""
        self.playlist_image_url: str = ""

    def get_likes(self) -> LikesDetails:
        driver  = self._build_driver()
        details = LikesDetails()
        try:
            driver.set_page_load_timeout(self.page_load_timeout)
            LOG.info("Opening Spotify login page…")
            driver.get(LOGIN_URL)
            LOG.info("Waiting up to %d seconds for login + page render…", self.login_timeout)
            tracklist_sel, row_sel, link_sel = self._wait_until_ready(driver)
            LOG.info("Page ready — starting to collect tracks.")
            links_found = self._collect_track_urls(driver, tracklist_sel, row_sel, link_sel)
        finally:
            driver.quit()
        details.track_urls = links_found
        details.title = self.playlist_title
        details.playlist_image_url = self.playlist_image_url
        LOG.info("Collected %d liked tracks.", details.total_tracks)
        LOG.info(details)
        return details

    # ------------------------------------------------------------------
    # Readiness detection
    # ------------------------------------------------------------------
    def _wait_until_ready(self, driver: webdriver.Chrome):
        """
        Phase 1 – wait for URL to be the likes page.
        Phase 2 – dump DOM every 5s and try every possible selector combo
                  until we find one that returns track links.
        Returns (tracklist_sel, row_sel, link_sel) once found.
        """
        deadline      = time.monotonic() + self.login_timeout
        last_url      = ""
        phase         = 1
        last_dump     = 0.0

        while time.monotonic() < deadline:
            try:
                current_url = driver.current_url
            except WebDriverException:
                time.sleep(self._POLL_INTERVAL)
                continue

            if current_url != last_url:
                LOG.info("URL → %s", current_url)
                last_url = current_url

            # Phase 1
            if phase == 1:
                if self._is_likes_url(current_url):
                    LOG.info("Phase 1 ✓ — on likes URL, probing DOM…")
                    phase = 2
                else:
                    time.sleep(self._POLL_INTERVAL)
                    continue

            # Phase 2 — dump DOM periodically and probe for any working selectors
            now = time.monotonic()
            if now - last_dump >= self._DUMP_INTERVAL:
                self._dump_dom(driver)
                last_dump = now

            result = self._probe_selectors(driver)
            if result:
                t_sel, r_sel, l_sel, count = result
                LOG.info(
                    "Phase 2 ✓ — found %d links with:\n"
                    "  tracklist : %s\n  row       : %s\n  link      : %s",
                    count, t_sel, r_sel, l_sel,
                )
                return t_sel, r_sel, l_sel

            time.sleep(self._POLL_INTERVAL)

        raise TimeoutException(
            f"Likes page not ready within {self.login_timeout} seconds."
        )

    def _probe_selectors(self, driver: webdriver.Chrome):
        """
        Try a wide range of selector combos via JS.
        Returns (tracklist_sel, row_sel, link_sel, count) on first match, else None.
        """
        # Each entry: (description, js_query_returning_count)
        probes = [
            # Confirmed combo from previous diagnostic run
            (
                '[role="list"]', '[data-testid="tracklist-row"]', 'a[data-testid="internal-track-link"]',
                'return document.querySelectorAll(\'[role="list"] [data-testid="tracklist-row"] a[data-testid="internal-track-link"]\').length'
            ),
            # Without tracklist parent
            (
                '(any)', '[data-testid="tracklist-row"]', 'a[data-testid="internal-track-link"]',
                'return document.querySelectorAll(\'[data-testid="tracklist-row"] a[data-testid="internal-track-link"]\').length'
            ),
            # Any internal-track-link anywhere
            (
                '(any)', '(any)', 'a[data-testid="internal-track-link"]',
                'return document.querySelectorAll(\'a[data-testid="internal-track-link"]\').length'
            ),
            # Any link to /track/
            (
                '(any)', '(any)', 'a[href*="/track/"]',
                'return document.querySelectorAll(\'a[href*="/track/"]\').length'
            ),
            # role=row inside role=list
            (
                '[role="list"]', '[role="row"]', 'a[href*="/track/"]',
                'return document.querySelectorAll(\'[role="list"] [role="row"] a[href*="/track/"]\').length'
            ),
            # role=listitem
            (
                '[role="list"]', '[role="listitem"]', 'a[href*="/track/"]',
                'return document.querySelectorAll(\'[role="list"] [role="listitem"] a[href*="/track/"]\').length'
            ),
            # grid
            (
                '[role="grid"]', '[role="row"]', 'a[href*="/track/"]',
                'return document.querySelectorAll(\'[role="grid"] [role="row"] a[href*="/track/"]\').length'
            ),
        ]

        for t_sel, r_sel, l_sel, js in probes:
            count = self._js(driver, js) or 0
            LOG.debug("Probe [%s > %s > %s] → %d", t_sel, r_sel, l_sel, count)
            if count > 0:
                return t_sel, r_sel, l_sel, count

        return None

    def _dump_dom(self, driver: webdriver.Chrome) -> None:
        """Log a full DOM snapshot to identify what's actually rendered."""
        try:
            testids = self._js(driver, """
                return [...new Set(
                    [...document.querySelectorAll('[data-testid]')]
                    .map(el => el.getAttribute('data-testid'))
                )].sort();
            """) or []

            roles = self._js(driver, """
                return [...new Set(
                    [...document.querySelectorAll('[role]')]
                    .map(el => el.getAttribute('role'))
                )].sort();
            """) or []

            track_hrefs = self._js(driver,
                "return document.querySelectorAll('a[href*=\"/track/\"]').length"
            ) or 0

            all_links = self._js(driver,
                "return [...document.querySelectorAll('a[href]')].map(a=>a.href).filter(h=>h.includes('spotify')).slice(0,20);"
            ) or []

            body_text = self._js(driver,
                "return document.body ? document.body.innerText.slice(0, 300) : '(no body)'"
            ) or ""

            LOG.info("── DOM snapshot ──────────────────────────────")
            LOG.info("readyState       : %s", self._js(driver, "return document.readyState"))
            LOG.info("data-testid list : %s", testids)
            LOG.info("role list        : %s", roles)
            LOG.info("a[href*/track/]  : %d", track_hrefs)
            LOG.info("spotify links    : %s", all_links)
            LOG.info("body text        : %s", body_text.replace('\n', ' '))
            LOG.info("──────────────────────────────────────────────")
        except Exception as exc:
            LOG.debug("DOM dump error: %s", exc)

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------
    def _collect_track_urls(self, driver: webdriver.Chrome, tracklist_sel: str, row_sel: str, link_sel: str) -> List[str]:
        
        # ---- grab playlist title ----
        title_el = driver.find_element(
            By.CSS_SELECTOR, 'span[data-testid="entityTitle"]'
        )
        self.playlist_title = title_el.text
        # ---- grab playlist image URL (mosaic cover) ----
        # The main playlist image is rendered inside a container with
        # data-testid="playlist-image", which holds an <img> whose src is
        # the mosaic URL like the one you provided.
        self.playlist_image_url = ""
        try:
            image_el = driver.find_element(
                By.CSS_SELECTOR, 'div[data-testid="playlist-image"] img'
            )
            self.playlist_image_url = image_el.get_attribute("src") or ""
        except Exception:
             # If we fail to locate the image, keep the field empty.
            self.playlist_image_url = ""
        
        
        links_found: List[str] = []
        stable_loops     = 0
        max_stable_loops = 5
        max_scrolls      = 500
        prev_count       = 0

        # Build the most specific query we can
        if tracklist_sel.startswith("("):
            full_row_sel = row_sel if not row_sel.startswith("(") else ""
        else:
            full_row_sel = f"{tracklist_sel} {row_sel}" if not row_sel.startswith("(") else tracklist_sel

        full_link_sel = link_sel

        LOG.info("Collecting with row_sel=%r  link_sel=%r", full_row_sel or row_sel, link_sel)

        for _ in range(max_scrolls):
            if full_row_sel:
                rows = driver.find_elements(By.CSS_SELECTOR, full_row_sel)
            else:
                rows = driver.find_elements(By.CSS_SELECTOR, row_sel)

            if not rows:
                # broadest fallback: grab all matching links directly
                anchors = driver.find_elements(By.CSS_SELECTOR, full_link_sel)
                for anchor in anchors:
                    try:
                        href = anchor.get_attribute("href") or ""
                        if is_valid_link(href) and href not in links_found:
                            links_found.append(href)
                    except StaleElementReferenceException:
                        pass
            else:
                for row in rows:
                    try:
                        anchor = row.find_element(By.CSS_SELECTOR, full_link_sel)
                        href   = anchor.get_attribute("href") or ""
                        if is_valid_link(href) and href not in links_found:
                            links_found.append(href)
                    except (NoSuchElementException, StaleElementReferenceException):
                        pass

            current_count = len(links_found)
            #LOG.info("Scroll %d: %d tracks found", scroll_num + 1, current_count)

            if current_count == prev_count:
                stable_loops += 1
                if stable_loops >= max_stable_loops:
                    LOG.info("No new tracks for %d scrolls — done.", max_stable_loops)
                    break
            else:
                stable_loops = 0
                prev_count   = current_count

            


            driver.execute_script(
                    """
                    const rows = document.querySelectorAll(
                        "div[data-testid='track-list'] div[data-testid='tracklist-row']"
                    );
                    if (rows.length) {
                        rows[rows.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                    """
            )
            time.sleep(self.scroll_pause)

        return links_found

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _is_likes_url(url: str) -> bool:
        try:
            bare = url.lower()
            for scheme in ("https://", "http://"):
                if bare.startswith(scheme):
                    bare = bare[len(scheme):]
                    break
            bare = bare.split("#")[0].split("?")[0].rstrip("/")
            host, _, path = bare.partition("/")
            return host == LIKES_HOST and ("/" + path) == LIKES_PATH
        except Exception:
            return False

    @staticmethod
    def _js(driver: webdriver.Chrome, script: str):
        try:
            return driver.execute_script(script)
        except WebDriverException:
            return None

    def _build_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        options.add_argument("--remote-allow-origins=*")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1280,900")
        try:
            return webdriver.Chrome(options=options)
        except WebDriverException:
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)


if __name__ == "__main__":
    import sys
    login_timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    result = SpotifyLikesInfo(login_timeout=login_timeout).get_likes()
    print(f"\nTotal liked tracks : {result.total_tracks}")
    for i, url in enumerate(result.track_urls, 1):
        print(f"  {i:>4}. {url}")
