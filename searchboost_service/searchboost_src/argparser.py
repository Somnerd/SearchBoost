# -*- coding: utf-8 -*-
# SearchBoost: AI-Powered Semantic Search & Reliability Engine
# Copyright (C) 2026 Nikolaos Alexandrakis
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ---------------------------------------------------------------------
# COMMERCIAL USE NOTICE:
# For licensing outside the scope of AGPLv3, contact: nikolasalexandrakis.work@gmail.com
# ---------------------------------------------------------------------

import argparse
from searchboost_src.logger import setup_logger

class Argsparser_Instance:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="SearchBoost: Optimize, search, and summarize queries.")
        self.logger = setup_logger()
        self._setup_arguments()

    def _setup_arguments(self):
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

        self.parser.add_argument(
            "-u","--username",
            type=str,
            default="guest",
            help="Username for identity and persistence (default: guest)"
        )

        self.parser.add_argument(
            "--thread_id",
            type=str,
            default="default",
            help="Conversation thread ID (default: default)"
        )

    async def parse_arguments(self, args=None):
        """
        Parses command-line arguments.
        Returns:
            argparse.Namespace: Parsed arguments.
        """
        self.args = self.parser.parse_args(args)
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