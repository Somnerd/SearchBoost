# -*- coding: utf-8 -*-
# SearchBoost Unit Tests: Automated Knowledge File Watcher Daemon
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from searchboost_src.watcher import KnowledgeFileWatcher, compute_file_hash


def test_compute_file_hash():
    """Verify compute_file_hash returns consistent sha256 hex digest."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
        tf.write("SearchBoost Knowledge Hash Test")
        tf_path = Path(tf.name)

    try:
        h1 = compute_file_hash(tf_path)
        h2 = compute_file_hash(tf_path)
        assert h1 == h2
        assert len(h1) == 64
    finally:
        tf_path.unlink(missing_ok=True)


def test_watcher_scan_directory():
    """Verify scan_directory identifies supported files and ignores unsupported ones."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "note1.md").write_text("# Note 1", encoding="utf-8")
        (tmp_path / "data.json").write_text("{}", encoding="utf-8")
        (tmp_path / "script.py").write_text("x = 1", encoding="utf-8")
        (tmp_path / "binary.exe").write_bytes(b"\x00\x01\x02")

        watcher = KnowledgeFileWatcher(
            watch_dir=str(tmp_path),
            session_factory=lambda: AsyncMock()
        )

        scanned = watcher.scan_directory()
        scanned_names = [p.name for p, _, _ in scanned.values()]
        assert "note1.md" in scanned_names
        assert "data.json" in scanned_names
        assert "script.py" in scanned_names
        assert "binary.exe" not in scanned_names


@pytest.mark.asyncio
async def test_watcher_sync_once_add_modify_delete():
    """Verify sync_once reconciles additions, content modifications, and deletions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        doc1 = tmp_path / "file1.md"
        doc1.write_text("Version 1 content", encoding="utf-8")

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_session

        mock_ollama = MagicMock()
        mock_ollama.get_embedding = AsyncMock(return_value=[0.1] * 768)

        watcher = KnowledgeFileWatcher(
            watch_dir=str(tmp_path),
            session_factory=mock_session_factory,
            ollama_client=mock_ollama,
            poll_interval=0.1
        )

        # 1. First sync: detects file1.md as added
        sync1 = await watcher.sync_once()
        assert len(sync1["added"]) == 1
        assert len(sync1["modified"]) == 0
        assert len(sync1["deleted"]) == 0

        # 2. Modify file1.md: detects as modified
        await asyncio.sleep(0.05)
        doc1.write_text("Version 2 updated content with new facts", encoding="utf-8")

        sync2 = await watcher.sync_once()
        assert len(sync2["added"]) == 0
        assert len(sync2["modified"]) == 1
        assert len(sync2["deleted"]) == 0

        # 3. Add file2.txt: detects as added
        doc2 = tmp_path / "file2.txt"
        doc2.write_text("Second file content", encoding="utf-8")

        sync3 = await watcher.sync_once()
        assert len(sync3["added"]) == 1
        assert len(sync3["modified"]) == 0
        assert len(sync3["deleted"]) == 0

        # 4. Delete file1.md: detects as deleted
        doc1.unlink()

        sync4 = await watcher.sync_once()
        assert len(sync4["added"]) == 0
        assert len(sync4["modified"]) == 0
        assert len(sync4["deleted"]) == 1


@pytest.mark.asyncio
async def test_watcher_lifecycle_run_and_stop():
    """Verify watcher run loop starts and stops gracefully upon stop() call."""
    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = KnowledgeFileWatcher(
            watch_dir=tmpdir,
            session_factory=lambda: AsyncMock(),
            poll_interval=0.05
        )

        task = asyncio.create_task(watcher.run())
        await asyncio.sleep(0.1)
        assert watcher._running is True

        watcher.stop()
        await task
        assert watcher._running is False
