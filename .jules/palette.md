## 2024-05-24 - Contextual Empty States
**Learning:** React applications that map data to the UI often fall back to generic empty states (e.g. "No messages") when the true state is that the parent context (e.g. "No workspace selected") is missing. This can confuse users.
**Action:** Always conditionally handle missing parent contexts first with a specific empty state before checking if the data array itself is empty.

## 2024-05-21 - Keyboard Shortcut Discoverability for Core Inputs
**Learning:** While implementing keyboard shortcuts (like `/` to focus search/chat inputs) significantly improves accessibility and power-user speed, they remain undiscovered unless explicitly hinted. Displaying a subtle, styled `<kbd>` element within the input field itself serves as an elegant, non-intrusive educational mechanism.
**Action:** Always pair global keyboard shortcuts that interact with specific UI elements with inline visual `<kbd>` cues. Ensure these cues fade or hide when the input contains text to prevent visual clutter.
## 2024-05-22 - Prevent UI Flicker During Hydration
**Learning:** During initial data fetching (hydration) when auto-selecting an active item (like a workspace), rendering a generic empty state (like "No workspace selected") before the fetch completes causes a jarring UI flicker.
**Action:** Always introduce an `isLoading` state for initial asynchronous data loads and render a visually distinct loading indicator (e.g., a spinner) to mask the hydration delay, only rendering the empty state or the content once the fetch definitively resolves.

## 2026-05-23 - Prevent layout shifts with skeleton loaders
**Learning:** Relying purely on empty arrays during data hydration causes a visually jarring layout shift and misleading empty states. Furthermore, using `role="status"` on a generic `div` inside a button is an accessibility anti-pattern that can suppress screen reader announcements.
**Action:** Always implement explicit `isLoading` checks to render localized skeleton placeholders (e.g., using `animate-pulse`) and use `<span className="sr-only">` for hidden status text.

## 2024-05-25 - Semantic HTML Landmarks in SPAs
**Learning:** Using generic `<div>` containers for major layout regions (like sidebars and main content areas) makes screen reader navigation difficult in Single Page Applications. Users lack context about where they are in the page structure.
**Action:** Always use semantic HTML5 landmarks (e.g., `<aside>`, `<main>`, `<nav>`) with descriptive `aria-label` attributes for primary application layout sections to ensure proper screen reader announcements and navigation.
