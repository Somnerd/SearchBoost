# -*- coding: utf-8 -*-
# SearchBoost Functional Tests: Argparser & Handshake Tests
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from searchboost_src.argparser import Argsparser_Instance
from main import submit_to_warden


# =====================================================================
# Argsparser_Instance Functional Test Suite
# =====================================================================

@pytest.mark.asyncio
async def test_argparser_defaults(monkeypatch):
    """Verify default values when minimal query arguments are passed."""
    monkeypatch.setattr(sys, "argv", ["main.py", "--query", "default test query"])
    parser_instance = Argsparser_Instance()
    args = await parser_instance.parse_arguments()

    assert args.query == "default test query"
    assert args.type == "local"
    assert args.engine == "searxng"
    assert args.model == "llama3.2"
    assert args.username == "guest"
    assert args.thread_id == "default"
    assert args.stream is False
    assert args.info == "info"


@pytest.mark.asyncio
async def test_argparser_custom_cli_options(monkeypatch):
    """Verify custom CLI options are parsed correctly into the namespace."""
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "-q", "custom search query",
        "-u", "alice_operator",
        "--thread_id", "session-tok-999",
        "-m", "qwen2.5:7b",
        "-e", "searxng_cluster",
        "-t", "cloud",
        "-i", "debug",
        "-s", "True"
    ])
    parser_instance = Argsparser_Instance()
    args = await parser_instance.parse_arguments()

    assert args.query == "custom search query"
    assert args.username == "alice_operator"
    assert args.thread_id == "session-tok-999"
    assert args.model == "qwen2.5:7b"
    assert args.engine == "searxng_cluster"
    assert args.type == "cloud"
    assert args.info == "debug"


@pytest.mark.asyncio
async def test_argparser_final_arguments_interactive_prompt(monkeypatch):
    """Verify fallback interactive input when --query is omitted."""
    monkeypatch.setattr(sys, "argv", ["main.py", "-u", "interactive_user"])
    monkeypatch.setattr("builtins.input", lambda _: "interactive prompt query")

    parser_instance = Argsparser_Instance()
    args = await parser_instance.final_arguments()

    assert args.query == "interactive prompt query"
    assert args.username == "interactive_user"
    assert args.thread_id == "default"


@pytest.mark.asyncio
async def test_argparser_debug_logs(monkeypatch):
    """Verify debug_logs logs all parsed arguments when info level is debug."""
    monkeypatch.setattr(sys, "argv", ["main.py", "-q", "debug query", "-i", "debug"])
    parser_instance = Argsparser_Instance()
    parser_instance.logger = MagicMock()
    args = await parser_instance.parse_arguments()
    await parser_instance.debug_logs()

    assert parser_instance.logger.debug.called
    logged_keys = [call[0][0] for call in parser_instance.logger.debug.call_args_list]
    assert any("query: debug query" in l for l in logged_keys)
    assert any("info: debug" in l for l in logged_keys)


# =====================================================================
# Distributed Handshake Schema Verification
# =====================================================================

@pytest.mark.asyncio
async def test_submit_to_warden_handshake_schema():
    """Verify submit_to_warden constructs payload matching Warden SearchRequest schema."""
    logger_mock = MagicMock()
    args_mock = MagicMock()
    args_mock.query = "rust vs python"
    args_mock.username = "test_user"
    args_mock.thread_id = "thread-xyz"
    args_mock.model = "llama3.2"

    captured_payload = None

    class MockResponse:
        status_code = 200
        def json(self):
            return {"status": "queued", "id": "SB-SESSION:test_user:thread-xyz:uuid-1234"}

    async def mock_post(self, url, json=None, **kwargs):
        nonlocal captured_payload
        captured_payload = json
        return MockResponse()

    with patch("httpx.AsyncClient.post", new=mock_post):
        job_id = await submit_to_warden(logger_mock, "rust vs python", args_mock, "http://sb_warden:14141/enqueue")

    assert job_id == "SB-SESSION:test_user:thread-xyz:uuid-1234"
    assert captured_payload is not None
    assert "query" in captured_payload and captured_payload["query"] == "rust vs python"
    assert "thread_id" in captured_payload and captured_payload["thread_id"] == "thread-xyz"
    assert "username" in captured_payload and captured_payload["username"] == "test_user"
    assert "options" in captured_payload
    assert "session_id" not in captured_payload  # Verified removed in favor of explicit fields


