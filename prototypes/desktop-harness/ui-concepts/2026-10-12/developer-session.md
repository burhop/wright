# Wright UI developer session

The GB10 source worktree is attached to this chat on `codex/host-adaptive-ui-debug`,
starting at `91da5d80`. The frontend has Vite live reload. The installed 0.4.0
plugin source/package and existing walkthrough data are preserved.

[Open the developer preview](http://127.0.0.1:5223/workspace/1b212827-4eee-482f-a32c-7b18c26b3a33?host=openai-desktop&workflow=canonical&workflowPath=workflows%2Fui-bug-review.workflow.wflow).
It uses a fresh **UI bug review** workspace and an exact copy of the saved
checkpoint fixture. No run was started during setup.

1. Open the preview in the desktop app's built-in browser beside this chat.
2. Select **Annotate** in the browser toolbar. Click a control or drag over an
   area; write what happened and what you expected, then save the comment.
3. Send “Address these UI annotations.” We will fix a small batch, refresh,
   then recheck the affected behaviour in the native plugin panel.

Ordinary browser annotations require no custom annotation code. Full CDP access
is a separate inspection permission, not needed merely to leave comments.
[Official browser guidance](https://learn.chatgpt.com/docs/browser#comment-on-the-page).

This serves the shared editor/working view in Wright's browser shell with the
OpenAI host presentation. It is a developer preview, not the native MCP panel
frame. Browser-only fixes do not establish native-panel acceptance. The backend
remains the installed isolated API8123 with its existing digital-only authority,
frozen routing and run owners; the frontend is loopback5223.

The browser retains Wright's authentication gate. A headless GB10 check used
the existing private credential and verified workspace → Workflows → the saved
copy, with no JavaScript errors. That does not authenticate the Windows browser.
The desktop opening was queued; actual visibility, remote access and annotation
support are awaiting user observation. Report **Unlock Wright** or a connection
error if displayed; never send the access token in chat. No auth gate was disabled.

Session details and the labelled GB10 browser screenshot are in `ui-debug-evidence/`.
The user's report is “Done. Lots of small bugs.” It is recorded as feedback,
not as a pass of every acceptance case. The individual bug list awaits annotations.
