from fastapi import FastAPI, Depends, HTTPException, status, Header, Request, Response
from contextlib import asynccontextmanager
from sqlmodel import Session, select, col
from sqlalchemy.exc import IntegrityError
from .database import create_db_and_tables, get_session, engine
from .models import User, TokenPool, Agent, Workspace, UserWorkspaceLink
from .auth import get_password_hash, verify_password, create_access_token, get_current_user_id, SECRET_KEY, ALGORITHM, DUMMY_HASH
from .encryption import encrypt_token, decrypt_token
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, field_validator
import socketio
import os
import asyncio
import uuid
import threading
from typing import AsyncIterator, Any, Callable, Awaitable
import httpx
import jwt
import time


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    yield
    await shared_transport.aclose()

app = FastAPI(title="The Union", lifespan=lifespan)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

# ⚡ Bolt Optimization: Add GZip middleware to compress request/response payloads
# This significantly reduces payload sizes for large API responses (like workspace/agent lists),
# lowering bandwidth usage and improving load times over slow networks.
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 🛡️ Sentinel: Add security headers middleware to defend against clickjacking,
# MIME-sniffing, and XSS attacks, and to enforce HTTPS connections.
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

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



# Sync endpoint for Chrome Extension
class SyncTokenRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    token: str = Field(..., min_length=1, max_length=4000)
    agent_id: uuid.UUID

import hmac
from typing import Any

@app.post("/sync-token")
def sync_token(req: SyncTokenRequest, x_api_key: str | None = Header(default=None), session: Session = Depends(get_session)) -> dict[str, str]:
    expected_api_key = os.getenv("EXTENSION_API_KEY")
    if not expected_api_key:
        raise HTTPException(status_code=500, detail="Server configuration error")

    if not x_api_key or not hmac.compare_digest(x_api_key.encode('utf-8'), expected_api_key.encode('utf-8')):
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # ⚡ Bolt Optimization: Use a JOIN query to fetch both the agent and their token pool entry
    # simultaneously, eliminating the N+1 sequential database queries.
    result = session.exec(
        select(Agent, TokenPool)
        .join(TokenPool, isouter=True)
        .where(Agent.id == req.agent_id)
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent, pool_entry = result

    encrypted = encrypt_token(req.token)
    if pool_entry:
        pool_entry.encrypted_session_token = encrypted
    else:
        # 🛡️ Sentinel: Fix IDOR vulnerability by always using the agent's actual owner_id
        # instead of trusting an unvalidated owner_id from the client request.
        pool_entry = TokenPool(agent_id=agent.id, owner_user_id=agent.owner_id, encrypted_session_token=encrypted)
        session.add(pool_entry)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Token for this agent already exists")
    return {"status": "success"}

# Socket.IO Event Handlers
@sio.event  # type: ignore[untyped-decorator]
async def connect(sid: str, environ: dict[str, Any]) -> None:
    print(f"Client connected: {sid}")

def verify_ws_auth_sync(workspace_id: str, token: str) -> uuid.UUID | None:
    try:
        ws_uuid = uuid.UUID(workspace_id)
        user_uuid = uuid.UUID(jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]).get("sub"))
        with Session(engine) as session:
            if session.get(UserWorkspaceLink, (user_uuid, ws_uuid)) is not None:
                return user_uuid
            return None
    except (jwt.PyJWTError, ValueError, TypeError, AttributeError):
        print("WebSocket auth error: Invalid token or workspace ID")
        return None

@sio.event  # type: ignore[untyped-decorator]
async def join_workspace(sid: str, data: dict[str, Any]) -> None:
    # 🛡️ Sentinel: Validate input type and length to prevent unhandled exceptions and DoS
    if not isinstance(data, dict):
        return
    workspace_id = data.get('workspace_id')
    token = data.get('token')
    if not isinstance(workspace_id, str) or len(workspace_id) > 100 or not isinstance(token, str):
        return

    user_uuid = await asyncio.to_thread(verify_ws_auth_sync, workspace_id, token)
    if user_uuid is None:
        return

    async with sio.session(sid) as session:
        auth_workspaces = session.get('workspaces', set())
        auth_workspaces.add(workspace_id)
        session['workspaces'] = auth_workspaces
        session['user_id'] = str(user_uuid)

    await sio.enter_room(sid, workspace_id)
    await sio.emit('message', {'msg': f'Someone joined {workspace_id}'}, room=workspace_id)

