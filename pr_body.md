💡 What: Added an `aria-live="polite"` region to the transient "Copied!" success state.
🎯 Why: Screen reader users completely miss visual-only success confirmations (like an icon changing to a checkmark) because the visual change doesn't naturally trigger an announcement.
📸 Before/After: Visuals remain unchanged, but assistive technologies now announce the success.
♿ Accessibility: Screen reader users now receive explicit audio feedback when a message is successfully copied to their clipboard.