@pytest.mark.asyncio
async def test_submit_to_warden_fallback_defaults():
    """Verify submit_to_warden applies default fallback values for thread_id and username."""
    logger_mock = MagicMock()
    class BareArgs:
        pass

    bare_args = BareArgs()
    captured_payload = None

    class MockResponse:
        status_code = 200
        def json(self):
            return {"status": "queued", "id": "SB-SESSION:default_user:default:uuid-5678"}

    async def mock_post(self, url, json=None, **kwargs):
        nonlocal captured_payload
        captured_payload = json
        return MockResponse()

    with patch("httpx.AsyncClient.post", new=mock_post):
        job_id = await submit_to_warden(logger_mock, "fallback query", bare_args, "http://sb_warden:14141/enqueue")

    assert job_id == "SB-SESSION:default_user:default:uuid-5678"
    assert captured_payload["thread_id"] == "default"
    assert captured_payload["username"] == "default_user"


@pytest.mark.asyncio
async def test_submit_to_warden_forwards_research_mode():
    """Verify submit_to_warden forwards research_mode flag in options."""
    logger_mock = MagicMock()
    args_mock = MagicMock()
    args_mock.query = "quantum computing"
    args_mock.username = "researcher"
    args_mock.thread_id = "thread-q"
    args_mock.research_mode = False

    captured_payload = None

    class MockResponse:
        status_code = 200
        def json(self):
            return {"status": "queued", "id": "SB-SESSION:researcher:thread-q:uuid-999"}

    async def mock_post(self, url, json=None, **kwargs):
        nonlocal captured_payload
        captured_payload = json
        return MockResponse()

    with patch("httpx.AsyncClient.post", new=mock_post):
        job_id = await submit_to_warden(logger_mock, "quantum computing", args_mock, "http://sb_warden:14141/enqueue")

    assert job_id == "SB-SESSION:researcher:thread-q:uuid-999"
    assert "options" in captured_payload
    assert captured_payload["options"].get("research_mode") is False


# =====================================================================
# SearchBoostService Research Mode Pipeline Tests
# =====================================================================

@pytest.mark.asyncio
async def test_searchboost_service_research_mode_enabled():
    """Verify research_mode=True executes full multi-step pipeline (optimization + research)."""
    from searchboost_src.service import SearchBoostService
    from searchboost_src.logger import setup_logger

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
    args.query = "What is Rust ownership?"
    args.research_mode = True

    service = SearchBoostService(
        ai=mock_cfg,
        search=mock_cfg,
        redis=MagicMock(),
        db=MagicMock(),
        logger=setup_logger("DEBUG"),
        args=args
    )

    reasons_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        return f"result for {self_handler.reason}"

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock), \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):
        
        mock_cache_get.return_value = None
        mock_web_search.return_value = "Rust ownership documentation snippets"

        result = await service.run(db_session=None)

    assert result == "result for research"
    assert "optimization" in reasons_called
    assert "research" in reasons_called
    assert reasons_called == ["optimization", "research"]


@pytest.mark.asyncio
async def test_searchboost_service_research_mode_disabled_fast_answer():
    """Verify research_mode=False bypasses query optimization and runs fast direct answer."""
    from searchboost_src.service import SearchBoostService
    from searchboost_src.logger import setup_logger

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
    args.query = "Fast answer query"
    args.research_mode = False

    service = SearchBoostService(
        ai=mock_cfg,
        search=mock_cfg,
        redis=MagicMock(),
        db=MagicMock(),
        logger=setup_logger("DEBUG"),
        args=args
    )

    reasons_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        return f"fast answer result"

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock), \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):
        
        mock_cache_get.return_value = None
        mock_web_search.return_value = "SearXNG direct snippets"

        result = await service.run(db_session=None)

    assert result == "fast answer result"
    assert "optimization" not in reasons_called
    assert reasons_called == ["fast_answer"]


@pytest.mark.asyncio
async def test_searchboost_service_fast_answer_greeting():
    """Verify greeting in fast answer mode directly answers conversationally without web search."""
    from searchboost_src.service import SearchBoostService
    from searchboost_src.logger import setup_logger

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
    args.query = "hi"
    args.research_mode = False

    service = SearchBoostService(
        ai=mock_cfg,
        search=mock_cfg,
        redis=MagicMock(),
        db=MagicMock(),
        logger=setup_logger("DEBUG"),
        args=args
    )

    reasons_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        return "Hello! How can I help you today?"

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock), \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):
        
        mock_cache_get.return_value = None

        result = await service.run(db_session=None)

    assert result == "Hello! How can I help you today?"
    assert mock_web_search.call_count == 0
    assert reasons_called == ["conversation"]


# =====================================================================
# Web Search Toggle & Offline Mode Functional Tests (Issue #47)
# =====================================================================

