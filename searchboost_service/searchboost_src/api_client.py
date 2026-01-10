import asyncio
import openai
from openai import AsyncOpenAI
from searchboost_src.chat_class import ChatDetails
import searchboost_src.logger


class ApiClient:
    def __init__(self,logger=None):
        self.logger = logger
        pass

    async def api_call(self, ChatDetails):
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
            self.logger.error(f"Error querying {base_url}: {e}")
            return "Error: Unable to connect to the LLM."