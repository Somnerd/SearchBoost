# -*- coding: utf-8 -*-
# SearchBoost: AI-Powered Semantic Search & Reliability Engine
# Copyright (C) 2026 Nikolaos Alexandrakis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------
# COMMERCIAL USE NOTICE:
# For licensing outside the scope of AGPLv3, contact: nikolasalexandrakis.work@gmail.com
# ---------------------------------------------------------------------


import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from searchboost_src.argparser import Argsparser_Instance
from searchboost_src.chat_class import ChatDetails
from searchboost_src.ai_handler import AIHandler
from searchboost_src.web_search import WebSearch
from searchboost_src.redis_manager import RedisManager
from searchboost_src.logger import setup_logger
from searchboost_src.models import SearchResult
from searchboost_src.database import HistoryService

class SearchBoostService:
    def __init__(self, ai, search, redis, db, logger=None, args=None, session_id=None):
        self.logger = logger or setup_logger(info=False)
        self.args = args
        self.session_id = session_id  # e.g. "SB-SESSION-guest", used for history isolation

        self.ai_config = ai
        self.search_config = search
        self.redis_config = redis
        self.db_config = db

        self.cache = RedisManager(self.redis_config, self.logger)

        self.chatdetails = ChatDetails(config=self.ai_config,
                                        prompt=self.args.query)
        self.web_search_instance = WebSearch(query=self.args.query,
                                            config=self.search_config,
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

    async def run(self, db_session: AsyncSession = None):

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
                return cached_result

            self.logger.info("--- CACHE MISS: Executing Research Loop ---")

            # Load prior conversation history for this session
            history_svc = None
            if db_session and self.session_id:
                history_svc = HistoryService(db_session, self.logger)
                self.chatdetails.history = await history_svc.load_history(self.session_id)
                # Save the current user turn immediately
                await history_svc.save_turn(self.session_id, "user", self.args.query)

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

            # Save the assistant's response to history
            if history_svc and self.session_id:
                await history_svc.save_turn(self.session_id, "assistant", final_response)

            await self.cache.cache_response(self.args.query, final_response)
            return final_response

        except Exception as e:
            self.logger.error(f"SearchBoostService : CRITICAL Runtime Error: {e}")

class PersistenceService:
    def __init__(self, session: AsyncSession, logger=None):
        self.session = session
        self.logger = logger or setup_logger(info=False)

    async def save_result(self, job_id: str, query: str, final_answer: str):
        self.logger.debug(f"PersistenceService: Saving result for Job ID: {job_id}")
        try:
            search_result = SearchResult(
                job_id=job_id,
                query=query,
                final_answer=final_answer
            )
            self.session.add(search_result)
            await self.session.commit()
            self.logger.info(f"PersistenceService: Saved result for Job ID: {job_id}")
        except Exception as e:
            self.logger.error(f"PersistenceService: Error saving result for Job ID {job_id}: {e}")