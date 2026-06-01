import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import uuid
import os

from app.main import app, get_session
from app.models import User, Workspace, Agent

# Setup in-memory sqlite database for testing
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

def get_session_override():
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture():
    SQLModel.metadata.create_all(engine)
    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    SQLModel.metadata.drop_all(engine)

def test_register(client: TestClient):
    response = client.post("/register", json={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    assert response.json() == {"msg": "User created"}

def test_register_duplicate_username(client: TestClient):
    client.post("/register", json={"username": "dupuser", "password": "password"})
    response = client.post("/register", json={"username": "dupuser", "password": "password"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

def test_login_success(client: TestClient):
    client.post("/register", json={"username": "loginuser", "password": "password"})
    response = client.post("/login", json={"username": "loginuser", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_password(client: TestClient):
    client.post("/register", json={"username": "loginuser2", "password": "password"})
    response = client.post("/login", json={"username": "loginuser2", "password": "wrongpassword"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect username or password"}

def test_login_nonexistent_user(client: TestClient):
    response = client.post("/login", json={"username": "nonexistent", "password": "password"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Incorrect username or password"}

def test_create_and_list_workspaces(client: TestClient):
    client.post("/register", json={"username": "wsuser", "password": "password"})
    login_response = client.post("/login", json={"username": "wsuser", "password": "password"})
    token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/workspaces", json={"name": "Test Workspace"}, headers=headers)
    assert response.status_code == 200
    ws_data = response.json()
    assert ws_data["name"] == "Test Workspace"
    assert "id" in ws_data

    response2 = client.get("/workspaces", headers=headers)
    assert response2.status_code == 200
    ws_list = response2.json()
    assert len(ws_list) >= 1
    assert any(ws["name"] == "Test Workspace" for ws in ws_list)

def test_unauthorized_access(client: TestClient):
    response = client.get("/workspaces")
    assert response.status_code == 401


def test_sync_token(client: TestClient):
    # Setup user
    client.post("/register", json={"username": "syncuser", "password": "password"})
    login_response = client.post("/login", json={"username": "syncuser", "password": "password"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # We need to manually add an Agent in db since there's no endpoint to create one
    from app.main import get_session
    from app.models import Agent, User
    from sqlmodel import select

    with next(get_session_override()) as session:
        user = session.exec(select(User).where(User.username == "syncuser")).first()
        assert user is not None
        user_id = user.id
        agent_id = uuid.uuid4()
        agent = Agent(id=agent_id, name="TestAgent", owner_id=user_id, provider="openai")
        session.add(agent)
        session.commit()

    ext_api_key = os.getenv("EXTENSION_API_KEY")
    assert ext_api_key is not None
    sync_headers = {"x-api-key": ext_api_key}
    sync_data = {
        "provider": "openai",
        "token": "my-secret-token",
        "agent_id": str(agent_id),
        "owner_id": str(user_id)
    }

    response = client.post("/sync-token", json=sync_data, headers=sync_headers)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

    # Update existing token pool entry
    sync_data["token"] = "new-secret-token"
    response2 = client.post("/sync-token", json=sync_data, headers=sync_headers)
    assert response2.status_code == 200
    assert response2.json() == {"status": "success"}

def test_sync_token_invalid_api_key(client: TestClient):
    sync_data = {
        "provider": "openai",
        "token": "my-secret-token",
        "agent_id": str(uuid.uuid4()),
    }
    response = client.post("/sync-token", json=sync_data, headers={"x-api-key": "invalid_key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid API Key"}

from unittest.mock import patch
from sqlalchemy.exc import IntegrityError

def test_sync_token_integrity_error(client: TestClient):
    client.post("/register", json={"username": "syncracer", "password": "password"})

    from app.main import get_session
    from app.models import Agent, User
    from sqlmodel import select

    with next(get_session_override()) as session:
        user = session.exec(select(User).where(User.username == "syncracer")).first()
        assert user is not None
        user_id = user.id
        agent_id = uuid.uuid4()
        agent = Agent(id=agent_id, name="RaceAgent", owner_id=user_id, provider="openai")
        session.add(agent)
        session.commit()

    ext_api_key = os.getenv("EXTENSION_API_KEY")
    assert ext_api_key is not None
    sync_headers = {"x-api-key": ext_api_key}
    sync_data = {
        "provider": "openai",
        "token": "my-secret-token",
        "agent_id": str(agent_id),
    }

    with patch("app.main.Session.commit", side_effect=IntegrityError("mocked", "params", "orig")) as mock_commit: # type: ignore
        response = client.post("/sync-token", json=sync_data, headers=sync_headers)

    assert response.status_code == 409
    assert response.json() == {"detail": "Token for this agent already exists"}

def test_sync_token_agent_not_found(client: TestClient):
    ext_api_key = os.getenv("EXTENSION_API_KEY")
    assert ext_api_key is not None
    sync_headers = {"x-api-key": ext_api_key}
    sync_data = {
        "provider": "openai",
        "token": "my-secret-token",
        "agent_id": str(uuid.uuid4()),
    }
    response = client.post("/sync-token", json=sync_data, headers=sync_headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Agent not found"}


def test_list_agents(client: TestClient):
    client.post("/register", json={"username": "agentuser", "password": "password"})
    login_response = client.post("/login", json={"username": "agentuser", "password": "password"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import get_session
    from app.models import Agent, User
    from sqlmodel import select

    with next(get_session_override()) as session:
        user = session.exec(select(User).where(User.username == "agentuser")).first()
        assert user is not None
        agent_id = uuid.uuid4()
        agent = Agent(id=agent_id, name="TestAgent2", owner_id=user.id, provider="openai")
        session.add(agent)
        session.commit()

    response = client.get("/agents", headers=headers)
    assert response.status_code == 200
    agents_list = response.json()
    assert len(agents_list) >= 1
    assert any(a["name"] == "TestAgent2" for a in agents_list)

from unittest.mock import patch, AsyncMock

def test_proxy_request(client: TestClient):
    client.post("/register", json={"username": "proxyuser", "password": "password"})
    login_response = client.post("/login", json={"username": "proxyuser", "password": "password"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import get_session
    from app.models import Agent, User, TokenPool
    from app.encryption import encrypt_token
    from sqlmodel import select

    with next(get_session_override()) as session:
        user = session.exec(select(User).where(User.username == "proxyuser")).first()
        assert user is not None
        agent_id = uuid.uuid4()
        agent = Agent(id=agent_id, name="ProxyTestAgent", owner_id=user.id, provider="openai")
        session.add(agent)

        # Add a TokenPool entry
        pool_entry = TokenPool(agent_id=agent.id, owner_user_id=user.id, encrypted_session_token=encrypt_token("mocked_token"))
        session.add(pool_entry)
        session.commit()

    # Mock call_provider_api since we don't want to make real API calls
    with patch('app.main.call_provider_api', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "Mocked API Response"

        # Valid Request
        proxy_data = {"agent_id": str(agent_id), "prompt": "Hello!"}
        response = client.post("/proxy-request", json=proxy_data, headers=headers)
        assert response.status_code == 200
        assert response.json() == {"response": "Mocked API Response"}
        mock_call.assert_called_once_with("openai", "mocked_token", "Hello!")

    # Agent Not Found
    response = client.post("/proxy-request", json={"agent_id": str(uuid.uuid4()), "prompt": "Hello!"}, headers=headers)
    assert response.status_code == 404
    assert response.json() == {"detail": "Agent not found"}

def test_proxy_request_unauthorized(client: TestClient):
    # Register two users
    client.post("/register", json={"username": "proxyuser_unauth1", "password": "password"})
    client.post("/register", json={"username": "proxyuser_unauth2", "password": "password"})

    # Login as user 2
    login_response = client.post("/login", json={"username": "proxyuser_unauth2", "password": "password"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import get_session
    from app.models import Agent, User, TokenPool
    from app.encryption import encrypt_token
    from sqlmodel import select

    with next(get_session_override()) as session:
        # Get user 1
        user1 = session.exec(select(User).where(User.username == "proxyuser_unauth1")).first()
        assert user1 is not None

        # Create an agent owned by user 1
        agent_id = uuid.uuid4()
        agent = Agent(id=agent_id, name="UnauthAgent", owner_id=user1.id, provider="openai")
        session.add(agent)

        # Add a token pool entry
        pool_entry = TokenPool(agent_id=agent.id, owner_user_id=user1.id, encrypted_session_token=encrypt_token("mocked_token"))
        session.add(pool_entry)
        session.commit()

    # User 2 tries to proxy request to User 1's agent
    response = client.post("/proxy-request", json={"agent_id": str(agent_id), "prompt": "Hello!"}, headers=headers)
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized to access this agent"}

def test_proxy_request_no_token(client: TestClient):
    client.post("/register", json={"username": "proxynotoken", "password": "password"})
    login_response = client.post("/login", json={"username": "proxynotoken", "password": "password"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import get_session
    from app.models import Agent, User
    from sqlmodel import select

    with next(get_session_override()) as session:
        user = session.exec(select(User).where(User.username == "proxynotoken")).first()
        assert user is not None
        agent_id = uuid.uuid4()
        agent = Agent(id=agent_id, name="NoTokenAgent", owner_id=user.id, provider="openai")
        session.add(agent)
        session.commit()

    response = client.post("/proxy-request", json={"agent_id": str(agent_id), "prompt": "Hello!"}, headers=headers)
    assert response.status_code == 400
    assert response.json() == {"detail": "No token available for this agent"}

def test_proxy_request_api_error(client: TestClient):
    client.post("/register", json={"username": "proxyuser2", "password": "password"})
    login_response = client.post("/login", json={"username": "proxyuser2", "password": "password"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from app.main import get_session
    from app.models import Agent, User, TokenPool
    from app.encryption import encrypt_token
    from sqlmodel import select

    with next(get_session_override()) as session:
        user = session.exec(select(User).where(User.username == "proxyuser2")).first()
        assert user is not None
        agent = Agent(id=uuid.uuid4(), name="ProxyTestAgent2", owner_id=user.id, provider="openai")
        session.add(agent)
        pool_entry = TokenPool(agent_id=agent.id, owner_user_id=user.id, encrypted_session_token=encrypt_token("mocked_token"))
        session.add(pool_entry)
        session.commit()
        agent_id = agent.id

    with patch('app.main.call_provider_api', new_callable=AsyncMock) as mock_call:
        mock_call.side_effect = Exception("API failure")
        response = client.post("/proxy-request", json={"agent_id": str(agent_id), "prompt": "Hello!"}, headers=headers)
        assert response.status_code == 500
        assert response.json() == {"detail": "An internal error occurred while communicating with the AI provider."}

def test_sync_token_missing_api_key_env(client: TestClient):
    with patch("os.getenv", return_value=None):
        response = client.post(
            "/sync-token",
            json={
                "provider": "openai",
                "token": "sk-123",
                "agent_id": str(uuid.uuid4()),
                "owner_id": str(uuid.uuid4())
            },
            headers={"x-api-key": "some-key"}
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "Server configuration error"

def test_register_integrity_error(client: TestClient):
    from sqlalchemy.exc import IntegrityError
    from unittest.mock import patch
    with patch("sqlmodel.Session.commit", side_effect=IntegrityError("statement", "params", "orig")): # type: ignore
        response = client.post("/register", json={"username": "race_condition_user", "password": "password123"})
        assert response.status_code == 400
        assert response.json() == {"detail": "Username already registered"}
