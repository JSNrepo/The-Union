from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import User, TokenPool, Agent, Workspace, UserWorkspaceLink
from .auth import get_password_hash, verify_password, create_access_token
from .encryption import encrypt_token, decrypt_token
from pydantic import BaseModel
import socketio
import os
import uuid

app = FastAPI(title="The Union")
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Sync endpoint for Chrome Extension
class SyncTokenRequest(BaseModel):
    provider: str
    token: str
    agent_id: uuid.UUID

import hmac

@app.post("/sync-token")
def sync_token(req: SyncTokenRequest, x_api_key: str = Header(None), session: Session = Depends(get_session)):
    expected_api_key = os.getenv("EXTENSION_API_KEY")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="Server configuration error")

    if not x_api_key or not hmac.compare_digest(x_api_key.encode('utf-8'), expected_api_key.encode('utf-8')):
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # In a real scenario, the extension would also pass user context.
    # For MVP, we'll assign to the first user or require owner_id in the request.
    agent = session.exec(select(Agent).where(Agent.id == req.agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    encrypted = encrypt_token(req.token)

    # Update or create token pool entry
    pool_entry = session.exec(select(TokenPool).where(TokenPool.agent_id == agent.id)).first()
    if pool_entry:
        pool_entry.encrypted_session_token = encrypted
    else:
        pool_entry = TokenPool(agent_id=agent.id, owner_user_id=agent.owner_id, encrypted_session_token=encrypted)
        session.add(pool_entry)

    session.commit()
    return {"status": "success"}

# Socket.IO Event Handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def join_workspace(sid, data):
    workspace_id = data.get('workspace_id')
    sio.enter_room(sid, workspace_id)
    await sio.emit('message', {'msg': f'Someone joined {workspace_id}'}, room=workspace_id)

@sio.event
async def chat_message(sid, data):
    workspace_id = data.get('workspace_id')
    message = data.get('message')
    # Later: intercept if tagging an agent and use the token pool
    await sio.emit('chat_update', {'msg': message}, room=workspace_id)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

# Basic Auth routes to test
class UserCreate(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    session.add(new_user)
    session.commit()
    return {"msg": "User created"}

# Mount socket app
app.mount("/", socket_app)

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(req: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == req.username)).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

class ProxyRequest(BaseModel):
    agent_id: uuid.UUID
    prompt: str

@app.post("/proxy-request")
def proxy_request(req: ProxyRequest, session: Session = Depends(get_session)):
    agent = session.exec(select(Agent).where(Agent.id == req.agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    pool_entry = session.exec(select(TokenPool).where(TokenPool.agent_id == agent.id)).first()
    if not pool_entry:
        raise HTTPException(status_code=400, detail="No token available for this agent")

    token = decrypt_token(pool_entry.encrypted_session_token)

    # Mock proxying request to Claude/Gemini
    print(f"Proxying request to {agent.provider} using token: {token[:10]}...")

    # In a real scenario we'd use httpx to hit the provider API
    mock_response = f"Simulated response from {agent.provider} agent '{agent.name}' for prompt: {req.prompt}"

    return {"response": mock_response}
