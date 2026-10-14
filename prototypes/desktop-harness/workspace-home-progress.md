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

## Reopen saved setup without recreating it

The existing install-plan owner now provides a bounded read of the 20 newest
plans for one exact workspace/provider. It queries the existing plan table;
no new state store, scheduler or setup lifecycle was added. The scoped desktop
endpoint filters exact identities again and returns only plan-list metadata.
A UI-only transport operation and Saved setup control let the operator select
an existing record and read its current full state through the existing owner.
Opening history does not approve, apply, validate, enable or retry anything.
Missing or unreadable history is distinct from an empty list. Expired or changed
plans remain subject to existing mutation guards; reading history grants nothing.

Verification: 87 existing install-plan/prototype tests passed, followed by the
new endpoint scope-filtering test (passed). The owner test uses real isolated
plan persistence and proves ordering, limit, workspace/provider exclusion and
unchanged original records. Thirteen Connections/home UI tests passed, including
reopening a completed plan using only catalog/list/read operations. Ruff,
ESLint, TypeScript, diff checks and native bundle build passed (2,202,836 bytes,
zero external assets). Real Windows reopening and provider authentication are
still unverified; installed plugin/services were not changed.

Baseline PR 153 remains at bcf03161. Current-head checks except the Windows
backend job have completed successfully. The specific job 116123620167 is still
in_progress in its Run pytest step, verified via the GitHub job API. No restart,
additional push or premature merge was performed.

## Combined real-MCP browser qualification

Created fresh isolated state at `/tmp/wright-desktop-combined-proof-20261014-01`
and loopback API 8133 from feature db12003a (native editor/common working view
enabled, MCP autostart disabled). Existing services/state/plugin remain untouched.
The official MCP client created a new desktop-bound workspace and an unchanged
copy of the existing SteveCAD native workflow; source SHA-256 remains
`04a55022d096694bee841163ee710b26f573affd47f16aa789bd403231e2c5de`.
Tool discovery reports 29 tools. A fresh setup plan records the user's existing
publisher account confirmation and is reviewable; it was not approved/applied.
Receipts: `home-probe.json`, `plan-confirmed-probe-02.json` and private service logs
in that state directory. No provider call, sign-in, workspace grant or run began.

Upgraded the existing browser acceptance harness to use the actual official MCP
client/stdio bridge for all UI operations, instead of recreating their transport
responses through direct HTTP reads. The simulated host fixture permits only
specific read tools and exact source/workspace scope. Direct source-owner reads
remain solely as before/after integrity checks. The MCP client closes on normal
walkthrough cleanup.

All combined checks passed in
`/tmp/wright-desktop-combined-proof-20261014-01/browser-home-1792015977834/report.json`:
workspace/source discovery, shared editor entry, exact workspace restoration,
real catalog search and saved-plan reopening, narrow fit, draft protection,
unchanged accepted source and zero browser errors. Screenshots include home,
editor, saved setup and narrow home. Visually inspected the saved-setup image;
it clearly labels the simulated desktop host and no engineering run. Windows
rendering, actual sign-in/enablement and engineering outcomes remain separate.

## Named 0.6.0 installed — Windows acceptance pending

Applied the saved goal's authorization to update only the named prototype after
package/MCP/browser qualification and preparing `native-home-update.md` with
scoped rollback. Private backup/receipts:
`/tmp/wright-desktop-plugin-update-20261014-01/`. Semantic config comparison proves
only the named marketplace source changed. Installed 0.6.0 files match the
candidate exactly. Earlier cached 0.3.0/0.4.0 bytes were preserved/restored; existing
services and old source/state remain unchanged. The old selected state had no
native process run rows. No desktop restart or unrelated setting change.

The selected service is API8133, runtime feature db12003a with identical later
documentation/package checkpoints, and isolated combined-proof state. Preserve
this served runtime: do further runtime work in a separate checkout/state until
another deliberate qualified update. `desktop-home-walkthrough.md` gives a short
read-only fresh-chat Windows check. Fresh-chat rendering, host permissions,
OAuth navigation and actual engineering runs are not established by installation.

The current official plugin packaging documentation still supports the legacy
compatibility manifest and local marketplace source; installed CLI0.159.2's
scoped commands were locally verified rather than assuming all current desktop
surfaces share the same lifecycle. Documentation reference:
https://developers.openai.com/plugins/build/plugins

