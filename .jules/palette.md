## 2025-05-15 - [A11y and Disabled States on Icon-only Buttons]
**Learning:** Icon-only buttons often miss ARIA labels, making them inaccessible to screen readers. Furthermore, adding visual disabled states (like disabling a send button when the input is empty) prevents frustrating user interactions and makes the UI intuitively communicate constraints.
**Action:** Always add `aria-label` to icon-only buttons (`Settings`, `Send message`) and utilize the `disabled` property when a primary action requires input to be valid.
