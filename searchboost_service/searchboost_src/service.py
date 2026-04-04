# -*- coding: utf-8 -*-
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from searchboost_src.chat_class import ChatDetails
from searchboost_src.ai_handler import AIHandler
from searchboost_src.web_search import WebSearch
from searchboost_src.redis_manager import RedisManager
from searchboost_src.logger import setup_logger
from searchboost_src.models import SearchResult
from searchboost_src.database import HistoryService
from searchboost_src.pii_detector import PIIDetector

class CacheService:
    def __init__(self, redis_manager: RedisManager, logger):
        self.cache = redis_manager
        self.logger = logger

    async def get(self, query: str):
        await self.cache.connect()
        return await self.cache.get_cached_response(query)

    async def set(self, query: str, response: str, cache_eligible: bool):
        if cache_eligible:
            self.logger.debug(f"CacheService: Caching response for query.")
            await self.cache.cache_response(query, response)
        else:
            self.logger.warning("CacheService: Cache write SKIPPED — PII detected or ineligible.")


class ContextService:
    def __init__(self, history_svc: HistoryService, logger):
        self.history = history_svc
        self.logger = logger

    async def assemble_context(self, session_id: str, query: str) -> str:
        """Assembles efficient semantic context from cross-thread conversations."""
        parts = session_id.split(':')
        if len(parts) >= 2:
            username = parts[1]
            session_prefix = f"SB-SESSION:{username}:"
            self.logger.info(f"ContextService: Fetching cross-thread semantic context for user '{username}'")
            semantic_context = await self.history.search_relevant_history(
                session_prefix, 
                query,
                exclude_session_id=session_id
            )
            
            if semantic_context:
                # Filter meaningless short context fragments
                filtered = [ctx for ctx in semantic_context if len(ctx['content']) > 15]
                if filtered:
                    context_str = "\n".join([
                        f"[{ctx['role'].upper()} from thread '{ctx['session_id'].split(':')[-1]}']: {ctx['content']}"
                        for ctx in filtered
                    ])
                    return f"--- CROSS-THREAD CONTEXT ---\n{context_str}\n----------------------------\n\n"
        return ""


class SearchBoostService:
    def __init__(self, ai, search, redis, db, logger=None, args=None, session_id=None):
        self.logger = logger or setup_logger(info=False)
        self.args = args
        self.session_id = session_id  

        self.ai_config = ai
        self.search_config = search

        if hasattr(self.args, 'model') and self.args.model:
            self.logger.info(f"SearchBoostService: Overriding default model '{self.ai_config.model}' with '{self.args.model}'")
            self.ai_config.model = self.args.model

        self.cache_svc = CacheService(RedisManager(redis, self.logger), self.logger)

        self.chatdetails = ChatDetails(config=self.ai_config, prompt=self.args.query)
        self.web_search_instance = WebSearch(query=self.args.query, config=self.search_config, logger=self.logger)


    async def run(self, db_session: AsyncSession = None):
        self.logger.info("SearchBoostService: Running service...")

        history_svc = None
        if db_session and self.session_id:
            from searchboost_src.ollama_client import OllamaClient
            ollama_client = OllamaClient(logger=self.logger, ChatDetails=self.chatdetails)
            history_svc = HistoryService(db_session, self.logger, ollama_client=ollama_client)
            
            self.chatdetails.history = await history_svc.load_history(self.session_id)
            
            context_svc = ContextService(history_svc, self.logger)
            semantic_injection = await context_svc.assemble_context(self.session_id, self.args.query)
            if semantic_injection:
                self.chatdetails.prompt = semantic_injection + self.chatdetails.prompt

        # Attempt Cache Hit
        cached_result = await self.cache_svc.get(self.args.query)
        if cached_result:
            self.logger.info("--- CACHE HIT ---")
            if history_svc and self.session_id:
                # Fire and forget history save
                asyncio.gather(
                    history_svc.save_turn(self.session_id, "user", self.args.query),
                    history_svc.save_turn(self.session_id, "assistant", cached_result)
                )
            return cached_result

        self.logger.info("--- CACHE MISS: Executing Research Loop ---")

        if history_svc and self.session_id:
            await history_svc.save_turn(self.session_id, "user", self.args.query)

        pii_detector = PIIDetector(logger=self.logger)
        original_query_pii = pii_detector.scan(self.args.query)

        self.ai_handler = AIHandler(self.logger, reason="optimization")
        optimized_query = await self.ai_handler.query_LLM(self.chatdetails)

        post_opt_cache = await self.cache_svc.get(optimized_query)
        if post_opt_cache:
            self.logger.info("--- CACHE HIT (POST-OPTIMIZATION) ---")
            if history_svc and self.session_id:
                asyncio.gather(history_svc.save_turn(self.session_id, "assistant", post_opt_cache))
            return post_opt_cache

        optimized_query_pii = pii_detector.scan(optimized_query)
        cache_eligible = not original_query_pii and not optimized_query_pii

        self.web_search_instance.query = optimized_query
        web_search_results = await self.web_search_instance.searxng_search()
        
        self.chatdetails.prompt = f"Using the following web search results, answer the question: {self.chatdetails.prompt}\n\nWeb Search Results:\n{web_search_results}"

        self.ai_handler = AIHandler(self.logger, reason="research")
        final_response = await self.ai_handler.query_LLM(self.chatdetails)

        if history_svc and self.session_id:
            await history_svc.save_turn(self.session_id, "assistant", final_response)

        final_response_pii = pii_detector.scan(final_response)
        
        await self.cache_svc.set(self.args.query, final_response, cache_eligible and not final_response_pii)
        if self.args.query != optimized_query:
            await self.cache_svc.set(optimized_query, final_response, cache_eligible and not final_response_pii)

        return final_response


class PersistenceService:
    def __init__(self, session: AsyncSession, logger=None):
        self.session = session
        self.logger = logger or setup_logger(info=False)

    async def save_result(self, job_id: str, query: str, final_answer: str):
        search_result = SearchResult(job_id=job_id, query=query, final_answer=final_answer)
        self.session.add(search_result)
        await self.session.commit()