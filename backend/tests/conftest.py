import os

# Set environment variables before any module imports
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["UNION_MASTER_KEY"] = "test_master_key_for_encryption"
os.environ["EXTENSION_API_KEY"] = "test_extension_api_key"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

import pytest

@pytest.fixture(autouse=True)
def setup_env():
    yield
    # Clean up environment variables after tests if needed
