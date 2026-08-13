# Capability Library UI Journey Contract

## Top-level information architecture

The existing global registry navigation opens **Capability Library**. The page has three stable regions:

1. **Library header**: global search, offline/update status, Add capability, and administrator Catalog history.
2. **Filter rail/drawer**: domain, application/lifecycle, machine compatibility, evidence, platform, maturity, risk, locality, host software, validation, and installed state.
3. **Results and detail**: comparison-friendly summary cards/list plus a detail drawer/page. Selecting an item never installs, starts, or enables it.

Discovery, onboarding, workspace enablement, and workflow execution must never share a single ambiguous “Enable” action.

## Capability result contract

Every result shows:

- name, vendor, canonical id
- engineering domain/task summary
- evidence-class badge
- current-machine status: Works here / Does not work here / Needs a check / Blocked
- exact primary reason for any non-compatible state
- locality/transport and host-software indicator
- installed/connected state separately from workspace-use state

Unknown, failed, blocked, excluded, and no-public-MCP records remain searchable. Their action is Details, Check requirements, View alternative, or Report/update evidence—not Install.

## Details contract

Detail tabs or sections use this order:

1. Overview and engineering tasks
2. Works on this machine
3. Source and evidence
4. Setup requirements and exact data/credentials touched
5. Validation history and limitations
6. Example workflows and alternatives
7. User-owned status: installed, explicitly disabled, workspaces

The primary action is selected from `Check requirements`, `Review setup`, `Validate again`, or `Choose workspace`; never from catalog metadata alone.

## Add capability wizard

### Step 1: Choose source

Cards with stable test IDs:

- From Wright catalog
- Paste MCP configuration
- Remote HTTP/SSE endpoint
- Local command/development server
- Report a missing capability

### Step 2: Normalize

- Catalog: confirm identity/revision.
- Paste: detected format, one row per normalized server, redacted fields, field-level warnings/errors.
- Remote/local: structured fields, never a single shell-evaluated text blob.
- Report: structured vendor/domain/task/platform/source form.

Back and Cancel have no side effects.

### Step 3: Check this machine

Show observation time, platform/architecture, resolved runtime/package manager/host facts, and reason-coded compatibility. The check is visibly labeled read-only.

### Step 4: Review Install Plan

Sections:

- What Wright will add or connect
- Exact pinned source, endpoint, command tokens, and transport
- Network, storage, host, credential, and license/terms requirements, including whether the user must independently complete external acceptance before Wright can apply the plan
- Files/processes/configuration affected
- Validation after setup
- How rollback/remove works
- Approval requirements and blockers

The approval control repeats the capability name and is disabled for blocked/stale plans. A material recheck returns the user here with a changed-fields summary.

Wright never presents an “Accept license” control. When external terms are required, the plan links to the authoritative source, remains blocked, and permits the user to record only that they independently completed the external step.

### Step 5: Credentials

Credential inputs use the existing secret component and API. The wizard sees configured/not-configured booleans after save, never reads values back. The plan stores names and requirements only.

### Step 6: Apply and validate

Show ordered progress with prepare/apply/initialize/discover/read-only-probe/rollback states. Failure copy identifies the failed stage, what was cleaned up, any residue, and next recovery step.

### Step 7: Choose workspace

After acceptable validation, list permitted workspaces. Explain: “Available in this workspace” does not mean “approved to run every tool.” Completion returns to capability detail with both global and workspace states.

## Catalog update panel

Administrator-only panel shows:

- current bundled/active/previous snapshot and update channel health
- Check for update (no auto activation)
- signer/key id, issue/expiry, sequence, schema, and verification results
- counts and expandable identity/field diff
- explicit “Activate catalog data” language
- rollback to the named previous snapshot
- permanent note: updates do not install, connect, enable, disable, or change credentials

If verification fails, keep the current state dominant and show stable failure/recovery information. Do not offer an override that bypasses signature, freshness, schema, or identity failures.

## Missing capability form

Replaces all browser prompts. Fields: name, vendor, source URL, domains, task, platform, host, and notes. Search and current filters are included visibly as context. Submission success says the report is pending review and is not an installable catalog entry.

## Accessibility and responsive behavior

- All interactive controls have `data-testid`, semantic labels, visible keyboard focus, and keyboard operation.
- Badges are accompanied by text; color is never the sole signal.
- Drawer/wizard focus is trapped and restored to the launching control.
- Loading announcements use polite live regions; errors use assertive alerts.
- Desktop uses filter rail plus details; narrow layout uses reversible Filters and Details drawers without losing search or wizard state.
- No serious or critical automated accessibility violations are accepted.

## Required UI states

Each component covers default, loading, empty, offline, update available, incompatible, uncertain, blocked, validation running, validation failed, rollback running, rollback failed, and stale-plan states as applicable.

## Journey acceptance tests

1. Offline search/filter/detail with blocked alternative.
2. Signed update preview, activation, restart projection, and rollback without state changes.
3. Paste multi-server Claude and VS Code fixtures; redact inline values; display one invalid field without registering either draft.
4. Review deterministic local-package plan, apply, validate, and select one workspace.
5. Remote endpoint plan and validation fixture.
6. Host bridge detected/missing/unsupported/read-only validation fixture.
7. Changed snapshot or machine observation invalidates an approved plan.
8. Structured missing report preserves search context.
9. Keyboard-only primary journey and accessibility scan.
