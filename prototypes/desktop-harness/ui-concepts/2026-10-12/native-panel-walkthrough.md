# Native Windows / GB10 panel check

Named plugin update 0.2.0 is installed on GB10, approved by the user. The only
semantic configuration change is the named marketplace source. Old 0.1.1 bytes,
settings and state are preserved. No desktop restart or other chat was created.
The existing chat's daemon inventory still reports an MCP startup failure; no
Wright tools are exposed here. Native rendering is therefore **unverified**.

Use a fresh desktop conversation on the existing **GB10 execution host** (not a
Windows-local project). Keep the current conversation. Do not start a run, change
model/authentication/permissions, or install another package to make this pass.

Paste this into that conversation:

> Test only the installed Wright read-only native panel. Use the native
> `wright_workspace_panel` tool with workspace_id
> `aec8d7db-e77b-4c48-a8cb-f4b3b7e87ad9` and session_id
> `desktop-a9c0ddc7-4356-43d6-b82e-66d72124aac9`. Do not create a replacement
> workspace or start a workflow. Let the desktop render the tool's declared
> MCP App resource. If tools or native rendering are unavailable, report the
> exact gap without using a browser URL as native proof. If rendered, check
> the heading "UI panel qualification", Refresh status, narrow/wide resizing,
> and a light/dark change. Report the actual desktop app build and any observed
> open/close/restoration hooks separately from GB10 CLI 0.159.2. Preserve this
> isolated workspace and all original state. Do not use a separate model worker.

A resource read or a browser screenshot alone does not establish rendering.
Record a real desktop screenshot, exact build, tool result and observed theme /
resize behavior. Tabs, file handlers and automatic conversation continuation
remain separate checks; this probe neither implements nor claims them.

If native discovery fails in the new conversation, inspect the named plugin's
startup diagnostics without exposing tokens. Do not restart other services or
reload all conversations as a workaround. Return the failure; shared UI work can
continue independently.

Private installation/rollback evidence:
`/tmp/wright-host-ui-native-install-20261012-01` (0700).
Approved proposal and scoped rollback: [native-panel-update.md](native-panel-update.md).
