import asyncio
import ollama
from ollama import AsyncClient
import searchboost_src.logger

async def query_ollama(model, prompt):
    logger = await searchboost_src.logger.setup_logger()

    try:
        response = await AsyncClient().message(model=model, messages=[{"role": "user", "content": prompt}])

        if response != None:
            return response["text"].strip()
        else:
            logger.error("Error: No 'text' field found in response.")
            return "Error: No response text from LLM."
    except Exception as e:
        logger.error(f"Error querying Ollama API: {e}")
        return "Error: Unable to connect to the LLM."
