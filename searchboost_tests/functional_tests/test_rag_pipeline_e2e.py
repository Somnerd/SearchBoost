# -*- coding: utf-8 -*-
# SearchBoost End-to-End Pipeline & Mode Matrix Test Suite
# Verifies the 4 operational modes:
#   1. deep:web   (Deep Research + Live Meta-Search + Vector Docs)
#   2. deep:local (Deep Research + Complete Web Bypass + Vector Docs)
#   3. fast:web   (Fast Answer + Live Meta-Search + Vector Docs)
#   4. fast:local (Fast Answer + Complete Web Bypass + Vector Docs)
# Plus fault tolerance and cache segregation.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from searchboost_src.service import SearchBoostService
from searchboost_src.logger import setup_logger


def create_mock_service(query: str, research_mode: bool, web_search: bool):
    """Helper to instantiate SearchBoostService with standardized mocks."""
    mock_cfg = MagicMock()
    mock_cfg.model = "llama3.2"
    mock_cfg.base_url = "http://localhost:11434"
    mock_cfg.role = "user"
    mock_cfg.format = "json"
    mock_cfg.language = "en"
    mock_cfg.safe_search = 1
    mock_cfg.engine = "searxng"
    mock_cfg.num_results = 5
    mock_cfg.region = "all"

    args = MagicMock()
    args.query = query
    args.research_mode = research_mode
    args.web_search = web_search
    args.username = "matrix_tester"
    args.thread_id = "test_thread"

    service = SearchBoostService(
        ai=mock_cfg,
        search=mock_cfg,
        redis=MagicMock(),
        db=MagicMock(),
        logger=setup_logger("DEBUG"),
        args=args
    )
    return service, args


@pytest.mark.asyncio
async def test_e2e_mode_deep_web():
    """Mode 1: Deep Research + Web Search.
    Verifies query optimization, SearXNG search, and deep:web cache key tagging.
    """
    service, _ = create_mock_service(
        query="Explain distributed microservices in Rust",
        research_mode=True,
        web_search=True
    )

    reasons_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        if self_handler.reason == "optimization":
            return "rust distributed microservices architecture"
        return "Deep research synthesis with web and docs."

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock) as mock_cache_set, \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):

        mock_cache_get.return_value = None
        mock_web_search.return_value = "Rust microservice search snippets"
        mock_doc_search.return_value = [
            {"source_file": "docs/rust.md", "chunk_index": 0, "content": "Internal Rust guide"}
        ]

        mock_db_session = AsyncMock()
        result = await service.run(db_session=mock_db_session)

    assert result == "Deep research synthesis with web and docs."
    assert "optimization" in reasons_called
    assert "research" in reasons_called
    assert mock_web_search.call_count == 1
    assert mock_doc_search.call_count == 1
    assert mock_cache_set.called
    assert mock_cache_set.call_args.kwargs.get("mode") == "deep:web"


@pytest.mark.asyncio
async def test_e2e_mode_deep_local():
    """Mode 2: Deep Research + Offline Local Knowledge Only.
    Verifies query optimization executes, SearXNG is strictly bypassed (0 calls),
    and cache key is tagged as deep:local.
    """
    service, _ = create_mock_service(
        query="How does Antigravity manage sidecar lifecycle?",
        research_mode=True,
        web_search=False
    )

    reasons_called = []
    prompts_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        prompts_called.append(chatdetails.prompt)
        return "Internal offline sidecar documentation answer."

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock) as mock_cache_set, \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):

        mock_cache_get.return_value = None
        mock_doc_search.return_value = [
            {"source_file": "docs/sidecar.md", "chunk_index": 0, "content": "Sidecar process supervision details."}
        ]

        mock_db_session = AsyncMock()
        result = await service.run(db_session=mock_db_session)

    assert result == "Internal offline sidecar documentation answer."
    # CRITICAL: Complete bypass of SearXNG
    assert mock_web_search.call_count == 0
    assert mock_doc_search.call_count == 1
    assert mock_cache_set.called
    assert mock_cache_set.call_args.kwargs.get("mode") == "deep:local"
    assert any("INTERNAL DOCUMENT KNOWLEDGE" in p for p in prompts_called)


