import argparse
import logging
import sys

async def parse_arguments():
    """
    Parses command-line arguments.
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="SearchBoost: Optimize, search, and summarize queries.")

    # Search engine argument
    parser.add_argument(
        "-e","--engine",
        type=str,
        default="google.com",
        help="Search engine domain to use (default: google.com)"
    )

    # Search query argument
    parser.add_argument(
        "-q","--query",
        type=str,
        required=False,
        help="Search query"
    )

    # LLM model argument
    parser.add_argument(
        "-m","--model",
        type=str,
        default="llama3.2",
        help="LLM model to use for optimization and summarization (default: llama3)"
    )

    return parser.parse_args()

async def final_arguments():
    args = await parse_arguments()
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        encoding='utf-8',
        format='%(levelname)s - %(message)s - %(asctime)s',
        handlers=[
            logging.FileHandler("searchboost.log", mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
            ]
        )

    for arg_name , arg_value in vars(args).items():
        logger.info(f"{arg_name}: {arg_value}")

    if args.query is None:
        logger.warning("No query provided via command line. Prompting for input.")
        args.query = input("Please enter your search query: ")
    
    return args