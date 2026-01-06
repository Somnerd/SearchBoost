import asyncio

from searchboost_src.chat_class import *
from searchboost_src.ollama_client import *
from searchboost_src.api_client import *
import searchboost_src.logger


class AIHandler:
    def __init__(self,logger=None,reason="optimization"):
        self.logger = logger
        self.reason = reason

        self.query_optimization_prompt = (
            "You are a search query optimizer. Convert the user's request "
            "into a concise, keyword-rich search string for a search engine. "
            "Output ONLY the optimized string."
        )

        self.query_system_instruction = (
            "You are an expert research assistant. Use the provided search context to "
            "answer the user's question accurately. If the answer isn't in the context, "
            "say so. Cite your sources using [Source Title](URL)."
        )
        pass

    async def query_LLM(self, ChatDetails):
        try:
            if self.reason == "optimization":
                ChatDetails.system_prompt = self.query_optimization_prompt
            elif self.reason == "research":
                ChatDetails.system_prompt = self.query_system_instruction
            else:
                self.logger.warning(f"AI Handler : Unknown reason for LLM query: {self.reason}")
                return ChatDetails.prompt

            if ChatDetails.model.lower() == "cloud" or "gpt" in ChatDetails.model.lower() or "poe" in ChatDetails.model.lower():
                self.logger.debug(f"AIHandler : Using cloud AI for query {self.reason}.")
                optimized_query = await api_client().api_call(ChatDetails)
                self.logger.debug(f"AIHandler : Optimized Query: {optimized_query}")
                return optimized_query
            elif ChatDetails.model.lower() == "local" or "llama" in ChatDetails.model.lower():
                pass
            else:
                self.logger.warning(f"AIHandler : Unknown model specified: {ChatDetails.model}. Defaulting to cloud AI.")

            self.logger.debug(f"AIHandler : Using local AI for query {self.reason}.")
            optimized_query = await OllamaClient(logger = self.logger,ChatDetails = ChatDetails).query_ollama()
            self.logger.debug(f"AIHandler : Optimized Query: {optimized_query}")
            return optimized_query
        except Exception as e:
            self.logger.error(f"AI Handler : Error in AI Handler: {e}")
            return ChatDetails.prompt
