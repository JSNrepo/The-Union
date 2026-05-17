## 2025-05-15 - [A11y and Disabled States on Icon-only Buttons]
**Learning:** Icon-only buttons often miss ARIA labels, making them inaccessible to screen readers. Furthermore, adding visual disabled states (like disabling a send button when the input is empty) prevents frustrating user interactions and makes the UI intuitively communicate constraints.
**Action:** Always add `aria-label` to icon-only buttons (`Settings`, `Send message`) and utilize the `disabled` property when a primary action requires input to be valid.

## 2025-05-16 - [Keyboard Navigability & Semantic Elements in Lists]
**Learning:** In this project, there's a pattern of using `div` elements with `onClick` handlers for interactive lists (like selecting workspaces). This breaks accessibility, making it impossible for keyboard-only users to navigate to these items using Tab and activate them using Enter/Space. Screen readers also miss the context of what these items are.
**Action:** Always replace interactive `div` wrappers with semantic `<button>` elements, add appropriate `focus-visible` ring styling for keyboard navigation, ensure `w-full text-left` to maintain layout, and use ARIA attributes like `aria-current="page"` (or `true`) or `aria-selected` to convey the active state clearly to assistive technologies.

## 2025-05-17 - [Empty States in Dynamic Lists]
**Learning:** Initializing chat interfaces or dynamic lists with a completely blank area can leave users confused about what to do next or whether the application has loaded successfully.
**Action:** Always provide a visually distinct "empty state" component with helpful icon, text, and guidance (e.g., "No messages yet. Start the conversation in...") when the data array is empty.
