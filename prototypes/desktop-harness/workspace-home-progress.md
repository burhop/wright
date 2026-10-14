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

## Connections discovery slice — local candidate

The home now has Workflows and Connections views within the selected workspace.
`wright_connections_list` validates the exact workspace/session, then reads the
existing `/api/mcp/capabilities` owner with search and cursor pagination. It
validates that owner's typed response and projects only presentation fields:
installation, activation, observed process status, compatibility, missing-credential
boolean and membership in the selected workspace. Other workspace memberships,
credential names and raw requirements are not returned. No provider is started,
installed, authenticated, enabled or granted permission by this read.

The panel distinguishes loading/failure/empty results, rejects mismatched scope,
ignores obsolete responses, supports search and pagination, and labels setup
and permission mutations as not yet available. An enabled entry is not described
as connected or granted execution authority. Workspace selection and returning
to Workflows retain the home state. Returning from an open editor to Connections
with its exact document return target remains unfinished.

Validation: 18 focused bridge tests passed; seven Connections/home component
tests passed; TypeScript and focused Python lint passed. Native resource rebuilt
with 657 modules. The source bridge exposes 22 tools in the editor/working profile.
This is not installed, actual-host accepted, or live-catalog browser qualified.
Next prove the current catalog through the official MCP client with matching
fresh runtime assets; then expose the existing onboarding plan/authentication
owners and their permission checks rather than adding a parallel setup executor.

## Actual catalog and setup-plan continuation

A fresh current-assets backend on loopback 8131 uses isolated state
`/tmp/wright-desktop-connections-proof-20261014-01`. The official MCP-client
`connections_probe.py` passed against its real bundled catalog and rejected the
wrong desktop session before catalog access. Receipt:
`connections-probe-1792014067299778403.json`. It found `stevecad-mcp`, not installed,
not enabled, and compatibility uncertain because no machine observation existed.
No provider was contacted or engineering task executed. The fresh source-only
workspace and unchanged SteveCAD source have their separate `home-probe.json`.

The next local candidate adds an explicit UI-only `wright_connection_plan` port.
Its desktop endpoint checks the exact workspace/session and delegates to the
existing install-plan API owner with workspace scope. It cannot request global
scope or assert independent license completion. The UI renders the plan effects
and blockers; installation, authentication and permission mutation remain unavailable.
No approve/apply/grant operation is invoked by plan creation. This addition is
not yet served by the 8131 backend and needs a matching-assets live qualification.

Validation: 25 scoped backend/bridge tests passed outside the sandbox; the sandbox
attempt was interrupted after stalling at the synchronous FastAPI dependency test.
This is a host-boundary observation, not proof of its exact cause. Eight home/
Connections UI tests, TypeScript and focused Python lint passed. The rebuilt native
resource is 2,194,170 bytes with zero external assets; editor/working tool count 23.

OAuth investigation: the existing remote MCP runner owns discovery, PKCE, secret
storage and loopback callback, but `_OAuthCallbackServer.open_authorization_url`
currently invokes `webbrowser.open` on the execution host. GB10/Windows setup must
surface the pending sign-in through an explicitly qualified host handoff; browser
login alone is not MCP authorization. Reuse the existing transport rather than
introducing a second OAuth implementation. The provider recipe, qualification
follow-up and usage guide were read; no credentials were requested or exposed.

## Live setup-plan proof and explicit publisher completion

The existing setup owner was exercised through the official MCP client on a fresh
matching-assets backend at 8132, state `/tmp/wright-desktop-setup-proof-20261014-01`.
`plan-probe.json` records an exact workspace-scoped SteveCAD plan in `blocked`
state, with `external_license_incomplete`; no approve/apply or provider operation
was called. It preserves the actual cloud-data/network approval gates and remote
registration effect. This is successful qualification of blocked setup, not
successful installation or authentication.

The user was asked whether publisher account/terms setup is already complete;
that answer is pending. A further local candidate exposes an unchecked explicit
publisher-completion checkbox scoped to the selected capability. Its value is
forwarded to the existing owner only when preparing a new plan. Switching to a
different provider does not reuse that confirmation. The UI displays publisher
context and separate setup approval requirements. It never infers completion
from an installed app, browser session or an agent's plan. Purchase, OAuth sign-in,
setup approval and workflow grants remain distinct. No actual confirmation was
submitted in the real probe.

After this addition: 25 backend/bridge tests and three Connections UI tests pass;
TypeScript and Python lint passed. The native bundle is 2,194,848 bytes, no
external assets. Live installation is unchanged. The updated checkbox candidate
still needs matching-assets served/native qualification before installation.

Baseline PR work: full merge gate passed on `e5b39c57`; documentation-only
checkpoint `bcf03161` records its receipt and the retained browser limitation.
The required push gate is running in isolated state at
`/tmp/wright-desktop-demo-push-20261014-01`; no correction push or merge has yet
occurred. Keep the dependent feature branch separate until baseline CI/integration.

## Scoped setup lifecycle and real isolated registration

User confirmation received: use the existing SteveCAD account; publisher setup
is complete. The new `plan-confirmed-probe-02.json` in the 8132 proof state records
that explicit answer, a reviewable plan with no blockers, and exact digest readback.
The first confirmed-plan attempt failed before MCP connection while the owned
backend was starting; its failure was retained and no plan call reached the API.
Only then was a separate attempt made. Original blocked plan and evidence remain.

Added read/approve/apply desktop setup ports over the existing onboarding owner.
Backend checks the exact desktop workspace/session and the persisted plan's
workspace scope; approval/application retain the existing administrator dependency
and owner digest validation. UI-only visibility is not the authority. Viewing a
plan is read-only. No automatic retry or workflow-tool grant is introduced.
The new ports are not yet wired to frontend approval/application controls.

`apply-probe.json` records real official-MCP-client exact read → approve → apply →
readback → catalog checks, under the submitted isolated-install authorization.
The reviewed effect registers SteveCAD locally only. The catalog confirms installed,
inactive and not enabled in this workspace. Registry validation explicitly does
not establish protocol readiness, OAuth authentication or engineering use.
The setup proof backend was the only restarted process; pre-restart binding,
version and preview files were archived under `before-plan-recovery/`, old logs
retained, and no engineering runs existed in that state.

Eight scoped backend tests and 18 bridge/catalog tests passed. They cover
non-admin denial before plan access, cross-workspace plan denial, stale-digest
propagation to the existing owner, read without apply and explicit publisher
completion. Focused Python lint passed. Tool count is now 25 in source.
Next: visible setup action/reconciliation controls, provider sign-in handoff,
protocol readiness and explicit workspace permission qualification.

Baseline push gate passed on `bcf03161`, receipt/log in
`/tmp/wright-desktop-demo-push-20261014-01`. Remote dev remained `c1a8d009` at fetch.
The single consolidated correction push to PR 153 was initiated after both
local gates; current-head CI and its result must be checked before merge.
