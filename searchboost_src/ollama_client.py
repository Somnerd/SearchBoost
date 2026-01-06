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
        self.client = AsyncClient(headers={"Ollama-Client": "SearchBoost"})

        pass

    async def query_ollama(self):
        try:
            response = await self.client.chat(
                model=self.ChatDetails.model,
                messages=[
                    {
                    "role": "system",
                    "content": self.ChatDetails.system_prompt
                    },
                    {
                    "role": self.ChatDetails.role,
                    "content": self.ChatDetails.prompt
                    }
                ]
            )
            return response['message']['content']
            await self.client.aclose()
        except Exception as e:
            self.logger.error(f"Error querying Ollama API: {e}")
            return "Error: Unable to connect to the LLM."