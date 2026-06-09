import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../searchboost_service')))

from searchboost_src.ollama_client import OllamaClient
from searchboost_src.chat_class import ChatDetails
import searchboost_src.logger as logger_module

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.base_url = "http://localhost:11434"
    config.model = "test-model"
    config.role = "user"
    return config

@pytest.fixture
def mock_chat_details(mock_config):
    details = ChatDetails(mock_config, "test prompt")
    details.system_prompt = "system test prompt"
    return details

@pytest.fixture
def mock_logger():
    return logger_module.setup_logger("debug")

@pytest.mark.asyncio
async def test_query_ollama_success(mock_logger, mock_chat_details):
    with patch("searchboost_src.ollama_client.AsyncClient") as MockAsyncClient:
        mock_client_instance = MockAsyncClient.return_value
        mock_client_instance.chat = AsyncMock(return_value={
            'message': {'content': 'Mocked LLM Response'}
        })

        client = OllamaClient(logger=mock_logger, ChatDetails=mock_chat_details)

        response = await client.query_ollama()

        assert response == 'Mocked LLM Response'
        mock_client_instance.chat.assert_called_once_with(
            model="test-model",
            messages=[
                {
                    "role": "system",
                    "content": "system test prompt"
                },
                {
                    "role": "user",
                    "content": "test prompt"
                }
            ]
        )

@pytest.mark.asyncio
async def test_query_ollama_exception(mock_logger, mock_chat_details):
    with patch("searchboost_src.ollama_client.AsyncClient") as MockAsyncClient:
        mock_client_instance = MockAsyncClient.return_value
        mock_client_instance.chat = AsyncMock(side_effect=Exception("Connection failed"))

        client = OllamaClient(logger=mock_logger, ChatDetails=mock_chat_details)

        response = await client.query_ollama()

        assert response == "Error: Unable to connect to the LLM."
