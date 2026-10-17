# Next management gap: custom MCP source in the desktop panel

Experimental implementation in a separate worktree; not installed or enabled. Remote preview, exact-source publisher review and saved-plan recovery have bounded qualification below.

User journey: Connections → Add custom connection → enter a supported source →
review normalized source and effects → explicitly approve/apply → validate/sign in
→ enable for this workspace → return to the original workflow. Registration,
authentication, workspace availability, task grants and engineering review remain
separate authorities.

Existing owners:
- OnboardingWizard.tsx source normalization UI and mcp-service.previewImport.
- POST /api/mcp/imports/preview and install-plan source fields import_preview_id,
  draft_id, draft_digest (InstallPlanRequest already supports workspace scope).
- NativeConnections.tsx existing workspace/session identity, plan review,
  uncertain-result stop, saved plans, sign-in, validation and enable controls.
- desktop_backend.py scoped_plan and connection_plan; mcp_bridge.py closed
  app-visible connection-plan operations. No generic REST or command proxy.

Important discovered mismatch: the current standalone OnboardingWizard buildPlan
sets requested_scope=global_registered and independently_completed_license=true.
A straight component transplant would broaden desktop scope and silently attest
publisher setup. Reuse its source-entry/normalization presentation where useful,
but retain the existing native workspace plan and explicit publisher state.
Do not weaken or change the standalone global flow as incidental scope.

Before implementing, inspect import-preview redaction/ownership and plan replay
contracts. Desktop UI tool arguments must not carry raw passwords, OAuth tokens,
credential headers or secret environment values. Start with the supported
non-secret source forms and explicitly diagnose unsupported credential entry;
credential setup continues through the existing private credential/sign-in owner.
Do not silently interpret a local command as authorized execution.

Qualification: no effect from preview; exact source/draft digest and workspace
scope enforced; stale/cross-workspace plan denied; malformed/secret-bearing input
handled without leaking; duplicate and lost acknowledgement reconcile saved plan;
apply only on explicit reviewed plan, no automatic task grants. Test default
standalone source flow as well as desktop transport. Use a private non-effecting
fixture, not the independent MCP catalog-testing session's state. Preserve the
original SteveCAD process and return target; this feature does not qualify OAuth
callback routing or engineering execution.

Keep the currently running integration gate candidate frozen. Implement this
follow-on separately after verifying the smallest existing-owner contract.

## Existing contract findings

ImportPreviewRepository is intentionally in-memory with expiry. It discards raw
source and retains a normalized/redacted preview. A backend restart invalidates
an unapplied preview; the UI should say so and request an explicit new preview,
not pretend it is durable. Saved InstallPlan records already persist the source,
draft digest, workspace and separate approval state; no new database is needed.

Existing saved-plan discovery requires both workspace_id and capability_id.
Imported capability identity is computed by the owning planner (`import:<id>`).
An acknowledgement lost before receiving that identity cannot be recovered by
the existing catalog-only picker. Before enabling apply, add bounded workspace
plan discovery through the same owner (or a verified existing identity-based
lookup), then test lost-response reconciliation. Do not infer installation success
from preview, re-create plans automatically or put recovery truth in browser state.

Existing test_install_plans.py already covers secret non-disclosure and bounded
workspace/provider-scoped saved-plan discovery. Extend those owners' meaningful
cases for imported sources, retaining global-vs-workspace and cross-workspace
separation. Standalone wizard assumptions and transient preview behavior are
implementation facts, not new product requirements.

## Implementation tasks

- [x] Extend the existing plan owner with optional provider filtering; prove workspace/global isolation, bounded results and imported-plan recovery without changing approval.
- [x] Expose discovery through the scoped desktop transport and existing Connections UI; served-panel qualification remains pending.
- [ ] Add non-secret custom-source preview and exact-draft plan creation with explicit publisher setup state.
- [ ] Qualify lost response, expiry, restart, source mismatch and uncertain effects.
- [ ] Verify served panel, shared regression and repository gates before a named plugin candidate.

No installed runtime or live configuration is changed by this worktree. Evidence will distinguish owner tests, transport, served browser and Windows acceptance.

## Recovery foundation checkpoint

Implemented optional provider filtering in the existing durable install-plan owner,
service and scoped desktop read tool. Omitted provider discovers at most 20 plans
from this exact workspace; explicit empty/unknown provider still filters. Global
and other-workspace plans remain excluded. No approval/apply path changed.

