# Windows connection candidate — not installed or qualified

The user requested a Windows handoff. This bundle prepares the connection; it
does not authorize live desktop settings changes. Wright and its dependencies
remain on GB10. No additional LLM worker is part of this connection.

Read `windows-handoff.md`, `capabilities.md` and `qualified-gateway-evidence.json`
in the supplied archive before proceeding. The existing test runs and captures
prove GB10 behavior, not Windows installation or desktop-panel rendering.

## Resolve the two missing local facts

Inspect the existing Windows SSH executable and already-authorized GB10 SSH
alias. Do not invent a host, disable host-key checks or create another auth route.
The candidate `plugins/wright-desktop-windows-prototype/mcp.json` deliberately
uses invalid placeholders so it cannot accidentally connect before review.

Replace `command` with the verified absolute Windows `ssh.exe` path and replace
`WRIGHT_APPROVED_GB10_ALIAS_NOT_CONFIGURED` with the verified authorized alias.
Keep the strict SSH options and fixed remote command intact. An alias must be
an actual trusted local SSH configuration entry, not model-supplied command text.
Validate JSON and inspect the final arguments before installation.

The fixed remote command starts the pinned GB10 Python MCP bridge against proof
state 05. The bridge obtains its Wright credential privately on GB10. Check its
recorded binding and current process identity/liveness before connecting; a
changed adapter/transport requires a fresh qualified profile, not deleting the
version check or overwriting older evidence.

## Prepare browser forwarding

The GB10 web server is loopback 5202 and proxies authenticated API requests to
GB10 loopback 8102. Forward only the web port. Use a dedicated terminal/process
so its ownership is clear. Proposed PowerShell command, after resolving values
and reviewing this exact experiment:

```powershell
& $wrightSshExecutable -N -o BatchMode=yes -o ForwardAgent=no -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:5202:127.0.0.1:5202 $wrightGb10Alias
```

Check that Windows local port 5202 is free first. If occupied, prepare an explicit
URL mapping for review; the current plugin returns localhost:5202. An alternative
forward port alone would make that URL incorrect. Do not expose a public listener
or disable Wright's authentication. Browser unlock credentials stay outside
chat, screenshots, manifests and command-line arguments.

## Live change, only after specific approval

Inspect current desktop build, available plugin controls and CLI help. Show the
resolved package, SSH executable/alias, exact registration command, tunnel,
affected config entries and rollback before requesting approval. Preserve all
other settings. With support confirmed, the proposed registration is:

```powershell
codex plugin marketplace add $wrightBundleRoot
```

Then install this one plugin from its marketplace in the desktop Plugins
directory. Do not assume a CLI plugin installation updates the GUI on this
build. Do not restart the whole app or other active chats automatically.

## Actual desktop proof

Use installed Wright tools in a desktop chat: read connection status, create a
fresh workspace, author/save a no-tools workflow, prepare/start, read the exact
bounded task, reason in that chat, submit its response and read the same run.
Open the returned URL in the desktop browser beside chat; enter via Workflows,
edit/save and inspect the completed result. A protocol client or browser outside
the app is useful diagnostics but not installed desktop proof.

Next qualify a declared input and same-run continuation. Exact enrolled file
inspection already passed locally on GB10; the private grant is not a user review
or general permission and enrollment is not a plugin tool. Other tools,
application/CAD/external actions and generated interfaces remain gated.

Capture a clean image showing actual desktop chat beside Wright. Suggested
caption, only after it works: “Wright workflows beside the OpenAI desktop
conversation: the desktop supplies reasoning; Wright retains execution and
evidence.” Record the observed app build, execution host, protocol, connection
profile, workspace/source/run IDs, denials and limitations.

## Rollback

Remove only `wright-desktop-windows-prototype@wright-desktop-windows-prototype`
and its newly registered marketplace using verified supported commands or the
desktop controls. Stop only the owned tunnel. Preserve other plugins, concurrent
settings changes, workspaces, accepted workflows, runs and evidence. Do not
restore an entire older config over unrelated changes.

Sources rechecked 11 October 2026:
[plugin packaging](https://developers.openai.com/plugins/build/plugins),
[stdio MCP](https://learn.chatgpt.com/docs/extend/mcp),
[desktop browser](https://learn.chatgpt.com/docs/browser).
The SSH wrapper is a proposed stdio transport requiring Windows qualification.
