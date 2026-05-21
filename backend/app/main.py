from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import User, TokenPool, Agent, Workspace, UserWorkspaceLink
from .auth import get_password_hash, verify_password, create_access_token, get_current_user
from .encryption import encrypt_token, decrypt_token
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import socketio
import os
import uuid
import httpx

app = FastAPI(title="The Union")

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=ALLOWED_ORIGINS)
socket_app = socketio.ASGIApp(sio, socketio_path="")

# ⚡ Bolt Optimization: Use a global HTTP transport to share the TCP connection pool
# safely across requests without sharing stateful data like cookies.
shared_transport = httpx.AsyncHTTPTransport()

@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()

@app.on_event("shutdown")
async def on_shutdown() -> None:
    await shared_transport.aclose()

# Sync endpoint for Chrome Extension
class SyncTokenRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    token: str = Field(..., min_length=1, max_length=4000)
    agent_id: uuid.UUID
    owner_id: uuid.UUID | None = None

import hmac
from typing import Any

@app.post("/sync-token")
def sync_token(req: SyncTokenRequest, x_api_key: str = Header(None), session: Session = Depends(get_session)) -> dict[str, str]:
    expected_api_key = os.getenv("EXTENSION_API_KEY")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="Server configuration error")

    if not x_api_key or not hmac.compare_digest(x_api_key.encode('utf-8'), expected_api_key.encode('utf-8')):
        raise HTTPException(status_code=403, detail="Invalid API Key")

    agent = session.exec(select(Agent).where(Agent.id == req.agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    owner_id = req.owner_id or agent.owner_id

    encrypted = encrypt_token(req.token)

    # Update or create token pool entry
    pool_entry = session.exec(select(TokenPool).where(TokenPool.agent_id == agent.id)).first()
    if pool_entry:
        pool_entry.encrypted_session_token = encrypted
    else:
        pool_entry = TokenPool(agent_id=agent.id, owner_user_id=owner_id, encrypted_session_token=encrypted)
        session.add(pool_entry)

    session.commit()
    return {"status": "success"}

# Socket.IO Event Handlers
@sio.event
async def connect(sid: str, environ: dict) -> None:
    print(f"Client connected: {sid}")

@sio.event
async def join_workspace(sid: str, data: dict) -> None:
    # 🛡️ Sentinel: Validate input type and length to prevent unhandled exceptions and DoS
    if not isinstance(data, dict):
        return
    workspace_id = data.get('workspace_id')
    if not isinstance(workspace_id, str) or len(workspace_id) > 100:
        return

    await sio.enter_room(sid, workspace_id)
    await sio.emit('message', {'msg': f'Someone joined {workspace_id}'}, room=workspace_id)

async def call_provider_api(provider: str, token: str, prompt: str) -> str:
    async with httpx.AsyncClient(transport=shared_transport) as client:
        if provider == "openai":
            res = await client.post(
                    "https://chatgpt.com/backend-api/conversation",
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={
                        "action": "next",
                        "messages": [{"id": str(uuid.uuid4()), "role": "user", "content": {"content_type": "text", "parts": [prompt]}}],
                        "model": "text-davinci-002-render-sha"
                    }
                )
            return f"OpenAI: {res.text[:100]}..."
        elif provider == "claude":
            res = await client.post(
                    "https://claude.ai/api/append_message",
                    headers={"Cookie": f"sessionKey={token}", "Content-Type": "application/json"},
                    json={"prompt": prompt}
                )
            return f"Claude: {res.text[:100]}..."
        elif provider == "gemini":
            res = await client.post(
                    "https://gemini.google.com/_/BardChat/data/batchexecute",
                    headers={"Cookie": f"__Secure-1PSID={token}", "Content-Type": "application/x-www-form-urlencoded"},
                    data={"f.req": prompt}
                )
            return f"Gemini: {res.text[:100]}..."
        else:
            raise Exception("Unsupported provider")

@sio.event
async def chat_message(sid: str, data: dict) -> None:
    # 🛡️ Sentinel: Validate input type and length to prevent unhandled exceptions and DoS
    if not isinstance(data, dict):
        return

    workspace_id = data.get('workspace_id')
    message = data.get('message')

    if not isinstance(workspace_id, str) or len(workspace_id) > 100:
        return

    if not isinstance(message, str) or len(message) > 5000:
        return

    await sio.emit('chat_update', {'msg': message}, room=workspace_id)

    # Intercept if tagging an agent
    if message and "@" in message:
        # Simple extraction for MVP (e.g. "@Claude")
        words = message.split()
        for word in words:
            if word.startswith("@"):
                agent_name = word[1:]
                # We need a db session
                from .database import engine

                # ⚡ Bolt Optimization: Extract token and provider inside DB session and close it
                # immediately to avoid connection pool exhaustion during slow LLM API calls.
                agent_info = None
                with Session(engine) as session:
                    # ⚡ Bolt Optimization: Use a JOIN query to fetch both the agent and their token pool entry
                    # simultaneously, eliminating the N+1 sequential database queries in the hot path.
                    result = session.exec(
                        select(Agent, TokenPool)
                        .join(TokenPool, Agent.id == TokenPool.agent_id, isouter=True)
                        .where(Agent.name == agent_name)
                    ).first()
                    if result:
                        agent, pool_entry = result
                        if pool_entry:
                            token = decrypt_token(pool_entry.encrypted_session_token)
                            agent_info = {"name": agent.name, "provider": agent.provider, "token": token}
                        else:
                            agent_info = {"name": agent.name, "offline": True}

                if agent_info:
                    if agent_info.get("offline"):
                        await sio.emit('chat_update', {'msg': f"Agent {agent_info['name']} is offline (no token available)."}, room=workspace_id)
                    else:
                        print(f"Intercepted message for {agent_info['name']}, proxying request...")
                        try:
                            ai_response = await call_provider_api(agent_info["provider"], agent_info["token"], message)
                            await sio.emit('chat_update', {'msg': ai_response}, room=workspace_id)
                        except Exception as e:
                            print(f"Error calling provider for agent {agent_info['name']}: {str(e)}") # Secure logging
                            await sio.emit('chat_update', {'msg': f"An error occurred while processing your request with {agent_info['name']}."}, room=workspace_id)

@sio.event
async def disconnect(sid: str) -> None:
    print(f"Client disconnected: {sid}")

# Basic Auth routes to test
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

@app.post("/register")
def register(user: UserCreate, session: Session = Depends(get_session)) -> dict[str, str]:
    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    session.add(new_user)
    session.commit()
    return {"msg": "User created"}

# Workspaces
class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

@app.post("/workspaces")
def create_workspace(req: WorkspaceCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> Workspace:
    ws = Workspace(name=req.name)
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws

@app.get("/workspaces")
def list_workspaces(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> list[Workspace]:
    workspaces = session.exec(select(Workspace)).all()
    return list(workspaces)

@app.get("/agents")
def list_agents(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> list[Agent]:
    agents = session.exec(select(Agent)).all()
    return list(agents)

# Mount socket app
app.mount("/socket.io", socket_app)

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)

@app.post("/login")
def login(req: LoginRequest, session: Session = Depends(get_session)) -> dict[str, str]:
    user = session.exec(select(User).where(User.username == req.username)).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

class ProxyRequest(BaseModel):
    agent_id: uuid.UUID
    prompt: str = Field(..., min_length=1, max_length=5000)

@app.post("/proxy-request")
async def proxy_request(req: ProxyRequest, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> dict[str, str]:
    agent = session.exec(select(Agent).where(Agent.id == req.agent_id)).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    pool_entry = session.exec(select(TokenPool).where(TokenPool.agent_id == agent.id)).first()
    if not pool_entry:
        raise HTTPException(status_code=400, detail="No token available for this agent")

    token = decrypt_token(pool_entry.encrypted_session_token)

    print(f"Proxying request to {agent.provider} using token: {token[:10]}...")

    try:
        response_text = await call_provider_api(agent.provider, token, req.prompt)
        return {"response": response_text}
    except Exception as e:
        print(f"Proxy request error for agent {agent.id}: {str(e)}") # Secure logging
        raise HTTPException(status_code=500, detail="An internal error occurred while communicating with the AI provider.")
