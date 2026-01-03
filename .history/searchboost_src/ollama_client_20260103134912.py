import asyncio
import ollama
from ollama import AsyncClient

from searchboost_src.chat_class import *
import searchboost_src.logger

class OllamaClient:
    def __init__(self,logger=None):
        self.client = AsyncClient()
        pass

    async def query_ollama(self, ChatDetails):
        logger = await searchboost_src.logger.setup_logger()

        system_instruction = (
                "You are an expert research assistant. Use the provided search context to "
                "answer the user's question accurately. If the answer isn't in the context, "
                "say so. Cite your sources using [Source Title](URL)."
            )

        try:
            response = await AsyncClient().message(model=ChatDetails.model, messages=[{"role": "user", "content": ChatDetails.prompt}])

            if response != None:
                logger.info(f"Ollama response: {response.strip()}")
                return response["text"].strip()
            else:
                logger.error("Error: No 'text' field found in response.")
                return "Error: No response text from LLM."
        except Exception as e:
            logger.error(f"Error querying Ollama API: {e}")
            return "Error: Unable to connect to the LLM."
