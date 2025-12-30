import asyncio

from searchboost_src.argparser import *
from searchboost_src.chat_class import *
from searchboost_src.ai_handler import *
from searchboost_src.web_scraper import *
from searchboost_src.logger import *

async def main():
    try:
        args = await final_arguments()
        logger = await searchboost_src.logger.setup_logger()

        chat_details = ChatDetails()
        await chat_details.args_to_class(args)

        logger.info("Optimizing query...")
        optimized_query = await optimizer_query(chat_details)
        logger.info(f"Optimized Query: {optimized_query}")
        logger.info("Fetching search results...")
        logger.info("Summarizing search results...")
        logger.info(f"Summary:{await test_searxng(optimized_query)}")
    except Exception as e:
        logger.error(f"MAIN MODULE:{e}")

if __name__ == "__main__":
    asyncio.run(main())