# Exact native-panel test update

Prepared 12 October 2026; installed after explicit user approval. This expands the earlier approved named
plugin from tool-only 0.1.1 to a read-only UI probe and moves its execution to the
isolated UI worktree/target. The user approved this specific live change under
the submitted goal's configuration boundary. No unrelated setting is required.

## Change

- Plugin/marketplace: `wright-desktop-gb10-prototype`, version `0.2.0`.
- MCP server remains `wright-desktop-gb10`.
- Adds `wright_workspace_panel`, a read-only operation, and an immutable HTML
  resource addressed by its content hash. No new filesystem/gateway authority.
- The other twelve tools retain their existing behavior. The new execution
  target is fresh isolated state, not a migration of existing workspaces/runs.
- Python: `/tmp/wright-host-adaptive-ui-prototype/.venv/bin/python`.
- Bridge: `/tmp/wright-host-adaptive-ui-prototype/prototypes/desktop-harness/mcp_bridge.py`.
- State: `/tmp/wright-host-ui-target-20261012-01`; API 8120, frontend 5220.
- Existing API 8116 / frontend 5216 / source worktree stay in place.

Only the named marketplace source changes, and the same named plugin is installed
and enabled. No global feature/auth/model/permission changes or app restart.
The CLI may replace the selected package cache; preserve 0.1.1 bytes before it
does so. Do not change an active run's binding to the new target. Read old pending
work first; if present, retain the old connection and qualify the candidate in
an explicitly selected test conversation instead of interrupting that work.

## Commands after approval

```sh
codex plugin marketplace add /tmp/wright-host-adaptive-ui-prototype/prototypes/desktop-harness/ui-panel-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Back up the named installed package and configuration privately; compare semantic
configuration before/after and verify that unrelated settings are unchanged.
CLI 0.159.2 required removing the named marketplace reference before adding
the replacement; the scoped remove/add and plugin add succeeded. Semantic
configuration comparison found only its marketplace source path changed.

Refresh the named plugin through supported host controls where available. If
this chat cannot discover it, prepare an exact new-chat handoff rather than
silently creating or messaging another chat or restarting the desktop.

## Scoped rollback

```sh
codex plugin marketplace add /tmp/wright-openai-desktop-harness-prototype-next/prototypes/desktop-harness/native-host-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Use the preserved 0.1.1 package if its original source has since changed. Rollback
changes only this marketplace/plugin selection; do not replace the entire user
configuration with an old backup or erase either target's data.

## Evidence before promotion

11 focused Python checks and 69 existing frontend checks passed. The actual
Python MCP SDK discovered thirteen tools, called the scoped panel read and
retrieved the resource with `text/html;profile=mcp-app`; no run started. Six
browser checks passed with a simulated MCP App host and real recorded Wright
data. The initial fixture-creation probe failed after its successful create
because legacy tool results are JSON text; it was reconciled and never repeated.

The update is installed; the existing chat still reports an initialize-handshake
failure with no Wright tools. See [native-panel-walkthrough.md](native-panel-walkthrough.md).

These establish protocol/browser readiness, not installed Windows rendering,
native tabs, supported continuation or user acceptance. Qualification next:
open the actual installed panel, record actual app build/host context, resize,
change theme and refresh the exact scoped workspace. Source evidence files are
linked in the main integration plan.