Installed-package read-only protocol verification also passed: 29 tools and the
exact resource hash, receipt `installed-0.6.0.json` in combined-proof state.

## Continuation isolated from installed 0.6.0

Further implementation now uses `/tmp/wright-desktop-engineering-demos-next`,
branch `codex/desktop-engineering-demos-next`, based on 6e894f3d. Its locked
`uv sync --frozen --all-packages --all-groups` completed in a separate environment.
The selected plugin continues using the previous worktree and API8133 unchanged.
This chat's actual connection-status tool still reports the preserved 0.4.0
binding `115211f7574bf6f4a8b9dbb8866d9830825e182607fa470aee3e10e76799afed`,
not API8133's `c94b7ca3a50b14a00a018c932b7781fb67fff5dba6fc63a5f804b56f37d43955`.
Thus this chat's old tool inventory is confirmed, not inferred from a stale UI.
Use the prepared fresh-chat walkthrough for actual Windows acceptance.

The next engineering slice must qualify more than SteveCAD sign-in. Static
inventory of the unchanged native workflow is retained in
`engineering-dependency-inventory.json`: desktop AI responses, SteveCAD bounded
agent/tool tasks, existing shell-backed transfer operations, document export and
Blender rendering. Three saved provider UUIDs are local bindings, not portable
capability identities. Do not silently remove those stages or replace their
engineering outputs with text. Rebind through the existing accepted-source and
readiness owners only after provider qualification. The current desktop adapter
explicitly rejects image inputs, and the native representation port supports only
bounded raw text; image/artifact handoff qualification is a real next requirement.
No provider was installed/called and no source requirements changed in this audit.

## Bounded PNG/JPEG representation transport — development only

The continuation worktree's existing native representation port now admits raw
PNG/JPEG alongside its existing passive text formats. It reuses the existing
scoped process representation owner, exact run/source/reference request, response
hash/nosniff headers, streamed byte count and SHA-256 verification. The unchanged
1 MiB transport ceiling remains explicit; SVG and other unsupported formats or
oversize files return capability-unavailable. No arbitrary URL/file access,
derived renderer, executor or independent artifact owner was added. The shared
process client/UI kit already has passive image rendering; its native transport
can now carry the same bounded bytes and media type.

21 Python port tests and 15 native-client tests passed, including altered-byte
rejection for both image media types, explicit SVG/oversize rejection, exact
run/reference requests and existing text/permission behavior. Ruff, ESLint and
TypeScript passed. These tests prove transport contracts using synthetic bytes;
they do not prove image decoding, actual CAD-image presentation, native desktop
payload limits or model image reasoning. Actual browser/desktop image proofs,
large artifacts and model-input handoff remain qualification work. No resource
bundle or installed package was replaced; 0.6.0 remains frozen on API8133.

## Actual browser image decode and fallback

`native_image_acceptance.mjs` builds the real native process client and shared
RepresentationViewer into a local browser fixture. Its tool reply is controlled;
it is not an API, actual MCP transport or Windows-host proof. The fixture uses
only representation reads. The retained historical CAD capture
`artifacts/stevecad-demonstrations/qualification/native/06-inspect-coupon-1.png`
(13,661 bytes, SHA-256
`b85a1e81d4e36cc2452df4f96a348e9e474c415207996b1884ddc312bd7a4adb`)
decoded at its actual 800×640 dimensions through the native client and shared
viewer. A deliberately malformed bitmap then reached the existing explicit
fallback without another request. The malformed reply is a decoder fixture,
not a claim that corrupt bytes passed the backend hash guard.

Evidence: `/tmp/wright-desktop-image-display-20261014-01/report.json` and
`historical-image.png`. Visually inspected the screenshot; the historical part
is visible and the fixture/no-new-run label is explicit. The initial harness
attempt failed before launch because React's Vite plugin is installed in the
web workspace; resolving it from that workspace fixed the harness without a
dependency change. No source artifact, installed runtime or live configuration
was modified. Real owner-to-MCP-to-native rendering and JPEG decoding remain
separate qualification work, as does model image reasoning.

Optional progress caption, not published: “Checking CAD image inspection in
Wright's desktop integration. This local display test uses a retained historical
capture; the new end-to-end engineering run is still ahead.” Prefer real workflow
screenshots for a fuller milestone; do not market this fixture as a fresh design.

