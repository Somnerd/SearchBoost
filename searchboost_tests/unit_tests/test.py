import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../searchboost_service')))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from searchboost_src.ollama_client import OllamaClient

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_chat_details():
    chat_details = MagicMock()
    chat_details.config = MagicMock()
    chat_details.config.base_url = "http://test-host:11434"
    chat_details.config.model = "test-model"
    chat_details.config.role = "user"
    chat_details.prompt = "test prompt"
    chat_details.system_prompt = "test system prompt"
    return chat_details

@pytest.mark.asyncio
@patch('searchboost_src.ollama_client.AsyncClient')
async def test_ollama_client_success(mock_async_client_class, mock_logger, mock_chat_details):
    # Setup mock AsyncClient instance
    mock_async_client = AsyncMock()
    mock_async_client_class.return_value = mock_async_client

    mock_response = {
        'model': 'test-model',
        'message': {'role': 'assistant', 'content': 'This is a test response.'}
    }
    mock_async_client.chat.return_value = mock_response

    # Initialize OllamaClient
    client = OllamaClient(logger=mock_logger, ChatDetails=mock_chat_details)

    # Verify AsyncClient was initialized with correct host
    mock_async_client_class.assert_called_with(
        host="http://test-host:11434",
        headers={"Ollama-Client": "SearchBoost"}
    )

    # Query Ollama
    result = await client.query_ollama()

    # Assert result
    assert result == 'This is a test response.'

    # Assert chat was called correctly
    mock_async_client.chat.assert_called_once_with(
        model="test-model",
        messages=[
            {
                "role": "system",
                "content": "test system prompt"
            },
            {
                "role": "user",
                "content": "test prompt"
            }
        ]
    )

    # Assert logger was used
    mock_logger.debug.assert_called()

@pytest.mark.asyncio
@patch('searchboost_src.ollama_client.AsyncClient')
async def test_ollama_client_exception(mock_async_client_class, mock_logger, mock_chat_details):
    # Setup mock AsyncClient instance
    mock_async_client = AsyncMock()
    mock_async_client_class.return_value = mock_async_client

    mock_async_client.chat.side_effect = Exception("Test connection error")

    # Initialize OllamaClient
    client = OllamaClient(logger=mock_logger, ChatDetails=mock_chat_details)

    # Query Ollama
    result = await client.query_ollama()

    # Assert result
    assert result == "Error: Unable to connect to the LLM."

    # Assert logger was used to log error
    mock_logger.error.assert_called_once()
    assert "Test connection error" in mock_logger.error.call_args[0][0]
