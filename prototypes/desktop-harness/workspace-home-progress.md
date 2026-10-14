# Workspace discovery and native home — 14 October 2026

Implementation in progress, not installed or accepted on Windows.
Worktree: `/tmp/wright-desktop-engineering-demos`, branch
`codex/desktop-engineering-demos`, temporarily based on the unmerged PR 153
candidate `e5b39c57`. Reconcile this dependency with current remote dev after
baseline integration. Do not push this branch as an independent baseline yet.

## Implemented slice

- A read-only desktop workspace list uses the existing lifecycle/repository.
  It returns only this connection's isolated-root, desktop-bound sessions and
  does not activate or rebind them. Another platform's newer session does not
  redirect selection. Missing owned directories remain visible as unavailable;
  unrelated paths and escaping symlinks are excluded. Storage failure is not
  converted to an empty successful list.
- Scoped file metadata delegates to the existing workspace file owner after
  exact workspace/session validation. No generic proxy, file execution or model
  fallback is introduced.
- `wright_home` renders the existing native resource with a compact workspace
  picker and saved `.wflow` list. Selecting a file opens the shared editor with
  its exact identity; a Workspaces control returns to discovery. Existing dirty
  draft checks prevent discarding work. Native frame sizing now uses available
  container height, including its navigation row.
- Late file responses from a previous workspace and mismatched response scopes
  are rejected. Failures remain distinct from empty catalogs. This initial slice
  still creates workspaces/workflows through the existing conversation tools;
  forms, Connections, Files, Recent runs and broader management are unfinished.

The bridge now has 21 tools when editor and working view are enabled. This is a
source candidate only: installed 0.4.0 and its services/configuration are unchanged.
General engineering and image gates remain in place. No engineering run occurred.

## Current evidence

- Prototype backend/bridge suite: 65 passed, including real SQLite workspace
  identity/scope checks and file-owner delegation.
- All native-panel component/client suites: 31 passed across five files.
- TypeScript passed; focused Python lint passed. Focused frontend lint has no
  errors and one cleanup-counter warning in the home component to review.
- Native resource build: 656 modules, zero external assets, 2,190,030 bytes.
  This is build evidence, not actual desktop rendering/acceptance.
- First source audit compiled both existing SteveCAD variants without running
  them. The native-render variant has 16 tasks: text reasoning, bounded MCP
  agents and configured tool calls; it does not require a new CAD executor.
  Exact source hashes/task records are retained privately in
  `/tmp/wright-desktop-demo-baseline-20261014-02/source-capability-audit.json`.

## Next qualification

1. Finish baseline full gate/browser checks, fast push gate and all corrected-head
   CI before merging PR 153. Its patched image passed the current vulnerability
   scan; the full gate and supported browser matrix were still running at this
   checkpoint. Logs remain in `/tmp/wright-desktop-demo-baseline-20261014-02`.
2. Exercise this home/resource through a simulated MCP App host against a fresh
   isolated real Wright API, including workspace choice, workflow open, draft
   preservation, Back, narrow layout and theme. Retain a clearly labeled real
   screenshot; do not present a fixture as a Windows or engineering-demo pass.
3. Qualify actual native installation only after the concrete candidate and
   scoped rollback are ready. Preserve the prior named plugin/cache and state.
4. Continue connection management and the bounded engineering/task/image paths
   from the submitted goal. This navigation slice does not complete M1.

Dependency work uses a separate worktree so it cannot change the candidate under
qualification or its active services. Its Python and Node dependencies are
installed locally from the existing lockfiles; no global software was upgraded.

## Real-storage browser qualification and path correction

The official MCP client proof in
`/tmp/wright-desktop-home-proof-20261014-01/home-probe.json` created one isolated
workspace and saved an unchanged copy of the existing SteveCAD native workflow.
List/home/file calls succeeded. This created source only, not an engineering run.

The first browser probe found that file-tree paths have a leading slash while
canonical workflow-source identities are relative. Home now removes that single
root separator before opening; all remaining characters are preserved. The
component fixture now uses actual file-tree path conventions. Five focused
component tests pass; the rebuilt resource is 2,190,048 bytes with no external
assets. A second browser attempt exposed a fixture mistake: at narrow width the
editor uses its existing view selector, not the hidden wide-screen tab. The test
now uses the visible selector; no editor capability or assertion was removed.

The corrected `native_home_acceptance.mjs` probe passed against real isolated
Wright owners. It verifies workspace discovery, source open, Back, narrow-home
width, unsaved-draft navigation denial, unchanged accepted source digest and no
browser errors. It only permits the four exact read operations and rejects any
mutation. Evidence (including failed attempts) is retained under the state above;
the passing report and screenshots are in `browser-home-1792013828358/`.

This is a simulated MCP App host in Chromium on GB10, not Windows native
acceptance, full editor responsive qualification, permission-prompt qualification
or engineering execution. The server's frozen runtime predates the rebuilt UI;
no run or continuation was attempted under that binding. Before further runtime
qualification, use a new isolated candidate with matching recorded assets.

Suggested social content, for review only:
“Wright's workspace picker now opens a saved SteveCAD engineering workflow in our
shared editor. This GB10 browser prototype also protects unsaved work when
switching workspaces. Next: connection setup and real desktop-driven CAD runs.”
Use `browser-home-1792013828358/editor.png` with its visible simulated-host label.
Do not caption it as a completed CAD run or a Windows desktop capture.

Next: qualify Connections through existing catalog/onboarding owners, preserving
workspace scope and the return to the same workflow. Finish baseline gates and
actual desktop acceptance independently; neither is implied by this browser pass.
