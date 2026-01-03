import asyncio
import requests
import searchboost_src.logger

class WebScraper:
    def __init__(self,query):
        self.params = {
            "q": query,
            "format": "json",
            "language": "en-US"
            }

        pass


    async def searxng_search(self, host="http://localhost:8080"):
        self.logger = await searchboost_src.logger.setup_logger()

        try:
            response = requests.get(f"{host}/search", params=self.params, timeout=10)
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
                return f"Could not connect to {host}"
            return str(e)