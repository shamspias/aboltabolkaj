import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union


class SitemapJSONProcessor:
    """
    Processes a sitemap JSON file by removing URLs containing a given keyword.
    """

    def __init__(self, filepath: Union[str, Path]):
        """
        Initializes the processor with the path to the sitemap JSON file.
        """
        self.filepath = Path(filepath)
        if not self.filepath.is_file():
            raise FileNotFoundError(f"Sitemap file not found: {self.filepath}")
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def load_sitemap(self) -> Any:
        """
        Loads and returns the JSON content of the sitemap file.
        """
        with self.filepath.open('r', encoding='utf-8') as f:
            data = json.load(f)
        self.logger.info(f"Loaded sitemap from %s", self.filepath)
        return data

    def filter_urls(self, data: Any, keyword: str) -> Any:
        """
        Recursively filters out URLs containing the keyword from the sitemap data.

        Supports:
        - list of URL strings
        - dict with a 'urls' key mapping to a list of URL strings
        - nested structures

        :param data: Parsed JSON data
        :param keyword: Substring to search for in URLs
        :return: Filtered data
        """
        if isinstance(data, list):
            filtered_list = [url for url in data if keyword not in url]
            removed = len(data) - len(filtered_list)
            self.logger.info(f"Removed %d URL(s) containing '%s'", removed, keyword)
            return filtered_list

        if isinstance(data, dict):
            new_data: Dict[str, Any] = {}
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    new_data[key] = self.filter_urls(value, keyword)
                else:
                    new_data[key] = value
            return new_data

        # If data is neither list nor dict, return as is
        return data

    def save_sitemap(self, data: Any) -> None:
        """
        Saves the filtered sitemap data back to the file.
        """
        with self.filepath.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Saved filtered sitemap to %s", self.filepath)

    def process(self, keyword: str) -> None:
        """
        Loads the sitemap, filters URLs containing the keyword, and saves the result.
        """
        data = self.load_sitemap()
        filtered = self.filter_urls(data, keyword)
        self.save_sitemap(filtered)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Filter URLs from a sitemap JSON file.')
    parser.add_argument('filepath', help='Path to sitemap.json')
    parser.add_argument(
        '--keyword',
        default='langgraphjs',
        help='Substring to filter out from URLs (default: langgraphjs)'
    )
    args = parser.parse_args()

    processor = SitemapJSONProcessor(args.filepath)
    processor.process(args.keyword)
