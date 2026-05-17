## 2025-05-17 - Missing Authentication on Sensitive Endpoints
**Vulnerability:** Several sensitive API endpoints in FastAPI (like creating workspaces, listing workspaces, listing agents, and proxying AI requests) were completely unauthenticated, allowing any unauthenticated user to access or modify data.
**Learning:** FastAPI endpoints do not automatically enforce authentication even if auth functions are defined in the project. Developers must explicitly inject the authentication dependency (e.g., `Depends(get_current_user)`) into every route that requires it.
**Prevention:** Always verify that sensitive routes include authentication dependencies. When creating a new route, default to requiring authentication unless it is explicitly intended to be public (like login or register).
