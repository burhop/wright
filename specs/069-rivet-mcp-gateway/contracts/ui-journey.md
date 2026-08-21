# UI Journey: Review and Run a Multi-MCP Rivet Workflow

## Entry and layout

The existing workflow detail/editor surface gains a `Capabilities` step before review. Non-MCP workflows keep their current compact review/run flow. At narrow widths, capability and run details become stacked panels; identity/risk fields are never hidden behind hover-only UI.

## 1. Resolve requirements

- Each MCP node row shows requirement, node title, selected graph, resolution state, and one exact namespaced implementation.
- Search/filter results show server, tool, schema/validation freshness, platform/locality, data/effect risk, approval gates, and compatibility.
- Ambiguous/missing/incompatible states block review and provide actions such as enable for this workspace, validate, choose implementation, or update the graph.
- Direct child configuration is shown only as a redacted invalid-workflow warning; it is never offered as an execution option.

Stable controls:

- `workflow-capabilities-tab`
- `workflow-binding-row-{nodeId}`
- `workflow-binding-select-{nodeId}`
- `workflow-binding-details-{nodeId}`
- `workflow-binding-refresh`
- `workflow-binding-blocker-{nodeId}`

## 2. Review exact scope

The review panel summarizes workflow revision/digest, graph, binding-set digest, node/tool/schema/server/validation identities, units/material assumptions, and risk/approval implications. It states plainly: approving the workflow does not approve destructive tool calls.

Stable controls:

- `workflow-review-binding-summary`
- `workflow-review-policy-summary`
- `workflow-review-approve`
- `workflow-review-reject`
- `workflow-review-stale-reason`

## 3. Start and monitor

Start remains disabled until the exact review is current. The run timeline groups events by node while preserving total order and shows child server/tool, approval, progress, artifacts, and stable failure boundaries. It never shows bearer tokens, commands, environments, or raw credentials.

Stable controls:

- `workflow-run-start`
- `workflow-run-cancel`
- `workflow-run-timeline`
- `workflow-run-node-{nodeId}`
- `workflow-run-call-{callId}`
- `workflow-run-artifact-{artifactId}`

## 4. Exact-call approval

When a call needs approval, an accessible modal identifies the node, exact namespaced tool, safe argument summary and digest, effects/data, gates, and expiry. Approve/deny changes only that call. Focus is trapped, Escape closes without approval, and focus returns to the triggering timeline item.

Stable controls:

- `workflow-call-approval-dialog`
- `workflow-call-approval-arguments`
- `workflow-call-approval-approve`
- `workflow-call-approval-deny`

## 5. Cancel and recover

Cancel immediately changes the run to `Cancelling`, explains authority revocation and child cancellation separately, and prevents repeated action. Terminal state distinguishes `Cancelled cleanly` from `Cancelled; external cleanup unconfirmed`. Recovery links point to application/lifecycle status, not generic retry for a non-idempotent call.

Stable controls:

- `workflow-run-cancellation-status`
- `workflow-run-residue`
- `workflow-run-recovery-action`

## 6. Stale review recovery

If a workflow, binding, grant, server revision, schema, validation, or policy identity changes, Start stays disabled and the UI shows a field-level safe diff. The engineer refreshes discovery, deliberately chooses a replacement when needed, and submits a new review. Wright never silently rebinds.

## Accessibility and responsive acceptance

- Every interactive control is keyboard reachable and has a stable accessible name and `data-testid`.
- Loading, success, warning, blocked, approval, cancellation, residue, and stale states use text/icons in addition to color.
- Progress and approval changes use appropriate live regions without announcing every high-frequency child update.
- Dialogs trap/restore focus; table/card layouts remain readable at 320 CSS pixels and 200% zoom.
- Serious/critical automated accessibility findings are zero in mocked Playwright journeys.
- Browser logs and rendered text pass secret-like pattern scans.