async def call_provider_api(provider: str, token: str, prompt: str) -> str:
    # 🛡️ Sentinel: Add explicit timeout to prevent external API hangs from exhausting resources
    async with httpx.AsyncClient(transport=shared_transport, timeout=10.0) as client:
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
            res.raise_for_status()
            return f"OpenAI: {res.text[:100]}..."
        elif provider == "claude":
            res = await client.post(
                    "https://claude.ai/api/append_message",
                    headers={"Cookie": f"sessionKey={token}", "Content-Type": "application/json"},
                    json={"prompt": prompt}
                )
            res.raise_for_status()
            return f"Claude: {res.text[:100]}..."
        elif provider == "gemini":
            res = await client.post(
                    "https://gemini.google.com/_/BardChat/data/batchexecute",
                    headers={"Cookie": f"__Secure-1PSID={token}", "Content-Type": "application/x-www-form-urlencoded"},
                    data={"f.req": prompt}
                )
            res.raise_for_status()
            return f"Gemini: {res.text[:100]}..."
        else:
            raise Exception("Unsupported provider")

@sio.event  # type: ignore[untyped-decorator]
async def chat_message(sid: str, data: dict[str, Any]) -> None:
    # 🛡️ Sentinel: Validate input type and length to prevent unhandled exceptions and DoS
    if not isinstance(data, dict):
        return

    workspace_id = data.get('workspace_id')
    message = data.get('message')

    if not isinstance(workspace_id, str) or len(workspace_id) > 100:
        return

    session_data = await sio.get_session(sid)
    if workspace_id not in session_data.get('workspaces', set()):
        return

    try:
        ws_uuid = uuid.UUID(workspace_id)
    except (ValueError, TypeError, AttributeError):
        return

    if not isinstance(message, str) or len(message) > 5000:
        return

    await sio.emit('chat_update', {'msg': message}, room=workspace_id)

    # Intercept if tagging an agent
    if message and "@" in message:
        # Simple extraction for MVP (e.g. "@Claude")
        words = message.split()
        agent_names = list(set([word[1:] for word in words if word.startswith("@")]))

        if not agent_names:
            return

        from .database import engine
        import asyncio

        # ⚡ Bolt Optimization: Move synchronous database operations and CPU-bound decryption
        # to a separate thread using asyncio.to_thread to prevent blocking the ASGI event loop.
        def fetch_agent_infos() -> list[dict[str, Any]]:
            infos = []
            try:
                user_uuid = uuid.UUID(session_data.get('user_id'))
            except (ValueError, TypeError, AttributeError):
                return []

            with Session(engine) as session:
                # 🛡️ Sentinel: Fix IDOR by securely scoping agent lookups. Agents without a workspace
                # can only be queried if the authenticated user is their owner.
                results = session.exec(
                    select(Agent, TokenPool)
                    .join(TokenPool, isouter=True)
                    .where(col(Agent.name).in_(agent_names))
                    .where((col(Agent.workspace_id) == ws_uuid) | ((col(Agent.workspace_id).is_(None)) & (col(Agent.owner_id) == user_uuid)))
                ).all()

                for agent, pool_entry in results:
                    if pool_entry:
                        try:
                            token = decrypt_token(pool_entry.encrypted_session_token)
                            infos.append({"name": agent.name, "provider": agent.provider, "token": token, "offline": False})
                        except ValueError:
                            infos.append({"name": agent.name, "offline": True})
                    else:
                        infos.append({"name": agent.name, "offline": True})
            return infos

        agent_infos = await asyncio.to_thread(fetch_agent_infos)

        async def handle_agent(agent_info: dict[str, Any]) -> None:
            if agent_info.get("offline"):
                await sio.emit('chat_update', {'msg': f"Agent {agent_info['name']} is offline (no token available)."}, room=workspace_id)
            else:
                print(f"Intercepted message for {agent_info['name']}, proxying request...")
                try:
                    ai_response = await call_provider_api(agent_info["provider"], agent_info["token"], message)
                    await sio.emit('chat_update', {'msg': ai_response}, room=workspace_id)
                except Exception as e:
                    print(f"Error calling provider for agent {agent_info['name']}: {type(e).__name__}") # Secure logging
                    await sio.emit('chat_update', {'msg': f"An error occurred while processing your request with {agent_info['name']}."}, room=workspace_id)

        if agent_infos:
            await asyncio.gather(*(handle_agent(info) for info in agent_infos))

