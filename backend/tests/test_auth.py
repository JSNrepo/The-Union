import os
import pytest
import jwt
from datetime import datetime, timezone, timedelta
from app.auth import get_password_hash, verify_password, create_access_token, ALGORITHM

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

def test_create_access_token_with_expiry():
    data = {"sub": "testuser"}
    expires_delta = timedelta(minutes=5)
    token = create_access_token(data, expires_delta=expires_delta)

    secret_key = os.getenv("SECRET_KEY")
    decoded = jwt.decode(token, secret_key, algorithms=[ALGORITHM])

    assert decoded.get("sub") == "testuser"
    assert "exp" in decoded