## Native image read against the real artifact owner

Added an integration case in the existing authenticated artifact API suite. It
uploads a copy of the historical PNG through the real input owner, prepares its
exact file binding, then invokes the actual native MCP tool against the real
representation endpoint through an in-process HTTP transport. The image bytes,
media type and SHA-256 match; changing only the isolated uploaded copy produces
SUBJECT_STALE. Both reads retain the exact prepared-input identity and no run
is created. The original historical capture remains untouched.

The first fixture correctly failed because it declared an engineering-document
input and attempted to supply a bitmap. The revised private fixture declares
reference_images on the input output and its consumer input. No production
readiness rule was changed. The focused integration test then passed (4.28s).
Existing Starlette/httpx deprecation warnings remain unrelated to the result.
This composes actual upload/preparation/artifact owners with the native tool;
it does not establish a live network, actual desktop UI or model image uptake.
Combined with the separate real decoder fixture it strengthens local evidence,
but cannot replace the required installed-host engineering demonstration.

## Model-image handoff boundary audit

The panel-image work does not enable model image tasks. Inspected the actual
workflow reference, desktop adapter/request, pending-task tool and invocation
redaction owners and recorded the concrete next spike in
`model-image-handoff-spike.md`. Reuse inline references and existing durable
request/evidence ownership with the unchanged 256 KiB total payload cap; do not
remove rejection or invent an attachment store without qualification. Thirty-three
existing desktop boundary/repository/execution tests passed together before any
model-image change. Actual desktop image perception remains a required proof.

## Opt-in model-image request profile — not served

The isolated continuation now adds `image_input_profile` to the frozen desktop
binding, defaulting to `unavailable`. The opt-in `inline-png-jpeg-v1` path admits
bounded inline PNG/JPEG data in response requests and validates canonical image
parts in bounded-action requests. No URL/file fetch, image resizing, skipped
input or alternate model path is introduced. Media signatures and base64 encoding
are checked; full decoding remains the existing reference-reader responsibility
and separate qualification, not a claim made by the transport signature check.
The existing 256 KiB aggregate request guard still runs before persistence.

39 desktop boundary/repository/execution tests passed. New cases prove exact
image retention in a real isolated durable request, distinct frozen resolution,
redacted invocation observations, rejection of URL/SVG/bad encoding/media
signature, and rejection of aggregate oversize. The reply is explicitly synthetic
and establishes no image perception. Existing default image denial remains green.
Ruff passed. No preview composition selects the new profile, and the installed
0.6.0 runtime is unchanged. MCP image-content delivery, actual desktop perception,
action-image success and continuation/failure qualification remain required
before dependent engineering image tasks can be enabled.

## Exact pending-image MCP port — development only

Added a read-only pending-image tool to the continuation bridge. It reads only
from the existing scoped pending-request owner, reconstructs the typed request,
verifies original request/binding digests and requires the opt-in image profile
and exact image index. It emits one standard MCP image content block plus identity
metadata. No file/URL lookup, state mutation, response submission or dispatch.
The ordinary pending view replaces image bytes with indexed hash/media/size
references and explicitly identifies itself as a presentation projection; the
original request digest still identifies the original durable bytes. Projection
uses a fresh parsed copy and does not modify the owner payload.

Seven new tests pass: exact PNG content, no base64 in text/structured metadata,
nonmutating projection, wrong request/binding/scope/index denial. Sixteen existing
bridge tests also passed. The initial new test assumed the pending tool had a
structured-result tuple; it actually retains its existing text JSON result.
Correcting that test to inspect the real return contract resolved the failure;
the production return contract was not changed to satisfy the test. Ruff/diff
checks passed. These are direct MCP-server function tests, not a wire/desktop
perception proof. No installed profile selects the new 30-tool development bridge;
installed 0.6.0 remains unchanged at 29 tools with image reasoning unavailable.

## Image connection identity and opt-in composition

The image read port now compares the pending request's full frozen binding with
the live client binding, in addition to checking the supplied digests. A stale
request from another connection is denied even when its own digests are valid.
The preview composition exposes an explicit `--enable-image-inputs` flag that
requires the desktop bridge; its value is included in the runtime identity and
selects the typed image profile. It does not relax engineering source readiness.
Installed 0.6.0 and all existing services remain unchanged.

