import asyncio
import requests
import searchboost_src.logger

async def test_searxng(query: str, host="http://localhost:8080"):
    logger = await searchboost_src.logger.setup_logger()

    params = {
        "q": query, 
        "format": "json",
        "language": "en-US"
        }

    try:
        response = requests.get(f"{host}/search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        normalized_context = []

        for result in results[:5]:
            normalized_context.append(
                f"Source: {result.get("title")}\n"
                f"Content: {result.get("content")}\n"
                f"URL: {result.get("url")}\n"
            )

        engine = {"searxng.example.com"}
        results = {"TEST RESUTLS FROM SEARXNG"}
        
        return results
    except Exception as e:
        logger.error(f"ERROR: Error during searxng search: {e}")
        return