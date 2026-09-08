# -*- coding: utf-8 -*-
# SearchBoost Unit Tests: Document Service & Ingestion Engine
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

from searchboost_src.database import DocumentService
from searchboost_src.ingester import chunk_text, DocumentIngester, SUPPORTED_EXTENSIONS
from searchboost_src.models import InternalDocument


# =====================================================================
# Text Chunking Tests
# =====================================================================

def test_chunk_text_empty_or_whitespace():
    """Verify empty text or whitespace returns an empty list."""
    assert chunk_text("") == []
    assert chunk_text("   \n\n   ") == []


def test_chunk_text_short():
    """Verify text shorter than chunk_size produces a single chunk."""
    text = "This is a concise piece of documentation."
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long_paragraphs():
    """Verify text with multiple paragraphs splits appropriately with boundaries."""
    p1 = "Paragraph 1: " + ("word " * 60)
    p2 = "Paragraph 2: " + ("sentence " * 60)
    p3 = "Paragraph 3: " + ("data " * 60)
    full_text = f"{p1}\n\n{p2}\n\n{p3}"

    chunks = chunk_text(full_text, chunk_size=200, overlap=30)
    assert len(chunks) >= 3
    assert any("Paragraph 1" in c for c in chunks)
    assert any("Paragraph 2" in c for c in chunks)
    assert any("Paragraph 3" in c for c in chunks)


# =====================================================================
# DocumentService Unit Tests
# =====================================================================

@pytest.mark.asyncio
async def test_document_service_insert_chunk_with_precomputed_embedding():
    """Verify insert_chunk persists InternalDocument with provided embedding."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    service = DocumentService(session=mock_session)

    embedding = [0.05] * 768
    doc = await service.insert_chunk(
        source_file="docs/architecture.md",
        content="Antigravity architecture overview",
        embedding=embedding,
        chunk_index=0,
        total_chunks=1,
        metadata_json=json.dumps({"size": 100})
    )

    assert doc is not None
    assert doc.source_file == "docs/architecture.md"
    assert doc.content == "Antigravity architecture overview"
    assert doc.embedding == embedding
    assert mock_session.add.called
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_document_service_insert_chunk_generates_embedding():
    """Verify insert_chunk requests embedding from ollama_client when not provided."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_ollama = MagicMock()
    mock_ollama.get_embedding = AsyncMock(return_value=[0.1] * 768)

    service = DocumentService(session=mock_session, ollama_client=mock_ollama)

    doc = await service.insert_chunk(
        source_file="docs/setup.md",
        content="Local setup instructions",
        embedding=None,
        chunk_index=0,
        total_chunks=1
    )

    assert doc is not None
    mock_ollama.get_embedding.assert_awaited_once_with("Local setup instructions")
    assert doc.embedding == [0.1] * 768
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_document_service_search_documents():
    """Verify search_documents queries pgvector cosine distance and formats results."""
    mock_session = AsyncMock()
    mock_ollama = MagicMock()
    mock_ollama.get_embedding = AsyncMock(return_value=[0.2] * 768)

    # Mock database return
    mock_doc1 = MagicMock(spec=InternalDocument)
    mock_doc1.id = 1
    mock_doc1.source_file = "docs/guide.md"
    mock_doc1.content = "Guide chunk 1"
    mock_doc1.chunk_index = 0
    mock_doc1.total_chunks = 2
    mock_doc1.metadata_json = '{"author": "Nikolaos"}'

    mock_doc2 = MagicMock(spec=InternalDocument)
    mock_doc2.id = 2
    mock_doc2.source_file = "docs/guide.md"
    mock_doc2.content = "Guide chunk 2"
    mock_doc2.chunk_index = 1
    mock_doc2.total_chunks = 2
    mock_doc2.metadata_json = '{"author": "Nikolaos"}'

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_doc1, mock_doc2]
    mock_session.execute = AsyncMock(return_value=mock_result)

    service = DocumentService(session=mock_session, ollama_client=mock_ollama)
    results = await service.search_documents("guide overview", limit=5)

    assert len(results) == 2
    assert results[0]["id"] == 1
    assert results[0]["source_file"] == "docs/guide.md"
    assert results[0]["content"] == "Guide chunk 1"
    assert results[1]["chunk_index"] == 1
    mock_ollama.get_embedding.assert_awaited_once_with("guide overview")