22 focused image/boundary tests passed (3.67s), including foreign-connection
denial and default/opt-in frozen identity separation. Ruff and whitespace checks
passed. Actual MCP wire delivery and desktop perception remain unverified; the
flag is a development qualification option, not engineering-image acceptance.

The repeated account response confirms the existing SteveCAD account prerequisite
already recorded above. No sign-in, billing, workflow review or external-action
approval is inferred. Corrected the Windows handoff's stale installed-version
note to 0.6.0; callback routing and Windows observations are still pending.
PR 153 remains draft with Windows backend CI in progress at this check; no merge
or further push was attempted.

## Actual MCP image wire and reconnect qualification

Started a new loopback-only preview on port 8134 with isolated state
`/tmp/wright-desktop-image-wire-20261014-01`, explicitly enabling image transport
but no native editor, provider connections or engineering execution capability.
The installed 0.6.0 service/plugin is unchanged. The previous turn made concrete
progress (committed connection guards); this turn adds actual transport evidence.

`image_wire_probe.py` creates a private workspace through the normal MCP tool,
then inserts a clearly synthetic request through the existing durable request
owner. It uses the retained 13,661-byte CAD capture, not a newly engineered result.
The official Python MCP client starts the actual bridge process; that bridge calls
the real authenticated HTTP service. Protocol 2025-11-25 delivered one PNG content
block with exact SHA-256
`b85a1e81d4e36cc2452df4f96a348e9e474c415207996b1884ddc312bd7a4adb`.
The pending presentation omitted base64, a wrong digest returned an error without
image content, and the original request remained unchanged. Receipt:
`/tmp/wright-desktop-image-wire-20261014-01/image-wire.json`.

`image_wire_lifecycle_probe.py` starts another actual MCP process against that
same service/state and retrieves the identical image. It then cancels only this
synthetic request through its existing repository owner: the same image call is
denied and the original durable payload remains retained. Receipt:
`/tmp/wright-desktop-image-wire-20261014-01/image-wire-lifecycle.json`.
Both probes passed; Ruff passed. No model response was submitted, no engineering
run exists, no workflow-cancel or API-restart claim is made. Actual desktop image
perception, action-task image delivery and broader lifecycle qualification remain
required before enabling dependent engineering tasks.

The baseline Windows CI job 116123620167 was authoritatively confirmed still
running its pytest step during this checkpoint. No cancellation/restart/merge.

## Files discovery in the native home

The shared home now offers Files alongside Workflows and Connections, using the
same exact workspace/session file-tree read already owned by Wright. Files lists
all saved file metadata and filters by path; Workflows retains its `.wflow`
filter and existing editor entry. Selection clears old files and the query;
existing stale-response and foreign-scope checks remain in force. There is no
new file service, content read, executable tool or automatic open. Preview,
upload and download are explicitly unavailable, not represented as completed.
Recent runs and the remaining file lifecycle still need implementation.

Eight home component tests passed, including nested non-workflow discovery and
filtering with no additional tool calls. The rebuilt native resource is 2,203,940
bytes with no external assets. A fresh isolated service on 8135 and workspace
`7d4ed5ed-6f02-479c-95a3-c6432893af52` use an unchanged SteveCAD workflow copy and
an unapplied reviewable setup plan. No provider or engineering run was started.
All six existing/extended browser acceptance checks passed through the actual
MCP bridge: home/Workflows/editor/Back, Files filtering, saved setup recovery,
narrow layout, draft protection and unchanged accepted source with zero errors.

Report and screenshots:
`/tmp/wright-desktop-files-proof-20261014-01/browser-home-1792017344207/`.
Visually inspected `files.png`: scoped selection, compact controls, search and
explicit limitations are legible. This is a simulated desktop host on GB10,
not Windows acceptance or an installed plugin update. Suggested progress caption:
“Wright prototype: find workspace files beside engineering workflows. Local
integration preview; file transfers and live engineering qualification are next.”
No publication performed.

The first TypeScript check caught a test-only unsupported `exact` option on
Testing Library's role query. Removed it; production UI behavior was unchanged.
The subsequent complete TypeScript build check and targeted ESLint check passed.
PR 153 still reports Windows backend tests in progress; no merge was attempted.

## Recent runs — implementation and component qualification

