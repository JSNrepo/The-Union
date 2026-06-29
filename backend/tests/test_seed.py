import pytest
from unittest.mock import patch
from sqlmodel import Session, select, SQLModel, create_engine
from seed import seed
from app.models import User, Workspace, Agent
from app.database import engine

def test_seed_creates_records() -> None:
    # Setup in-memory sqlite database for testing
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)

    # Patch the engine in the seed module
    with patch("seed.engine", test_engine):
        seed()

        with Session(test_engine) as session:
            # Check user
            user = session.exec(select(User).where(User.username == "admin")).first()
            assert user is not None

            # Check workspaces
            ws1 = session.exec(select(Workspace).where(Workspace.name == "General")).first()
            assert ws1 is not None

            ws2 = session.exec(select(Workspace).where(Workspace.name == "Engineering")).first()
            assert ws2 is not None

            # Check agents
            agent1 = session.exec(select(Agent).where(Agent.name == "Alice's Claude")).first()
            assert agent1 is not None

            agent2 = session.exec(select(Agent).where(Agent.name == "Bob's Gemini")).first()
            assert agent2 is not None

def test_seed_idempotent() -> None:
    # Setup in-memory sqlite database for testing
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)

    with patch("seed.engine", test_engine):
        # Run seed twice
        seed()
        seed()

        with Session(test_engine) as session:
            # Check that there is only one user
            users = session.exec(select(User)).all()
            assert len(users) == 1

            # Check workspaces
            workspaces = session.exec(select(Workspace)).all()
            assert len(workspaces) == 2

            # Check agents
            agents = session.exec(select(Agent)).all()
            assert len(agents) == 2

def test_seed_main_execution() -> None:
    import runpy
    test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)

    # When runpy.run_module executes "seed.py", it re-imports app.database.engine.
    # Patching "seed.engine" here only patches it in the *already imported* seed module.
    # We need to patch "app.database.engine" so when the fresh module imports it, it gets the mock.
    with patch("app.database.engine", test_engine):
        runpy.run_module("seed", run_name="__main__")

        # Verify the seed actually ran by checking the database contents
        with Session(test_engine) as session:
            assert session.exec(select(User).where(User.username == "admin")).first() is not None
