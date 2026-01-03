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

    async def query_optimization(self, ChatDetails):
        #TODO : implement pass through llm , and follow up question to refine the query . There should be no more than one query from LLM to user

        try:
            self.logger.info(f"Original Query: {ChatDetails.prompt}")
            ChatDetails.prompt = self.query_optimization_prompt + ChatDetails.prompt

            if (ChatDetails.model.lower() == "local" or "llama" in ChatDetails.model.lower()):
                self.logger.info("Using local AI for query optimization.")

                return ChatDetails.prompt
                #optimized_query = await ollama_client().query_ollama(ChatDetails)
                #return optimized_query
            else:
                self.logger.info("Using cloud AI for query optimization.")
                optimized_query = await api_client().api_call(ChatDetails)
                return optimized_query
        except Exception as e:
            self.logger.error(f"Error optimizing query: {e}")
            return ChatDetails.prompt

    async def research_answer(self, ChatDetails):
        try:
            if (ChatDetails.model.lower() == "local" or "llama" in ChatDetails.model.lower()):
                self.logger.info("Using local AI for research answer.")

                ollama_client_instance = OllamaClient(self.logger)
                answer = await ollama_client_instance.query_ollama(ChatDetails)
                return answer
            else:
                self.logger.info("Using cloud AI for research answer.")
                api_client_instance = ApiClient(self.logger)
                answer = await api_client_instance.api_call(ChatDetails)
                return answer
        except Exception as e:
            self.logger.error(f"Error getting research answer: {e}")
            return "Error: Unable to get answer from the LLM."