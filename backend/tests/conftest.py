import os

# Set environment variables before any module imports
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["UNION_MASTER_KEY"] = "test_master_key_for_encryption"
os.environ["EXTENSION_API_KEY"] = "test_extension_api_key"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"

import pytest

from typing import Generator
@pytest.fixture(autouse=True)
def setup_env() -> Generator[None, None, None]:
    yield
    # Clean up environment variables after tests if needed
