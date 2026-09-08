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
        """Creates tables, pgvector HNSW indexes, and full-text search indexes."""
        async with self.engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(Base.metadata.create_all)

            # HNSW Indexes for sub-millisecond approximate nearest neighbor search (Issue #51)
            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_internal_docs_hnsw 
                    ON internal_documents USING hnsw (embedding vector_cosine_ops);
                """))
            except Exception:
                pass

            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_turns_hnsw 
                    ON conversation_turns USING hnsw (embedding vector_cosine_ops);
                """))
            except Exception:
                pass

            # GIN Index for hybrid full-text BM25 search (Issue #52)
            try:
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_internal_docs_fts 
                    ON internal_documents USING gin (to_tsvector('english', content));
                """))
            except Exception:
                pass

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
        if not content:
            return

        # Prevent saving raw error outputs or leaked prompt templates into conversation history
        if role == "assistant" and (
            str(content).startswith("Error:")
            or str(content).startswith("Using the following")
            or str(content).startswith("REFERENCE ONLY")
        ):
            if self.logger:
                self.logger.warning(f"HistoryService: Skipped saving invalid/corrupt '{role}' turn for session '{session_id}'")
            return

        embedding = None
        if self.ollama_client:
            try:
                embedding = await self.ollama_client.get_embedding(content)
                if self.logger and embedding:
                    self.logger.debug(f"HistoryService: Generated embedding ({len(embedding)} dims) for '{role}' turn")
            except Exception:
                if self.logger:
                    self.logger.exception("HistoryService: Embedding generation failed (turn will lack semantic context)")

        try:
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
        except Exception:
            await self.session.rollback()
            if self.logger:
                self.logger.exception(f"HistoryService: Failed to save turn for '{session_id}'")
            raise

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
            escaped_prefix = session_prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            stmt = select(ConversationTurn).where(ConversationTurn.session_id.like(f"{escaped_prefix}%", escape='\\'))
            
            if exclude_session_id:
                stmt = stmt.where(ConversationTurn.session_id != exclude_session_id)
            
            stmt = stmt.where(ConversationTurn.embedding.isnot(None))
            # Require minimum cosine similarity (distance < 0.4, where 0 is exact match)
            stmt = stmt.where(ConversationTurn.embedding.cosine_distance(query_embedding) < 0.4)
            stmt = stmt.order_by(ConversationTurn.embedding.cosine_distance(query_embedding)).limit(limit)

            result = await self.session.execute(stmt)
            turns = result.scalars().all()
            
            relevant_context = [
                {"role": t.role, "content": t.content, "session_id": t.session_id} 
                for t in turns
                if not str(t.content).startswith("Using the following")
                and not str(t.content).startswith("REFERENCE ONLY")
                and not str(t.content).startswith("Error:")
            ]
            
            if self.logger:
                self.logger.info(f"HistoryService: Found {len(relevant_context)} semantically relevant turns (Excluded: {exclude_session_id})")
            return relevant_context
        except Exception as e:
            if self.logger:
                self.logger.error(f"HistoryService: Semantic search failed: {e}")
            return []


class DocumentService:
    """Manages indexing, ingestion, and vector similarity search over internal documents in PostgreSQL."""

    def __init__(self, session: AsyncSession, logger=None, ollama_client=None):
        self.session = session
        self.logger = logger
        self.ollama_client = ollama_client

    async def insert_chunk(
        self,
        source_file: str,
        content: str,
        embedding: list[float] = None,
        chunk_index: int = 0,
        total_chunks: int = 1,
        metadata_json: str = None
    ):
        """Insert a document chunk with vector embedding."""
        from searchboost_src.models import InternalDocument
        if not content:
            return None

        if embedding is None and self.ollama_client:
            try:
                embedding = await self.ollama_client.get_embedding(content)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"DocumentService: Failed to generate embedding for chunk: {e}")

        try:
            doc = InternalDocument(
                source_file=source_file,
                content=content,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                metadata_json=metadata_json,
                embedding=embedding
            )
            self.session.add(doc)
            await self.session.commit()
            return doc
        except Exception:
            await self.session.rollback()
            raise

    async def search_documents(
        self,
        query: str,
        limit: int = 5,
        distance_threshold: float = 0.45,
        hybrid: bool = True,
        rrf_k: int = 60
    ) -> list[dict]:
        """
        Hybrid vector and full-text search using Reciprocal Rank Fusion (RRF).
        - Dense Vector: Cosine distance (<=>) with HNSW index.
        - Sparse Full-Text: PostgreSQL tsvector and plainto_tsquery.
        - Fusion: RRF score = sum(1 / (k + rank_i)) across active modalities.
        """
        from searchboost_src.models import InternalDocument
        from sqlalchemy import func
        try:
            if not query or not query.strip():
                return []

            if not self.ollama_client:
                return []

            query_embedding = await self.ollama_client.get_embedding(query)
            if not query_embedding:
                return []

            # 1. Dense Vector Similarity Search
            stmt = select(InternalDocument).where(InternalDocument.embedding.isnot(None))
            stmt = stmt.where(InternalDocument.embedding.cosine_distance(query_embedding) < distance_threshold)
            stmt = stmt.order_by(InternalDocument.embedding.cosine_distance(query_embedding)).limit(limit * 2)

            result = await self.session.execute(stmt)
            vector_docs = result.scalars().all()

            if not hybrid:
                results = [
                    {
                        "id": d.id,
                        "source_file": d.source_file,
                        "content": d.content,
                        "chunk_index": d.chunk_index,
                        "total_chunks": d.total_chunks,
                        "metadata": d.metadata_json,
                        "score": 1.0,
                        "match_type": "vector"
                    }
                    for d in vector_docs[:limit]
                ]
                return results

            # 2. Sparse Full-Text Search (PostgreSQL tsvector / plainto_tsquery)
            fts_docs = []
            try:
                clean_query = query.strip()
                fts_stmt = (
                    select(InternalDocument)
                    .where(
                        func.to_tsvector("english", InternalDocument.content).op("@@")(
                            func.plainto_tsquery("english", clean_query)
                        )
                    )
                    .order_by(
                        func.ts_rank_cd(
                            func.to_tsvector("english", InternalDocument.content),
                            func.plainto_tsquery("english", clean_query)
                        ).desc()
                    )
                    .limit(limit * 2)
                )
                fts_result = await self.session.execute(fts_stmt)
                fts_docs = fts_result.scalars().all()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"DocumentService: FTS search bypassed: {e}")
                fts_docs = []

            # 3. Reciprocal Rank Fusion (RRF)
            # RRF(d) = sum(1 / (k + rank_i))
            rrf_scores = {}
            doc_map = {}
            match_sources = {}

            for rank, d in enumerate(vector_docs, start=1):
                doc_map[d.id] = d
                rrf_scores[d.id] = rrf_scores.get(d.id, 0.0) + (1.0 / (rrf_k + rank))
                match_sources.setdefault(d.id, set()).add("vector")

            for rank, d in enumerate(fts_docs, start=1):
                doc_map[d.id] = d
                rrf_scores[d.id] = rrf_scores.get(d.id, 0.0) + (1.0 / (rrf_k + rank))
                match_sources.setdefault(d.id, set()).add("fts")

            sorted_ids = sorted(rrf_scores.keys(), key=lambda did: rrf_scores[did], reverse=True)[:limit]

            results = [
                {
                    "id": doc_map[did].id,
                    "source_file": doc_map[did].source_file,
                    "content": doc_map[did].content,
                    "chunk_index": doc_map[did].chunk_index,
                    "total_chunks": doc_map[did].total_chunks,
                    "metadata": doc_map[did].metadata_json,
                    "score": round(rrf_scores[did], 6),
                    "match_type": "hybrid" if len(match_sources[did]) > 1 else list(match_sources[did])[0]
                }
                for did in sorted_ids
            ]

            if self.logger:
                self.logger.info(
                    f"DocumentService: Found {len(results)} chunks for '{query}' (Hybrid RRF: {len(vector_docs)} vector, {len(fts_docs)} fts)"
                )
            return results
        except Exception as e:
            if self.logger:
                self.logger.error(f"DocumentService: Search failed: {e}")
            return []

    async def delete_by_source(self, source_file: str) -> int:
        """Deletes all chunks for a source file before re-indexing."""
        from searchboost_src.models import InternalDocument
        from sqlalchemy import delete
        try:
            stmt = delete(InternalDocument).where(InternalDocument.source_file == source_file)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount
        except Exception:
            await self.session.rollback()
            raise

    async def get_document_count(self) -> int:
        """Return total count of indexed document chunks."""
        from searchboost_src.models import InternalDocument
        from sqlalchemy import func
        try:
            stmt = select(func.count(InternalDocument.id))
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            if self.logger:
                self.logger.error(f"DocumentService: Failed to count documents: {e}")
            return 0

    async def list_sources(self) -> list[str]:
        """Return distinct source files that have been indexed."""
        from searchboost_src.models import InternalDocument
        try:
            stmt = select(InternalDocument.source_file).distinct()
            result = await self.session.execute(stmt)
            return [row[0] for row in result.all()]
        except Exception as e:
            if self.logger:
                self.logger.error(f"DocumentService: Failed to list sources: {e}")
            return []

    async def list_sources_detailed(self) -> list[dict]:
        """Return distinct source files with chunk counts and latest indexing timestamp."""
        from searchboost_src.models import InternalDocument
        from sqlalchemy import func
        try:
            stmt = (
                select(
                    InternalDocument.source_file,
                    func.count(InternalDocument.id).label("chunk_count"),
                    func.max(InternalDocument.created_at).label("last_indexed")
                )
                .group_by(InternalDocument.source_file)
                .order_by(func.max(InternalDocument.created_at).desc())
            )
            result = await self.session.execute(stmt)
            return [
                {
                    "source_file": row[0],
                    "chunk_count": int(row[1]),
                    "last_indexed": row[2].isoformat() if row[2] else None
                }
                for row in result.all()
            ]
        except Exception as e:
            if self.logger:
                self.logger.error(f"DocumentService: Failed to list sources detailed: {e}")
            return []