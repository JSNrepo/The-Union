## 2024-05-24 - Contextual Empty States
**Learning:** React applications that map data to the UI often fall back to generic empty states (e.g. "No messages") when the true state is that the parent context (e.g. "No workspace selected") is missing. This can confuse users.
**Action:** Always conditionally handle missing parent contexts first with a specific empty state before checking if the data array itself is empty.

## 2024-05-21 - Keyboard Shortcut Discoverability for Core Inputs
**Learning:** While implementing keyboard shortcuts (like `/` to focus search/chat inputs) significantly improves accessibility and power-user speed, they remain undiscovered unless explicitly hinted. Displaying a subtle, styled `<kbd>` element within the input field itself serves as an elegant, non-intrusive educational mechanism.
**Action:** Always pair global keyboard shortcuts that interact with specific UI elements with inline visual `<kbd>` cues. Ensure these cues fade or hide when the input contains text to prevent visual clutter.
