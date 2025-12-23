import argparse

def parse_arguments():
    """
    Parses command-line arguments.
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="SearchBoost: Optimize, search, and summarize queries.")

    # Search engine argument
    parser.add_argument(
        "--engine",
        type=str,
        default="google.com",
        help="Search engine domain to use (default: google.com)"
    )

    # Search query argument
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="Search query"
    )

    # LLM model argument
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.2",
        help="LLM model to use for optimization and summarization (default: llama3)"
    )

    return parser.parse_args()
