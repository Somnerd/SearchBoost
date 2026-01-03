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

        chatdetails = ChatDetails()
        await chatdetails.args_to_class(args)

        logger.info("Optimizing query...")

        ai_handler = AIHandler(logger, reason="optimization")
        optimized_query = await ai_handler.query_LLM(chatdetails)
        logger.info(f"MAIN : Optimized Query: \n---{optimized_query}")

        WebScraperInstance = WebScraper(optimized_query)
        logger.info(f"MAIN : Summary:\n---{await WebScraperInstance.searxng_search()}")

    except Exception as e:
        logger.error(f"CRITICAL:{e}")

if __name__ == "__main__":
    asyncio.run(main())