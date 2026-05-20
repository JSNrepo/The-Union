## 2025-05-17 - Missing Authentication on Sensitive Endpoints
**Vulnerability:** Several sensitive API endpoints in FastAPI (like creating workspaces, listing workspaces, listing agents, and proxying AI requests) were completely unauthenticated, allowing any unauthenticated user to access or modify data.
**Learning:** FastAPI endpoints do not automatically enforce authentication even if auth functions are defined in the project. Developers must explicitly inject the authentication dependency (e.g., `Depends(get_current_user)`) into every route that requires it.
**Prevention:** Always verify that sensitive routes include authentication dependencies. When creating a new route, default to requiring authentication unless it is explicitly intended to be public (like login or register).

## 2025-05-18 - Hardcoded Extension API Key
**Vulnerability:** A static, hardcoded API key ("static-extension-key") was found in the Chrome Extension's `background.js` file, which is used to authenticate requests to the backend for token synchronization.
**Learning:** Client-side code, including browser extensions, is inherently public and can be easily inspected by users or malicious actors. Hardcoded secrets inside client-side bundles offer no real security and act merely as "security theater."
**Prevention:** Never hardcode secrets in client-side code. If authentication is required from a client, either the user must provide the credential via configuration (like an options page), or proper session-based authentication (like JWTs) should be used.

## 2025-05-19 - Missing Input Validation and DoS Risk
**Vulnerability:** The application was missing input length constraints on user authentication and proxy endpoints (`UserCreate`, `LoginRequest`, `ProxyRequest`, etc.), allowing massive payloads (e.g., extremely long passwords parsed by bcrypt) to cause CPU/RAM exhaustion. Furthermore, the WebSocket event handlers (like `chat_message`) did not validate data types or lengths before processing (e.g., calling `.split()` on untyped user input), leading to unhandled exceptions and crashes if dicts or other objects were passed instead of strings.
**Learning:** Frameworks like FastAPI and Socket.IO do not strictly limit payload sizes or enforce types by default in all scenarios (especially WebSockets). Unvalidated inputs to expensive operations (like hashing or external API proxies) represent a clear Denial of Service (DoS) vector.
**Prevention:** Always use Pydantic's `Field` constraints (`min_length`, `max_length`) for all data models. For WebSockets, explicitly validate both the type (`isinstance`) and length of the incoming payload before interacting with it.

## 2025-05-20 - Missing Input Type Validation on WebSockets
**Vulnerability:** The Socket.IO event handlers `join_workspace` and `chat_message` expected a dictionary payload (`data`) and called `.get()` on it, but did not explicitly validate its type. This could lead to an unhandled `AttributeError` exception if a malicious client sent a string or other data type instead of a JSON object.
**Learning:** In WebSocket frameworks like `python-socketio`, the framework passes the decoded payload directly as received from the client. It does not enforce that the payload matches the type hint (e.g., `data: dict`) provided in the function signature.
**Prevention:** Always explicitly validate the type of incoming WebSocket payloads (e.g., `if not isinstance(data, dict): return`) before interacting with their attributes to prevent unhandled exceptions and potential service degradation.
