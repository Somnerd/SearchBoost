import asyncio
import openai



async def api_call(model, prompt):

    try:
        client = openai.OpenAI(
            api_key = "YOUR_POE_API_KEY",  # or os.getenv("POE_API_KEY")
            base_url = "https://api.poe.com/v1",
        )

        chat = client.chat.completions.create(
            model = "claude-sonnet-4.5",
            messages = [{"role": "user", "content": "Hello world"}],
            extra_body = {
            "thinking_budget": 4096,
            "web_search": True
            }
        )

        print(chat.choices[0].message.content)
        else:
            print("Error: No 'text' field found in response.")
            return "Error: No response text from LLM."
    except Exception as e:
        print(f"Error querying Ollama API: {e}")
        return "Error: Unable to connect to the LLM."
