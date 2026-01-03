import asyncio
import openai
from openai import AsyncOpenAI
from searchboost_src.chat_class import ChatDetails
import searchboost_src.logger


class api_client:
    def __init__(self):
        pass

    async def api_call(self, ChatDetails):
    logger = await searchboost_src.logger.setup_logger()
    
    # Check if we should use the local Ollama instance
    if self.model.lower() == "local" or "llama" in self.model.lower():
        base_url = "http://localhost:11434/v1"
        api_key = "ollama"  # Ollama doesn't need a real key, but the client requires a string
        model_name = "llama3.2" if self.model.lower() == "local" else self.model
        extra_params = {} # Local models don't support Poe's 'extra_body'
    else:
        # Default to Poe Cloud API
        base_url = "https://api.poe.com/v1"
        api_key = API_KEY

    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        chat = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": self.role, "content": self.prompt}],
            **extra_params
        )

        if chat.choices and chat.choices[0].message.content:
            content = chat.choices[0].message.content
            return content

    except Exception as e:
        logger.error(f"Error querying {base_url}: {e}")
        return "Error: Unable to connect to the LLM."