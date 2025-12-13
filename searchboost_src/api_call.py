import asyncio
import openai

class ChatDetails:
    def __init__(self, model, prompt):
        self.model = model
        self.prompt = prompt
        self.role = "user"
        self.extra_body = {
            "thinking_budget": 4096,
            "web_search": True
        }



async def api_call(ChatDetails, API_KEY):

    try:
        client = openai.OpenAI(
            api_key = API_KEY,  # or os.getenv("POE_API_KEY")
            base_url = "https://api.poe.com/v1",
        )

        chat = client.chat.completions.create(
            model = ChatDetails.model,
            messages = [{"role": ChatDetails.role, "content": ChatDetails.prompt}],
            extra_body = ChatDetails.extra_body
        )

        print(chat.choices[0].message.content)
        else:
            print("Error: No 'text' field found in response.")
            return "Error: No response text from LLM."
    except Exception as e:
        print(f"Error querying Poe API: {e}")
        return "Error: Unable to connect to the LLM."
