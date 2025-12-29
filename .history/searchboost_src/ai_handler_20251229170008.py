import asyncio
from searchboost_src.chat_class import ChatDetails
from searchboost_src.ollama_client import query_ollama
from searchboost_src.api_client import api_call
from searchboost_src.logger import *

#TODO : Implement the optimizer_query method
async def optimizer_query(ChatDetails):
    logger = await logger.setup_logger()
    #TODO : implement pass through llm , and follow up question to refine the query . There should be no more than one query from LLM to user
    logger.info("Simulating query optimization...")
    logger.info(f"Original Query: {ChatDetails.prompt}")
    await asyncio.sleep(1)  # Simulate some processing time
    logger.info("Passing through optimizer...")
    await asyncio.sleep(1)  # Simulate some processing time
    logger.info("Query optimized.")

    if (ChatDetails.model.lower() == "local" or "llama" in ChatDetails.model.lower()):
        logging.info("Using local for query optimization.")
        optimized_query = await query_ollama(ChatDetails)
    else:
        logging.info("Using cloud for query optimization.")
        optimized_query = await api_call(ChatDetails)