## 2026-05-14 - React.memo for MessageList
**Learning:** Found a common React performance bottleneck where the entire chat history was re-rendering on every keystroke in the input field. The fix was wrapping the message rendering logic in React.memo to prevent unnecessary re-renders.
**Action:** Always check if a component is unnecessarily re-rendering large lists when unrelated state (like input fields) changes.
