from cryptography.fernet import Fernet
import os
import hashlib
import base64
import uuid

def get_encryption_key() -> bytes:
    master_key = os.getenv("UNION_MASTER_KEY")
    if not master_key:
        raise RuntimeError("UNION_MASTER_KEY environment variable is not set")

    # Optional hardware salt. If not available, we use a fallback.
    try:
        hw_salt = str(uuid.getnode())
    except Exception:
        hw_salt = os.getenv("UNION_FALLBACK_SALT", "default-fallback-salt")

    combined = (master_key + hw_salt).encode('utf-8')
    # Use SHA256 to ensure we get a 32-byte key, then base64 encode it for Fernet
    digest = hashlib.sha256(combined).digest()
    return base64.urlsafe_b64encode(digest)

fernet = Fernet(get_encryption_key())

def encrypt_token(token: str) -> str:
    return fernet.encrypt(token.encode('utf-8')).decode('utf-8')

def decrypt_token(encrypted_token: str) -> str:
    return fernet.decrypt(encrypted_token.encode('utf-8')).decode('utf-8')
