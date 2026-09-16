# Approval, Resume, and External-Action Contract

This contract extends canonical workflow execution with durable human checkpoints. Current terminal artifact review is reusable evidence infrastructure but does not satisfy this contract until it can resume into CAD/MCP/external operations and attribute decisions through current identity policy.

## Create checkpoint

Execution entering an approval block persists completed steps and creates exactly one `pending` checkpoint. The canonical `subject_digest` covers:

- definition/workflow revision and digest;
- referenced input and output artifact digests;
- engineering assertion results and evidence;
- exact server, tool, and input-schema bindings;
- external destination/device identity and reconciled state;
- material/profile/quantity/service/action settings;
- action kind and bounded proposed argument summary.

The runtime releases active tool resources while waiting. Canvas and run detail show what is proposed, why approval is required, exact artifacts/settings/destination, relevant checks, and consequence.

## Decide

`POST /api/workspace/workflow-runs/{run_id}/approvals/{checkpoint_id}/decisions`

```json
{
  "subject_digest": "exact displayed digest",
  "decision": "approved | changes_requested",
  "reason": "bounded human-readable reason",
  "request_id": "idempotency identifier"
}
```

Only the authorized workspace user may decide. The service re-reads exact artifacts and current source, checks digests and expiry, and atomically records the immutable decision. A stale subject returns `409 approval_subject_changed` and creates no external action. Approval does not dispatch by itself.

**2026-09-12 integration campaign extension:** The explicitly authorized test
campaign may instead use a locally enrolled, immutable automatic policy under
[integration-execution.md](../dataset-campaign/contracts/integration-execution.md).
The service derives an `integration_test:<campaign_id>` actor from that grant;
an API caller cannot supply or impersonate it. Manual policies retain the user
decision path. Automatic authority covers fixed local reviews and fixed
transport simulators bound to enrolled `test://` destinations only. Exact
subject checks, expiry, idempotency, artifact verification and safe continuation
remain mandatory. Normal workspace approval authority is unchanged.

## Resume

`POST /api/workspace/workflow-runs/{run_id}/resume`

```json
{
  "checkpoint_id": "...",
  "subject_digest": "...",
  "request_id": "idempotency identifier"
}
```

Resume reauthorizes the workspace, reloads the saved run snapshot, verifies completed outputs, bindings, destination/device state and decision, then continues at the stored next step. It never recompiles from changed live source or repeats completed mutating steps. `changes_requested`, stale, denied, expired, missing or consumed decisions cannot resume.

## Dispatch semantics

Immediately before a mutating call, the runtime writes an `ExternalActionRecord` with `not_dispatched`, then marks the approved checkpoint consumed in the same local transaction. It records attempt and observed outcome after the call. Network loss or timeout after dispatch yields `outcome_unknown`; automatic retry is prohibited until read-only reconciliation proves whether the action occurred and a new checkpoint is approved if needed.

## Initial action kinds

- `printer_transfer`: bound to sliced package, printer identity, machine/process/filament profiles and current printer status. Acceptance by printer is distinct from print started/completed/quality accepted.
- `supplier_upload_preview`: bound to exact upload file, units/scale, supplier endpoint/tab/session and selections. This action may upload/configure for preview only; no support contact, cart acceptance or order.
- `cart_quote_handoff`: bound to verified uploaded-file association, material/thickness/quantity/services/bends/warnings, actual price/currency/delivery/tax/shipping availability and timestamp. It presents the handoff to the user; it cannot purchase, pay, release production, or accept credit terms.

## Invalidation and tests

Every subject component is mutated independently in tests; all must stale the decision. Tests also cover approval races, decision/request idempotency, expiry, missing output, changed binding schema, device mismatch, successful dispatch, rejection, timeout after dispatch, restart while waiting, cancellation, reconciliation, and no blind replay.
