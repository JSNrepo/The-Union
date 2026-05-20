import pytest
from app.main import call_provider_api
import uuid
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.anyio
async def test_call_provider_api_openai():
    with patch('app.main.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.text = "This is a response from OpenAI"
        mock_post.return_value = mock_response

        response = await call_provider_api('openai', 'token123', 'Hello')
        assert response == "OpenAI: This is a response from OpenAI..."
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://chatgpt.com/backend-api/conversation"
        assert kwargs["headers"] == {"Authorization": "Bearer token123", "Content-Type": "application/json"}
        assert kwargs["json"]["action"] == "next"
        assert kwargs["json"]["messages"][0]["content"]["parts"][0] == "Hello"

@pytest.mark.anyio
async def test_call_provider_api_claude():
    with patch('app.main.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.text = "This is a response from Claude"
        mock_post.return_value = mock_response

        response = await call_provider_api('claude', 'token456', 'Hi Claude')
        assert response == "Claude: This is a response from Claude..."
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://claude.ai/api/append_message"
        assert kwargs["headers"] == {"Cookie": "sessionKey=token456", "Content-Type": "application/json"}
        assert kwargs["json"] == {"prompt": "Hi Claude"}

@pytest.mark.anyio
async def test_call_provider_api_gemini():
    with patch('app.main.httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_response = MagicMock()
        mock_response.text = "This is a response from Gemini"
        mock_post.return_value = mock_response

        response = await call_provider_api('gemini', 'token789', 'Hi Gemini')
        assert response == "Gemini: This is a response from Gemini..."
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://gemini.google.com/_/BardChat/data/batchexecute"
        assert kwargs["headers"] == {"Cookie": "__Secure-1PSID=token789", "Content-Type": "application/x-www-form-urlencoded"}
        assert kwargs["data"] == {"f.req": "Hi Gemini"}

@pytest.mark.anyio
async def test_call_provider_api_unsupported():
    with pytest.raises(Exception, match="Unsupported provider"):
        await call_provider_api('unknown', 'token', 'Hello')
