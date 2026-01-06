import asyncio

from searchboost_src.argparser import parse_arguments, final_arguments
from searchboost_src.chat_class import ChatDetails
from searchboost_src.ai_handler import AIHandler
from searchboost_src.web_search import WebSearch
from searchboost_src.logger import setup_logger
from searchboost_src.config_loader import ConfigLoader

class SearchBoostService:
    def __init__(self,logger=None, args=None):
        self.logger = logger
        self.args = args
        self.chatdetails = None
        self.ai_handler = None
        self.web_search_instance = None

    async def initialize(self):

        try:
            self.logger.info("SearchBoostService : Initializing service...")
            if self.args.info.lower() == "debug":
                self.logger.setLevel("DEBUG")
                self.logger.debug("SearchBoostService : Debug logging enabled.")

            self.ai_config = ConfigLoader(config_name="local_ai",logger=self.logger)
            self.search_config = ConfigLoader(config_name="web_search",logger=self.logger)

            self.chatdetails = ChatDetails()
            await self.chatdetails.config_setup(self.ai_config.load_config())
            await self.chatdetails.args_to_class(self.args)
            self.logger.debug(f"SearchBoostService : ChatDetails configured: Model: {self.chatdetails.model}, Host: {self.chatdetails.host}, Port: {self.chatdetails.port}, Stream: {self.chatdetails.stream}")

            self.web_search_instance = WebSearch(self.args.query,logger=self.logger)
            await self.web_search_instance.config_setup(self.search_config.load_config())
            self.logger.info("SearchBoostService : Initialization complete.")

        except Exception as e:
            self.logger.error(f"SearchBoostService : CRITICAL Initialization Error: {e}")

    async def run(self):

        try:
            self.logger.info("SearchBoostService : Running service...")
            self.logger.debug("SearchBoostService : Optimizing query...")
            self.ai_handler = AIHandler(self.logger, reason="optimization")
            optimized_query = await self.ai_handler.query_LLM(self.chatdetails)
            self.logger.debug(f"SearchBoostService : Optimized Query: {optimized_query}")

            self.web_search_instance.query = optimized_query
            web_search_results = await self.web_search_instance.searxng_search()
            self.chatdetails.prompt = f"Using the following web search results, answer the question: {self.chatdetails.prompt}\n\nWeb Search Results:\n{web_search_results}"

            self.logger.debug("SearchBoostService : Querying LLM with web search context...")
            self.ai_handler = AIHandler(self.logger, reason="research")
            final_response = await self.ai_handler.query_LLM(self.chatdetails)
            self.logger.info(f"SearchBoostService : Final Response :\n---\n{final_response}")
        except Exception as e:
            self.logger.error(f"SearchBoostService : CRITICAL Runtime Error: {e}")