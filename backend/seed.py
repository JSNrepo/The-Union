import sys
import os

# Ensure backend directory is in the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlmodel import Session, select
from app.database import engine
from app.models import Workspace, Agent, User
from app.auth import get_password_hash
import uuid

def seed():
    with Session(engine) as session:
        # Check if user exists
        user = session.exec(select(User).where(User.username == "admin")).first()
        if not user:
            user = User(username="admin", hashed_password=get_password_hash("password"))
            session.add(user)
            session.commit()
            session.refresh(user)

        # Workspaces
        ws1 = session.exec(select(Workspace).where(Workspace.name == "General")).first()
        if not ws1:
            ws1 = Workspace(name="General")
            session.add(ws1)

        ws2 = session.exec(select(Workspace).where(Workspace.name == "Engineering")).first()
        if not ws2:
            ws2 = Workspace(name="Engineering")
            session.add(ws2)

        # Agents
        agent1 = session.exec(select(Agent).where(Agent.name == "Alice's Claude")).first()
        if not agent1:
            agent1 = Agent(name="Alice's Claude", provider="claude", owner_id=user.id)
            session.add(agent1)

        agent2 = session.exec(select(Agent).where(Agent.name == "Bob's Gemini")).first()
        if not agent2:
            agent2 = Agent(name="Bob's Gemini", provider="gemini", owner_id=user.id)
            session.add(agent2)

        session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    seed()
