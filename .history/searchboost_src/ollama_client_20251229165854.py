import asyncio
import ollama
from ollama import AsyncClient

from searchboost_src.chat_class import ChatDetails
import searchboost_src.logger

async def query_ollama(ChatDetails):
    logger = await searchboost_src.logger.setup_logger()

    try:
        response = await AsyncClient().message(model=ChatDetails.model, messages=[{"role": "user", "content": ChatDetails.prompt}])

        if response != None:
            return response["text"].strip()
        else:
            logger.error("Error: No 'text' field found in response.")
            return "Error: No response text from LLM."
    except Exception as e:
        logger.error(f"Error querying Ollama API: {e}")
        return "Error: Unable to connect to the LLM."
