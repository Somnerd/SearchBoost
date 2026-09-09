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
import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, Set, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from searchboost_src.database import DocumentService
from searchboost_src.ingester import DocumentIngester, SUPPORTED_EXTENSIONS
from searchboost_src.ollama_client import OllamaClient
from searchboost_src.logger import setup_logger


def compute_file_hash(path: Path) -> str:
    """Compute sha256 hex digest of a file to detect content modifications."""
    try:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


class KnowledgeFileWatcher:
    """
    Asynchronous file watcher and incremental ingestion daemon for SearchBoost local knowledge.
    Monitors a directory for additions, modifications, and deletions of supported knowledge files.
    """

    def __init__(
        self,
        watch_dir: str,
        session_factory: Callable[[], AsyncSession],
        ollama_client: Optional[OllamaClient] = None,
        logger: Optional[logging.Logger] = None,
        poll_interval: float = 2.0,
        chunk_size: int = 800,
        overlap: int = 100
    ):
        self.watch_dir = Path(watch_dir).resolve()
        self.session_factory = session_factory
        self.ollama_client = ollama_client
        self.logger = logger or setup_logger("INFO")
        self.poll_interval = poll_interval
        self.chunk_size = chunk_size
        self.overlap = overlap

        # State tracking: rel_path -> (mtime, size, sha256)
        self.known_files: Dict[str, Tuple[float, int, str]] = {}
        self._running = False
        self._stop_event = asyncio.Event()

    def scan_directory(self) -> Dict[str, Tuple[Path, float, int]]:
        """Scan target directory and return map of rel_path -> (absolute_path, mtime, size)."""
        if not self.watch_dir.is_dir():
            return {}

        results = {}
        for path in self.watch_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    stat = path.stat()
                    try:
                        rel = str(path.relative_to(Path.cwd()))
                    except ValueError:
                        rel = str(path)
                    results[rel] = (path, stat.st_mtime, stat.st_size)
                except (OSError, PermissionError):
                    continue
        return results

    async def sync_once(self) -> Dict[str, list]:
        """
        Execute a single reconciliation pass comparing disk state against known state.
        Returns a summary of modified, added, and deleted files.
        """
        current_disk = self.scan_directory()
        added = []
        modified = []
        deleted = []

        # Detect additions and modifications
        for rel_path, (abs_path, mtime, size) in current_disk.items():
            if rel_path not in self.known_files:
                file_hash = compute_file_hash(abs_path)
                self.known_files[rel_path] = (mtime, size, file_hash)
                added.append((rel_path, abs_path))
            else:
                old_mtime, old_size, old_hash = self.known_files[rel_path]
                if mtime != old_mtime or size != old_size:
                    new_hash = compute_file_hash(abs_path)
                    if new_hash != old_hash:
                        self.known_files[rel_path] = (mtime, size, new_hash)
                        modified.append((rel_path, abs_path))
                    else:
                        # Mtime changed but content identical (e.g. touch)
                        self.known_files[rel_path] = (mtime, size, old_hash)

        # Detect deletions
        current_rel_set = set(current_disk.keys())
        for rel_path in list(self.known_files.keys()):
            if rel_path not in current_rel_set:
                deleted.append(rel_path)
                del self.known_files[rel_path]

        # Apply changes to database
        if added or modified or deleted:
            async with self.session_factory() as session:
                ingester = DocumentIngester(
                    session=session,
                    ollama_client=self.ollama_client,
                    logger=self.logger
                )
                doc_svc = DocumentService(
                    session=session,
                    logger=self.logger,
                    ollama_client=self.ollama_client
                )

                # Process additions and updates
                for rel_path, abs_path in added + modified:
                    self.logger.info(f"Watcher: Ingesting file update '{rel_path}'")
                    await ingester.ingest_file(
                        str(abs_path),
                        chunk_size=self.chunk_size,
                        overlap=self.overlap
                    )

                # Process deletions
                for rel_path in deleted:
                    self.logger.info(f"Watcher: Removing deleted document source '{rel_path}'")
                    deleted_count = await doc_svc.delete_by_source(rel_path)
                    self.logger.info(f"Watcher: Pruned {deleted_count} chunks for '{rel_path}'")

        return {
            "added": [r for r, _ in added],
            "modified": [r for r, _ in modified],
            "deleted": deleted
        }

    async def run(self):
        """Continuously monitor directory until stop() is called."""
        self._running = True
        self._stop_event.clear()
        self.logger.info(f"KnowledgeFileWatcher started on '{self.watch_dir}' (Interval: {self.poll_interval}s)")

        # Initial baseline scan
        initial_disk = self.scan_directory()
        for rel_path, (abs_path, mtime, size) in initial_disk.items():
            self.known_files[rel_path] = (mtime, size, compute_file_hash(abs_path))
        self.logger.info(f"KnowledgeFileWatcher: Baseline loaded with {len(self.known_files)} files")

        while self._running:
            try:
                await self.sync_once()
            except Exception as e:
                self.logger.error(f"KnowledgeFileWatcher error during sync: {e}")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.poll_interval)
                break  # Stop requested
            except asyncio.TimeoutError:
                continue

        self.logger.info("KnowledgeFileWatcher stopped.")

    def stop(self):
        """Signal the watcher loop to terminate gracefully."""
        self._running = False
        self._stop_event.set()


async def main():
    import argparse
    from searchboost_src.configurator import get_configurator
    from searchboost_src.database import DatabaseManager

    parser = argparse.ArgumentParser(description="SearchBoost Local Knowledge Base Watcher Daemon")
    parser.add_argument("--dir", default="./docs", help="Directory to monitor (default: ./docs)")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    parser.add_argument("--chunk-size", type=int, default=800, help="Document chunk size")
    parser.add_argument("--overlap", type=int, default=100, help="Chunk overlap")

    args = parser.parse_args()
    log = setup_logger("INFO")

    config_manager = get_configurator(log)
    settings = await config_manager.initialize(None)

    db_manager = DatabaseManager(settings["db"])
    await db_manager.init_db()

    from searchboost_src.chat_class import ChatDetails
    chatdetails = ChatDetails(config=settings["ai"], prompt="")
    ollama_client = OllamaClient(logger=log, ChatDetails=chatdetails)

    watcher = KnowledgeFileWatcher(
        watch_dir=args.dir,
        session_factory=db_manager.get_session,
        ollama_client=ollama_client,
        logger=log,
        poll_interval=args.interval,
        chunk_size=args.chunk_size,
        overlap=args.overlap
    )

    try:
        await watcher.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        watcher.stop()


if __name__ == "__main__":
    asyncio.run(main())
