from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional
import uuid

class UserWorkspaceLink(SQLModel, table=True):
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", primary_key=True)

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    workspaces: List["Workspace"] = Relationship(back_populates="members", link_model=UserWorkspaceLink)
    agents: List["Agent"] = Relationship(back_populates="owner")

class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    members: List["User"] = Relationship(back_populates="workspaces", link_model=UserWorkspaceLink)

class Agent(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    owner_id: uuid.UUID = Field(foreign_key="user.id")
    owner: User = Relationship(back_populates="agents")
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id")
    provider: str # e.g. claude, gemini

class TokenPool(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: uuid.UUID = Field(foreign_key="agent.id")
    owner_user_id: uuid.UUID = Field(foreign_key="user.id")
    encrypted_session_token: str
