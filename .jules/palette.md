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
## 2026-05-29 - Accessible Skip to Main Content Link
**Learning:** Single Page Applications without a "Skip to main content" link force keyboard users and screen readers to traverse the entire navigation menu on every page load.
**Action:** Always add an accessible skip-to-content link (using `sr-only focus:not-sr-only`) right after the `<body>` tag, and ensure the target `<main>` container has `tabIndex={-1}` and `outline-none` so it can cleanly receive focus programmatically.

## 2024-05-30 - Discoverable Truncation and Contextual Density
**Learning:** When using CSS truncation (truncate) in constrained spaces like sidebars, users lose information. Furthermore, showing only a primary name (e.g., an agent's name) without secondary context (e.g., their provider) reduces utility.
**Action:** Always pair CSS truncate with a native title attribute for discoverability on hover, and utilize vertical stacking (flex-col) to present secondary, muted context without compromising horizontal layout constraints.
## 2026-05-31 - Chat layout flex and overflow
**Learning:** In flex layouts containing user-generated text, parent containers require min-w-0 and the text container needs break-words to prevent the UI from stretching and breaking.
**Action:** Always combine min-w-0 on flex containers with break-words on text elements for message bubbles.

## 2024-06-01 - Prevent Ancillary UI Flicker During Hydration
**Learning:** During initial application load, rendering full layout structural elements (like top headers or chat inputs) before data hydration completes can cause a jarring flicker where generic empty states (e.g., "Select a Workspace") flash for a second before the real data arrives.
**Action:** Always pass the `isLoading` state down to ancillary structural components (like headers and inputs). Use it to conditionally render skeleton loaders (e.g. `animate-pulse`) in headers, and explicitly display "Loading..." in input placeholders or disabled buttons to provide a cohesive loading experience.