Located and reused `/api/workspace/workflow-sources/runs`, backed by the canonical
source recorder's bounded `recent_workflow_runs` reader and existing review owner.
The separate Rivet operations history is not the source of this panel's records.
A new read-only `wright_workflow_history` port verifies workspace/session first,
checks the returned exact source/workspace and bounded record list, and projects
only run/source identities, timestamps and recorded state. It does not send
embedded results into the home panel or invent execution status.

Recent runs in home selects a workflow explicitly, loads its recent recorded
history, distinguishes load failure from no records, and permits Inspect run only
with recorded run and source identities. The action delegates to the existing
`wright_process_view` read port. Existing process/source checks remain authority;
there is no Start, Resume, approval, replay or current-source substitution.
Older-source navigation remains constrained by the panel's existing revision gate.
Successful older-revision inspection is not claimed.

23 Python history/bridge tests passed, including denied-session no-read, wrong
workspace/source/list bounds, preserved state and omitted embedded payloads.
11 home/history component tests passed, including explicit navigation and a
failed exact-run open without retry. TypeScript, targeted ESLint and Ruff passed.
Initial failures are retained here: the pinned MCP SDK requires `dict[str, Any]`
for forced structured output (bare `dict` failed registration); the new read port
also requires the exact development inventory count to change from 30 to 31.
Both were fixed without relaxing schema or inventory assertions.

This new UI is not yet bundled, browser-qualified, installed or user-accepted.
Next: prove actual recorded run discovery and exact-run opening through a fresh
served home, including stale source and empty history. Existing 8134/8135 services
were started with earlier frozen bridge bytes: do not reuse them as current-runtime
qualification after this bridge edit. Installed 0.6.0 is separate and unchanged.
The previous goal turn was progress (qualified Files implementation); this turn
adds the run-history implementation. The outstanding Windows CI check was still
in progress on the latest authoritative PR query; no merge or push attempted.

## Recent runs served qualification — real digital recorder entry

Rebuilt the native resource (2,206,768 bytes, no external assets) and started fresh
isolated service 8136/state `/tmp/wright-desktop-history-proof-20261014-01` with
the native editor/common working view. Used the existing protocol probe to run
the bounded inspection-brief fixture. This desktop conversation read the exact
pending instructions and authored the response; the existing MCP transport
submitted it and Wright saved/completed the run. No API model, Hermes worker,
provider invocation, CAD measurement, review or manufacturing release occurred.
Run `626df06a391f45589a590212d2210da0` completed; exact request/reply and owner
receipts remain in that state's `protocol-probe.json` and answer file.

Extended the existing browser harness to permit only the scoped history read and
exact-run snapshot ports. It entered through home, discovered the actual recorder
entry, opened its shared working view and verified “Process completed,” returned
to the same workspace, and retained editor/draft/narrow/Files checks. Six checks
passed in `browser-home-1792017656281/report.json`; the earlier initial navigation
pass is retained in `browser-home-1792017621727/`. Visually inspected the actual
working-view screenshot. The fixture banner correctly identifies a simulated
desktop host; no Windows user-acceptance claim is made.

Then saved a comment-only new revision of this isolated text workflow through
the normal source CAS tool. Original run/output and source revision are retained;
`history-drift.json` records before/after digests. Opening its older run correctly
kept the home history visible and displayed the existing exact-source warning.
The initial browser assertion incorrectly expected the component's local alert;
the warning actually resides in the panel's top-level status area. Failure and
screenshot retained in `browser-home-1792017688563/`; no production guard was
changed. Corrected the assertion to require that exact rendered warning and
continued qualification. This confirms a safe limitation, not successful viewing
of arbitrary historical source revisions. Full older-revision navigation remains
work to assess against the existing historical recorder adapter.

This text-only run is navigation evidence, not a replacement for SteveCAD,
OASiS, Robot Tracking Diagnosis or manufacturing-preparation qualification.
Installed 0.6.0 remains unchanged. Windows CI job 116123620167 remained in progress
at the authoritative check during this turn.
The corrected stale-source walkthrough passed all six checks in
`browser-home-1792017716545/report.json`, with zero browser errors and no mutation
during navigation. Suggested screenshot/caption: `browser-home-1792017656281/recorded-run.png`
— “Wright prototype: revisit a recorded process from the desktop-side panel.
This local demonstration is a text-only inspection brief; live CAD qualification
is still ahead.” Prepared only, not published.
