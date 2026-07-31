# Focus mode and accessible surface controls

Workspace Surfaces keep an application or graph beside Wright chat. Focus mode removes the activity bar, file drawer, and other nonessential workspace chrome, but it never hides or pauses chat. Choose **Maximize surface while keeping chat** in the active surface, then choose **Restore workspace layout** to return to the prior normal layout.

## Resize chat without a mouse

Move focus to the divider between the surface and chat. It is announced as **Resize chat and surface**.

| Key | Result |
| --- | --- |
| Left / Right arrow | Change the chat share by 2% |
| Page Up / Page Down | Change the chat share by 10% |
| Home / End | Move to the smallest / largest legal chat size |

Normal mode starts with chat at 38%. Focus mode starts at 360 CSS pixels and never lets chat exceed half of the available area or 720 CSS pixels. Wright always reserves at least 320 CSS pixels for chat and 480 CSS pixels for the surface when both panes are visible.

## Narrow windows and 200% zoom

When those two minimums plus the 8-pixel divider do not fit, Wright shows a labeled **Chat / Surface** switcher. Select either destination; switching does not close the hidden pane. Returning to a wider size restores the previous normal or focus ratio. This also applies when browser zoom or platform text scaling reduces the available CSS-pixel width.

Hidden chat updates are announced without forcing a pane change. Essential controls use horizontal scrolling or labeled overflow controls rather than being clipped.

## Surface tabs and host focus

- Left and Right arrow move focus among surface tabs. Home and End jump to the first and last tab.
- Enter or Space selects the focused surface. Delete closes a closable surface.
- After close, focus moves to the next tab, then the previous tab, then the Workspace surfaces heading.
- F6 cycles through chat, surface tabs, the surface toolbar, and the return-to-host control while focus is in Wright chrome. Shift+F6 cycles backward.

Wright places an **Enter embedded application** control before a live frame and a **Return to surface controls** control after it. The desktop application also supplies an application-level return-to-host shortcut: Ctrl+Shift+F6 on Windows/Linux or Command+Shift+F6 on macOS. A cross-origin application can control keyboard behavior inside its own frame, so Wright labels escape behavior as unverified until the application proves conformance and continues to offer **Open in browser**.

## Retained application state

Wright retains up to six live, MCP App, or WebMCP hosts per workspace by default. Static graphs and other reproducible displays are suspended before stateful applications. If retaining another live application would exceed the limit, Wright names the least-recently-used surface and asks whether to keep it, reload it, or open it in the browser. Reloading can lose unsaved application-local state; stopping or closing a presentation remains a separate explicit action.

## Accessibility expectations for application authors

Managed applications should expose visible keyboard focus, a logical Tab order, accessible names, and an escape route from any modal or composite control. Test at 200% zoom, in forced-colors/high-contrast mode, with keyboard only, and with a screen reader. Wright-owned fixtures must pass automated scans with no serious or critical accessibility violations; an embedded application remains responsible for the content inside its security boundary.
