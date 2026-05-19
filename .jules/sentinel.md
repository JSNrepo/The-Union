## 2025-05-17 - Missing Authentication on Sensitive Endpoints
**Vulnerability:** Several sensitive API endpoints in FastAPI (like creating workspaces, listing workspaces, listing agents, and proxying AI requests) were completely unauthenticated, allowing any unauthenticated user to access or modify data.
**Learning:** FastAPI endpoints do not automatically enforce authentication even if auth functions are defined in the project. Developers must explicitly inject the authentication dependency (e.g., `Depends(get_current_user)`) into every route that requires it.
**Prevention:** Always verify that sensitive routes include authentication dependencies. When creating a new route, default to requiring authentication unless it is explicitly intended to be public (like login or register).

## 2025-05-18 - Hardcoded Extension API Key
**Vulnerability:** A static, hardcoded API key ("static-extension-key") was found in the Chrome Extension's `background.js` file, which is used to authenticate requests to the backend for token synchronization.
**Learning:** Client-side code, including browser extensions, is inherently public and can be easily inspected by users or malicious actors. Hardcoded secrets inside client-side bundles offer no real security and act merely as "security theater."
**Prevention:** Never hardcode secrets in client-side code. If authentication is required from a client, either the user must provide the credential via configuration (like an options page), or proper session-based authentication (like JWTs) should be used.
