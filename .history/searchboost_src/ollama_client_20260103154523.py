import asyncio
import ollama
from ollama import AsyncClient

from searchboost_src.chat_class import *
import searchboost_src.logger

class OllamaClient:
    def __init__(self,logger=None,ChatDetails=None):
        self.client = AsyncClient()
        self.logger = logger
        self.ChatDetails = ChatDetails
        pass

    async def query_ollama(self):

        try:
            response = await AsyncClient().chat(
                model=ChatDetails.model,
                messages=[{"role": ChatDetails.role, "content": ChatDetails.prompt}]
                )

            if response != None:
                self.logger.info(f"Ollama response: {response.strip()}")
                return response["text"].strip()

            else:
                self.logger.error("Error: No 'text' field found in response.")
                return "Error: No response text from LLM."
        except Exception as e:
            self.logger.error(f"Error querying Ollama API: {e}")
            return "Error: Unable to connect to the LLM."
