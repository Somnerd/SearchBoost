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
import httpx
import searchboost_src.logger

class WebSearch:
    def __init__(self,query ,config , logger=None):
        self.config = config
        self.query = query

        self.host = self.config.base_url
        self.params = {
            "q": self.query,
            "format": self.config.format,
            "language": self.config.language,
            "safesearch": self.config.safe_search,
            "engine": self.config.engine,
            "num_results": self.config.num_results,
            "region": self.config.region
        }
        self.logger = logger

        pass

    async def searxng_search(self):

        try:
            self.params["q"] = self.query
            self.logger.debug(f"Web Search : params {self.params} ")
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.host}/search", params=self.params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
            results = data.get("results", [])
            normalized_context = []

            for result in results[:5]:
                normalized_context.append(
                    f"Source: {result.get('title')}\n"
                    f"Content: {result.get('content')}\n"
                    f"URL: {result.get('url')}\n"
                )

            self.logger.debug(f"Web Search : Results {normalized_context}")
            return "\n---\n".join(normalized_context) if normalized_context else "No results found."

        except httpx.TimeoutException as e:
            self.logger.warning(f"SearXNG Error: Request Timed Out ({self.host})")
            return "Web search timed out. Could not fetch results."
        except Exception as e:
            self.logger.error(f"SearXNG Error: {e}")
            if 'ConnectionError' in str(e) or 'ConnectError' in str(e):
                return f"Could not connect to {self.host}. Please ensure the SearXNG instance is running."
            return str(e)