import pytest
import uuid
from unittest.mock import patch
from sqlmodel import Session, create_engine, SQLModel
from app.main import verify_ws_auth_sync
from app.models import UserWorkspaceLink
from app.auth import create_access_token

def test_verify_ws_auth_sync_success():
    test_engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(test_engine)

    user_uuid = uuid.uuid4()
    ws_uuid = uuid.uuid4()

    with Session(test_engine) as session:
        link = UserWorkspaceLink(user_id=user_uuid, workspace_id=ws_uuid)
        session.add(link)
        session.commit()

    token = create_access_token({"sub": str(user_uuid)})

    with patch('app.main.engine', test_engine):
        assert verify_ws_auth_sync(str(ws_uuid), token) == True

def test_verify_ws_auth_sync_not_found():
    test_engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(test_engine)

    user_uuid = uuid.uuid4()
    ws_uuid = uuid.uuid4()

    token = create_access_token({"sub": str(user_uuid)})

    with patch('app.main.engine', test_engine):
        assert verify_ws_auth_sync(str(ws_uuid), token) == False

def test_verify_ws_auth_sync_exception():
    token = create_access_token({"sub": str(uuid.uuid4())})
    # invalid uuid will trigger ValueError inside try block
    assert verify_ws_auth_sync("not-a-uuid", token) == False
