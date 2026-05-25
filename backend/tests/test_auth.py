import os
import pytest
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from unittest.mock import MagicMock
from app.auth import get_password_hash, verify_password, create_access_token, ALGORITHM, get_current_user
from app.models import User

def test_password_hashing():
    password = "supersecretpassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data)

    # decode the token to verify its contents
    secret_key = os.getenv("SECRET_KEY")
    decoded = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

    assert decoded.get("sub") == "testuser"
    assert "exp" in decoded

def test_get_current_user_invalid_token():
    mock_session = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        get_current_user("invalid.token.string", session=mock_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

def test_get_current_user_missing_sub():
    # Token without 'sub' claim
    data = {"other": "data"}
    token = create_access_token(data)
    mock_session = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, session=mock_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"

def test_get_current_user_not_found():
    user_id = str(uuid.uuid4())
    token = create_access_token({"sub": user_id})
    mock_session = MagicMock()
    mock_session.get.return_value = None  # Simulate user not found

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, session=mock_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Could not validate credentials"

def test_get_current_user_success():
    user_id = str(uuid.uuid4())
    token = create_access_token({"sub": user_id})

    mock_user = User(id=uuid.UUID(user_id), username="testuser", hashed_password="hashedpassword")
    mock_session = MagicMock()
    mock_session.get.return_value = mock_user

    user = get_current_user(token, session=mock_session)

    assert user == mock_user
    mock_session.get.assert_called_once_with(User, uuid.UUID(user_id))

def test_create_access_token_with_expiry():
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=5)
    token = create_access_token(data, expires_delta=expires_delta)

    secret_key = os.getenv("SECRET_KEY")
    decoded = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

    assert decoded.get("sub") == "testuser"
    assert "exp" in decoded

def test_auth_missing_secret_key():
    import importlib
    import os
    import app.auth

    # Temporarily remove SECRET_KEY
    original_secret = os.getenv("SECRET_KEY")
    if "SECRET_KEY" in os.environ:
        del os.environ["SECRET_KEY"]

    with pytest.raises(RuntimeError) as exc_info:
        importlib.reload(app.auth)

    assert "SECRET_KEY environment variable is not set" in str(exc_info.value)

    # Restore SECRET_KEY
    if original_secret is not None:
        os.environ["SECRET_KEY"] = original_secret

    # Reload again to restore module state for subsequent tests
    importlib.reload(app.auth)
