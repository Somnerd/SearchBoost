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


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from searchboost_src.configurator import PostgreSQLSettings
from searchboost_src.models import ConversationTurn

Base = declarative_base()

class DatabaseManager:
    def __init__(self, settings: PostgreSQLSettings):
        self.settings = settings
        self.engine = create_async_engine(
            self.settings.database_url,
            pool_size=10,
            max_overflow=20
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def init_db(self):
        """Creates tables if they don't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def get_session(self) -> AsyncSession:
        return self.session_factory()


class HistoryService:
    """Loads and saves multi-turn conversation history from PostgreSQL."""

    def __init__(self, session: AsyncSession, logger=None, ollama_client=None):
        self.session = session
        self.logger = logger
        self.ollama_client = ollama_client

    async def load_history(self, session_id: str, limit: int = 10, max_age_minutes: int = 15) -> list[dict]:
        """
        Fetch the last `limit` turns for a session_id within `max_age_minutes`, 
        returned oldest-first so Ollama reads the conversation in chronological order.
        """
        from searchboost_src.models import ConversationTurn
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
            # Remove tzinfo before comparison since SQLAlchemy schema stores naive datetime via func.now()
            cutoff = cutoff.replace(tzinfo=None)

            result = await self.session.execute(
                select(ConversationTurn)
                .where(ConversationTurn.session_id == session_id)
                .where(ConversationTurn.created_at >= cutoff)
                .order_by(ConversationTurn.created_at.desc())
                .limit(limit)
            )
            turns = result.scalars().all()
            # Reverse so the oldest turn comes first (chronological order for Ollama)
            history = [{"role": t.role, "content": t.content} for t in reversed(turns)]
            if self.logger:
                self.logger.info(f"HistoryService: Loaded {len(history)} prior turns for session '{session_id}'")
            return history
        except Exception as e:
            if self.logger:
                self.logger.error(f"HistoryService: Failed to load history for '{session_id}': {e}")
            return []

    async def save_turn(self, session_id: str, role: str, content: str):
        """Persist a single conversation turn (user or assistant) with optional vector embedding."""
        from searchboost_src.models import ConversationTurn
        try:
            embedding = None
            if self.ollama_client:
                embedding = await self.ollama_client.get_embedding(content)
                if self.logger and embedding:
                    self.logger.debug(f"HistoryService: Generated embedding ({len(embedding)} dims) for '{role}' turn")

            turn = ConversationTurn(
                session_id=session_id, 
                role=role, 
                content=content,
                embedding=embedding
            )
            self.session.add(turn)
            await self.session.commit()
            if self.logger:
                self.logger.debug(f"HistoryService: Saved '{role}' turn for session '{session_id}' (Embedding: {embedding is not None})")
        except Exception as e:
            if self.logger:
                self.logger.error(f"HistoryService: Failed to save turn for '{session_id}': {e}")

    async def search_relevant_history(self, session_prefix: str, query: str, exclude_session_id: str = None, limit: int = 5) -> list[dict]:
        """Perform semantic vector search using pgvector to find relevant prior turns, excluding current session."""
        from searchboost_src.models import ConversationTurn
        try:
            if not self.ollama_client:
                return []

            query_embedding = await self.ollama_client.get_embedding(query)
            if not query_embedding:
                return []

            # Perform vector similarity search (<=> is cosine distance in pgvector)
            stmt = select(ConversationTurn).where(ConversationTurn.session_id.like(f"{session_prefix}%"))
            
            if exclude_session_id:
                stmt = stmt.where(ConversationTurn.session_id != exclude_session_id)
            
            stmt = stmt.where(ConversationTurn.embedding.isnot(None))
            stmt = stmt.order_by(ConversationTurn.embedding.cosine_distance(query_embedding)).limit(limit)

            result = await self.session.execute(stmt)
            turns = result.scalars().all()
            
            relevant_context = [
                {"role": t.role, "content": t.content, "session_id": t.session_id} 
                for t in turns
            ]
            
            if self.logger:
                self.logger.info(f"HistoryService: Found {len(relevant_context)} semantically relevant turns (Excluded: {exclude_session_id})")
            return relevant_context
        except Exception as e:
            if self.logger:
                self.logger.error(f"HistoryService: Semantic search failed: {e}")
            return []