@sio.event  # type: ignore[untyped-decorator]
async def disconnect(sid: str) -> None:
    print(f"Client disconnected: {sid}")

# Basic Auth routes to test
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be less than 72 bytes')
        return v

# 🛡️ Sentinel: Global dictionary for IP-based rate limiting on the register endpoint
register_attempts: dict[str, list[float]] = {}
register_last_cleanup: float = time.time()
register_lock = threading.Lock()

@app.post("/register")
def register(user: UserCreate, request: Request, session: Session = Depends(get_session)) -> dict[str, str]:
    global register_last_cleanup
    # 🛡️ Sentinel: Apply rate limiting to prevent DoS via expensive bcrypt operations
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Periodic cleanup of inactive IPs to prevent memory leaks
    if now - register_last_cleanup > 3600:
        with register_lock:
            if now - register_last_cleanup > 3600: # Double-checked locking
                register_last_cleanup = now
                inactive_ips = []
                for ip in list(register_attempts.keys()):
                    attempts = register_attempts.get(ip, [])
                    valid_attempts = [t for t in attempts if now - t < 3600]
                    if valid_attempts:
                        register_attempts[ip] = valid_attempts
                    else:
                        inactive_ips.append(ip)
                for ip in inactive_ips:
                    register_attempts.pop(ip, None)

    with register_lock:
        if client_ip in register_attempts:
            register_attempts[client_ip] = [t for t in register_attempts[client_ip] if now - t < 3600]
            if len(register_attempts[client_ip]) >= 10:
                raise HTTPException(status_code=429, detail="Too many registration attempts")

        register_attempts.setdefault(client_ip, []).append(now)

    # 🛡️ Sentinel: Mitigate timing attacks by always hashing the password
    # regardless of whether the user exists or not.
    hashed_pwd = get_password_hash(user.password)

    db_user = session.exec(select(User).where(User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    new_user = User(username=user.username, hashed_password=hashed_pwd)
    session.add(new_user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Username already registered")
    return {"msg": "User created"}

# Workspaces
class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

@app.post("/workspaces")
def create_workspace(req: WorkspaceCreate, session: Session = Depends(get_session), current_user_id: uuid.UUID = Depends(get_current_user_id)) -> Workspace:
    ws = Workspace(name=req.name)
    session.add(ws)
    try:
        session.flush()
        # ⚡ Bolt Optimization: Manually create the UserWorkspaceLink using the current_user_id
        # extracted directly from the JWT. This eliminates a redundant database query to fetch
        # the entire User object, improving endpoint response time.
        link = UserWorkspaceLink(user_id=current_user_id, workspace_id=ws.id)
        session.add(link)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Workspace name already exists")
    session.refresh(ws)
    return ws

@app.get("/workspaces")
def list_workspaces(session: Session = Depends(get_session), current_user_id: uuid.UUID = Depends(get_current_user_id)) -> list[Workspace]:
    # 🛡️ Sentinel: Fix authorization bypass to only return user's workspaces
    workspaces = session.exec(
        select(Workspace)
        .join(UserWorkspaceLink)
        .where(UserWorkspaceLink.user_id == current_user_id)
    ).all()
    return list(workspaces)

@app.get("/agents")
def list_agents(session: Session = Depends(get_session), current_user_id: uuid.UUID = Depends(get_current_user_id)) -> list[Agent]:
    # 🛡️ Sentinel: Fix authorization bypass to only return user's agents
    agents = session.exec(select(Agent).where(Agent.owner_id == current_user_id)).all()
    return list(agents)

# Mount socket app
app.mount("/socket.io", socket_app)

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator('password')
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be less than 72 bytes')
        return v

# 🛡️ Sentinel: Global dictionary for IP-based rate limiting on the login endpoint
login_attempts: dict[str, list[float]] = {}
login_last_cleanup: float = time.time()
login_lock = threading.Lock()

@app.post("/login")
def login(req: LoginRequest, request: Request, session: Session = Depends(get_session)) -> dict[str, str]:
    global login_last_cleanup
    # 🛡️ Sentinel: Apply rate limiting to prevent brute-force attacks
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Periodic cleanup of inactive IPs to prevent memory leaks
    if now - login_last_cleanup > 900:
        with login_lock:
            if now - login_last_cleanup > 900: # Double-checked locking
                login_last_cleanup = now
                inactive_ips = []
                for ip in list(login_attempts.keys()):
                    attempts = login_attempts.get(ip, [])
                    valid_attempts = [t for t in attempts if now - t < 900]
                    if valid_attempts:
                        login_attempts[ip] = valid_attempts
                    else:
                        inactive_ips.append(ip)
                for ip in inactive_ips:
                    login_attempts.pop(ip, None)

    with login_lock:
        if client_ip in login_attempts:
            login_attempts[client_ip] = [t for t in login_attempts[client_ip] if now - t < 900]
            if len(login_attempts[client_ip]) >= 5:
                raise HTTPException(status_code=429, detail="Too many login attempts")

    user = session.exec(select(User).where(User.username == req.username)).first()

    if not user:
        # 🛡️ Sentinel: Mitigate timing attacks by performing a dummy hash verification
        # to ensure the response time is indistinguishable from a valid user lookup
        verify_password(req.password, DUMMY_HASH)
        with login_lock:
            login_attempts.setdefault(client_ip, []).append(time.time())
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if not verify_password(req.password, user.hashed_password):
        with login_lock:
            login_attempts.setdefault(client_ip, []).append(time.time())
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

class ProxyRequest(BaseModel):
    agent_id: uuid.UUID
    prompt: str = Field(..., min_length=1, max_length=5000)

@app.post("/proxy-request")
async def proxy_request(req: ProxyRequest, session: Session = Depends(get_session), current_user_id: uuid.UUID = Depends(get_current_user_id)) -> dict[str, str]:
    # ⚡ Bolt Optimization: Move synchronous database operations and CPU-bound decryption
    # to a separate thread using asyncio.to_thread to prevent blocking the ASGI event loop.
    def fetch_agent_data() -> dict[str, Any]:
        # ⚡ Bolt Optimization: Use a JOIN query to fetch both the agent and their token pool entry
        # simultaneously, eliminating the N+1 sequential database queries.
        result = session.exec(
            select(Agent, TokenPool)
            .join(TokenPool, isouter=True)
            .where(Agent.id == req.agent_id)
        ).first()

        if not result:
            raise HTTPException(status_code=404, detail="Agent not found")

        agent, pool_entry = result

        if agent.owner_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this agent")

        if not pool_entry:
            raise HTTPException(status_code=400, detail="No token available for this agent")

        try:
            token = decrypt_token(pool_entry.encrypted_session_token)
        except ValueError:
            raise HTTPException(status_code=400, detail="Stored token for this agent is invalid or corrupt")

        # Eagerly extract required data
        return {
            "token": token,
            "provider": agent.provider,
            "agent_id": agent.id
        }

    agent_data = await asyncio.to_thread(fetch_agent_data)

    token = agent_data["token"]
    provider = agent_data["provider"]
    agent_id = agent_data["agent_id"]

    # ⚡ Bolt Optimization: Eagerly extract required data and close the DB session before
    # making the slow external API call to prevent connection pool exhaustion.
    session.close()

    print(f"Proxying request to {provider}...")

    try:
        response_text = await call_provider_api(provider, token, req.prompt)
        return {"response": response_text}
    except Exception as e:
        print(f"Proxy request error for agent {agent_id}: {type(e).__name__}") # Secure logging
        raise HTTPException(status_code=500, detail="An internal error occurred while communicating with the AI provider.")
