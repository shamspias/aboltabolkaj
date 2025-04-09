import logging
import time
from typing import List, Tuple, Optional, Dict, Any
from duckduckgo_search import DDGS


class AdvancedDuckDuckGoSearcher:
    """
    A class to perform advanced (deep) searches on DuckDuckGo using duckduckgo_search v8.0.0.

    It supports:
      - Text (web) searches with an option to include raw text content (i.e. full webpage text).
      - Image searches filtered by valid image file extensions.
      - Region selection for both text and image searches.
      - Domain restriction by building a query fragment (using allowed_sites).

    The advanced search returns a structured result with:
      - query: The original query.
      - follow_up_questions: Reserved (currently None).
      - answer: Reserved (currently None).
      - images: List of image URLs.
      - results: List of web results (each item includes title, url, content, score, and raw_content if enabled).
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
            timelimit (Optional[str]): Time limit for search results (e.g. "d" for day, "w" for week, etc.).
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
            str: A query fragment like "(site:etm.ru OR site:smartec-security.com OR ...)".
        """

        def normalize(site: str) -> str:
            # Remove protocol and trailing slash for consistency.
            return site.replace("https://", "").replace("http://", "").rstrip("/")

        sites_fragment = " OR ".join(f"site:{normalize(site)}" for site in allowed_sites)
        fragment = f"({sites_fragment})" if sites_fragment else ""
        logging.debug("Constructed allowed query fragment: %s", fragment)
        return fragment

    def search_text(self, query: str, max_results: int = 5, allow_raw_content: bool = False) -> List[Dict[str, Any]]:
        """
        Perform a text (web) search using DDGS.text.

        Args:
            query (str): Base search query.
            max_results (int): Maximum number of text results.
            allow_raw_content (bool): If True, include the raw text content (full page text) from the website result.

        Returns:
            List[Dict[str, Any]]: A list of search result dictionaries with keys:
                "title", "url", "content", "score", and "raw_content" (if enabled).
        """
        full_query = f"{query} {self.allowed_query_fragment}" if self.allowed_query_fragment else query
        logging.info("Performing text search with query: %s", full_query)
        results: List[Dict[str, Any]] = []
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
                        # If allow_raw_content is True, include the full text content from the page.
                        "raw_content": result.get("raw_content") if allow_raw_content else None,
                        "score": result.get("score")
                    }
                    logging.debug("Fetched text result: %s", item)
                    results.append(item)
        except Exception as e:
            logging.error("Error during text search: %s", e, exc_info=True)
        return results

    def search_images(self, query: str, max_results: int = 5) -> List[str]:
        """
        Perform an image search using DDGS.images. Only returns image URLs ending with valid extensions.

        Args:
            query (str): Base search query.
            max_results (int): Maximum number of image URLs to return.

        Returns:
            List[str]: List of valid image URLs.
        """
        full_query = f"{query} {self.allowed_query_fragment}" if self.allowed_query_fragment else query
        logging.info("Performing image search with query: %s", full_query)
        images: List[str] = []
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
                else:
                    logging.info("No image results found for query: %s", full_query)
        except Exception as e:
            logging.error("Error during image search: %s", e, exc_info=True)
        return images

    def advanced_search(self,
                        query: str,
                        max_image_results: int = 5,
                        max_text_results: int = 5,
                        allow_raw_content: bool = False) -> Dict[str, Any]:
        """
        Perform an advanced deep search that combines both image and text searches.

        Returns a structured result with:
          - query: The original query (with a trailing newline).
          - follow_up_questions: Reserved (currently None).
          - answer: Reserved (currently None).
          - images: List of image URLs.
          - results: List of text/web search result items.
          - response_time: Total time taken for the search in seconds.

        Args:
            query (str): Base search query.
            max_image_results (int): Maximum number of image URLs.
            max_text_results (int): Maximum number of text results.
            allow_raw_content (bool): Whether to include the full raw text from the website.

        Returns:
            Dict[str, Any]: Structured advanced search results.
        """
        logging.info("Starting advanced search for query: %s", query)
        start_time = time.time()

        images = self.search_images(query, max_results=max_image_results)
        text_results = self.search_text(query, max_results=max_text_results, allow_raw_content=allow_raw_content)

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


if __name__ == "__main__":
    # Allowed websites for domain-restricted search (if needed).
    allowed_sites = [
        "https://luis.ru",
        "https://bolid.ru",
        "https://www.dkc.ru",
        "https://www.ltcompany.com",
        "https://www.perco.ru",
        "https://tahion.spb.ru",
        "https://www.promrukav.ru",
        "https://ivkz.ru",
        "https://arsenal-sib.ru",
        "https://itk-group.ru",
        "https://catalog.argus-spectr.ru",
        "https://argus-spectr.ru",
        "https://hikvisionpro.ru",
        "https://www.eternis.ru",
        "https://spectron-ops.ru",
        "http://etm.ru/",
        "https://smartec-security.com",
        "https://st54.ru"
    ]

    # Create an instance of the advanced searcher.
    # Here, region can be chosen as needed (e.g. "ru-ru" for Russian results).
    searcher = AdvancedDuckDuckGoSearcher(allowed_sites=allowed_sites, region="ru-ru", debug=True)

    # Example search query.
    query = "Видеорегистратор STI-A1640"

    # Perform the advanced deep search.
    advanced_results = searcher.advanced_search(query,
                                                max_image_results=5,
                                                max_text_results=5,
                                                allow_raw_content=True)

    # Print the structured results as formatted JSON.
    import json

    print(json.dumps(advanced_results, indent=2, ensure_ascii=False))
