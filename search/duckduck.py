import logging
import time
from typing import List, Tuple, Optional, Dict, Any
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException, DuckDuckGoSearchException


class AdvancedDuckDuckGoSearcher:
    """
    A class to perform advanced (deep) searches on DuckDuckGo using duckduckgo_search v8.0.0.

    It supports:
      - Text (web) searches with an option to include raw text content (full webpage text).
      - Image searches filtered by valid image file extensions.
      - Region selection for both text and image searches.
      - Domain restriction by building a query fragment (using allowed_sites).

    The advanced search returns a structured result with:
      - query: The original query.
      - follow_up_questions: Reserved (currently None).
      - answer: Reserved (currently None).
      - images: List of image URLs.
      - results: List of text/web results (each with title, url, content, score, and raw_content if enabled).
      - response_time: Total search time (in seconds).
    """

    def __init__(self,
                 allowed_sites: Optional[List[str]] = None,
                 valid_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.gif'),
                 region: str = "wt-wt",
                 safesearch: str = "moderate",
                 timelimit: Optional[str] = None,
                 backend: str = "auto",
                 debug: bool = False) -> None:
        """
        Initialize the searcher.

        Args:
            allowed_sites (Optional[List[str]]): List of allowed website URLs (e.g. ["https://luis.ru", ...]).
                When provided, a domain-restriction fragment is appended to the query.
            valid_extensions (Tuple[str, ...]): Valid image file extensions.
            region (str): Region parameter for searches (e.g. "wt-wt", "ru-ru", "us-en").
            safesearch (str): Safesearch level ("on", "moderate", or "off").
            timelimit (Optional[str]): Time limit for search results (e.g. "d", "w", etc.).
            backend (str): Backend for text search ("auto", "html", or "lite").
            debug (bool): If True, sets logging to DEBUG for detailed output.
        """
        self.allowed_sites = allowed_sites or []
        self.valid_extensions = valid_extensions
        self.region = region
        self.safesearch = safesearch
        self.timelimit = timelimit
        self.backend = backend
        self.allowed_query_fragment = self._build_allowed_query(self.allowed_sites) if self.allowed_sites else ""

        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                            format="%(levelname)s: %(message)s")
        logging.debug("Initialized AdvancedDuckDuckGoSearcher with query fragment: %s", self.allowed_query_fragment)

    def _build_allowed_query(self, allowed_sites: List[str]) -> str:
        """
        Build a query fragment from allowed_sites so that only results from these domains are returned.

        Args:
            allowed_sites (List[str]): List of allowed website URLs.

        Returns:
            str: A query fragment like "(site:domain1 OR site:domain2 ...)".
        """

        def normalize(site: str) -> str:
            return site.replace("https://", "").replace("http://", "").rstrip("/")

        sites_fragment = " OR ".join(f"site:{normalize(site)}" for site in allowed_sites)
        fragment = f"({sites_fragment})" if sites_fragment else ""
        logging.debug("Constructed allowed query fragment: %s", fragment)
        return fragment

    def search_text(self,
                    query: str,
                    max_results: int = 5,
                    allow_raw_content: bool = False,
                    retry_forever: bool = False,
                    max_retries: int = 3,
                    initial_delay: int = 2) -> List[Dict[str, Any]]:
        """
        Perform a text (web) search using DDGS.text with retry handling for rate limits.

        Args:
            query (str): Base search query.
            max_results (int): Maximum number of text results.
            allow_raw_content (bool): If True, include raw page text.
            retry_forever (bool): If True, keep retrying indefinitely until a response is obtained.
            max_retries (int): Maximum retries if retry_forever is False.
            initial_delay (int): Starting delay (in seconds) between retries.

        Returns:
            List[Dict[str, Any]]: A list of search result dictionaries.
        """
        full_query = f"{query} {self.allowed_query_fragment}" if self.allowed_query_fragment else query
        logging.info("Performing text search with query: %s", full_query)
        results: List[Dict[str, Any]] = []
        attempt = 1
        delay = initial_delay

        while True:
            try:
                with DDGS() as ddgs:
                    text_results = ddgs.text(
                        keywords=full_query,
                        region=self.region,
                        safesearch=self.safesearch,
                        timelimit=self.timelimit,
                        backend=self.backend,
                        max_results=max_results
                    )
                    for result in text_results:
                        item = {
                            "title": result.get("title"),
                            "url": result.get("href") or result.get("url"),
                            "content": result.get("body") or result.get("content"),
                            "raw_content": result.get("raw_content") if allow_raw_content else None,
                            "score": result.get("score")
                        }
                        logging.debug("Fetched text result: %s", item)
                        results.append(item)
                    return results

            except RatelimitException as e:
                logging.warning("Rate limit encountered on text search attempt %d: %s", attempt, e)
                logging.info("Waiting %d seconds before retrying text search...", delay)
                time.sleep(delay)
                attempt += 1
                delay *= 2
                if not retry_forever and attempt > max_retries:
                    logging.error("Max retries reached for text search; returning accumulated results.")
                    break
            except DuckDuckGoSearchException as e:
                logging.error("DuckDuckGo search error during text search: %s", e, exc_info=True)
                break
            except Exception as ex:
                logging.error("Unexpected error during text search: %s", ex, exc_info=True)
                break
        return results

    def search_images(self,
                      query: str,
                      max_results: int = 5,
                      retry_forever: bool = False,
                      max_retries: int = 3,
                      initial_delay: int = 2) -> List[str]:
        """
        Perform an image search using DDGS.images with retry handling for rate limits.
        Only returns image URLs ending with valid extensions.

        Args:
            query (str): Base search query.
            max_results (int): Maximum number of image URLs to return.
            retry_forever (bool): If True, keep retrying indefinitely until a response is obtained.
            max_retries (int): Maximum retries if retry_forever is False.
            initial_delay (int): Starting delay (in seconds) between retries.

        Returns:
            List[str]: A list of valid image URLs.
        """
        full_query = f"{query} {self.allowed_query_fragment}" if self.allowed_query_fragment else query
        logging.info("Performing image search with query: %s", full_query)
        images: List[str] = []
        attempt = 1
        delay = initial_delay

        while True:
            try:
                with DDGS() as ddgs:
                    image_results = ddgs.images(
                        keywords=full_query,
                        region=self.region,
                        safesearch=self.safesearch,
                        timelimit=self.timelimit,
                        max_results=max_results
                    )
                    if image_results:
                        for result in image_results:
                            url = result.get("image")
                            if url and url.lower().endswith(self.valid_extensions):
                                logging.debug("Accepted image URL: %s", url)
                                images.append(url)
                            if len(images) >= max_results:
                                break
                        return images
                    else:
                        logging.info("No image results found for query: %s", full_query)
                        return images

            except RatelimitException as e:
                logging.warning("Rate limit encountered on image search attempt %d: %s", attempt, e)
                logging.info("Waiting %d seconds before retrying image search...", delay)
                time.sleep(delay)
                attempt += 1
                delay *= 2
                if not retry_forever and attempt > max_retries:
                    logging.error("Max retries reached for image search; returning accumulated results.")
                    break
            except Exception as e:
                logging.error("Error during image search: %s", e, exc_info=True)
                break
        return images

    def advanced_search(self,
                        query: str,
                        max_image_results: int = 5,
                        max_text_results: int = 5,
                        allow_raw_content: bool = False,
                        retry_forever: bool = False,
                        max_retries: int = 3,
                        initial_delay: int = 2) -> Dict[str, Any]:
        """
        Perform an advanced search that combines both image and text searches.

        Returns a structured result with:
          - query: The original query (with trailing newline).
          - follow_up_questions: Reserved (currently None).
          - answer: Reserved (currently None).
          - images: List of image URLs.
          - results: List of text/web search result items.
          - response_time: Total search time (in seconds).

        Args:
            query (str): Base search query.
            max_image_results (int): Maximum number of image URLs.
            max_text_results (int): Maximum number of text results.
            allow_raw_content (bool): Whether to include full raw text from pages.
            retry_forever (bool): If True, retry indefinitely on rate limits.
            max_retries (int): Maximum retry attempts when retry_forever is False.
            initial_delay (int): Starting delay (in seconds) for retries.

        Returns:
            Dict[str, Any]: Structured advanced search results.
        """
        logging.info("Starting advanced search for query: %s", query)
        start_time = time.time()

        images = self.search_images(query, max_results=max_image_results,
                                    retry_forever=retry_forever,
                                    max_retries=max_retries,
                                    initial_delay=initial_delay)
        if max_text_results > 0:
            text_results = self.search_text(query, max_results=max_text_results,
                                            allow_raw_content=allow_raw_content,
                                            retry_forever=retry_forever,
                                            max_retries=max_retries,
                                            initial_delay=initial_delay)
        else:
            text_results = []

        response_time = round(time.time() - start_time, 2)
        advanced_result = {
            "query": query.strip() + "\n",
            "follow_up_questions": None,
            "answer": None,
            "images": images,
            "results": text_results,
            "response_time": response_time
        }
        logging.info("Advanced search completed in %s seconds", response_time)
        return advanced_result


# Example usage:
if __name__ == '__main__':
    # Allowed websites for domain-restricted search.
    allowed_sites = [
        "https://shamspais.com",
        "https://wtf.com",
    ]

    # Create an instance of the advanced searcher.
    searcher = AdvancedDuckDuckGoSearcher(allowed_sites=allowed_sites, region="ru-ru", debug=True)

    # Example search query.
    query = "Giga Chad"

    # Perform the advanced deep search.
    advanced_results = searcher.advanced_search(query,
                                                max_image_results=15,
                                                max_text_results=5,
                                                allow_raw_content=True,
                                                retry_forever=True)  # Set to True to retry indefinitely

    # Print the structured results as formatted JSON.
    import json

    print(json.dumps(advanced_results, indent=2, ensure_ascii=False))
