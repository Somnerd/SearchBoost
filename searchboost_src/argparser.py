import argparse
import searchboost_src.logger

async def parse_arguments():
    """
    Parses command-line arguments.
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="SearchBoost: Optimize, search, and summarize queries.")

    parser.add_argument(
        "-s","--stream",
        type = bool,
        default=False,
        help="Enable streaming responses from the LLM (default: False)"
    )

    # Search engine argument
    parser.add_argument(
        "-e","--engine",
        type=str,
        default="searxng",
        help="Search engine domain to use (default: searxng)"
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
        help="LLM model to use for optimization and summarization (default: llama3.2)"
    )

    return parser.parse_args()

async def final_arguments():
    try :
        args = await parse_arguments()
        logger = await searchboost_src.logger.setup_logger()

        for arg_name , arg_value in vars(args).items():
            logger.info(f"{arg_name}: {arg_value}")

        if args.query is None:
            logger.warning("No query provided via command line. Prompting for input.")
            args.query = input("Please enter your search query: ")

        return args
    except Exception as e:
        logger = await searchboost_src.logger.setup_logger()
        logger.error(f"Error in Argparser: {e}")
        raise e