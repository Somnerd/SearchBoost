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

import openai
from openai import AsyncOpenAI
from searchboost_src.chat_class import ChatDetails
import searchboost_src.logger


class ApiClient:
    def __init__(self,logger=None):
        self.logger = logger
        pass

    async def api_call(self, chat_details):
        api_key = getattr(chat_details.config, "api", None)
        base_url = getattr(chat_details.config, "provider", None)
        model = getattr(chat_details.config, "model", None)
        role = getattr(chat_details.config, "role", "user")

        messages = []
        if chat_details.system_prompt:
            messages.append({"role": "system", "content": chat_details.system_prompt})
        messages.append({"role": role, "content": chat_details.prompt})

        extra_params = getattr(chat_details, "extra_body", {})

        try:
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
            )

            chat = await client.chat.completions.create(
                model=model,
                messages=messages,
                **extra_params
            )

            if chat.choices and chat.choices[0].message.content:
                content = chat.choices[0].message.content
                return content

        except Exception as e:
            self.logger.error(f"Error querying {base_url}: {e}")
            return "Error: Unable to connect to the LLM."