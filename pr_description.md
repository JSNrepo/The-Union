💡 What: Extract inline `workspaces.map()` items into a standalone `React.memo` component (`WorkspaceItem`), use `useCallback` for the workspace selection handler, and isolate the `agents.map()` logic into an independent `useMemo` block.

🎯 Why: Previously, the entire `sidebarContent` block (including the agents list and all workspaces) was re-evaluating and re-rendering every time the user switched between workspaces because `activeWorkspace` changed. Inline mapping forced an O(N) re-render of all child elements.

📊 Impact: Reduces sidebar rendering cost from O(N) to O(1) on workspace switch. Now, only the previously active and newly active `WorkspaceItem` components will re-render, and the agents list remains entirely untouched.

🔬 Measurement: Profile the application using React DevTools. Switching between workspaces should no longer cause flashes on the `agents` list or inactive workspaces in the profiler flamegraph.
