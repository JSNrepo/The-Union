import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import join_workspace, chat_message, sio, call_provider_api, connect, disconnect
import uuid

@pytest.mark.anyio
async def test_connect():
    with patch('builtins.print') as mock_print:
        await connect('sid1', {})
        mock_print.assert_called_once_with('Client connected: sid1')

@pytest.mark.anyio
async def test_disconnect():
    with patch('builtins.print') as mock_print:
        await disconnect('sid1')
        mock_print.assert_called_once_with('Client disconnected: sid1')

@pytest.mark.anyio
async def test_join_workspace():
    with patch.object(sio, 'enter_room') as mock_enter, \
         patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await join_workspace('sid1', {'workspace_id': 'ws1'})
        mock_enter.assert_called_once_with('sid1', 'ws1')
        mock_emit.assert_called_once_with('message', {'msg': 'Someone joined ws1'}, room='ws1')

@pytest.mark.anyio
async def test_chat_message_basic():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await chat_message('sid1', {'workspace_id': ws_id, 'message': 'Hello world'})
        mock_emit.assert_called_once_with('chat_update', {'msg': 'Hello world'}, room=ws_id)

@pytest.mark.anyio
async def test_chat_message_invalid():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await chat_message('sid1', {'workspace_id': ws_id, 'message': None})
        mock_emit.assert_not_called()

        await chat_message('sid1', {'workspace_id': ws_id, 'message': 'a'*5001})
        mock_emit.assert_not_called()

@pytest.mark.anyio
async def test_chat_message_mention_agent():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit, \
         patch('app.main.call_provider_api', new_callable=AsyncMock) as mock_call, \
         patch('app.main.Session') as mock_session:

        # Setup mock DB
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        # Mock Agent
        mock_agent = MagicMock()
        mock_agent.id = uuid.uuid4()
        mock_agent.name = "TestAgent"
        mock_agent.provider = "openai"

        # Mock TokenPool
        mock_pool = MagicMock()
        from app.encryption import encrypt_token
        mock_pool.encrypted_session_token = encrypt_token("mocked_token")

        mock_db.exec.return_value.all.return_value = [(mock_agent, mock_pool)]

        mock_call.return_value = "Mock API Response"

        await chat_message('sid1', {'workspace_id': ws_id, 'message': 'Hello @TestAgent'})

        assert mock_emit.call_count == 2
        mock_emit.assert_any_call('chat_update', {'msg': 'Hello @TestAgent'}, room=ws_id)
        mock_emit.assert_any_call('chat_update', {'msg': 'Mock API Response'}, room=ws_id)
        mock_call.assert_called_once_with("openai", "mocked_token", "Hello @TestAgent")

@pytest.mark.anyio
async def test_chat_message_mention_agent_offline():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit, \
         patch('app.main.Session') as mock_session:

        # Setup mock DB
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        # Mock Agent
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"

        mock_db.exec.return_value.all.return_value = [(mock_agent, None)] # No token pool entry

        await chat_message('sid1', {'workspace_id': ws_id, 'message': 'Hello @TestAgent'})

        assert mock_emit.call_count == 2
        mock_emit.assert_any_call('chat_update', {'msg': 'Hello @TestAgent'}, room=ws_id)
        mock_emit.assert_any_call('chat_update', {'msg': 'Agent TestAgent is offline (no token available).'}, room=ws_id)

@pytest.mark.anyio
async def test_chat_message_mention_agent_api_error():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit, \
         patch('app.main.call_provider_api', new_callable=AsyncMock) as mock_call, \
         patch('app.main.Session') as mock_session:

        # Setup mock DB
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        # Mock Agent
        mock_agent = MagicMock()
        mock_agent.id = uuid.uuid4()
        mock_agent.name = "TestAgent"
        mock_agent.provider = "openai"

        # Mock TokenPool
        mock_pool = MagicMock()
        from app.encryption import encrypt_token
        mock_pool.encrypted_session_token = encrypt_token("mocked_token")

        mock_db.exec.return_value.all.return_value = [(mock_agent, mock_pool)]

        mock_call.side_effect = Exception("API error")

        await chat_message('sid1', {'workspace_id': ws_id, 'message': 'Hello @TestAgent'})

        assert mock_emit.call_count == 2
        mock_emit.assert_any_call('chat_update', {'msg': 'Hello @TestAgent'}, room=ws_id)
        mock_emit.assert_any_call('chat_update', {'msg': 'An error occurred while processing your request with TestAgent.'}, room=ws_id)

@pytest.mark.anyio
async def test_join_workspace_invalid():
    with patch.object(sio, 'enter_room') as mock_enter, \
         patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:

        # Test invalid data type
        await join_workspace('sid1', 'not a dict') # type: ignore
        mock_enter.assert_not_called()

        # Test missing workspace_id
        await join_workspace('sid1', {})
        mock_enter.assert_not_called()

        # Test workspace_id too long
        await join_workspace('sid1', {'workspace_id': 'a'*101})
        mock_enter.assert_not_called()

@pytest.mark.anyio
async def test_chat_message_invalid_data():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        # Test invalid data type
        await chat_message('sid1', 'not a dict') # type: ignore
        mock_emit.assert_not_called()

        # Test invalid workspace_id type
        await chat_message('sid1', {'workspace_id': 123, 'message': 'Hello'})
        mock_emit.assert_not_called()

        # Test workspace_id too long
        await chat_message('sid1', {'workspace_id': 'a'*101, 'message': 'Hello'})
        mock_emit.assert_not_called()

        # Test malformed UUID for workspace_id
        await chat_message('sid1', {'workspace_id': 'not-a-uuid', 'message': 'Hello'})
        mock_emit.assert_not_called()

@pytest.mark.anyio
async def test_chat_message_mention_without_valid_agents():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit, \
         patch('app.main.call_provider_api', new_callable=AsyncMock) as mock_call:

        # Test string with just "@" but no agent name attached
        await chat_message('sid1', {'workspace_id': ws_id, 'message': 'Hello @ everyone'})

        # chat_update is emitted for the original message
        mock_emit.assert_called_once_with('chat_update', {'msg': 'Hello @ everyone'}, room=ws_id)

        # But call_provider_api is not called because no valid agent names extracted
        mock_call.assert_not_called()

@pytest.mark.anyio
async def test_chat_message_mention_agent_no_names_empty():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await chat_message('sid1', {'workspace_id': ws_id, 'message': 'hello@world'})
        mock_emit.assert_called_once_with('chat_update', {'msg': 'hello@world'}, room=ws_id)
