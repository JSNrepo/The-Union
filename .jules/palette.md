## 2024-05-24 - Contextual Empty States
**Learning:** React applications that map data to the UI often fall back to generic empty states (e.g. "No messages") when the true state is that the parent context (e.g. "No workspace selected") is missing. This can confuse users.
**Action:** Always conditionally handle missing parent contexts first with a specific empty state before checking if the data array itself is empty.
