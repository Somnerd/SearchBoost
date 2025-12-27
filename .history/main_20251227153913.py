import asyncio

from searchboost_src.argparser import final_arguments
import searchboost_src.chat_class import ChatDetails
import searchboost_src.ai_handler 
import searchboost_src.web_scraper
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
    logger.info("Fetching search results...")
    
    await test_query(optimized_query)

    logger.info("Summarizing search results...")
    summary = await test_searxng(optimized_query, chat_details.engine)
    logger.info("Summary:")
    logger.info(summary)


if __name__ == "__main__": # Fix 3: Usually you want "__main__" to run the script
    asyncio.run(main())