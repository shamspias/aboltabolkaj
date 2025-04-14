import asyncio
import json
import logging
import difflib
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

# Configure logging with detailed timestamp and level information.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class FinalSitemapProcessorWithDeduplication:
    """
    Processes a sitemap by:
      1. Fetching the page for each URL.
      2. Verifying that the page is valid (HTTP status 200, not a 404).
      3. Extracting and cleaning text from the page.
      4. Checking if the new page content is almost identical (>= 99% similarity)
         to any previously processed content.
      5. Saving only unique pages to sequentially numbered JSON files.

    Each output JSON file includes:
      - "url": the page URL.
      - "raw_text": the cleaned text content.
    """

    def __init__(
            self,
            input_file: str = "sitemap_cleaned.json",
            output_dir: str = "pages_data",
            concurrency_limit: int = 5,
            navigation_timeout: int = 10000,
            similarity_threshold: float = 0.99
    ) -> None:
        self.input_file: Path = Path(input_file)
        self.output_dir: Path = Path(output_dir)
        self.concurrency_limit: int = concurrency_limit
        self.navigation_timeout: int = navigation_timeout
        self.similarity_threshold: float = similarity_threshold
        self.urls: List[str] = []
        # List to hold unique page content for deduplication.
        self.accepted_contents: List[str] = []
        # Counter for accepted pages to generate file names.
        self.saved_count: int = 0

        # Create the output directory if it does not exist.
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_sitemap(self) -> None:
        """
        Loads the list of URLs from the sitemap JSON file.
        """
        if not self.input_file.exists():
            logging.error(f"Input file '{self.input_file}' not found.")
            raise FileNotFoundError(f"Input file '{self.input_file}' does not exist.")
        try:
            with self.input_file.open("r", encoding="utf-8") as f:
                self.urls = json.load(f)
            logging.info(f"Loaded {len(self.urls)} URLs from '{self.input_file}'.")
        except json.JSONDecodeError as e:
            logging.error("Error decoding JSON from the sitemap file.")
            raise e

    async def fetch_and_clean_page(self, page, url: str) -> Optional[str]:
        """
        Fetches a URL, validates the response, and cleans the HTML to extract text.

        Args:
            page: A Playwright page instance.
            url: The URL to fetch.

        Returns:
            The cleaned text if successful and valid; otherwise, None.
        """
        try:
            logging.info(f"Fetching URL: {url}")
            response = await page.goto(url, timeout=self.navigation_timeout)
            if response is None:
                logging.warning(f"No response received for URL: {url}")
                return None

            if response.status != 200:
                logging.warning(f"Non-200 response ({response.status}) for URL: {url}. Skipping.")
                return None

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Remove undesired tags.
            for tag in soup(["script", "style"]):
                tag.decompose()

            raw_text = soup.get_text(separator=" ", strip=True)
            if not raw_text:
                logging.warning(f"No textual content extracted from URL: {url}")
                return None

            return raw_text
        except PlaywrightTimeoutError:
            logging.warning(f"Timeout while fetching URL: {url}")
        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")
        return None

    def is_duplicate(self, new_content: str) -> bool:
        """
        Checks the new page content against already accepted content.

        Args:
            new_content: The text content extracted from the current page.

        Returns:
            True if the new content is almost identical (>= similarity_threshold)
            to any accepted content; False otherwise.
        """
        for accepted in self.accepted_contents:
            similarity = difflib.SequenceMatcher(None, accepted, new_content).ratio()
            if similarity >= self.similarity_threshold:
                logging.info(f"Duplicate content found (similarity: {similarity:.2f}). Skipping.")
                return True
        return False

    async def process_url(self, browser, url: str, index: int, semaphore: asyncio.Semaphore) -> None:
        """
        Processes an individual URL: fetches, validates, cleans, deduplicates, and saves the page.

        Args:
            browser: A Playwright browser instance.
            url: The URL to process.
            index: An index for logging purposes.
            semaphore: A semaphore to control concurrency.
        """
        async with semaphore:
            page = await browser.new_page()
            try:
                raw_text = await self.fetch_and_clean_page(page, url)
                if raw_text is None:
                    logging.info(f"Skipping URL due to no valid content: {url}")
                    return

                # Check for duplicate content.
                if self.is_duplicate(raw_text):
                    logging.info(f"Skipping duplicate content for URL: {url}")
                    return

                # Accept and store the unique content.
                self.accepted_contents.append(raw_text)
                self.saved_count += 1
                file_name = f"{self.saved_count}.json"
                file_path = self.output_dir / file_name
                data = {
                    "url": url,
                    "raw_text": raw_text
                }
                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                logging.info(f"Saved URL ({url}) as {file_name}")

            except Exception as e:
                logging.error(f"Error processing URL {url}: {e}")
            finally:
                await page.close()

    async def fetch_all_pages(self) -> None:
        """
        Uses Playwright and asyncio to concurrently process all URLs from the sitemap.
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
    processor = FinalSitemapProcessorWithDeduplication()
    try:
        processor.load_sitemap()
    except Exception as e:
        logging.error(f"Failed to load sitemap: {e}")
        return

    await processor.fetch_all_pages()
    logging.info(f"Processing completed. {processor.saved_count} unique pages saved.")


if __name__ == "__main__":
    asyncio.run(main())
