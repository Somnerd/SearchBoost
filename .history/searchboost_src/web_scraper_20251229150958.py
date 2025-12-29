import asyncio
import requests
import searchboost_src.logger

async def test_query(query: str):
    logger = await searchboost_src.logger.setup_logger() 

    try:
        #TODO : Implement searxng function to fetch real search results 
        logger.info("Simulating search results fetch...")
        results = ["Result 1 content", "Result 2 content", "Result 3 content"]
        logger.info(f"Fetched {len(results)} results.")
        return results
    except Exception as e:
        logger.error(f"ERROR: Error during search: {e}")
        return

async def test_searxng(query: str, host="http://localhost:8080"):
    engine = {"searxng.example.com"}
    results = {"TEST RESUTLS FROM SEARXNG"}
    return results