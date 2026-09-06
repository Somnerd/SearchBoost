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

import asyncio

from searchboost_src.chat_class import *
from searchboost_src.ollama_client import *
from searchboost_src.api_client import *
import searchboost_src.logger


class AIHandler:
    def __init__(self,logger=None,reason="optimization"):
        self.logger = logger
        self.reason = reason

        self.query_optimization_prompt = (
            "You are a search query optimizer. Convert the user's request "
            "into a concise, keyword-rich search string for a search engine. "
            "Output ONLY the optimized string."
        )

        self.query_system_instruction = (
            "You are an expert research assistant. Use the provided search context to "
            "answer the user's question accurately. If the answer isn't in the context, "
            "say so. Cite your sources using [Source Title](URL)."
        )
        pass

    async def query_LLM(self, ChatDetails):
        try:
            self.logger.debug(f"AI Handler : Reason for LLM Call : {self.reason}")
            if self.reason == "optimization":
                ChatDetails.system_prompt = self.query_optimization_prompt
            elif self.reason == "research":
                ChatDetails.system_prompt = self.query_system_instruction
            else:
                self.logger.warning(f"AI Handler : Unknown reason for LLM query: {self.reason}")
                return ChatDetails.prompt

            self.logger.debug("AI Handler : Calling model")
            model_str = str(getattr(ChatDetails.config, 'model', 'llama3.2')).lower()
            if model_str == "cloud" or "gpt" in model_str or "poe" in model_str:
                self.logger.debug(f"AIHandler : Using cloud AI for query {self.reason}.")
                optimized_query = await ApiClient(logger=self.logger).api_call(ChatDetails)
                self.logger.debug(f"AIHandler : Optimized Query: {optimized_query}")
                return optimized_query
            else:
                self.logger.debug(f"AIHandler : Using local AI ({model_str}) for query {self.reason}.")
                optimized_query = await OllamaClient(logger=self.logger, ChatDetails=ChatDetails).query_ollama()
                self.logger.debug(f"AIHandler : Optimized Query: {optimized_query}")
                return optimized_query
        except Exception as e:
            self.logger.error(f"AI Handler : Error in AI Handler: {e}")
            return ChatDetails.prompt
