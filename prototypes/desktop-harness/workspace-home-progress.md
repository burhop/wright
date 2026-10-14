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

## Explicit setup controls and lost-acknowledgement UI

Connections now exposes the qualified plan read/approve/apply ports. Approval
and application are separate explicit controls, shown only for reviewable and
approved plans respectively. Each successful mutation is followed by a read of
the exact durable plan. A failed/unconfirmed response disables mutations and
new plan creation in that view, offers “Check saved setup status”, and performs
no automatic mutation retry. Readback verifies workspace, session, plan,
capability and workspace scope. Completed registration is labeled separately
from sign-in, protocol validation and workspace permission. Catalog status is
refreshed after confirmed completion.

Nine home/Connections component tests pass, including a forced lost apply
acknowledgement: exactly one apply request, disabled apply, explicit read-only
reconciliation, then observed completed state without another mutation. TypeScript
and focused ESLint passed. Native resource rebuilt; this remains a source candidate,
not installed-host or real-browser qualification of the new controls.

Next OAuth boundary: the existing runner owns PKCE, secrets and its loopback
callback. Its lifecycle coordinator does not expose a runner until startup
completes, so polling `runner_for` cannot retrieve an in-progress sign-in request.
Use an explicit presentation callback attached to the existing transport/startup
path; do not patch the browser module globally or invent another OAuth client.
A Windows-browser/GB10-loopback callback route must be qualified before promising
one-click sign-in. No provider authentication attempt has yet started.

## Headless OAuth presentation hook — transport qualification

Added an optional async authorization presenter to the existing remote MCP
runner, passed through both coordinated and legacy manager construction paths.
It receives server identity, authorization URL and the actual loopback callback
URI. A `None` URL clears the presentation. When supplied, it replaces only the
browser-opening step: SDK OAuth discovery, PKCE, state processing, secret storage
and callback handling remain in the existing transport. The default browser
path remains unchanged. No global browser monkeypatch or second OAuth client.

Pending presentation clears after callback receipt, timeout, cancellation or
close. A failed presenter propagates rather than silently opening another browser.
31 transport/lifecycle tests passed, including synthetic real-loopback callback,
completion, timeout, cancellation, presentation failure, default-browser behavior
and existing lifecycle regressions. Focused Ruff passed. These tests do not prove
provider login, valid OAuth state acceptance by the upstream SDK, remote callback
routing or Windows UI behavior; the callback tests use explicit synthetic values.

The hook is not yet selected by the installed plugin or prototype API. Next wire
an authenticated, workspace-scoped ephemeral sign-in presentation into the owned
prototype backend and existing validation/startup service. Keep authorization URLs
out of model output and evidence, clear them on completion/expiry, and preserve
actual callback port identity. Qualify the Windows-to-GB10 callback route before
starting a real SteveCAD sign-in. Ordinary workflow tools must not acquire an
operator authentication or approval capability from this UI integration.

## Scoped sign-in presentation and existing validation owner

The opt-in preview now supplies the OAuth presenter when the normal API lifespan
constructs its MCP engine. Ordinary API deployments retain the default browser
behavior. `DesktopOAuthPresentation` keeps only an ephemeral authorization URL,
actual loopback callback URI and exact workspace/session/plan binding; no tokens,
codes or URLs are persisted to evidence. HTTPS authorization and the existing
127.0.0.1 callback path are required; embedded credentials and alternate callback
hosts/paths are rejected. Presentation expires after the bounded sign-in window.
Expiry removes the URL but does not unlock a second validation while the original
operation is pending; only operation cleanup releases that binding.

New operator endpoints validate a completed exact-digest setup plan, bind its
server to that scope, and delegate to the existing capability-validation owner.
They do not add a workflow executor or grant a workspace tool. Readback requires
administrator authorization, exact plan scope and returns `Cache-Control: no-store`.
The owner retains OAuth/protocol/validation outcomes and existing cleanup; transient
presentation is not authentication or validation authority. Cleanup removes the
binding on success/failure/cancellation. Restart has no presentation to restore;
it must not trigger automatic sign-in or validation replay.

All 75 prototype tests passed, including a synthetic pending validation: real
FastAPI administrator enforcement, cross-plan denial, duplicate validation refusal,
exact transient read, cleanup and no workspace enable call. Additional tests cover
expiry, clean restart, malicious address rejection and retained single-flight
binding after expiry. Focused lint passed. These are local synthetic transport/
owner tests, not actual SteveCAD authentication or Windows acceptance.

The new endpoints are not exposed as model tools or installed plugin controls.
Next expose sensitive sign-in URLs only in app-private UI metadata, qualify long
validation/readback/cancellation behavior, and establish the actual Windows-to-
GB10 callback route. No real account login was started in this checkpoint.

