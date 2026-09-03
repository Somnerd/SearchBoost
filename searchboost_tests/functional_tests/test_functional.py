# -*- coding: utf-8 -*-
# SearchBoost Functional Tests: PII Detector & Configuration Tests
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, patch

from searchboost_src.pii_detector import PIIDetector
from searchboost_src.argparser import Argsparser_Instance
from main import submit_to_warden


# =====================================================================
# PIIDetector Functional Test Suite
# =====================================================================

def test_pii_detector_clean_text():
    """Verify that clean informational queries without PII pass cleanly."""
    detector = PIIDetector()
    result = detector.scan("What is the difference between Rust and Go in concurrency?")
    assert not result.contains_pii
    assert bool(result) is False
    assert len(result.matches) == 0

    result2 = detector.scan("Search for latest research on quantum computing and AI models.")
    assert not result2.contains_pii
    assert len(result2.matches) == 0


def test_pii_detector_payment_cards():
    """Verify detection of payment cards in various formats (dashes, spaces, continuous)."""
    detector = PIIDetector()

    # Hyphenated 16-digit card
    res1 = detector.scan("Please charge my card 4111-2222-3333-4444 for the subscription.")
    assert res1.contains_pii
    assert bool(res1) is True
    assert any(m.pattern_name == "payment_card" and "4111-2222-3333-4444" in m.matched_value for m in res1.matches)

    # Space-separated card
    res2 = detector.scan("Credit card: 5555 4444 3333 2222 expiration 12/28")
    assert res2.contains_pii
    assert any(m.pattern_name == "payment_card" for m in res2.matches)

    # Continuous 16-digit card
    res3 = detector.scan("Card number 4111222233334444")
    assert res3.contains_pii
    assert any(m.pattern_name == "payment_card" for m in res3.matches)


def test_pii_detector_ssn():
    """Verify US Social Security Number detection."""
    detector = PIIDetector()
    result = detector.scan("Confidential user identity: SSN 123-45-6789.")
    assert result.contains_pii
    assert any(m.pattern_name == "ssn" and m.matched_value == "123-45-6789" for m in result.matches)


def test_pii_detector_email():
    """Verify email address detection."""
    detector = PIIDetector()
    result = detector.scan("Contact the administrator at admin@enterprise-domain.com for help.")
    assert result.contains_pii
    assert any(m.pattern_name == "email" and m.matched_value == "admin@enterprise-domain.com" for m in result.matches)


def test_pii_detector_ipv4():
    """Verify IPv4 address detection."""
    detector = PIIDetector()
    result = detector.scan("Database internal host address is 192.168.1.105 on port 5432.")
    assert result.contains_pii
    assert any(m.pattern_name == "ipv4_address" and m.matched_value == "192.168.1.105" for m in result.matches)


def test_pii_detector_multiple_matches():
    """Verify detection of multiple distinct PII types in a single prompt."""
    detector = PIIDetector()
    text = "User test@company.com with card 5555 4444 3333 2222 and SSN 987-65-4321 at 10.0.0.1"
    result = detector.scan(text)
    assert result.contains_pii
    matched_patterns = {m.pattern_name for m in result.matches}
    assert "email" in matched_patterns
    assert "payment_card" in matched_patterns
    assert "ssn" in matched_patterns
    assert "ipv4_address" in matched_patterns
    assert len(result.matches) >= 4


def test_pii_detector_edge_cases():
    """Verify edge cases such as empty strings, None, and non-string types."""
    detector = PIIDetector()
    assert not detector.scan("")
    assert not detector.scan(None)
    assert not detector.scan(123456789)
    assert not detector.scan(["192.168.1.1"])


def test_pii_detector_logging():
    """Verify logger messages on PII detection and clean scans."""
    logger_mock = MagicMock()
    detector = PIIDetector(logger=logger_mock)

    # Clean text logs debug
    detector.scan("Clean text without PII")
    logger_mock.debug.assert_called_with("PIIDetector: No PII detected. Text is safe to cache.")

    # PII text logs warning
    detector.scan("My email is alice@example.com")
    assert logger_mock.warning.called
    warning_arg = logger_mock.warning.call_args[0][0]
    assert "PII detected in text" in warning_arg
    assert "BLOCKED" in warning_arg


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
