import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath('searchboost_service'))

from searchboost_src.ollama_client import OllamaClient
from searchboost_src.chat_class import ChatDetails

@pytest.mark.asyncio
async def test_ollama_client_success():
    config_mock = MagicMock()
    config_mock.base_url = "http://localhost:11434"
    config_mock.model = "llama2"
    config_mock.role = "user"

    chat_details = ChatDetails(config=config_mock, prompt="Hello")
    chat_details.system_prompt = "System prompt"

    logger_mock = MagicMock()

    with patch('searchboost_src.ollama_client.AsyncClient') as MockAsyncClient:
        mock_client_instance = MockAsyncClient.return_value
        mock_client_instance.chat = AsyncMock(return_value={'message': {'content': 'Hi there!'}})

        client = OllamaClient(logger=logger_mock, ChatDetails=chat_details)
        response = await client.query_ollama()

        assert response == 'Hi there!'
        mock_client_instance.chat.assert_called_once_with(
            model='llama2',
            messages=[
                {'role': 'system', 'content': 'System prompt'},
                {'role': 'user', 'content': 'Hello'}
            ]
        )

@pytest.mark.asyncio
async def test_ollama_client_exception():
    config_mock = MagicMock()
    config_mock.base_url = "http://localhost:11434"
    config_mock.model = "llama2"
    config_mock.role = "user"

    chat_details = ChatDetails(config=config_mock, prompt="Hello")
    chat_details.system_prompt = "System prompt"

    logger_mock = MagicMock()

    with patch('searchboost_src.ollama_client.AsyncClient') as MockAsyncClient:
        mock_client_instance = MockAsyncClient.return_value
        mock_client_instance.chat = AsyncMock(side_effect=Exception("API Error"))

        client = OllamaClient(logger=logger_mock, ChatDetails=chat_details)
        response = await client.query_ollama()

        assert response == "Error: Unable to connect to the LLM."
        logger_mock.error.assert_called_once_with("OLLAMA CLIENT : Error querying Ollama API: API Error")
