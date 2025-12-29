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
        engine = {"searxng.example.com"}
        results = {"TEST RESUTLS FROM SEARXNG"}
        return results
    except Exception as e:
        logger.error(f"ERROR: Error during searxng search: {e}")
        return