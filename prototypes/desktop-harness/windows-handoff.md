# Windows desktop → GB10: preparation handoff

Status: proposed connection experiment, not locally qualified. No Windows
configuration, installation or desktop action has been performed by this branch.
Use this if the desktop client runs on Windows; do not assume its MCP commands
execute on GB10 merely because the current chat's shell does.

The user confirmed on 11 October 2026 that the desktop is on Windows and asked
for this handoff. This authorizes preparation, not live plugin installation.
GB10 host name observed: `promaxgb10-9666`; its reachable Windows SSH alias and
Windows desktop build are still unknown. Do not guess either.

## Current verified GB10 target

- Feature worktree: `/tmp/wright-openai-desktop-harness-prototype`, branch
  `codex/openai-desktop-harness-prototype`, uncommitted local prototype on
  `ba2fad68`. Do not assume that branch is available from GitHub.
- Locked Python: that worktree's `.venv/bin/python`; MCP SDK 1.28.1.
- Remote script: `prototypes/desktop-harness/mcp_bridge.py` in that worktree.
- Private state: `/tmp/wright-desktop-mcp-proof-20261011-05`.
- Authenticated API: GB10 loopback 8102. Hosted editor: GB10 loopback 5202,
  with `/api` proxied to 8102. Do not forward the API separately.
- Recorded connection profile:
  `wright-desktop-prototype:9c72a8e7389a3c04245fc1af4d89ceef115a943dcf31923dcd9fb9f19e0c0c1f`.
- Protocol `2025-11-25`; 12 tools including typed action submission.
- Completed run `5a9f0dedc8b84aba931ad251e27ebf00` used actual desktop-authored
  proposals/results, one exact permitted file inspection, and same-run reconnect
  without replay. Ungranted start was denied (403). Other tool scopes are gated.
- Browser screenshots are actual Wright captures; installed desktop loading and
  right-panel rendering are not yet proved. 114 focused tests passed.

These processes are temporary. Check their actual identity, liveness and profile
before using them. If unavailable, coordinate fresh isolated startup on GB10;
do not silently reuse another Wright instance, the installed command, or an old
state after adapter/transport changes.

## Prompt to relay to the Windows agent

> Inspect the OpenAI desktop harness on Windows for connecting a local Wright
> prototype whose code, dependencies, API and workflow runs stay on GB10. This
> is preparation and connection qualification, not another implementation branch.
> Preserve current desktop settings, plugins, chats, worktrees and evidence. Do
> not install/upgrade software, change live configuration or restart the desktop
> without specific approval. Do not push, merge, release or perform physical work.
>
> Read the supplied handoff archive's README, windows-handoff.md, capabilities.md
> and qualified-gateway-evidence.json. The feature branch is unpublished; use the
> supplied files or authenticated SSH file copy, not an assumed remote branch.
> Its implemented files are on
> GB10 at `/tmp/wright-openai-desktop-harness-prototype`. The exact original
> Codex-inside-Wright pilot must remain preserved.
>
> Use the OpenAI documentation skill to check this installed desktop build's
> supported local plugin, stdio MCP and browser/right-panel behavior. Establish
> which host executes MCP commands. Report the actual GUI build separately from
> CLI version. Inspect existing GB10 SSH access without printing credentials or
> private config. Do not create new authentication routes silently.
>
> Prefer a thin stdio SSH connection using already-authorized SSH access, if
> supported on this installation. The remote command would launch the GB10
> worktree's pinned Python `mcp_bridge.py` against an explicitly selected isolated
> state directory. The helper reads its private Wright API credential on GB10.
> No Wright installation, Python environment, MCP server dependency or model
> worker should be necessary on Windows for that route.
>
> For the browser, propose a loopback-only SSH forward of the selected Wright
> web-preview port. Wright's GB10 Vite server already proxies `/api` to its own
> authenticated loopback API. Do not bind either service publicly or disable
> authentication. Keep any browser unlock credential outside chat/screenshots.
>
> Prepare the exact minimal local package/configuration, approved SSH alias,
> paths and ports, plus rollback. Explain what would change before asking for
> specific approval. If the app instead supplies a documented remote executor
> that can load this package on GB10, qualify that route explicitly; do not assume
> remote shell access establishes plugin-config propagation.
>
> After approval, verify MCP initialization/tool listing, authenticated status,
> a fresh workspace, workflow save/start, and real desktop reasoning returning to
> the same durable Wright run. Open the hosted URL inside the desktop right panel
> and record actual rendering. A CLI protocol client or ordinary browser capture
> does not prove installed desktop-plugin behavior. The local prototype permits
> only exact privately enrolled file inspection in its separate opt-in profile.
> Other tools, application/CAD/external actions and generated UI authoring remain
> gated. Never enroll authority from desktop tools or mistake a fixture grant for
> engineering approval.
>
> Return exact observed capability/build evidence, setup/rollback steps, any
> blocker and a clean actual desktop screenshot if available. Clearly distinguish
> verified behavior from proposed commands. Do not overwrite or restart another
> workstream's Wright services or protected engineering runs.

