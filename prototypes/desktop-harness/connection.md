# Desktop connection candidate

Prepared for review; no live desktop configuration has been changed.

The user has now confirmed a Windows desktop and requested a handoff. Do not
execute the GB10 registration commands below: they are retained as an earlier
candidate, not the selected host route. Use windows-handoff.md and the separate
Windows package candidate. No live plugin installation has been authorized.

The local package is in `local-marketplace/plugins/wright-desktop-prototype`.
It contains a portable manifest, one workflow skill and a stdio MCP transport.
The transport calls only the isolated, authenticated Wright API on GB10 loopback
8102 (proof state `/tmp/wright-desktop-mcp-proof-20261011-05`). Its credential is read from a private file, never embedded in the package,
tool schema, conversation, screenshot or command line. No model endpoint is used.

## Before enabling

Confirm which machine hosts the desktop client and where its MCP processes run.
The prepared command paths are **GB10 paths**. They cannot run unchanged on a
Windows client. Do not open an unauthenticated network listener to bridge hosts.
If Windows hosts the client, qualify its remote-executor support or prepare an
authenticated connection/forwarding handoff first; no such route is claimed yet.
An exact investigation prompt and candidate transport shape are prepared in
[windows-handoff.md](windows-handoff.md). Its placeholders are proposals, not
working Windows configuration or authorization to install it.

On GB10, the existing CLI reports 0.159.2; the actual desktop GUI build remains
unverified. The locked Python MCP SDK is 1.28.1 and the tested protocol is
2025-11-25. Package loading and tool appearance still require desktop verification.

## Exact proposed live changes, requiring user approval

The prepared package now targets the newly qualified 12-tool profile, including
typed action submission and separately enabled confined inspection. The previous
pending approval request targeted the earlier text-only profile; it is not
authorization for installing this revised candidate. Review this exact package
and host route before any live change. Other tool scopes remain unavailable.

Register this one local marketplace, then install/enable this one plugin. The
official guide documents marketplace registration and desktop-directory
installation; the second command is additionally supported by this host's CLI
help, but its effect on the desktop has not yet been tested:

```bash
codex plugin marketplace add /tmp/wright-openai-desktop-harness-prototype/prototypes/desktop-harness/local-marketplace
codex plugin add wright-desktop-prototype@wright-desktop-prototype
```

These commands may add marketplace/plugin settings to
`/home/burhop/.codex/config.toml` and copy the plugin into the desktop's cache.
They must preserve other settings, credentials, plugins and MCP connections.
Before mutation, record the current target entries and save a private backup for
comparison; do not display configuration secrets. Initial read-only inspection
found no existing prototype plugin or same-named MCP entry.

Use the desktop Plugins directory to inspect the installed package and enable its
MCP server. Verify tool listing and authenticated connection in this conversation
or a user-chosen chat. A restart may be needed; let the user choose when, since
other chats may be running. Do not quit/restart their desktop app automatically.

First installed-plugin check: connection status, fresh workspace creation, saved
workflow, prepare/start receipt, actual desktop reasoning answer, then read the
same durable run. Open the returned URL beside the conversation and verify its
normal Workflows control. Browser opening alone is not rendering evidence.

## Rollback, only for the newly approved prototype entries

```bash
codex plugin remove wright-desktop-prototype@wright-desktop-prototype
codex plugin marketplace remove wright-desktop-prototype
```

Compare configuration afterward and preserve unrelated concurrent changes. Do
not restore an entire old config over new user settings. Do not delete prototype
workspaces, accepted source, runs or evidence as part of disconnection.

Normal MCP disconnect has preserved pending reasoning. A separate digital
checkpoint test also continued the same durable run after normal MCP disconnect
and a controlled isolated Wright API restart, retaining the frozen binding and
first output. Abrupt-process liveness expiry and restart during pending reasoning
or an uncertain operation remain qualification work.

## Isolated connection evidence before approval

The pinned MCP SDK successfully initialized the stdio transport, listed its 11
tools, created workspace `59bc92bd-e5bb-4f52-9a9c-2dce30d05a43`, saved source,
prepared inputs, and started durable run `ef1ba07937a74281a7fe165af18ef250`.
This desktop conversation supplied the retained reasoning answer through the
protocol client. Wright accepted it and recorded a completed run and the saved
`inspection-brief.md`, SHA-256
`3e9a74e02ce0446e3e35ff116087ab2059b2df4b3c30202be291a0bd60d10500`.
This proves the MCP transport and owning services, not installed-plugin loading.
Evidence: `/tmp/wright-desktop-mcp-proof-20261011-03/protocol-probe.json`.
The normal workspace Workflows entry, exact saved workflow and result viewer
also passed a served-browser capture with no standalone agent/inference API
requests. Desktop chrome and right-panel rendering remain unverified.

## Current limits

The default runtime admits text reasoning and declared input checkpoints. The
prepared proof profile additionally admits only exact privately enrolled
`inspect_file` tasks. It does not expose policy enrollment or arbitrary gateway
calls as MCP tools. Application/CAD execution, other tools, external actions and
generated UI authoring remain gated. The desktop's global native-tool
ceiling, private instructions, exact model identity and GUI build are unverified.
Wright's API and gateway authority remain distinct from desktop tool approvals.

The current profile completed run `5a9f0dedc8b84aba931ad251e27ebf00` through
the real MCP protocol after a controller disconnect. One inspection dispatch
succeeded, its input stayed unchanged, and no first-decision replay occurred.
An ungranted start was denied with 403. This is protocol qualification, not
installed-desktop loading. Evidence: `qualified-gateway-evidence.json`.

Sources: [plugin packaging](https://developers.openai.com/plugins/build/plugins)
and [desktop MCP configuration](https://learn.chatgpt.com/docs/extend/mcp).
Current official documentation and local CLI help support the proposed setup;
they do not establish that this package has loaded in the desktop.
