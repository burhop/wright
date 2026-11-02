# Ordinary local handoff simulation — controlled verification

Date: 2026-10-23. Scope: T007 local implementation and controlled tests, not an
installed customer run, a new engineering validation campaign, or a physical
handoff. Root owns candidate packaging and native verification.

## Accepted contract and ownership

The ordinary customer route uses a distinct fixed `wright/local_simulate_handoff`
binding, schema digest SHA-256 of `wright.local_simulate_handoff.v1`, and the exact
destination `{"kind":"integration_test","id":"local-simulation://workspace"}`.
The action retains its existing kind (`printer_transfer`,
`supplier_upload_preview`, or `cart_quote_handoff`) and explicitly sets
`mode: local_simulation` and `simulation: true`. Source settings contain only
`simulation: true`; the existing `wright.run-path/1` binding supplies the receipt
path. No extra device, credential, network, or annotation settings are accepted.

The existing compiler requires a run-scoped JSON receipt and connected
workspace-file output produced by an upstream task. Additional static profile
inputs are permitted and retain the existing `input_files` and `input_digests`
hash checks. Bare-input-only simulation is outside this initial bounded
capability and fails compilation before work. Normal
readiness qualifies all action dispatchers before model resolution. An ordinary
legacy test-handoff destination fails readiness; the old test binding remains
available only after its existing exact enrollment authorization.

The existing approval checkpoint and one-use dispatcher own manual decisions,
consumption, durable run continuation and recovery. The new binding rejects auto
approval and enrolled execution context. Before decision/resume, every connected
workspace-file output must have a nonempty, sealed artifact group whose hashes
belong to the exact subject. Existing source and file hashes are checked again at
the dispatch boundary. No second executor or network/provider implementation was
introduced.

The existing filesystem owner gained an internal `exclusive` publication policy
for this receipt. Complete temporary bytes are atomically linked to the exact
confined path; collision cannot overwrite a receipt or choose an indexed sibling.
An existing receipt is rejected before consumption. A race after consumption is
retained as an uncertain outcome with replay prohibited. Reopening the same run
recovers confirmed evidence without dispatching again.

The receipt preserves `integration_test: true`, `simulated_handoff: true`,
`network_dispatch: false`, the exact package digest list and the original
`integration_test` destination kind. Its explicit authority is
`authority_mode: manual_local_simulation` with the actual checkpoint actor.
It contains no campaign, dataset, or integration-grant identity. The legacy test
receipt and its enrollment mechanism are unchanged. No validator or engineering
profile was changed.

## Verification

Executed outside the host sandbox because its known asyncio executor wakeup
failure causes ordinary temporary-file operations to time out. No product
workaround was introduced; the stalled owned test process was stopped. The
scoped escalated tests used temporary workspaces and controlled callbacks only,
with no model, engineering-provider or native-service call.

- Owning approval, external-action, file-publication and template-readiness suites:
  **56 passed, 2 skipped in 6.40 s**. Skips are existing Windows file-sharing tests
  on Linux.
- Final affected verification: **24 passed in 3.12 s**: the expanded 23-case
  `test_workflow_local_simulation.py` plus the actual installed-customer setup
  proposal/CAS-acceptance test. This includes direct-input-only rejection,
  missing connected output identity, permitted static-profile dependencies and
  refusal to resume after static-profile bytes change.
- Ruff checks and `git diff --check` passed for the owned change.

The tests exercise ordinary manual success, automatic/enrolled rejection,
changed package bytes before and after decision, strict source keys and local
URI, missing run scope, existing receipt collision, a concurrent publication
race, durable reopen, and refusal to replay uncertain consumed actions. A real
concurrent filesystem control proves exactly one complete exclusive winner and
no indexed sibling or temporary-file leak.

The unchanged printing `transfer_binding` reader accepts actual controlled
receipt bytes against their exact controlled package digest. This proves receipt
compatibility only; it does not claim a new slice or geometry result. The second
controlled case reuses the `supplier_upload_preview` action from the accepted
sheet-metal wall-dock validation profile. Its original campaign-specific
validation profile is preserved and is not claimed to pass under ordinary manual
authority. The complete sheet-metal engineering workflow was not rerun.

## Files and integration status

Owners changed: `workflow_external_actions.py`, `workflow_source_execution.py`,
`workflow_run_preparation.py`, `workflow_approval_execution.py`, and
`adapters/filesystem.py`. Tests are `test_workflow_local_simulation.py`, the
existing approval fixture, and `test_generated_file_sharing.py`.

The packaged setup service imports the binding and destination constants, creates
an ordinary proposal using the existing slice-package connection, and relies on
normal source acceptance. Setup grants no approval or enrollment. Independent
review of the contract and final implementation, including the upstream-file
scope and static-profile integration correction, passed with no actionable blocker. No candidate build,
installation, runtime restart, push or merge was performed for this change by
this subtask.

The initial strict compiler condition incorrectly rejected static profile inputs
alongside the produced package. Actual customer setup caught this before a
candidate build. The corrected condition requires at least one task-produced
workspace file while preserving declared static inputs; the approval check still
requires every connected task-produced file group to be sealed. The 24-case
verification above includes the actual setup regression and static-input change
control.