@pytest.mark.asyncio
async def test_document_service_search_documents_no_embedding():
    """Verify search_documents returns empty list if Ollama fails to embed."""
    mock_session = AsyncMock()
    mock_ollama = MagicMock()
    mock_ollama.get_embedding = AsyncMock(return_value=None)

    service = DocumentService(session=mock_session, ollama_client=mock_ollama)
    results = await service.search_documents("missing embedding")

    assert results == []
    assert not mock_session.execute.called


@pytest.mark.asyncio
async def test_document_service_delete_by_source():
    """Verify delete_by_source executes delete statement and returns deleted count."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 4
    mock_session.execute = AsyncMock(return_value=mock_result)

    service = DocumentService(session=mock_session)
    deleted = await service.delete_by_source("docs/old_guide.md")

    assert deleted == 4
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_document_service_get_document_count():
    """Verify get_document_count returns total count."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 42
    mock_session.execute = AsyncMock(return_value=mock_result)

    service = DocumentService(session=mock_session)
    count = await service.get_document_count()

    assert count == 42


@pytest.mark.asyncio
async def test_document_service_list_sources():
    """Verify list_sources returns list of distinct source files."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [("docs/a.md",), ("docs/b.txt",), ("docs/c.json",)]
    mock_session.execute = AsyncMock(return_value=mock_result)

    service = DocumentService(session=mock_session)
    sources = await service.list_sources()

    assert sources == ["docs/a.md", "docs/b.txt", "docs/c.json"]


# =====================================================================
# DocumentIngester Unit Tests
# =====================================================================

@pytest.mark.asyncio
async def test_document_ingester_file_and_directory():
    """Verify DocumentIngester ingests supported files and skips unsupported files."""
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_session.execute = AsyncMock(return_value=mock_result)

    mock_ollama = MagicMock()
    mock_ollama.get_embedding = AsyncMock(return_value=[0.05] * 768)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create supported files
        doc1 = tmp_path / "intro.md"
        doc1.write_text("# Welcome to SearchBoost\n\nHigh-performance AI search engine.", encoding="utf-8")

        doc2 = tmp_path / "config.json"
        doc2.write_text('{"app": "searchboost", "version": "2.0"}', encoding="utf-8")

        # Create unsupported file
        doc_unsupported = tmp_path / "binary.bin"
        doc_unsupported.write_bytes(b"\x00\x01\x02\x03")

        ingester = DocumentIngester(session=mock_session, ollama_client=mock_ollama)

        # Ingest directory
        summary = await ingester.ingest_directory(str(tmp_path), chunk_size=300)

        assert summary["indexed_files"] == 2
        assert "intro.md" in summary["files"]
        assert "config.json" in summary["files"]
        assert "binary.bin" not in summary["files"]
        assert summary["indexed_chunks"] >= 2


def test_chunk_text_unicode_and_emojis():
    """Verify chunk_text cleanly handles multilingual unicode and emojis."""
    greek_text = "Η αναζήτηση και η ευρετηρίαση διανυσμάτων στο SearchBoost είναι ταχύτατη. 🚀⚡"
    chunks = chunk_text(greek_text, chunk_size=100)
    assert len(chunks) == 1
    assert "SearchBoost" in chunks[0]
    assert "🚀⚡" in chunks[0]


def test_chunk_text_unbroken_long_string():
    """Verify chunk_text slices long strings that exceed chunk_size without newlines."""
    long_unbroken = "A" * 500
    chunks = chunk_text(long_unbroken, chunk_size=100, overlap=20)
    assert len(chunks) >= 5
    assert all(len(c) <= 100 for c in chunks)


@pytest.mark.asyncio
async def test_document_ingester_empty_file():
    """Verify ingesting a zero-byte empty file returns 0 indexed chunks gracefully."""
    mock_session = AsyncMock()
    ingester = DocumentIngester(session=mock_session)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
        tf.write("")
        tf_path = tf.name

    try:
        count = await ingester.ingest_file(tf_path)
        assert count == 0
    finally:
        Path(tf_path).unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_document_ingester_nonexistent_file():
    """Verify ingesting a non-existent file returns 0 without raising an exception."""
    mock_session = AsyncMock()
    ingester = DocumentIngester(session=mock_session)
    count = await ingester.ingest_file("/path/to/nonexistent/document.md")
    assert count == 0

