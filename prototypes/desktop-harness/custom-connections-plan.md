# Next management gap: custom MCP source in the desktop panel

Read-only architecture checkpoint; not implemented or enabled.

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
