import asyncio
import requests
import searchboost_src.logger

class WebSearch:
    def __init__(self,query, logger=None):

        self.format = "json"
        self.language = "en-US"
        self.safe_search = "1"
        self.query = query
        self.engine = "searxng"
        self.num_results = 5
        self.region = "us"
        self.host = "localhost"
        self.port = 8080

        self.host = f"http://{self.host}:{self.port}"
        self.params = {
            "q": self.query,
            "format": self.format,
            "language": self.language,
            "safesearch": self.safe_search,
            "engine": self.engine,
            "num_results": self.num_results,
            "region": self.region
        }
        self.logger = logger

        pass

    async def config_setup(self,config):
            self.format = config["format"]
            self.language = config["language"]
            self.safe_search = config["safe_search"]
            self.engine = config["search_engine"]
            self.num_results = config["num_results"]
            self.region = config["region"]
            self.host = config["host"]
            self.port = config["port"]

            self.host = f"http://{self.host}:{self.port}"

            self.params = {
                "q": self.query,
                "format": self.format,
                "language": self.language,
                "safesearch": self.safe_search,
                "engine": self.engine,
                "num_results": self.num_results,
                "region": self.region
            }

    async def searxng_search(self):

        try:
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

            return "\n---\n".join(normalized_context) if normalized_context else "No results found."

        except Exception as e:
            self.logger.error(f"SearXNG Error: {e}")
            if 'ConnectionError' in str(e):
                return f"Could not connect to {self.host}. Please ensure the SearXNG instance is running."
            return str(e)