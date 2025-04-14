import asyncio
import json
import logging
import difflib
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging with timestamps and level indicators.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class UniqueContentSitemap:
    """
    Loads a cleaned sitemap (JSON list of URLs), fetches page content for each URL,
    performs deduplication based on near-identical content (>= 99% similarity), and saves
    the deduplicated URL list into a final JSON file.
    """

    def __init__(self,
                 input_file: str = "sitemap_cleaned.json",
                 output_file: str = "final_sitemap.json",
                 similarity_threshold: float = 0.99,
                 concurrency_limit: int = 5) -> None:
        self.input_file: Path = Path(input_file)
        self.output_file: Path = Path(output_file)
        self.similarity_threshold: float = similarity_threshold
        self.concurrency_limit: int = concurrency_limit
        self.urls: List[str] = []
        self.contents: Dict[str, str] = {}  # Map URL -> page content
        self.unique_urls: List[str] = []

    def load_urls(self) -> None:
        """
        Loads URLs from the input JSON file.
        """
        if not self.input_file.exists():
            logging.error(f"Input file '{self.input_file}' not found.")
            raise FileNotFoundError(f"Input file '{self.input_file}' does not exist.")

        try:
            with self.input_file.open("r", encoding="utf-8") as f:
                self.urls = json.load(f)
            logging.info(f"Loaded {len(self.urls)} URLs from {self.input_file}.")
        except json.JSONDecodeError as e:
            logging.error("Failed to decode JSON from the sitemap file.")
            raise e

    async def fetch_content(self, page, url: str) -> Optional[str]:
        """
        Fetches the full page content for the given URL using Playwright.

        Args:
            page: The Playwright page object.
            url: The URL to fetch.

        Returns:
            The page content as a string or None if an error occurs.
        """
        try:
            logging.info(f"Fetching content for URL: {url}")
            await page.goto(url, timeout=10000)
            content = await page.content()
            return content
        except PlaywrightTimeoutError:
            logging.warning(f"Timeout while loading {url}. Skipping.")
        except Exception as e:
            logging.error(f"Error fetching content from {url}: {e}")
        return None

    async def fetch_all_contents(self) -> None:
        """
        Launches Playwright and concurrently fetches page content for all URLs
        using a semaphore to limit concurrency. Fetched content is stored in `self.contents`.
        """
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            async def fetch_with_semaphore(url: str) -> None:
                async with semaphore:
                    content = await self.fetch_content(page, url)
                    if content:
                        self.contents[url] = content

            tasks = [fetch_with_semaphore(url) for url in self.urls]
            await asyncio.gather(*tasks)
            await browser.close()

        logging.info(f"Fetched contents for {len(self.contents)} URLs out of {len(self.urls)}.")

    def deduplicate_contents(self) -> None:
        """
        Iterates through fetched page contents and filters out URLs whose page content
        is nearly identical (99% similarity or greater) to any earlier accepted content.
        Only the first occurrence is kept.
        """
        accepted_urls: List[str] = []
        accepted_contents: List[str] = []

        for url, content in self.contents.items():
            is_duplicate = False
            for existing in accepted_contents:
                similarity = difflib.SequenceMatcher(None, existing, content).ratio()
                if similarity >= self.similarity_threshold:
                    logging.info(f"Content at {url} is duplicate (similarity {similarity:.2f}). Skipping URL.")
                    is_duplicate = True
                    break
            if not is_duplicate:
                accepted_urls.append(url)
                accepted_contents.append(content)

        self.unique_urls = accepted_urls
        logging.info(f"Deduplication complete. {len(self.unique_urls)} unique URLs retained out of {len(self.urls)}.")

    def save_final_sitemap(self) -> None:
        """
        Saves the final list of unique URLs to the output JSON file.
        """
        try:
            with self.output_file.open("w", encoding="utf-8") as f:
                json.dump(self.unique_urls, f, indent=4)
            logging.info(f"Final sitemap with {len(self.unique_urls)} URLs saved to {self.output_file}.")
        except Exception as e:
            logging.error(f"Error saving final sitemap: {e}")
            raise e


async def main() -> None:
    sitemap_processor = UniqueContentSitemap()
    try:
        sitemap_processor.load_urls()
    except Exception as e:
        logging.error(f"Error loading URLs: {e}")
        return

    await sitemap_processor.fetch_all_contents()
    sitemap_processor.deduplicate_contents()
    sitemap_processor.save_final_sitemap()


if __name__ == "__main__":
    asyncio.run(main())
