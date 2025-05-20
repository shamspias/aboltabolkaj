"""
Ekamed Center – **full‑site plain‑text crawler** (Playwright 1.52+, 2025‑05‑16)

What it does
------------
* Starts at ``https://www.ekamedcenter.ru/`` and **recursively follows every internal link** that
  • begins with ``/`` **and**
  • stays on the same domain.
* Visits **each unique page once**, strips ``<header>``, ``<footer>``, ``<script>``, ``<style>`` and
  returns **plain, tag‑free body text**.
* Saves all texts to ``pages_plain.json`` *(UTF‑8 JSON array)*.
* For every page it also **POSTs** the text to your Dify chat endpoint (same as before) and stores
  the LLM’s ``answer`` in ``parsed_data/response_<n>.txt``.

Install
-------
python -m pip install playwright==1.52.* beautifulsoup4 lxml
python -m playwright install            # one‑time browser download
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

# ── Constants ──────────────────────────────────────────────────────────────
BASE_URL = "https://shamspias.com"
START_URL = f"{BASE_URL}/"  # root – crawl everything that stays on this domain
OUTPUT_PATH = Path("pages_plain.json")
HEADERS_TO_REMOVE = {"header", "footer", "script", "style"}

USER_AGENTS: tuple[str, ...] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/18.0 Safari/605.1.15",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("ekamed-crawler")


# ── Scraper ────────────────────────────────────────────────────────────────
@dataclass
class EkamedCrawler:
    """Context‑managed **full‑site crawler** that yields plain text for every page."""

    headless: bool = True
    timeout: int = 15_000  # Playwright timeout (ms)
    max_pages: int | None = None  # ``None`` ⇒ no limit (crawl everything)

    _pw: Playwright | None = field(init=False, default=None, repr=False)
    _browser: Browser | None = field(init=False, default=None, repr=False)

    # ── context‑manager hooks ─────────────────────────────────────────────
    def __enter__(self) -> "EkamedCrawler":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.headless)
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    # ── public API ────────────────────────────────────────────────────────
    def run(self) -> List[str]:
        """Return **plain‑text bodies** for *all* pages on the domain."""

        to_visit: deque[str] = deque([START_URL])
        visited: Set[str] = set()
        bodies: List[str] = []

        while to_visit and (self.max_pages is None or len(visited) < self.max_pages):
            url = to_visit.popleft()
            if url in visited:
                continue
            visited.add(url)

            try:
                text, links = self._scrape_page(url)
            except Exception as err:  # noqa: BLE001
                logger.error("Failed %s — %s", url, err)
                continue

            bodies.append(text)
            logger.info("%d pages scraped — queue: %d", len(visited), len(to_visit))

            # Enqueue new internal links
            for link in links:
                if link.startswith("/"):
                    link = f"{BASE_URL}{link}"
                if link.startswith(BASE_URL) and link not in visited:
                    to_visit.append(link)

        return bodies

    # ── helpers ──────────────────────────────────────────────────────────
    def _new_page(self) -> Page:
        ctx = self._browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
            ignore_https_errors=True,
        )
        page = ctx.new_page()
        page.set_default_timeout(self.timeout)
        return page

    def _scrape_page(self, url: str) -> tuple[str, List[str]]:
        """Return *(plain_text, internal_links)* for one page."""
        page = self._new_page()
        page.goto(url, wait_until="domcontentloaded")
        html = page.content()
        page.close()

        soup = BeautifulSoup(html, "lxml")

        # Remove unwanted global blocks
        for tag_name in HEADERS_TO_REMOVE:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        plain_text = soup.body.get_text("\n", strip=True) if soup.body else ""

        # Extract internal links (anchor hrefs that look like site pages)
        internal_links: List[str] = []
        for a in soup.find_all("a", href=True):
            href: str = a["href"]
            if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
                continue
            internal_links.append(href)

        return plain_text, internal_links


# ── CLI entrypoint ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # ── Configuration for Dify API ────────────────────────────────────────
    API_URL = "https://codeai.club/v1"
    API_KEY = "app-api-key"
    USER_ID = os.getenv("DIFY_USER_ID", str(random.randint(1, 100)))

    if not API_KEY:
        raise RuntimeError("Please set the DIFY_API_KEY environment variable")

    parsed_dir = Path("parsed_data")
    parsed_dir.mkdir(exist_ok=True)

    # ── Crawl the whole site ──────────────────────────────────────────────
    with EkamedCrawler(headless=True) as crawler:
        plain_bodies = crawler.run()

    # Save a single JSON array for reference / audit
    OUTPUT_PATH.write_text(json.dumps(plain_bodies, ensure_ascii=False, indent=2), "utf-8")
    logger.info("Dumped %d pages → %s", len(plain_bodies), OUTPUT_PATH.resolve())

    # ── POST each page text to Dify and persist answers ──────────────────
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    for idx, body in enumerate(plain_bodies, start=1):
        payload = {
            "query": body,
            "inputs": {},
            "response_mode": "blocking",
            "user": USER_ID,
        }
        try:
            resp = requests.post(f"{API_URL}/chat-messages", headers=headers, json=payload)
            resp.raise_for_status()
            answer = resp.json().get("answer", "")
        except Exception as e:  # noqa: BLE001
            logger.error("Error sending page %d to API: %s", idx, e)
            answer = ""

        resp_path = parsed_dir / f"response_{idx}.txt"
        resp_path.write_text(answer, "utf-8")
        logger.info("Saved API response → %s", resp_path.resolve())
