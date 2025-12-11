from .ollama_client import query_ollama

async def optimize_query(model, query):
    prompt = f"Optimize the following search query for better search engine results: {query}"
    return await query_ollama(model, prompt)

async def summarize_results(model, results):
        prompt = "Here are the top search results:\n" + "\n".join(
            f"Title: {result['title']}\nSnippet: {result['snippet']}" for result in results
            ) + "\nSummarize the key findings."
        return await query_ollama(model, prompt)





