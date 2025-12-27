import asyncio
from searchboost_src.argparser import parse_arguments
from searchboost_src.chat_class import ChatDetails
from searchboost_src.ai_handler import optimizer_query
from searchboost_src.web_scraper import test_searxng

async def main():
    args = await parse_arguments()
    
    chat_details = ChatDetails()
    chat_details.prompt=args.query
    chat_details.model=args.model  
    chat_details.engine=args.engine

    if args.query is None :
        print("\nERROR: No query provided. Use --query to specify a search query.")
        chat_details.prompt=input("\nNo query provided. \nPlease provide a search query: ")
        print(f"\nUsing query: {chat_details.prompt}")

    if args.model is None : 
        print("No model specified. Defaulting to 'local'.")
        chat_details.model="local"
    
    if args.engine is None :
        print("No search engine specified. Defaulting to 'import json'.")
        chat_details.engine={"import json"}    
    
    # Step 1: Optimize query
    print("Optimizing query...")
    optimized_query = await optimizer_query()
    print(f"Optimized Query: {optimized_query}")

    # Step 2: Scrape search results
    print("\nFetching search results...")
    try:
        #TODO : Implement searxng function to fetch real search results 
        print("Simulating search results fetch...")
        results = ["Result 1 content", "Result 2 content", "Result 3 content"]
        print(f"Fetched {len(results)} results.")
    except Exception as e:
        print(f"ERROR: Error during search: {e}")
        return

    # Step 3: Summarize results
    print("\nSummarizing search results...")
    summary = await test_searxng(optimized_query, chat_details.engine)
    print("\nSummary:")
    print(summary)


if __name__ == "__main__": # Fix 3: Usually you want "__main__" to run the script
    asyncio.run(main())