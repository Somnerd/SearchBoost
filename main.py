import asyncio

from searchboost_src.argparser import parse_arguments, final_arguments
from searchboost_src.chat_class import ChatDetails
from searchboost_src.ai_handler import AIHandler
from searchboost_src.web_search import WebSearch
from searchboost_src.logger import setup_logger
from searchboost_src.config_loader import ConfigLoader

async def main():
    logger = await setup_logger()

    try:
        args = await final_arguments()

        if args.info.lower() == "debug":
            logger.setLevel("DEBUG")
            logger.debug("MAIN : Debug logging enabled.")

        ai_config = ConfigLoader(config_name="local_ai",logger=logger)
        search_config = ConfigLoader(config_name="web_search",logger=logger)


        chatdetails = ChatDetails()
        await chatdetails.config_setup(ai_config.load_config())
        await chatdetails.args_to_class(args)
        logger.debug(f"MAIN : ChatDetails configured: Model: {chatdetails.model}, Host: {chatdetails.host}, Port: {chatdetails.port}, Stream: {chatdetails.stream}")


        logger.debug("MAIN : Optimizing query...")
        ai_handler = AIHandler(logger, reason="optimization")
        optimized_query = await ai_handler.query_LLM(chatdetails)
        logger.debug(f"MAIN : Optimized Query: {optimized_query}")


        WebSearchInstance = WebSearch(optimized_query,logger=logger)
        await WebSearchInstance.config_setup(search_config.load_config())
        web_search_results = await WebSearchInstance.searxng_search()
        chatdetails.prompt = f"Using the following web search results, answer the question: {chatdetails.prompt}\n\nWeb Search Results:\n{web_search_results}"

        logger.debug("MAIN : Querying LLM with web search context...")
        ai_handler = AIHandler(logger, reason="research")
        final_response = await ai_handler.query_LLM(chatdetails)
        logger.info(f"MAIN : FINAL RESPONSE:\n---\n{final_response}")
    except Exception as e:
        logger.error(f"MAIN : CRITICAL:{e}")

if __name__ == "__main__":
    asyncio.run(main())