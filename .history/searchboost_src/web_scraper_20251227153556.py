import asyncio
import searchboost_src.logger

logger = await searchboost_src.logger.setup_logger() 


async def test_query(query: str, engine: list):

async def test_searxng(query: str, engine: list):
    engine = {"searxng.example.com"}
    results = {"TEST RESUTLS FROM SEARXNG"}
    return results