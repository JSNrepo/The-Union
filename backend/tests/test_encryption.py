import pytest
from app.encryption import encrypt_token, decrypt_token, get_encryption_key

def test_token_encryption_decryption():
    original_token = "my_super_secret_session_token_123!"

    # Encrypt the token
    encrypted = encrypt_token(original_token)

    # Make sure it's actually encrypted
    assert encrypted != original_token
    assert isinstance(encrypted, str)

    # Decrypt the token
    decrypted = decrypt_token(encrypted)

    # Make sure it matches the original
    assert decrypted == original_token

def test_encryption_key_generation():
    key1 = get_encryption_key()
    key2 = get_encryption_key()

    # Make sure the key generation is deterministic
    assert key1 == key2
    assert len(key1) > 0

import os
from unittest.mock import patch
import uuid

def test_get_encryption_key_missing_master_key():
    with patch.dict(os.environ, clear=True):
        with pytest.raises(RuntimeError, match="UNION_MASTER_KEY environment variable is not set"):
            get_encryption_key()

def test_get_encryption_key_fallback_salt():
    with patch("uuid.getnode", side_effect=Exception("Mocked exception")), \
         patch.dict(os.environ, {"UNION_MASTER_KEY": "123", "UNION_FALLBACK_SALT": "test-fallback-salt"}):
        key = get_encryption_key()
        assert len(key) > 0

def test_decrypt_invalid_token():
    with pytest.raises(ValueError, match="Invalid encryption token"):
        decrypt_token("invalid_token")