## Operator sign-in panel — local qualification

The completed setup plan now offers explicit sign-in/protocol validation and
read-only status controls. The MCP bridge puts transient authorization and callback
URLs only in app-private metadata, never model-visible content/structured data.
Private metadata is presentation, not access control: existing administrator,
workspace/session, exact-plan and digest checks remain authoritative. The host
opens the URL only after the operator clicks; no browser fallback or automatic
validation retry is introduced. Workspace tool permission remains separate.

The panel ignores late polling/manual status responses after validation finishes,
clears pending links, and reports lost acknowledgements as unconfirmed. One
validation request is allowed per mounted attempt. Host reload/recovery and the
six-minute request timeout still need real-host qualification; this does not
claim durable validation cancellation or safe automatic retry.

Verification: all 76 prototype Python tests passed (4.54s, local IPC enabled).
The restricted-sandbox attempt stopped progressing in endpoint tests and was
interrupted; it is not a pass. Three frontend suites passed 12 tests, followed by
all four sign-in tests after adding the late-manual-response regression. ESLint,
TypeScript and diff whitespace checks passed. The native bundle rebuilt to
2,199,676 bytes with zero external assets. An initial build command used the wrong
script path and failed before building; rerunning apps/web/build-native-panel.mjs
succeeded. These are synthetic/local checks, not Windows or SteveCAD acceptance.

Installed plugin 0.4.0 and retained API services were not updated. The current
candidate still requires a qualified Windows-to-GB10 callback route before real
sign-in. Existing account/terms completion is confirmed by the user; no new
account, billing choice, credentials, OAuth consent or engineering run is implied.

## Return to the same workspace — navigation correction

Returning from the shared editor now restores the previously selected workspace
only when the refreshed list still contains its exact workspace/session pair and
marks it available. A replacement session is not substituted. This is in-memory
panel navigation context, not a new workspace/run owner or durable host session.
It does not open a workflow automatically. Draft navigation protection remains.

Seven home component tests passed, including exact restoration and rejection of
a replaced session; focused lint and TypeScript passed. Built-panel browser
walkthrough against the retained isolated read-only API passed at
`/tmp/wright-desktop-home-proof-20261014-01/browser-home-1792015489306/report.json`:
real source discovery, editor entry, exact workspace return, narrow layout,
unsaved-draft containment and unchanged accepted source. Screenshots are in the
same directory. A subsequent behavior-preserving cleanup of generation invalidation
removed a lint warning; seven tests and build passed again (2,200,021-byte bundle,
zero external assets). Installed Windows acceptance remains outstanding.

Suggested social caption (not published): “Wright workflows alongside desktop
chat: choose a workspace, open the engineering canvas, and return without losing
your place. This is a local browser prototype; the full engineering demo is next.”
Use the real home/editor screenshots with the visible simulated-host label.

## Saved validation readback and explicit workspace enablement

Connections now projects the existing catalog owner's last local validation
identity, state, timestamp and reason codes. It deliberately labels that record
as historical evidence: catalog readback is not a full current-configuration
revalidation and cannot grant an action. A lost validation acknowledgement can
be investigated through Search / refresh without repeating validation. Unrelated
metadata and other-workspace membership remain excluded.

A separate operator-only enable operation requires the exact desktop scope,
completed setup plan and reviewed digest, then calls the existing capability
workspace-enable endpoint. That owner requires current passed validation against
its captured configuration and changes only the chosen workspace membership.
No registry/gateway policy was relaxed. A successful protocol check reveals an
explicit Enable in this workspace button; it is never called automatically.
An uncertain enable response disables the attempt and directs read-only catalog
refresh, without retry. Invocation approval and engineering reviews remain separate.

Verification: combined prototype/existing capability-enablement tests had 82 pass
and one new test fail because its assertion used the main application's normalized
error key rather than this small FastAPI fixture's raw detail.code. The assertion
was corrected to the existing route contract; that exact test then passed. The
existing owner tests cover absent/stale validation, exact workspace membership
and role enforcement. Four bridge catalog tests passed. Frontend suites passed
16 tests with one failure exposing stale unavailable-feature copy; corrected copy
then passed all five connection tests. Five sign-in and seven home tests passed
in the combined run. TypeScript, ESLint, Ruff and the rebuilt native bundle passed;
the final bundle has 2,201,327 bytes and zero external assets.

These are isolated fixtures/owner regressions, not SteveCAD OAuth or desktop
acceptance. No real workspace grant or engineering run was made. Installed
plugin 0.4.0 and retained services remain unchanged. Returning after a full panel
reload still needs durable plan discovery/recovery before a complete management
claim; current mounted attempts intentionally do not offer automatic retries.
