import asyncio
from searchboost_src.cli import parse_arguments
from searchboost_src.web_scraper import scrape_results
from searchboost_src.summarizer import optimize_query, summarize_results

async def main():
    try :
        args = parse_arguments()

        # Step 1: Optimize query
        print("Optimizing query...")
        optimized_query = await optimize_query(args.model, args.query)
        print(f"Optimized Query: {optimized_query}")

        # Step 2: Scrape search results
        print("\nFetching search results...")
        try:
            results = scrape_results(args.engine, optimized_query)
            for idx, result in enumerate(results):
                print(f"\nResult {idx + 1}:")
                print(f"Title: {result['title']}")
                print(f"URL: {result['url']}")
                print(f"Snippet: {result['snippet']}")
        except Exception as e:
            print("ERROR : ")
            print(f"Error during search: {e}")
            return

        # Step 3: Summarize results
        print("\nSummarizing search results...")
        summary = await summarize_results(args.model, results)
        print("\nSummary:")
        print(summary)
    except Exception as e:
        print("ERROR : ",e)
if __name__ == "__main__":

  asyncio.run(main())
