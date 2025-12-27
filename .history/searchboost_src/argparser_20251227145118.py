import argparse

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
    
    for arg_name , arg_value in vars(args).items():
        if arg_value is None:
            print(f"ERROR: No {arg_name} provided. Use --{arg_name} .")
            if arg_name == "query":
                args.query = input("Please enter your search query: ")
        else:
            print(f"Defaulting to {arg_name}: {arg_value}")

    return args