Validation: 10 install-plan tests and 6 desktop connection tool tests pass.
Ruff and git diff whitespace checks pass. HTTP discovery suite: 15 passed outside the sandbox (session 11903).
The original sandbox run (55814) was deliberately stopped after a minimal
anyio worker-thread callback reproduced a sandbox hang (exit 124) while the
same callback completed outside it (exit 0). This was a host-test limitation,
not a failed product assertion. Initial new HTTP test had a syntax
error during collection, corrected before rerun. Eight Connections UI tests, TypeScript and focused ESLint pass. The workspace-wide
Saved setup control is implemented; custom-source preview/creation remains
unimplemented. These are owner, HTTP, transport and component checks, not
served-panel or Windows acceptance. Installed 0.10.0 is untouched.

## Custom HTTPS preview and plan checkpoint

Implemented the first custom-source form, using existing preview and plan owners.
Two app-visible tools expose only typed public HTTPS endpoint preview and exact
preview/draft plan creation. No arbitrary REST/command bridge. Desktop preview
identity is ephemeral, bounded to 128 active entries and 15 minutes, and bound to
workspace/session. Owner expiry and digest checks remain authoritative. Restart
requires a new explicit preview; saved plans remain in the existing durable owner.
Publisher completion defaults false; the form does not approve/apply or grant tools.
Uncertain plan creation stops and points to bounded saved-plan recovery.

Credentials, query/fragment/userinfo URLs, local commands and full configuration
imports are explicitly unavailable in this form. This is an incremental remote
source path, not completion of all MCP management or engineering readiness.

Validation: 20 HTTP scope/expiry/owner tests and 11 form/connections component
tests pass; TypeScript and focused ESLint/Ruff pass. Initial bridge regression
reported the old 34-tool count against the intended two additions; the maintained
count is now 36 with explicit new-tool assertions; all 25 connection/bridge
tests pass. A synchronous in-flight guard prevents duplicate preview/plan calls
before React updates disabled controls; the form test double-clicks plan review.
Served panel, exact draft mismatch against real owner, restart with actual backend,
and installed/Windows acceptance still require qualification. Installed runtime
remains unchanged; no real connection, install or engineering run occurred.

### Shared-owner blocker found before installation qualification

`install_plans._license_requirement(entry=None)` always returns license_unknown,
even when independently_completed_license is true. No supported imported-license
review action was found in the owner/API. Therefore this remote-source slice
currently previews and saves a blocked plan; it does not enable custom installation.
The form now says so. Do not edit stored plans or equate the account/terms checkbox
with a source-license grant. Next work must define the smallest explicit review
record in the existing owner, bind it to exact imported source/draft and review
identity, invalidate on source changes and requalify through approval/apply.
This is shared onboarding debt, not a SteveCAD-specific workaround.

## Reused publisher review owner (supersedes the blocker above)

The existing missing-license catalog path already records independent completion
with a timestamp in an exact, actor-attributed plan. Imports now use that same
path, retaining unknown license metadata and requiring explicit completion.
No new review database, approval type, terms acceptance automation or exception
is introduced. Reviewable is not approved; plan digest, machine state, approval
and apply checks remain unchanged. Existing blocked plans are immutable.

Necessary caller correction: standalone OnboardingWizard formerly sent true
for every source. Custom imports/local commands/remote sources now default false
and require a source-bound checkbox; editing normalized source invalidates it.
The existing catalog/host behavior is unchanged by this narrow correction.
Desktop custom source has the same explicit confirmation and resets on edits.

11 plan-owner tests and 23 onboarding/desktop UI tests pass, including source
change, old/new plan digest mismatch, no automatic approval/apply, default block
and explicit review. Actual isolated apply/validation and served UI are next;
no provider installed and no real publisher review asserted by these fixtures.

## Actual MCP/API/storage proof

Five checks pass against the fresh authenticated loopback API on port 8169,
state `/tmp/wright-desktop-custom-source-state-20261015-01`: default source-review
block, explicit synthetic fixture review producing an unapproved workspace plan,
wrong draft digest rejection, wrong-session rejection, and exact saved-plan
discovery/readback. No provider was contacted and no plan was approved or applied.
The endpoint is fictional example.invalid; no real publisher review is claimed.

The first probe incorrectly expected structuredContent for workspace creation.
Its failed source/log/report are retained as failed-01-*; the corrected probe
recovered that same workspace through read-only discovery and did not recreate it.
The successful report records hashes of the actual backend, bridge and plan owner.
This establishes the observed transport/storage path, not native Windows UI,
installation/validation, credential entry or complete engineering demonstrations.

## Served-panel qualification