@pytest.mark.asyncio
async def test_argparser_web_search_options(monkeypatch):
    """Verify --web-search CLI option toggles boolean accurately."""
    monkeypatch.setattr(sys, "argv", ["main.py", "-q", "offline test", "--web-search", "false"])
    parser_instance = Argsparser_Instance()
    args = await parser_instance.parse_arguments()
    assert args.web_search is False

    monkeypatch.setattr(sys, "argv", ["main.py", "-q", "online test", "--web_search", "true"])
    parser_instance2 = Argsparser_Instance()
    args2 = await parser_instance2.parse_arguments()
    assert args2.web_search is True


@pytest.mark.asyncio
async def test_submit_to_warden_forwards_web_search():
    """Verify submit_to_warden forwards web_search toggle in options payload."""
    logger_mock = MagicMock()
    args_mock = MagicMock()
    args_mock.query = "offline query"
    args_mock.username = "offline_user"
    args_mock.thread_id = "thread-offline"
    args_mock.model = "llama3.2"
    args_mock.research_mode = True
    args_mock.web_search = False

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "job-offline-123"}
        mock_post.return_value = mock_response

        job_id = await submit_to_warden(
            logger=logger_mock,
            query="offline query",
            args=args_mock,
            warden_url="http://warden:14141/enqueue"
        )

        assert job_id == "job-offline-123"
        sent_payload = mock_post.call_args[1]["json"]
        assert sent_payload["options"]["web_search"] is False


@pytest.mark.asyncio
async def test_searchboost_service_offline_mode_bypasses_searxng():
    """Verify offline mode (web_search=False) completely bypasses SearXNG and uses local docs."""
    from searchboost_src.service import SearchBoostService
    from searchboost_src.logger import setup_logger

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
    args.query = "Tell me about internal architecture"
    args.research_mode = False
    args.web_search = False

    service = SearchBoostService(
        ai=mock_cfg,
        search=mock_cfg,
        redis=MagicMock(),
        db=MagicMock(),
        logger=setup_logger("DEBUG"),
        args=args
    )

    reasons_called = []
    prompts_called = []
    async def mock_query_llm(self_handler, chatdetails):
        reasons_called.append(self_handler.reason)
        prompts_called.append(chatdetails.prompt)
        return "Internal documentation answer"

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock) as mock_cache_set, \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):

        mock_cache_get.return_value = None
        mock_doc_search.return_value = [
            {"source_file": "docs/arch.md", "content": "Antigravity core engine operates locally."}
        ]

        mock_db_session = AsyncMock()
        result = await service.run(db_session=mock_db_session)

    assert result == "Internal documentation answer"
    # CRITICAL: SearXNG must NOT be invoked in offline mode
    assert mock_web_search.call_count == 0
    # DocumentService should be consulted
    assert mock_doc_search.call_count == 1
    # Cache mode must reflect local mode
    assert mock_cache_set.called
    assert ":local" in mock_cache_set.call_args.kwargs.get("mode", "")
    # Internal docs should be in the LLM prompt
    assert any("INTERNAL DOCUMENT KNOWLEDGE" in p for p in prompts_called)


@pytest.mark.asyncio
async def test_searchboost_service_hybrid_mode_with_web_search():
    """Verify hybrid mode (web_search=True) queries both SearXNG and local docs."""
    from searchboost_src.service import SearchBoostService
    from searchboost_src.logger import setup_logger

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
    args.query = "Compare local and web search"
    args.research_mode = False
    args.web_search = True

    service = SearchBoostService(
        ai=mock_cfg,
        search=mock_cfg,
        redis=MagicMock(),
        db=MagicMock(),
        logger=setup_logger("DEBUG"),
        args=args
    )

    async def mock_query_llm(self_handler, chatdetails):
        return "Hybrid synthesized answer"

    with patch("searchboost_src.service.CacheService.get", new_callable=AsyncMock) as mock_cache_get, \
         patch("searchboost_src.service.CacheService.set", new_callable=AsyncMock) as mock_cache_set, \
         patch("searchboost_src.web_search.WebSearch.searxng_search", new_callable=AsyncMock) as mock_web_search, \
         patch("searchboost_src.database.DocumentService.search_documents", new_callable=AsyncMock) as mock_doc_search, \
         patch("searchboost_src.ai_handler.AIHandler.query_LLM", new=mock_query_llm):

        mock_cache_get.return_value = None
        mock_web_search.return_value = "Web search snippets"
        mock_doc_search.return_value = [
            {"source_file": "docs/hybrid.md", "content": "Local knowledge chunk."}
        ]

        mock_db_session = AsyncMock()
        result = await service.run(db_session=mock_db_session)

    assert result == "Hybrid synthesized answer"
    assert mock_web_search.call_count == 1
    assert mock_doc_search.call_count == 1
    assert mock_cache_set.called
    assert ":web" in mock_cache_set.call_args.kwargs.get("mode", "")


