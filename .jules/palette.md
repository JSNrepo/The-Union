## 2025-05-15 - [A11y and Disabled States on Icon-only Buttons]
**Learning:** Icon-only buttons often miss ARIA labels, making them inaccessible to screen readers. Furthermore, adding visual disabled states (like disabling a send button when the input is empty) prevents frustrating user interactions and makes the UI intuitively communicate constraints.
**Action:** Always add `aria-label` to icon-only buttons (`Settings`, `Send message`) and utilize the `disabled` property when a primary action requires input to be valid.

## 2025-05-16 - [Keyboard Navigability & Semantic Elements in Lists]
**Learning:** In this project, there's a pattern of using `div` elements with `onClick` handlers for interactive lists (like selecting workspaces). This breaks accessibility, making it impossible for keyboard-only users to navigate to these items using Tab and activate them using Enter/Space. Screen readers also miss the context of what these items are.
**Action:** Always replace interactive `div` wrappers with semantic `<button>` elements, add appropriate `focus-visible` ring styling for keyboard navigation, ensure `w-full text-left` to maintain layout, and use ARIA attributes like `aria-current="page"` (or `true`) or `aria-selected` to convey the active state clearly to assistive technologies.

## 2025-05-17 - [Empty States in Dynamic Lists]
**Learning:** Initializing chat interfaces or dynamic lists with a completely blank area can leave users confused about what to do next or whether the application has loaded successfully.
**Action:** Always provide a visually distinct "empty state" component with helpful icon, text, and guidance (e.g., "No messages yet. Start the conversation in...") when the data array is empty.

## 2025-05-18 - [Holistic Disabled States in Forms]
**Learning:** Visually disabling a form's action button is insufficient UX; the associated inputs should also be disabled when the action cannot be performed (e.g. no active workspace selected). Leaving an input active while the submit button is disabled allows users to type into a useless field, causing confusion.
**Action:** Always ensure that disabled states are applied holistically to the entire form or input group, and visually communicate *why* they are disabled (e.g., via a contextual placeholder like "Select a workspace to message...").
## 2024-05-19 - Screen reader support for dynamic auto-scrolling chat
**Learning:** For dynamic auto-scrolling chat lists where messages are added dynamically, users with screen readers might not notice new content unless they navigate to it.
**Action:** Always add `role="log"` (and optionally `aria-live="polite"`) to the container holding chat messages. This ensures that screen readers correctly and politely announce new dynamically added elements without interrupting the user.
