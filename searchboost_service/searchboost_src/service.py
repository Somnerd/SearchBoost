import asyncio

from searchboost_src.argparser import Argsparser_Instance
from searchboost_src.chat_class import ChatDetails
from searchboost_src.ai_handler import AIHandler
from searchboost_src.web_search import WebSearch
from searchboost_src.redis_manager import RedisManager
from searchboost_src.logger import setup_logger

class SearchBoostService:
    def __init__(self ,ai,search,redis,logger=None, args=None):
        self.logger = logger
        self.args = args

        self.ai_config = ai
        self.search_config = search
        self.redis_config = redis

        self.cache = RedisManager(self.redis_config,self.logger)

        self.chatdetails = ChatDetails(config=self.ai_config,
                                        prompt=self.args.query)
        self.web_search_instance = WebSearch(query = self.args.query,
                                            config = self.search_config,
                                            logger=self.logger)


    async def debug_logs(self):
        try:
            self.logger.info("SearchBoostService : Debug Logs service...")

            self.logger.debug(f"""
                                SearchBoostService :
                                    ChatDetails configured:
                                        Model: {self.chatdetails.config.model}
                                        Host: {self.chatdetails.config.base_url}
                                        Port: {self.chatdetails.config.port}
                                        Stream: {self.chatdetails.config.stream}
                                        Role: {self.chatdetails.config.role}
                                        """)

            self.logger.debug(f"""
                                SearchBoostService :
                                    WebSearch configured:
                                        Query:{self.web_search_instance.query}
                                        Format:{self.web_search_instance.config.format}
                                        Language:{self.web_search_instance.config.language}
                                        SafeSearch:{self.web_search_instance.config.safe_search}
                                        Engine:{self.web_search_instance.config.engine}
                                        Number of Results:{self.web_search_instance.config.num_results}
                                        Region:{self.web_search_instance.config.region}
                                        Host:{self.web_search_instance.config.base_url}
                                        """)
            self.logger.info("SearchBoostService : Debug Logs complete.")
        except Exception as e:
            self.logger.error(f"SearchBoostService :  Debug LOGS Error: {e}")

    async def run(self):

        self.logger.debug("SearchBoostService : Debug logging enabled.")
        await self.debug_logs()

        try:
            self.logger.info("SearchBoostService : Running service...")
            self.logger.info("SearchBoostService : Connecting to Redis")

            await self.cache.connect()
            cached_result = await self.cache.get_cached_response(self.args.query)
            if cached_result:
                self.logger.info("--- CACHE HIT ---")
                print(f"\nFinal Response (Cached):\n{cached_result}")
                return

            self.logger.info("--- CACHE MISS: Executing Research Loop ---")

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
            await self.cache.cache_response(self.args.query, final_response)

            self.logger.info(f"SearchBoostService : Final Response :\n---\n{final_response}")
        except Exception as e:
            self.logger.error(f"SearchBoostService : CRITICAL Runtime Error: {e}")