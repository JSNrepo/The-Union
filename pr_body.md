💡 What: Replaced native title tooltip with a custom, keyboard-accessible tooltip on the Settings button.
🎯 Why: The native title attribute is not reliably announced or accessible via keyboard focus, making the icon-only Settings button difficult to understand for some users.
📸 Before/After: Added screenshot of the new accessible tooltip state to README.md.
♿ Accessibility: Added `role="tooltip"`, `aria-hidden="true"`, and `peer-focus-visible:opacity-100` to ensure the tooltip appears during keyboard navigation.