@pytest.mark.asyncio
async def test_e2e_mode_fast_web():
    """Mode 3: Fast Answer + Web Search.
    Verifies query optimization is bypassed for low-latency, SearXNG is queried,
    and cache key is tagged as fast:web.
    """
    service, _ = create_mock_service(
        query="Current weather in Athens Greece",
        research_mode=False,
        web_search=True
    )

    reasons_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        return "Athens weather: 26C and sunny."

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock) as mock_cache_set, \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):

        mock_cache_get.return_value = None
        mock_web_search.return_value = "Athens weather report: sunny 26C"
        mock_doc_search.return_value = []

        mock_db_session = AsyncMock()
        result = await service.run(db_session=mock_db_session)

    assert result == "Athens weather: 26C and sunny."
    assert "optimization" not in reasons_called
    assert reasons_called == ["fast_answer"]
    assert mock_web_search.call_count == 1
    assert mock_cache_set.called
    assert mock_cache_set.call_args.kwargs.get("mode") == "fast:web"


@pytest.mark.asyncio
async def test_e2e_mode_fast_local():
    """Mode 4: Fast Answer + Offline Local Knowledge Only.
    Verifies query optimization is bypassed, SearXNG is bypassed, internal docs are used,
    and cache key is tagged as fast:local.
    """
    service, _ = create_mock_service(
        query="Database schema definition for internal documents",
        research_mode=False,
        web_search=False
    )

    reasons_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        return "Internal documents schema uses pgvector."

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock) as mock_cache_set, \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):

        mock_cache_get.return_value = None
        mock_doc_search.return_value = [
            {"source_file": "schema.sql", "chunk_index": 0, "content": "CREATE TABLE internal_documents..."}
        ]

        mock_db_session = AsyncMock()
        result = await service.run(db_session=mock_db_session)

    assert result == "Internal documents schema uses pgvector."
    assert "optimization" not in reasons_called
    assert mock_web_search.call_count == 0
    assert mock_doc_search.call_count == 1
    assert mock_cache_set.called
    assert mock_cache_set.call_args.kwargs.get("mode") == "fast:local"


@pytest.mark.asyncio
async def test_e2e_resilience_when_document_service_errors():
    """Fault Tolerance: If vector document retrieval encounters an exception (e.g. db timeout),
    the service should log a warning and proceed gracefully without failing the user request.
    """
    service, _ = create_mock_service(
        query="What is the architecture?",
        research_mode=False,
        web_search=True
    )

    async def mock_query_llm(self_handler, chatdetails):
        return "Resilient response despite doc error"

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock), \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):

        mock_cache_get.return_value = None
        mock_web_search.return_value = "Fallback web results"
        mock_doc_search.side_effect = RuntimeError("Database connection reset by peer")

        mock_db_session = AsyncMock()
        # Should not raise exception
        result = await service.run(db_session=mock_db_session)

    assert result == "Resilient response despite doc error"
    assert mock_web_search.call_count == 1


@pytest.mark.asyncio
async def test_e2e_cache_hit_bypasses_pipeline_for_all_modes():
    """Cache Validation: Verifies that a cache hit immediately returns the cached answer
    and does not trigger LLM calls, SearXNG searches, or document scans.
    """
    for mode_name, r_mode, w_search in [
        ("deep:web", True, True),
        ("deep:local", True, False),
        ("fast:web", False, True),
        ("fast:local", False, False)
    ]:
        service, _ = create_mock_service("repeated query", r_mode, w_search)

        with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
             patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
             patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
             patch("searchboost_src.ai_handler.AIHandler.query_LLM", new_callable=AsyncMock) as mock_llm:

            mock_cache_get.return_value = f"Cached answer for {mode_name}"

            mock_db_session = AsyncMock()
            result = await service.run(db_session=mock_db_session)

            assert result == f"Cached answer for {mode_name}"
            mock_cache_get.assert_awaited_once_with("repeated query", mode=mode_name)
            assert mock_llm.call_count == 0
            assert mock_web_search.call_count == 0
            assert mock_doc_search.call_count == 0
