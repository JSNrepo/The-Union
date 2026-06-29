import pytest
from app.database import get_session, create_db_and_tables, engine
from sqlmodel import Session
from unittest.mock import patch

def test_get_session() -> None:
    generator = get_session()
    session = next(generator)
    assert isinstance(session, Session)
    try:
        next(generator)
    except StopIteration:
        pass

from typing import Any
@patch("app.database.SQLModel.metadata.create_all")
def test_create_db_and_tables(mock_create_all: Any) -> None:
    create_db_and_tables()
    mock_create_all.assert_called_once_with(engine)
