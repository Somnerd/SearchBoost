import asyncio
import openai
import chat_class

async def api_call(chatdetails, API_KEY):
    try:
        client = openai.OpenAI(
            api_key = API_KEY,  # or os.getenv("POE_API_KEY")
            base_url = "https://api.poe.com/v1",
        )

        chat = client.chat.completions.create(
            model = chatdetails.model,
            messages = [{"role": chatdetails.role, "content": chatdetails.prompt}],
            extra_body = chatdetails.extra_body
        )

        if response.choices and response.choices[0].message.content:
        print(chat.choices[0].message.content)
        return chat.choices[0].message.content
    except Exception as e:
        print(f"Error querying Poe API: {e}")
        return "Error: Unable to connect to the LLM."
