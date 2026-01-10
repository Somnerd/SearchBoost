import argparse
from searchboost_src.logger import setup_logger

class Argsparser_Instance:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="SearchBoost: Optimize, search, and summarize queries.")
        self.logger = setup_logger()

    async def parse_arguments(self):
        """
        Parses command-line arguments.
        Returns:
            argparse.Namespace: Parsed arguments.
        """
        self.parser.add_argument(
            "-s","--stream",
            type = bool,
            default=False,
            help="Enable streaming responses from the LLM (default: False)"
        )

        self.parser.add_argument(
            "-t","--type",
            type = str,
            default="local",
            help="Toggle between local or cloud AI provider (default: local)"
        )


        # Search engine argument
        self.parser.add_argument(
            "-e","--engine",
            type=str,
            default="searxng",
            help="Search engine domain to use (default: searxng)"
        )

        # Search query argument
        self.parser.add_argument(
            "-q","--query",
            type=str,
            required=False,
            help="Search query"
        )

        self.parser.add_argument(
            "-i","--info",
            type=str,
            default="info",
            help="Set logging level (default: info)"
        )

        # LLM model argument
        self.parser.add_argument(
            "-m","--model",
            type=str,
            default="llama3.2",
            help="LLM model to use for optimization and summarization (default: llama3.2)"
        )
        self.args = self.parser.parse_args()
        return self.args


    async def debug_logs(self):
        if self.args.info.lower() == "debug":
            for arg_name , arg_value in vars(self.args).items():
                self.logger.debug(f"{arg_name}: {arg_value}")


    async def final_arguments(self):
        try :
            await self.parse_arguments()


            if self.args.query is None:
                self.logger.warning("No query provided via command line. Prompting for input.")
                self.args.query = input("Please enter your search query: ")

            self.logger = setup_logger(self.args.info)
            await self.debug_logs()

            return self.args

        except Exception as e:
            self.logger.error(f"Error in Argparser: {e}")
            raise e