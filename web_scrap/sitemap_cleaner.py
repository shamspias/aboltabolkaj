import asyncio
import json
import logging
from pathlib import Path
from typing import List

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class SitemapCleaner:
    """
    A class to load a sitemap from a JSON file, scrape each URL to check for error messages,
    and save a cleaned list of URLs to an output JSON file.
    """

    def __init__(self, input_file: str = "sitemap.json", output_file: str = "sitemap_cleaned.json") -> None:
        self.input_file: Path = Path(input_file)
        self.output_file: Path = Path(output_file)
        self.error_keywords: List[str] = [
            "Sorry, this page could not be found.:",
            "К сожалению, данная страница не найдена."
        ]
        self.urls: List[str] = []
        self.valid_urls: List[str] = []

    def load_sitemap(self) -> None:
        """
        Loads URLs from the input JSON file into self.urls.
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

    async def process_url(self, page, url: str) -> bool:
        """
        Loads a URL and checks if the page content contains any error keywords.

        Args:
            page: The Playwright page instance.
            url: The URL to scrape.

        Returns:
            True if the page is valid (error keywords not found), False otherwise.
        """
        try:
            logging.info(f"Scraping URL: {url}")
            await page.goto(url, timeout=10000)
            content = await page.content()
            # Check if any error keyword is found in the page content
            if any(keyword in content for keyword in self.error_keywords):
                logging.info(f"Error detected. Removing URL: {url}")
                return False
            else:
                return True
        except PlaywrightTimeoutError:
            logging.warning(f"Timeout while loading {url}. URL will be skipped.")
            return False
        except Exception as e:
            logging.error(f"Unexpected error while processing {url}: {e}")
            return False

    async def clean_sitemap(self) -> None:
        """
        Iterates over the loaded URLs, scrapes each for error messages,
        and populates self.valid_urls with URLs whose pages appear valid.
        """
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            # Use one page instance to process all URLs sequentially.
            page = await context.new_page()

            for url in self.urls:
                is_valid = await self.process_url(page, url)
                if is_valid:
                    self.valid_urls.append(url)
            await browser.close()

        logging.info(f"Cleaned sitemap: {len(self.valid_urls)} valid URLs found out of {len(self.urls)}.")

    def save_sitemap(self) -> None:
        """
        Saves the valid URLs to the output JSON file.
        """
        try:
            with self.output_file.open("w", encoding="utf-8") as f:
                json.dump(self.valid_urls, f, indent=4)
            logging.info(f"Saved cleaned sitemap with {len(self.valid_urls)} URLs to {self.output_file}.")
        except Exception as e:
            logging.error(f"Error saving cleaned sitemap: {e}")
            raise e


async def main() -> None:
    cleaner = SitemapCleaner()
    try:
        cleaner.load_sitemap()
    except Exception as e:
        logging.error(f"Could not load sitemap: {e}")
        return

    await cleaner.clean_sitemap()
    cleaner.save_sitemap()


if __name__ == "__main__":
    asyncio.run(main())
