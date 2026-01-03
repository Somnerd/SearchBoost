import asyncio
import ollama

from searchboost_src.chat_class import *
from searchboost_src.ollama_client import *
from searchboost_src.api_client import *
import searchboost_src.logger

#TODO : Implement the optimizer_query method

class AIHandler:
    def __init__(self,logger=None):
        self.logger = logger
        self.client = ollama.AsyncClient()
        pass

    async def optimizer_query(self, ChatDetails):
        #TODO : implement pass through llm , and follow up question to refine the query . There should be no more than one query from LLM to user
        self.logger.info("Simulating query optimization...")
        self.logger.info(f"Original Query: {ChatDetails.prompt}")
        await asyncio.sleep(1)  # Simulate some processing time
        self.logger.info("Passing through optimizer...")
        await asyncio.sleep(1)  # Simulate some processing time
        self.logger.info("Query optimized.")

        if (ChatDetails.model.lower() == "local" or "llama" in ChatDetails.model.lower()):
            self.logger.info("Using local AI for query optimization.")
            return ChatDetails.prompt
            #optimized_query = await ollama_client().query_ollama(ChatDetails)
            #return optimized_query
        else:
            self.logger.info("Using cloud AI for query optimization.")
            optimized_query = await api_client().api_call(ChatDetails)
            return optimized_query