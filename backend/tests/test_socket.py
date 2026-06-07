import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import join_workspace, chat_message, sio, call_provider_api, connect, disconnect
import uuid

@pytest.fixture(autouse=True)
def mock_ws_auth():
    mock_user_uuid = uuid.uuid4()
    with patch('app.main.verify_ws_auth_sync', return_value=mock_user_uuid), \
         patch.object(sio, 'get_session', new_callable=AsyncMock) as mock_get_session, \
         patch.object(sio, 'session') as mock_session:
        class UniversalSet(set):
            def __contains__(self, item):
                return True
            def add(self, item):
                pass

        mock_get_session.return_value = {'workspaces': UniversalSet(), 'user_id': str(mock_user_uuid)}

        # We need a proper context manager mock for sio.session
        class MockSessionContext:
            def __init__(self, sid):
                self.sid = sid
                self.data = {'workspaces': UniversalSet(), 'user_id': str(mock_user_uuid)}
            async def __aenter__(self):
                return self.data
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        mock_session.side_effect = lambda sid: MockSessionContext(sid)

        yield

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
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'enter_room') as mock_enter, \
         patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await join_workspace('sid1', {'workspace_id': ws_id, 'token': 'mock'})
        mock_enter.assert_called_once_with('sid1', ws_id)
        mock_emit.assert_called_once_with('message', {'msg': f'Someone joined {ws_id}'}, room=ws_id)

@pytest.mark.anyio
async def test_chat_message_basic():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'Hello world'})
        mock_emit.assert_called_once_with('chat_update', {'msg': 'Hello world'}, room=ws_id)

@pytest.mark.anyio
async def test_chat_message_invalid():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': None})
        mock_emit.assert_not_called()

        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'a'*5001})
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

        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'Hello @TestAgent'})

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

        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'Hello @TestAgent'})

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

        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'Hello @TestAgent'})

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

        # Test malformed UUID for workspace_id
        await join_workspace('sid1', {'workspace_id': 'not-a-uuid'})
        mock_enter.assert_not_called()


@pytest.mark.anyio
async def test_join_workspace_unauthorized():
    ws_id = str(uuid.uuid4())
    with patch('app.main.verify_ws_auth_sync', return_value=None), \
         patch.object(sio, 'enter_room') as mock_enter, \
         patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit:
        await join_workspace('sid1', {'workspace_id': ws_id, 'token': 'mock'})
        mock_enter.assert_not_called()
        mock_emit.assert_not_called()

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
         patch('app.main.call_provider_api', new_callable=AsyncMock) as mock_call, \
         patch('app.main.Session') as mock_session:

        # Setup mock DB
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_db.exec.return_value.all.return_value = []

        # Test string with just "@" but no agent name attached
        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'Hello @ everyone'})

        # chat_update is emitted for the original message
        mock_emit.assert_called_once_with('chat_update', {'msg': 'Hello @ everyone'}, room=ws_id)

        # But call_provider_api is not called because no valid agent names extracted
        mock_call.assert_not_called()

@pytest.mark.anyio
async def test_chat_message_mention_agent_no_names_empty():
    ws_id = str(uuid.uuid4())
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit, \
         patch('app.main.Session') as mock_session:

        # Setup mock DB
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_db.exec.return_value.all.return_value = []

        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'hello@world'})
        mock_emit.assert_called_once_with('chat_update', {'msg': 'hello@world'}, room=ws_id)

@pytest.mark.anyio
async def test_chat_message_mention_agent_invalid_user_id():
    ws_id = str(uuid.uuid4())
    # Override get_session to return an invalid user_id
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit, \
         patch.object(sio, 'get_session', new_callable=AsyncMock) as mock_get_session, \
         patch('app.main.call_provider_api', new_callable=AsyncMock) as mock_call:

        class UniversalSet(set):
            def __contains__(self, item):
                return True
            def add(self, item):
                pass

        mock_get_session.return_value = {'workspaces': UniversalSet(), 'user_id': 'invalid-uuid'}

        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'Hello @TestAgent'})

        # Message is emitted, but agent proxying is skipped because of invalid user_id
        mock_emit.assert_called_once_with('chat_update', {'msg': 'Hello @TestAgent'}, room=ws_id)
        mock_call.assert_not_called()

@pytest.mark.anyio
async def test_chat_message_unauthorized_workspace():
    ws_id = str(uuid.uuid4())
    # Note: the mock_get_session fixture from conftest returns a UniversalSet which contains everything
    # So we need to override the get_session mock specifically for this test
    with patch.object(sio, 'emit', new_callable=AsyncMock) as mock_emit, \
         patch.object(sio, 'get_session', new_callable=AsyncMock) as mock_get_session:

        # This user has no authorized workspaces
        mock_get_session.return_value = {'workspaces': set()}

        await chat_message('sid1', {'workspace_id': ws_id, 'token': 'mock', 'message': 'Hello world'})

        # Message should not be emitted because the user hasn't joined the workspace
        mock_emit.assert_not_called()
