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

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from searchboost_src.database import DocumentService
from searchboost_src.ollama_client import OllamaClient
from searchboost_src.logger import setup_logger

SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".json", ".csv", ".py", ".html"}


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Split text into chunks by paragraphs or sentence boundaries with overlap.
    """
    if not text or not text.strip():
        return []

    # First attempt splitting by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: List[str] = []
    current_chunk = ""

    for para in paragraphs:
        if len(para) > chunk_size:
            # Paragraph itself is too large, split by single newlines or words
            lines = para.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if len(current_chunk) + len(line) + 1 <= chunk_size:
                    current_chunk = f"{current_chunk}\n{line}".strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    # If single line is larger than chunk_size, slice it
                    while len(line) > chunk_size:
                        chunks.append(line[:chunk_size])
                        line = line[chunk_size - overlap:]
                    current_chunk = line
        else:
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class DocumentIngester:
    """Scans, chunks, embeds, and indexes local files into PostgreSQL with pgvector."""

    def __init__(
        self,
        session: AsyncSession,
        ollama_client: Optional[OllamaClient] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.session = session
        self.doc_service = DocumentService(session, logger=logger, ollama_client=ollama_client)
        self.ollama_client = ollama_client
        self.logger = logger or setup_logger("INFO")

    async def ingest_file(self, file_path: str, chunk_size: int = 800, overlap: int = 100) -> int:
        """Read a single file, chunk it, embed chunks, and persist into the database."""
        path = Path(file_path).resolve()
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            self.logger.warning(f"Ingester: Skipping unsupported or missing file: {file_path}")
            return 0

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Ingester: Error reading {file_path}: {e}")
            return 0

        chunks = chunk_text(content, chunk_size=chunk_size, overlap=overlap)
        if not chunks:
            self.logger.info(f"Ingester: No text chunks extracted from {file_path}")
            return 0

        rel_path = str(path.relative_to(Path.cwd())) if str(path).startswith(str(Path.cwd())) else str(path)
        
        # Remove any previously indexed chunks for this source to avoid duplicates
        await self.doc_service.delete_by_source(rel_path)

        indexed_count = 0
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks):
            metadata = json.dumps({
                "source_file": rel_path,
                "file_name": path.name,
                "extension": path.suffix.lower(),
                "file_size": path.stat().st_size,
                "chunk_index": idx,
                "total_chunks": total_chunks
            })

            embedding = None
            if self.ollama_client:
                embedding = await self.ollama_client.get_embedding(chunk)

            await self.doc_service.insert_chunk(
                source_file=rel_path,
                content=chunk,
                embedding=embedding,
                chunk_index=idx,
                total_chunks=total_chunks,
                metadata_json=metadata
            )
            indexed_count += 1

        self.logger.info(f"Ingester: Successfully indexed {indexed_count} chunks for '{rel_path}'")
        return indexed_count

    async def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        chunk_size: int = 800,
        overlap: int = 100
    ) -> Dict[str, Any]:
        """Scan a directory for supported files and ingest them."""
        dir_path = Path(directory_path).resolve()
        if not dir_path.is_dir():
            self.logger.error(f"Ingester: Target directory not found: {directory_path}")
            return {"indexed_files": 0, "indexed_chunks": 0, "files": []}

        pattern = "**/*" if recursive else "*"
        all_files = [f for f in dir_path.glob(pattern) if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]

        self.logger.info(f"Ingester: Found {len(all_files)} eligible files in {directory_path}")

        total_chunks = 0
        indexed_files = []

        for f in all_files:
            count = await self.ingest_file(str(f), chunk_size=chunk_size, overlap=overlap)
            if count > 0:
                total_chunks += count
                indexed_files.append(str(f.name))

        return {
            "indexed_files": len(indexed_files),
            "indexed_chunks": total_chunks,
            "files": indexed_files
        }


async def main():
    import argparse
    from searchboost_src.configurator import get_configurator
    from searchboost_src.database import DatabaseManager

    parser = argparse.ArgumentParser(description="SearchBoost Local Document Ingestion Engine")
    parser.add_argument("--dir", default="./docs", help="Directory containing documents to index (default: ./docs)")
    parser.add_argument("--file", default=None, help="Specific file to index")
    parser.add_argument("--chunk-size", type=int, default=800, help="Target chunk size in characters")
    parser.add_argument("--overlap", type=int, default=100, help="Chunk overlap in characters")

    args = parser.parse_args()
    log = setup_logger("INFO")

    config_manager = get_configurator(log)
    settings = await config_manager.initialize(None)

    db_manager = DatabaseManager(settings["db"])
    await db_manager.init_db()

    from searchboost_src.chat_class import ChatDetails
    chatdetails = ChatDetails(config=settings["ai"], prompt="")
    ollama_client = OllamaClient(logger=log, ChatDetails=chatdetails)

    async with db_manager.get_session() as session:
        ingester = DocumentIngester(session, ollama_client=ollama_client, logger=log)
        if args.file:
            log.info(f"Ingesting single file: {args.file}")
            await ingester.ingest_file(args.file, chunk_size=args.chunk_size, overlap=args.overlap)
        else:
            log.info(f"Ingesting directory: {args.dir}")
            res = await ingester.ingest_directory(args.dir, chunk_size=args.chunk_size, overlap=args.overlap)
            log.info(f"Ingestion result: {res}")


if __name__ == "__main__":
    asyncio.run(main())
