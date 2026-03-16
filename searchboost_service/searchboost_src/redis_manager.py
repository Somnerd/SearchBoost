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


import redis.asyncio as redis
import json

class RedisManager:
    def __init__(self, config, logger):
        self.config = config # The RedisSettings object from your Configurator
        self._logger = logger
        self._redis = None

    async def connect(self):
        """Establish connection with the Redis container."""
        try:
            self._redis = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                decode_responses=True # Returns strings instead of bytes
            )
            # Test connection
            await self._redis.ping()
            self._logger.info("RedisManager: Successfully connected to Redis.")
        except Exception as e:
            self._logger.error(f"RedisManager: Failed to connect: {e}")
            self._redis = None

    async def get_cached_response(self, query: str):
        """Check if we have a result for this query."""
        if not self._redis: return None
        return await self._redis.get(f"query:{query}")

    async def cache_response(self, query: str, response: str, ttl: int = 3600):
        """Store result in Redis with an expiration (1 hour default)."""
        if not self._redis: return
        await self._redis.set(f"query:{query}", response, ex=ttl)