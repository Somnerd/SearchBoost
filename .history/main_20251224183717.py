import asyncio
from searchboost_src.cli import parse_arguments
from searchboost_src.web_scraper import scrape_results
from searchboost_src.summarizer import optimize_query, summarize_results
from searchboost_src.api_call import api_call as poe_api_call
from searchboost_src.chat_class import Chat_Details


async def main():
    args = parse_arguments()
    
    if args != None and args.query != None:
        chat_details = Chat_Details(
            model=args.model,
            query=args.query,
            engine=args.engine,
            api_call=poe_api_call
        )

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
                print(f"\nTitle: {result['title']}")
                print(f"\URL: {result['url']}")
                print(f"\nSnippet: {result['snippet']}")
        except Exception as e:
            print("ERROR : ")
            print(f"Error during search: {e}")
            return

        # Step 3: Summarize results
        print("\nSummarizing search results...")
        summary = await summarize_results(chat_details, results)
        print("\nSummary:")
        print(summary)
    else:
       str:query = input("No query provided. Please provide a search query .")
       print(f"You entered: {query}")

async def test():
    try:
        args = parse_arguments()

        chat_details = Chat_Details(
            model=args.model,
            query=args.query,
            engine=args.engine,
            api_call=poe_api_call
        )

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
                print(f"\nTitle: {result['title']}")
                print(f"\URL: {result['url']}")
                print(f"\nSnippet: {result['snippet']}")
        except Exception as e:
            print("ERROR : ")
            print(f"Error during search: {e}")
            return

        # Step 3: Summarize results
        print("\nSummarizing search results...")
        summary = await summarize_results(chat_details, results)
        print("\nSummary:")
        print(summary)


if __name__ == "__main__":

  asyncio.run(main())
