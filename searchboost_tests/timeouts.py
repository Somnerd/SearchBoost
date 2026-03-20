import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

# Import the classes we are going to test
from searchboost_src.web_search import WebSearch
from searchboost_src.ollama_client import OllamaClient
from searchboost_src.logger import setup_logger

class MockConfig:
    def __init__(self):
        self.base_url = "http://localhost"
        self.format = "json"
        self.language = "en"
        self.safe_search = 1
        self.engine = "google"
        self.num_results = 5
        self.region = "us"
        self.model = "test-model"
        self.role = "user"
        self.stream = False
        self.port = 8080
        self.timeout = 180.0  # Must match the default in OllamaClient/ollama_client.py

class MockChatDetails:
    def __init__(self):
        self.config = MockConfig()
        self.prompt = "Test prompt"
        self.system_prompt = "You are a test."

@pytest.fixture
def logger():
    return setup_logger("INFO")

@pytest.mark.asyncio
async def test_web_search_timeout_handling(logger):
    """
    Test that modifying web_search.py to httpx properly handles timeout exceptions
    without raising an unhandled exception or blocking the event loop.
    """
    config = MockConfig()
    ws = WebSearch("test query", config, logger)
    
    # BUG FIX: httpx.AsyncClient is used as an async context manager in web_search.py:
    #   `async with httpx.AsyncClient() as client: response = await client.get(...)`
    # Patching `httpx.AsyncClient.get` at the class level does NOT intercept calls
    # made through the context manager — __aenter__ returns a live instance.
    # Correct approach: mock the AsyncClient constructor to return a mock whose
    # __aenter__ returns a mock with .get configured to raise TimeoutException.
    mock_client_instance = AsyncMock()
    mock_client_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Mocked timeout"))
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        # It shouldn't crash; it should return the fallback string
        result = await ws.searxng_search()

        assert "Web search timed out. Could not fetch results." in result
        mock_client_instance.get.assert_called_once()


@pytest.mark.asyncio
async def test_ollama_query_timeout_handling(logger):
    """
    Test that our explicit asyncio.wait_for wrapper in query_ollama
    gracefully catches long-running jobs.
    """
    details = MockChatDetails()
    client = OllamaClient(logger=logger, ChatDetails=details)
    
    # Create an async function that sleeps for slightly more than the wait_for timeout
    # But since we're testing the timeout, we don't want to actually wait 15 seconds.
    # Instead, we will patch `asyncio.wait_for` directly just for this test,
    # or patch the `client.chat` to sleep and mock the timeout to be short, but the 
    # timeout is hardcoded to 15.0s in the source file. 
    # Actually, the easiest way is to mock `client.chat` to raise asyncio.TimeoutError directly.
    # This simulates what wait_for does when it expires.
    
    with patch.object(client.client, "chat", new_callable=AsyncMock) as mock_chat:
        with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait_for:
            mock_wait_for.side_effect = asyncio.TimeoutError()

            result = await client.query_ollama()

            # BUG FIX: timeout_limit defaults to 180.0 (from getattr fallback in ollama_client.py).
            # The assertion must match the actual formatted string: f"timeout after {timeout_limit}s"
            assert "timeout after 180.0s" in result
            mock_wait_for.assert_called_once()
