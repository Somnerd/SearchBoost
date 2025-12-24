import asyncio
from searchboost_src.argparser import parse_arguments
#from searchboost_src.web_scraper import scrape_results
#from searchboost_src.summarizer import optimize_query, summarize_results
from searchboost_src.chat_class import ChatDetails

async def main():
    args = parse_arguments()
    
    # Fix 1: Logic check for args. If args is None, we can't check args.query
    if args is None or args.query is None:
    
        chat_details = ChatDetails()
        chat_details.prompt=input("No query provided. Please provide a search query: ")
        print(f"Using query: {chat_details.prompt}")
        # Note: You likely need to define chat_details here too if the script is to continue
        return 
    else:
        # Fix 2: Indentation was too deep here
        chat_details = ChatDetails()
        model=args.model,
        query=args.query,
        engine=args.engine,
        
        # Step 1: Optimize query
        print("Optimizing query...")
        optimized_query = await optimize_query(chat_details)
        print(f"Optimized Query: {optimized_query}")

        # Step 2: Scrape search results
        print("\nFetching search results...")
        try:
            results = scrape_results(chat_details.engine, optimized_query)
            for idx, result in enumerate(results):
                print(f"\nResult {idx + 1}:")
                print(f"Title: {result['title']}")
                print(f"URL: {result['url']}")
                print(f"Snippet: {result['snippet']}")
        except Exception as e:
            print(f"ERROR: Error during search: {e}")
            return

        # Step 3: Summarize results
        print("\nSummarizing search results...")
        summary = await summarize_results(chat_details, results)
        print("\nSummary:")
        print(summary)


if __name__ == "__main__": # Fix 3: Usually you want "__main__" to run the script
    asyncio.run(main())