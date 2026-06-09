import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from searchboost_src.api_client import ApiClient

class MockConfig:
    def __init__(self, api, provider, model, role="user"):
        self.api = api
        self.provider = provider
        self.model = model
        self.role = role

class MockChatDetails:
    def __init__(self, system_prompt, prompt, config, extra_body=None):
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.config = config
        self.extra_body = extra_body or {}

@pytest.mark.asyncio
async def test_api_client_extracts_correct_properties():
    # Setup mock data
    mock_config = MockConfig(
        api="test-api-key",
        provider="https://test.provider.com",
        model="test-model",
        role="assistant"
    )
    mock_chat_details = MockChatDetails(
        system_prompt="You are a helper.",
        prompt="Hello world",
        config=mock_config,
        extra_body={"temperature": 0.7}
    )

    logger = MagicMock()
    client = ApiClient(logger=logger)

    mock_openai_client = MagicMock()
    mock_completions_create = AsyncMock()

    mock_choice = MagicMock()
    mock_choice.message.content = "Test response"
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_completions_create.return_value = mock_response
    mock_openai_client.chat.completions.create = mock_completions_create

    with patch("searchboost_src.api_client.AsyncOpenAI", return_value=mock_openai_client) as mock_async_openai:
        response = await client.api_call(mock_chat_details)

        # Verify AsyncOpenAI was created with the correct api_key and base_url
        mock_async_openai.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://test.provider.com"
        )

        # Verify completions.create was called with the correct model, messages, and extra_body params
        mock_completions_create.assert_called_once_with(
            model="test-model",
            messages=[
                {"role": "system", "content": "You are a helper."},
                {"role": "assistant", "content": "Hello world"}
            ],
            temperature=0.7
        )

        assert response == "Test response"
