import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from searchboost_src.ollama_client import OllamaClient

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_chat_details():
    chat_details = MagicMock()
    chat_details.config = MagicMock()
    chat_details.config.base_url = "http://localhost:11434"
    chat_details.config.model = "test-model"
    chat_details.config.role = "user"
    chat_details.prompt = "test prompt"
    chat_details.system_prompt = "system prompt"
    return chat_details

@pytest.mark.asyncio
async def test_ollama_client_success(mocker, mock_logger, mock_chat_details):
    mock_async_client_cls = mocker.patch('searchboost_src.ollama_client.AsyncClient')
    mock_async_client_instance = AsyncMock()
    mock_async_client_cls.return_value = mock_async_client_instance

    mock_async_client_instance.chat.return_value = {
        'message': {
            'content': 'test response'
        }
    }

    client = OllamaClient(logger=mock_logger, ChatDetails=mock_chat_details)

    response = await client.query_ollama()

    assert response == 'test response'
    mock_async_client_instance.chat.assert_called_once_with(
        model="test-model",
        messages=[
            {
            "role": "system",
            "content": "system prompt"
            },
            {
            "role": "user",
            "content": "test prompt"
            }
        ]
    )
    mock_logger.debug.assert_called()

@pytest.mark.asyncio
async def test_ollama_client_exception(mocker, mock_logger, mock_chat_details):
    mock_async_client_cls = mocker.patch('searchboost_src.ollama_client.AsyncClient')
    mock_async_client_instance = AsyncMock()
    mock_async_client_cls.return_value = mock_async_client_instance

    mock_async_client_instance.chat.side_effect = Exception("Test exception")

    client = OllamaClient(logger=mock_logger, ChatDetails=mock_chat_details)

    response = await client.query_ollama()

    assert response == "Error: Unable to connect to the LLM."
    mock_logger.error.assert_called_once_with("OLLAMA CLIENT : Error querying Ollama API: Test exception")
