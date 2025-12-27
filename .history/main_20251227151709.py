import asyncio

from searchboost_src.argparser import final_arguments
from searchboost_src.chat_class import ChatDetails
from searchboost_src.ai_handler import optimizer_query
from searchboost_src.web_scraper import test_searxng
import searchboost_src.logger 

async def main():
    args = await final_arguments()
    logger = await searchboost_src.logger.setup_logger() 

    chat_details = ChatDetails()
    chat_details.prompt=args.query
    chat_details.model=args.model  
    chat_details.engine=args.engine
    
    logger.info("Optimizing query...")
    optimized_query = await optimizer_query(chat_details)
    logger.info(f"Optimized Query: {optimized_query}")
    logger.info("\nFetching search results...")
    
    try:
        #TODO : Implement searxng function to fetch real search results 
        logger.info("Simulating search results fetch...")
        results = ["Result 1 content", "Result 2 content", "Result 3 content"]
        logger.info(f"Fetched {len(results)} results.")
    except Exception as e:
        logger.error(f"ERROR: Error during search: {e}")
        return

    # Step 3: Summarize results
    logger.info("\nSummarizing search results...")
    summary = await test_searxng(optimized_query, chat_details.engine)
    logger.info("\nSummary:")
    logger.info(summary)


if __name__ == "__main__": # Fix 3: Usually you want "__main__" to run the script
    asyncio.run(main())