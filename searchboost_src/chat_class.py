import asyncio
import openai
from openai import AsyncOpenAI


class ChatDetails:
    def __init__(self, model: str, prompt: str,role:str ="user"):
        self.model = model
        self.prompt = prompt
        self.role = role
        self.extra_body = {
            "thinking_budget": 4096,
            "web_search": True
        }

    async def api_call(self, API_KEY:str):
        try:
            client = openai.OpenAI(
                api_key = API_KEY,  # or os.getenv("POE_API_KEY")
                base_url = "https://api.poe.com/v1",
            )

            chat = await client.chat.completions.create(
                model = self.model,
                messages = [{"role": self.role, "content": self.prompt}],
                extra_body = self.extra_body
            )

            if chat.choices and chat.choices[0].message.content:
                print(chat.choices[0].message.content)
                return chat.choices[0].message.content

        except Exception as e:
            print(f"Error querying Poe API: {e}")
            return "Error: Unable to connect to the LLM."
