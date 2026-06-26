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
## 2024-06-03 - Actionable Error Messages
**Learning:** Generic "Failed to load data" messages with inappropriate icons (like Settings gears) leave users confused about what went wrong and what to do next. Replacing them with explicit headers (e.g., "Connection Error"), actionable next steps (e.g., "Please check your network connection"), and clear semantic icons (e.g., `AlertTriangle`) significantly improves the usability of error states.
**Action:** Always pair error states with an actionable suggestion and an appropriate visual indicator, rather than just displaying raw error strings or generic messages.

## 2024-06-04 - Decorative Icons and Truncated Secondary Text
**Learning:** Purely decorative icons (like `Users`, `Bot`, `Hash`, `MessageSquare`, etc.) inside interactive elements (like buttons or links) or general layout containers can cause redundant or confusing announcements for screen reader users. Also, secondary text (like a provider name) that gets truncated by CSS loses its meaning if it is not discoverable.
**Action:** Always add `aria-hidden="true"` to purely decorative icons to prevent screen readers from announcing them unnecessarily, especially when they are accompanied by visible text or semantic labels. Additionally, always add a `title` attribute to any secondary text that relies on CSS truncation to ensure users can hover to discover the full context.
## 2025-05-15 - Visual Keyboard Shortcut Hints vs Screen Readers
**Learning:** When adding visual `<kbd>` elements to show keyboard shortcuts within or overlaid on an input field, screen readers will announce the hint redundantly and sometimes confusingly (e.g. announcing "slash" out of context) if the input itself correctly uses the `aria-keyshortcuts` attribute.
**Action:** Always add `aria-hidden="true"` to decorative/visual keyboard shortcut hints, and rely on `aria-keyshortcuts` on the actual interactive element to communicate the shortcut to assistive technologies.

## 2024-06-07 - Contextual Hover Actions and Keyboard Accessibility
**Learning:** Adding contextual actions (like a "Copy message" button) that only appear on hover (`group-hover:opacity-100`) creates a cleaner UI, but completely breaks keyboard accessibility if keyboard users cannot focus and interact with the hidden button.
**Action:** Always pair `group-hover:opacity-100` with `focus-visible:opacity-100` to ensure interactive elements are discoverable and usable via keyboard navigation.

## 2026-06-08 - Keyboard-Accessible Scrolling and Visual Hint Visibility
**Learning:** Large scrollable areas (like chat histories) are often inaccessible to keyboard-only users if they lack a `tabIndex`. Additionally, permanent visual shortcut hints (like `<kbd>/`</kbd>) can add visual clutter once the user has already initiated the action and focused the input field.
**Action:** Always add `tabIndex={0}`, an appropriate `aria-label`, and `focus-visible` styles to primary scrollable containers to ensure keyboard accessibility. Use Tailwind's `peer` and `peer-focus:opacity-0` utilities to gracefully hide instructional hints once the associated input is focused, maintaining a clean UI during interaction.

## 2024-06-09 - Dynamic Contextual Keyboard Hints
**Learning:** While empty input states often include a global shortcut hint (like `/`), adding functional action hints (like "Enter ↵" to send) that only appear when the input has content provides excellent discoverability without cluttering the empty state.
**Action:** Use conditional rendering and Tailwind's peer focus utilities to swap static hints (like `/`) for action hints (like "Enter ↵") dynamically as the user interacts with the input and types text.
## 2024-05-18 - Actionable Error States
**Learning:** Generic error messages leave users frustrated and stuck, especially during network failures.
**Action:** When designing error states, always include explicit, actionable next steps (like a "Try Again" button) and semantic visual indicators rather than just stating the error.

## 2024-06-10 - Semantic HTML for Non-Interactive List Items
**Learning:** Using `<button>` elements for list items that are purely informational (read-only) and perform no action creates false expectations for screen reader users and adds confusing focus states for keyboard users.
**Action:** Always use semantic `<div>` or `<li>` elements for non-interactive list items instead of `<button>`, and avoid adding focus utilities (`focus:outline-none focus-visible:ring-2`) or cursor pointer classes if the element does not perform a direct action or navigation.

## 2024-06-12 - Dynamic Document Title Context
**Learning:** In Single Page Applications, relying solely on internal state for navigation means the browser tab title remains static. This deprives users navigating multiple tabs and screen reader users switching windows of critical context about which workspace or room they are currently in.
**Action:** Always dynamically update `document.title` to reflect the active primary context (e.g., active workspace or room) to improve external discoverability and accessibility context.

## 2024-06-17 - Accessible Skeleton Loaders and Skip Links
**Learning:** Screen readers announce empty animate-pulse divs as blank/silent, leading to confusion during loading states. Additionally, complex sidebar layouts without skip links force keyboard users to tab through all sidebar items to reach main content.
**Action:** Always embed visually hidden descriptions (`<span className="sr-only">Loading...</span>`) inside skeleton loaders, and implement standard skip-to-content links for major layout regions.

## 2026-06-21 - Screen Reader Announcements for Transient Success States
**Learning:** In React components with visual-only success states (e.g., an icon changing from a copy icon to a checkmark for 2 seconds after copying), screen reader users completely miss the success confirmation because the visual change doesn't naturally trigger an announcement.
**Action:** When implementing transient UI states like "Copied!", always include an `aria-live="polite"` region (such as `<span aria-live="polite" className="sr-only">{copied ? "Copied" : ""}</span>`) that renders the success text to explicitly announce the state change to assistive technologies.
## 2024-06-22 - Add workspace name to message input aria-label and placeholder
**Learning:** Screen reader users needed more context about which workspace they were typing in when focused on the message input. Adding the active workspace name dynamically to the input's placeholder and aria-label improves accessibility and usability.
**Action:** Always provide dynamic context in input labels/placeholders when the scope of the input changes based on application state (like a selected channel or workspace).

## 2024-06-25 - Actionable Empty States
**Learning:** Users encountering a "No messages yet" screen without a clear way to start interacting may feel stuck. Providing a direct call-to-action (like a "Say Hello" button) in empty states reduces friction and encourages engagement.
**Action:** Always include a helpful, contextual action button in empty state screens to guide the user's next step.

## 2024-06-26 - Organic Skeletons & Actionable Sidebar States
**Learning:** Identical repeating skeleton rectangles create a sterile, unnatural loading experience, and bare text for empty/error states in narrow sidebars feels broken. Staggered skeleton widths and styled empty states significantly improve perceived performance and UI completeness.
**Action:** When implementing loading states for lists, always use varying widths (e.g., `["w-full", "w-11/12", "w-5/6"]`) to create an organic text-like appearance. Ensure all empty/error states have appropriate visual hierarchy (borders, background tints, and icons) rather than floating plain text.
