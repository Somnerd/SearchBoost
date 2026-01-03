import asyncio

from searchboost_src.chat_class import *
from searchboost_src.ollama_client import *
from searchboost_src.api_client import *
import searchboost_src.logger

#TODO : Implement the optimizer_query method

class AIHandler:
    def __init__(self,logger=None):
        self.logger = logger

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
        #TODO : implement pass through llm , and follow up question to refine the query . There should be no more than one query from LLM to user

        try:
            self.logger.info(f"Original Query: {ChatDetails.prompt}")

            if reason == "optimization":

                ChatDetails.prompt = self.query_optimization_prompt + ChatDetails.prompt

                if (ChatDetails.model.lower() == "local" or "llama" in ChatDetails.model.lower()):
                    self.logger.info("Using local AI for query {reason}.")
                    return ChatDetails.prompt

                else:
                    self.logger.info(f"Using cloud AI for query {reason}.")
                    optimized_query = await api_client().api_call(ChatDetails)
                    return optimized_query
        except Exception as e:
            self.logger.error(f"Error optimizing query: {e}")
            return ChatDetails.prompt
