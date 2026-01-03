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
        self.host = "http://localhost:11434"
        self.client = AsyncClient(host=self.host)
        pass

    async def query_ollama(self):
        try:


            response = await self.client.chat(
            model=self.ChatDetails.model,
            messages=[{
                "role": self.ChatDetails.role,
                "content": self.ChatDetails.prompt
                }]
            )

            if response != None:
                self.logger.info(f"Ollama response: {response.strip()}")
                return response["text"].strip()

            else:
                self.logger.error("Error: No 'text' field found in response from Ollama API.")
                return "Error: No response text from LLM."
        except Exception as e:
            self.logger.error(f"Error querying Ollama API: {e}")
            return "Error: Unable to connect to the LLM."
