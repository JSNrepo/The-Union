## 2024-05-15 - [Initial Data Fetching Bottleneck]\n**Learning:** The frontend initially loaded critical app data (`workspaces` and `agents`) sequentially in `useEffect`, which doubled the network latency for the initial render. \n**Action:** Use `Promise.all` for independent initial data fetches to execute them concurrently and improve initial load time.

## 2024-05-16 - [React Render Bottleneck on Keystroke]
**Learning:** Having input state (like a chat message `message`) at the root level of a large parent component (`Home`) causes the entire view (including sidebars and complex maps) to re-render on every single keystroke.
**Action:** Extract input fields into their own components (e.g., `MessageInput`) to manage their state locally. Pass down a callback (e.g. `onSendMessage`) to push the final value up to the parent when complete.
## 2024-05-18 - Chat Interception Hot Path
**Learning:** The Union's architecture relies on intercepting real-time websocket chat messages to find @-mentions. This means every time a user tags an AI, the system executes two synchronous DB queries (`select(Agent).where(Agent.name == agent_name)` and `select(TokenPool).where(TokenPool.agent_id == agent.id)`) inside the event loop. Without indexes, this creates a major bottleneck as the workspace scales.
**Action:** Always verify if real-time event handlers perform synchronous database queries and ensure those specific fields are indexed to prevent full table scans in the critical path.
## 2024-05-18 - DB connection pool exhaustion during external API calls
**Learning:** Holding an open database session during slow network requests (like long-running LLM API calls) inside Socket.IO event handlers can quickly exhaust the database connection pool under load, creating a severe performance bottleneck and potential crashes.
**Action:** Always fetch required database objects, eagerly extract the specific data points needed, and immediately close the DB session before making external async network calls.
## 2024-05-19 - [LLM Proxy Connection Pooling]
**Learning:** Instantiating a new `httpx.AsyncClient()` inside the hot path for every proxied request to an LLM provider introduces significant latency due to repeated TCP connection and TLS handshake overhead. However, using a globally shared `httpx.AsyncClient()` introduces a critical security vulnerability by sharing its stateful `CookieJar` across distinct user sessions.
**Action:** Always utilize a global, reused HTTP transport instance (e.g., `shared_transport = httpx.AsyncHTTPTransport()`) and pass it to a localized `httpx.AsyncClient(transport=shared_transport)` to benefit from stateless HTTP connection pooling without leaking cookies or other state across users. Handle its lifecycle during app startup/shutdown.## 2024-05-20 - [N+1 Sequential Database Query]
**Learning:** In the `chat_message` websocket hot path, we were doing sequential queries to fetch the `Agent` and then their `TokenPool`. This means a second database round trip was made right inside the event loop for every message intercept.
**Action:** Use SQLModel's `.join()` feature with `isouter=True` to fetch both models simultaneously. Instead of fetching an object and then querying for its relation, join them to return a tuple `(Agent, TokenPool)` in a single database round trip.

## 2024-05-22 - [Batched Processing in Websocket Hot Paths]
**Learning:** Processing multi-entity commands (like mentioning multiple `@agents` in one message) sequentially inside an event loop is an anti-pattern. Sequentially looping through database queries and blocking network requests multiplies the latency by the number of entities mentioned.
**Action:** Always batch queries for related entities using `Model.field.in_(entity_list)` and execute slow independent external API calls concurrently using `asyncio.gather()` to minimize total request time and database load.

## 2024-05-23 - [React Memoization for Dynamic Views]
**Learning:** Frequent state updates (like appending to a `messages` array via websockets) cause the entire parent component to re-render. If the parent contains complex iterables (like sidebars mapping over `workspaces` and `agents`), these lists are needlessly re-evaluated on every incoming message.
**Action:** Use `useMemo` to memoize expensive JSX blocks (like sidebars) and `useCallback` coupled with `React.memo` to stabilize event handlers passed to child components.

## 2024-05-24 - [DB connection pool exhaustion during external API calls in endpoints]
**Learning:** Holding an open database session during slow network requests (like long-running LLM API calls) inside FastAPI endpoints can quickly exhaust the database connection pool under load, creating a severe performance bottleneck and potential crashes.
**Action:** Always fetch required database objects, eagerly extract the specific data points needed, and immediately close the DB session before making external async network calls.
## 2024-05-25 - [Async Event Loop Blocking by Synchronous DB calls]
**Learning:** In the `chat_message` websocket event handler, running synchronous database queries (`session.exec`) and CPU-intensive operations (like `decrypt_token`) directly in the `async def` function blocks the entire ASGI event loop. This degrades concurrency for all connected websocket clients.
**Action:** Move synchronous database operations and CPU-bound work inside an `async def` function to a separate thread using `asyncio.to_thread`. Always ensure the database `Session` is created inside the newly spawned thread and that you eagerly extract data into standard Python structures (like dicts/lists) before returning to avoid `DetachedInstanceError`.
