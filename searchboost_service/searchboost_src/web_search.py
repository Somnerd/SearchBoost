import asyncio
import requests
import searchboost_src.logger

class WebSearch:
    def __init__(self,query ,config , logger=None):
        self.config = config
        self.query = query

        self.host = self.config.base_url
        self.params = {
            "q": self.query,
            "format": self.config.format,
            "language": self.config.language,
            "safesearch": self.config.safe_search,
            "engine": self.config.engine,
            "num_results": self.config.num_results,
            "region": self.config.region
        }
        self.logger = logger

        pass

    async def searxng_search(self):

        try:
            self.logger.debug(f"Web Search : params {self.params} ")
            response = requests.get(f"{self.host}/search", params=self.params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            normalized_context = []

            for result in results[:5]:
                normalized_context.append(
                    f"Source: {result.get('title')}\n"
                    f"Content: {result.get('content')}\n"
                    f"URL: {result.get('url')}\n"
                )

            self.logger.debug(f"Web Search : Results {normalized_context}")
            return "\n---\n".join(normalized_context) if normalized_context else "No results found."

        except Exception as e:
            self.logger.error(f"SearXNG Error: {e}")
            if 'ConnectionError' in str(e):
                return f"Could not connect to {self.host}. Please ensure the SearXNG instance is running."
            return str(e)