Actual Chromium/native-resource/MCP/API/storage proof passes four journeys: preview
without plan creation, explicit synthetic review saving an unapproved exact
workspace plan, saved-plan discovery, and 460px layout without horizontal overflow.
The first passing functional probe exposed a visual defect: review was below the
long catalog. Review/saved results now precede the catalog and receive focus/scroll.
The final proof additionally requires the review in the viewport, exact endpoint
and recorded publisher-review status. Removed the inapplicable catalog confirmation
checkbox from imported plans and fixed checkbox width in the native frame.

See custom-connections-evidence.json for exact resource/report hashes and screenshots.
Earlier screenshots/reports remain in the private state directory. This does not
establish actual Windows native hosting, approval/apply, authentication, provider
validation or engineering readiness. Named installed 0.10.0 remains unchanged.

## Real restart and registry-only apply

Actual owned API restart preserved all five earlier plans exactly (matching
record hashes), rejected the transient preview with HTTP409, and created no new
plan or effect. Before/after logs, scripts and receipts remain in the isolated
state. Only the verified private API was stopped; installed services were untouched.

A subsequent explicit browser test created a distinct fictional endpoint plan,
proved unapproved apply was denied, then clicked approval and apply once each.
The actual owner completed one registry-only onboarding run. Independent readback
confirms installed=true, active=false, default_enabled=false and no workspace
enablement. No protocol-validation/enable tool was called. The six browser
checks and registry readback are indexed in custom-connections-evidence.json.
These are synthetic setup reviews and actual local registration, not live provider
validation, credentials, SteveCAD OAuth or engineering outputs.

SteveCAD registration was already qualified on14October; do not repeat it as new
progress. Existing confirmed account setup still needs Windows-to-GB10 callback
routing and genuine user OAuth consent before authenticated engineering runs.

## Unavailable-provider qualification

The registered example.invalid fixture was explicitly validated once through the
served panel. Wright recorded failed protocol validation, exposed no Enable
control, denied a direct exact-plan enable request and left the provider inactive
and workspace-disabled. A fresh read-only panel then searched the normal catalog
and displayed the saved failed validation and observation without retrying.
Three live failure checks and two reopen/narrow-panel checks pass. These receipts
are indexed in custom-connections-evidence.json; no real engineering provider
or user account was contacted.

Positive HTTPS fixture qualification is in progress in separate isolated state
/tmp/wright-desktop-custom-https-state-20261015-01. Default trust rejects its test
certificate; only the test API process trusts that certificate. No global TLS
change or disabled certificate checking. Do not claim its pending result.

## Imported credential identity defect found by positive qualification

The private HTTPS fixture passes direct protocol initialization and the unchanged
SseRunner with a normal ID. Imported IDs (import:draft-...) instead fail
CredentialReference owner validation before transport startup. Therefore the earlier
example.invalid validation established failure propagation/enable denial, but did
not establish a DNS/unreachable-provider response. Preserve and correct attribution.

Proposed narrow correction: permit colon in credential owner IDs only, preserving
canonical IDs and existing file keys. For these previously unsupported owners,
derive the environment/mounted filename from SHA256 of the exact full reference
under WRIGHT_SECRET_REF_SHA256_. Existing references retain their names. The new
prefix is disjoint from the four existing namespace prefixes, avoiding silent
credential aliasing with underscore-normalized server IDs. No slash/backslash or
name-character relaxation, no key migration, no gateway or vendor change.
Tests must prove imported isolation across file/environment/mounted providers,
legacy stability, unsafe-path rejection and actual HTTPS validation afterward.

## Positive HTTPS recovery result

The isolated served-panel recovery passed all five checks after the credential
identity correction: it recovered the exact completed setup without replaying
approval/registration, passed TLS-verified MCP initialization and tool discovery,
explicitly enabled workspace availability, rediscovered saved setup and fit a
460px panel. The report and hash are indexed in the evidence JSON. This is a
private protocol fixture in a simulated desktop host, not Windows acceptance,
SteveCAD sign-in, engineering invocation authority or a completed demo. The
named installed plugin is unchanged.

Focused credential/provider/catalog-preservation regression: 12 tests passed;
Ruff passed for the changed core source and tests. This does not replace the
repository integration gates or Windows native acceptance.

##17 October: local command form

The integration-completion follow-on adds typed, bounded literal command/argument
preview in the same custom form and existing setup owners. Environment/credential
values and full configuration-file import remain unavailable. The saved review
shows exact source after reopening, and uncertain plan creation recovers through
read-only saved-plan discovery. Actual resource/MCP/browser proof preserves two
blocked plans with publisher completion false and performs no onboarding effect
or provider call. This extends source entry, not general engineering qualification.
See integration-completion-plan.md and
/tmp/wright-desktop-command-setup-proof-20261017/checkpoint.json for exact tests,
retained failures and resource identity. Installed0.14 is unchanged.
