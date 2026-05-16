## 2024-05-15 - [Initial Data Fetching Bottleneck]\n**Learning:** The frontend initially loaded critical app data (`workspaces` and `agents`) sequentially in `useEffect`, which doubled the network latency for the initial render. \n**Action:** Use `Promise.all` for independent initial data fetches to execute them concurrently and improve initial load time.

## 2024-05-16 - [React Render Bottleneck on Keystroke]
**Learning:** Having input state (like a chat message `message`) at the root level of a large parent component (`Home`) causes the entire view (including sidebars and complex maps) to re-render on every single keystroke.
**Action:** Extract input fields into their own components (e.g., `MessageInput`) to manage their state locally. Pass down a callback (e.g. `onSendMessage`) to push the final value up to the parent when complete.