## Candidate transport shape to qualify

This is illustrative, with intentional placeholders, not a tested Windows
manifest or permission to connect. Resolve the approved executable/SSH alias,
remote worktree and retained state before preparing an installable package.

```json
{
  "mcpServers": {
    "wright-desktop": {
      "type": "stdio",
      "command": "<existing Windows ssh.exe path>",
      "args": [
        "-T", "-o", "BatchMode=yes", "-o", "ForwardAgent=no",
        "-o", "StrictHostKeyChecking=yes",
        "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
        "<already-authorized GB10 SSH alias>",
        "<GB10 worktree>/.venv/bin/python <GB10 worktree>/prototypes/desktop-harness/mcp_bridge.py --state-dir <explicit isolated GB10 state>"
      ]
    }
  }
}
```

Never interpolate model-provided hosts or command paths. SSH authentication,
host-key checking and remote shell quoting need actual host-specific validation.
No generic remote-shell tool should be exposed by the Wright plugin.

A browser forward would use the same approved SSH alias and a fresh local port:
`ssh -N -L 127.0.0.1:<local web port>:127.0.0.1:<GB10 web port> <approved alias>`.
Choose unused ports and own/stop only the new forward. Local/remote endpoints and
the plugin's returned browser URL must agree; the current GB10-only URL is not
evidence of a qualified cross-host connection.

SSH disconnect is not workflow cancellation. Pending tasks must remain in
Wright, and reconnect must reconcile receipts. Current abrupt-client lease
expiry is an explicit prototype gap; do not claim it fixed by an SSH wrapper.

A separate GB10 fault probe killed the API during pending reasoning (SIGKILL,
exit 137) and reopened the same database/profile. Wright retained the exact run
and request, reported reconciliation_required, and returned the original stable
start receipt without replay or output creation. However, the bridge incorrectly
accepted a late answer with no live consumer. Treat this as a failed admission
qualification: if the API restarts during reasoning, stop the demo and report the
same run for reconciliation. Do not submit answers, restart the workflow under a
new request, or claim this recovery is supported. This does not affect the
separately qualified restart at a durable declared-input checkpoint.
Reduced evidence is in qualified-restart-evidence.json; raw state is separate
from the Windows target. Its backend/transport/adapter/dispatch were not changed.

## Exact proposed Windows experiment

1. Inspect the desktop GUI build, current execution host, existing `ssh.exe` and
   already-authorized GB10 SSH alias. Verify trusted host-key and batch
   authentication. Do not expose keys or disable host-key checking. With no
   suitable access, report the exact missing prerequisite.
2. Copy/extract the prepared archive into a fresh local directory. Its Windows
   candidate deliberately has an invalid executable and SSH alias until these
   two values are resolved. Change only those values, preserving the fixed remote
   script/state command and strict SSH options. Inspect the resulting package.
3. Prepare a tunnel forwarding Windows loopback port **5202** to GB10 loopback
   port **5202**, with ExitOnForwardFailure=yes. Matching ports make the returned
   workspace URL correct. If occupied, prepare a reviewed URL/port mapping;
   do not attach to an existing process or quietly use a different local port.
4. Before installation or live configuration mutation, show the resolved
   marketplace directory, executable/alias, exact commands, affected settings,
   credential handling and rollback, then request specific approval. The user's
   handoff choice is not this approval. Do not restart the whole desktop app.
5. After approval, register the marketplace using the installed CLI's verified
   supported command; install its one Windows plugin in the desktop Plugins
   directory. Keep a private before/after comparison of only changed entries.
   No global Python, Wright or Node installation should be needed for this route.
6. Use actual installed tools in a desktop chat to read connection status, create
   a fresh workspace, save a no-tools digital workflow, prepare/start it, read
   its exact reasoning request, answer in the same chat and inspect the same run.
   A local protocol client does not count as installed desktop proof.
7. Open the returned localhost URL in the desktop browser/right panel. Unlock
   through the existing private token flow outside conversation/screenshots.
   An open acknowledgement is not rendering proof. Enter through Workflows and
   exercise editing, saving and result navigation.
8. Record a clean desktop screenshot showing chat beside the actual Wright view.
   Next prove a declared input checkpoint and same-run continuation. Preserve
   protected runs and keep unattended wakeup behavior explicitly unverified.

Rollback removes only the new Windows plugin/marketplace entries and stops only
the owned tunnel. Preserve workspaces, accepted source, runs, evidence, other
plugins and concurrent configuration changes. Do not restore an entire old
configuration file over new user settings.

Official documentation rechecked on 11 October 2026:
[local plugin packaging and marketplace registration](https://developers.openai.com/plugins/build/plugins),
[stdio MCP configuration and experimental remote execution](https://learn.chatgpt.com/docs/extend/mcp),
[desktop browser and local web apps](https://learn.chatgpt.com/docs/browser).
The SSH wrapper is a proposed use of documented stdio configuration, not an
OpenAI-documented Wright connection. Windows execution and panel behavior require
actual observations. Remote executor support remains an experimental alternative
to qualify if local stdio is unsuitable.
