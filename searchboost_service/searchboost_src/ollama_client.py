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
import ollama

from ollama import AsyncClient

from searchboost_src.chat_class import *
import searchboost_src.logger

class OllamaClient:
    def __init__(self,logger=None,ChatDetails=None):
        self.client = AsyncClient()
        self.logger = logger
        self.ChatDetails = ChatDetails
        self.host = self.ChatDetails.config.base_url

        self.client = AsyncClient(
            host=self.host,
            headers={"Ollama-Client": "SearchBoost"}
            )

        pass

    async def query_ollama(self):
        try:
            self.logger.debug(f"""OLLAMA  CLIENT: User Prompt :{self.ChatDetails.prompt}""")
            
            # Build a full multi-turn message array:
            #   [system] + [prior history turns...] + [current user message]
            messages = [{"role": "system", "content": self.ChatDetails.system_prompt}]

            history = getattr(self.ChatDetails, 'history', [])
            if history:
                self.logger.info(f"OLLAMA CLIENT: Injecting {len(history)} prior conversation turns into context.")
                messages.extend(history)
            
            messages.append({"role": self.ChatDetails.config.role, "content": self.ChatDetails.prompt})

            chat_coroutine = self.client.chat(
                model=self.ChatDetails.config.model,
                messages=messages
            )
            
            # Accommodating slow CPU inference with a configurable upper bound (default: 180s)
            timeout_limit = getattr(self.ChatDetails.config, 'timeout', 180.0)
            self.logger.info(f"OLLAMA CLIENT: Sending chat request to {self.host} (Timeout: {timeout_limit}s)")
            
            response = await asyncio.wait_for(chat_coroutine, timeout=timeout_limit)
            
            self.logger.info("OLLAMA CLIENT: Successfully received response from LLM.")
            self.logger.debug(f"""OLLAMA CLIENT :
                                    Ollama Response:
                                        {response}
                                        """)
            return response['message']['content']
        except asyncio.TimeoutError:
            self.logger.error(f"OLLAMA CLIENT: Timeout! The local LLM model failed to respond within {timeout_limit} seconds.")
            return f"Error: The AI model took too long to respond (timeout after {timeout_limit}s). Please try again later."
        except Exception as e:
            self.logger.error(f"OLLAMA CLIENT : Error querying Ollama API: {e}")
            return "Error: Unable to connect to the LLM."