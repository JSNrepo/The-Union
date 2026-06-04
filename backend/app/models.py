from sqlmodel import Field, SQLModel, Relationship
from typing import List, Optional
import uuid

class UserWorkspaceLink(SQLModel, table=True):
    # ⚡ Bolt Optimization: Add index to foreign keys to prevent full table scans during relation traversals
    user_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True, index=True)
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", primary_key=True, index=True)

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    workspaces: List["Workspace"] = Relationship(back_populates="members", link_model=UserWorkspaceLink)
    agents: List["Agent"] = Relationship(back_populates="owner")

class Workspace(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)
    members: List["User"] = Relationship(back_populates="workspaces", link_model=UserWorkspaceLink)

class Agent(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # ⚡ Bolt Optimization: Add index to name field as it is queried frequently during chat interception
    name: str = Field(index=True)
    # ⚡ Bolt Optimization: Add index to owner_id to prevent full table scans when listing a user's agents
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    owner: User = Relationship(back_populates="agents")
    # ⚡ Bolt Optimization: Add index to foreign key to prevent full table scans when filtering agents by workspace
    workspace_id: Optional[uuid.UUID] = Field(default=None, foreign_key="workspace.id", index=True)
    provider: str # e.g. claude, gemini

class TokenPool(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # ⚡ Bolt Optimization: Add unique index to agent_id to speed up token lookups and enforce 1:1 mapping
    agent_id: uuid.UUID = Field(foreign_key="agent.id", index=True, unique=True)
    # ⚡ Bolt Optimization: Add index to foreign key to prevent full table scans when querying or cascading deletes
    owner_user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    encrypted_session_token: str
