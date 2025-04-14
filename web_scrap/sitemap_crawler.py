import asyncio
import json
import logging
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class SitemapCrawler:
    def __init__(self, start_url: str, max_pages: int = 1000):
        self.start_url = start_url.rstrip('/')
        self.parsed_start_url = urlparse(self.start_url)
        self.domain = self.parsed_start_url.netloc
        self.visited = set()
        self.to_visit = {self.start_url}
        self.max_pages = max_pages

    def is_internal_link(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == '' or parsed.netloc == self.domain

    def normalize_url(self, url: str) -> str:
        # Remove fragment and trailing slashes
        url = url.split('#')[0].rstrip('/')
        return url

    async def extract_links(self, page) -> set:
        try:
            anchors = await page.eval_on_selector_all(
                "a[href]", "elements => elements.map(el => el.href)"
            )
            links = set()
            for href in anchors:
                if href:
                    normalized = self.normalize_url(href)
                    if self.is_internal_link(normalized):
                        full_url = urljoin(self.start_url, normalized)
                        links.add(full_url)
            return links
        except Exception as e:
            logging.error(f"Error extracting links: {e}")
            return set()

    async def crawl(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            while self.to_visit and len(self.visited) < self.max_pages:
                current_url = self.to_visit.pop()
                if current_url in self.visited:
                    continue

                try:
                    logging.info(f"Crawling: {current_url}")
                    await page.goto(current_url, timeout=10000)
                    self.visited.add(current_url)
                    links = await self.extract_links(page)
                    new_links = links - self.visited
                    self.to_visit.update(new_links)
                except PlaywrightTimeoutError:
                    logging.warning(f"Timeout while loading: {current_url}")
                except Exception as e:
                    logging.error(f"Error crawling {current_url}: {e}")

            await browser.close()

    def get_sitemap(self) -> list:
        return sorted(self.visited)


async def main():
    start_url = input("Enter the website URL (e.g., https://example.com): ").strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = 'https://' + start_url

    crawler = SitemapCrawler(start_url)
    await crawler.crawl()
    sitemap = crawler.get_sitemap()

    # Save the sitemap to a JSON file
    with open('sitemap.json', 'w', encoding='utf-8') as f:
        json.dump(sitemap, f, indent=4)

    print(f"\nSitemap saved to sitemap.json containing {len(sitemap)} URLs.")


if __name__ == "__main__":
    asyncio.run(main())
