# Scoped native editor update — prepared, not installed

The user confirmed the 0.2.0 Wright panel with “Refresh status” appeared in the
actual Windows desktop / GB10 arrangement. This candidate adds manual shared
canvas editing. It does not enable generated process-UI authoring or change the
workflow executor, model, authentication, global permissions or desktop settings.

## Exact change and limits

Same marketplace/plugin `wright-desktop-gb10-prototype`, version **0.3.0**; same
server `wright-desktop-gb10`. Adds `wright_workflow_open` (read only), an immutable
self-contained shared editor resource, and `wright_workflow_save` (UI-only
metadata; Wright still validates exact workspace/source/layout scope and CAS).
The other thirteen tools remain. The new target is
`/tmp/wright-native-editor-target-20261012-02`, API 8122. Its source is
`/tmp/wright-host-adaptive-native-editor`; neither the installed 0.2.0 source nor
its API 8120/state is changed. Old workspaces/runs remain there. The candidate
connection cannot access them; use the old connection or scoped rollback.

One panel, shared canvas, Add step, Source/Side by side, instructions, Undo/Redo,
saved source/layout and conflict recovery. No extra Wright chat or tab strip.
Run is not connected in this editor; existing conversation tools retain their
separately qualified digital-run behavior. Native tabs, close interception,
unsaved draft restoration, automatic chat wakeup and actual editor tool-call
permission behavior remain unverified. Save before closing. No credential is
sent to the resource; its CSP declares no external connect/resource domains.

## Concrete local qualification

41 backend/transport checks, 7 client checks, TypeScript, targeted ESLint and Ruff
pass. The final 14-check MCP bridge subset also passes with the added SDK-version drift guard. Official MCP client verified source save, stale revision rejection,
wrong-workspace denial and fresh-connection readback. Five packaged-editor
browser checks passed against real isolated source storage: open, edit/save,
reload restoration, theme/narrow controls and stale-save draft preservation.
These are not Windows editor acceptance. Existing served Workflows/editor and
platform regression evidence remains linked in implementation-evidence.md.

The first sandbox attempt stalled before any MCP operation and was stopped;
its state remains. The protocol script then failed at its reconnect assertion
because legacy results are JSON text; the saved edit was reconciled by reading,
without replay. Two browser failures were fixture selectors (tab role and narrow
view selector); preserved captures accompany the repaired report. See
[native-editor-evidence/candidate.json](native-editor-evidence/candidate.json).

## Commands only after specific approval

Before changing the named selection, back up its 0.2.0 package/config privately,
check pending work on the old target, and preserve unrelated settings. The tested
CLI 0.159.2 requires scoped remove/add when the source changes:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-host-adaptive-native-editor/prototypes/desktop-harness/native-editor-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Compare semantic configuration before/after: only this marketplace source may
change, with the same named plugin enabled. Do not restart the desktop or reload
all conversations. Use a fresh test chat if the existing one retains its old
inventory. See [native-editor-walkthrough.md](native-editor-walkthrough.md).

## Scoped rollback

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-host-adaptive-ui-prototype/prototypes/desktop-harness/ui-panel-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Restore only the named 0.2.0 package/selection from its private backup if the
source is unavailable. Never restore the whole configuration or delete either
state target. Keep any candidate accepted edits and evidence.
