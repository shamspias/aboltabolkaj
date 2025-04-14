import asyncio
import json
import logging
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

# Configure logging for detailed output.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class FinalSitemapTextFetcher:
    """
    Loads URLs from a JSON file (final_sitemap.json), fetches each page,
    extracts and cleans the page content to produce raw text, and saves the result
    in individual JSON files within a subdirectory. Each JSON file is sequentially
    numbered (e.g., 1.json, 2.json, ...) and includes:
        - url: The page URL.
        - raw_text: The cleaned page content.
    """

    def __init__(
            self,
            input_file: str = "final_sitemap.json",
            output_dir: str = "pages_data",
            concurrency_limit: int = 5,
            navigation_timeout: int = 10000
    ) -> None:
        self.input_file: Path = Path(input_file)
        self.output_dir: Path = Path(output_dir)
        self.concurrency_limit: int = concurrency_limit
        self.navigation_timeout: int = navigation_timeout
        self.urls: List[str] = []

        # Ensure the output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_sitemap(self) -> None:
        """
        Loads URLs from the input JSON file and stores them in self.urls.
        """
        if not self.input_file.exists():
            logging.error(f"Input file '{self.input_file}' does not exist.")
            raise FileNotFoundError(f"Input file '{self.input_file}' not found.")

        try:
            with self.input_file.open("r", encoding="utf-8") as f:
                self.urls = json.load(f)
            logging.info(f"Loaded {len(self.urls)} URLs from {self.input_file}.")
        except json.JSONDecodeError as e:
            logging.error("Error decoding JSON from sitemap file.")
            raise e

    async def fetch_and_clean_page(self, page, url: str) -> Optional[str]:
        """
        Fetches a URL using Playwright, extracts the page content, and cleans it
        to extract pure text using BeautifulSoup.

        Args:
            page: A Playwright page instance.
            url: The URL to fetch.

        Returns:
            The cleaned raw text of the page, or None if an error occurs.
        """
        try:
            logging.info(f"Fetching URL: {url}")
            await page.goto(url, timeout=self.navigation_timeout)
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style tags
            for tag in soup(["script", "style"]):
                tag.decompose()

            # Extract text with spaces for readability and strip extra whitespace.
            raw_text = soup.get_text(separator=" ", strip=True)
            return raw_text
        except PlaywrightTimeoutError:
            logging.warning(f"Timeout while fetching URL: {url}")
        except Exception as e:
            logging.error(f"Error fetching URL {url}: {e}")
        return None

    async def process_url(self, browser, url: str, index: int, semaphore: asyncio.Semaphore) -> None:
        """
        Processes a single URL by creating a new page, fetching and cleaning its content,
        and saving the data into a sequentially named JSON file.

        Args:
            browser: A Playwright browser instance.
            url: The URL to process.
            index: The sequential index (starting at 0) for naming the output file.
            semaphore: A semaphore to limit concurrent page fetches.
        """
        async with semaphore:
            page = await browser.new_page()
            try:
                raw_text = await self.fetch_and_clean_page(page, url)
                if raw_text:
                    data = {
                        "url": url,
                        "raw_text": raw_text
                    }
                    # Generate file name: e.g., "1.json", "2.json", etc.
                    file_path = self.output_dir / f"{index + 1}.json"
                    with file_path.open("w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                    logging.info(f"Saved content for URL: {url} into {file_path.name}")
                else:
                    logging.warning(f"No content fetched for URL: {url}")
            except Exception as e:
                logging.error(f"Error processing URL {url}: {e}")
            finally:
                await page.close()

    async def fetch_all_pages(self) -> None:
        """
        Uses Playwright to concurrently fetch and process all URLs from the sitemap,
        subject to a concurrency limit.
        """
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            tasks = [
                self.process_url(browser, url, idx, semaphore)
                for idx, url in enumerate(self.urls)
            ]
            await asyncio.gather(*tasks)
            await browser.close()


async def main() -> None:
    fetcher = FinalSitemapTextFetcher()
    try:
        fetcher.load_sitemap()
    except Exception as e:
        logging.error(f"Error loading sitemap: {e}")
        return

    await fetcher.fetch_all_pages()
    logging.info("All pages processed and saved.")


if __name__ == "__main__":
    asyncio.run(main())
