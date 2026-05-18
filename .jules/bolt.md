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
