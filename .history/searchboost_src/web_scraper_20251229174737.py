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
                f"Source: {result.get('title')}\n"
                f"Content: {result.get('content')}\n"
                f"URL: {result.get('url')}\n"
            )

        return "\n---\n".join(normalized_context) if normalized_context else "No results found."

    except Exception as e:
        logger.error(f"SearXNG Error: {e}")
        if 'ConnectionError' in str(e):
            return f"Could not connect to {host}"
        return str(e)