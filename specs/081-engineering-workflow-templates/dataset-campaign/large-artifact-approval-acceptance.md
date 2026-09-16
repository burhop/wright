# Large-artifact approval verification

Date: 2026-09-12. File identity and continuation acceptance only; engineering
content correctness remains unmeasured.

## Actual harness failure

Harness case 01 attempt 003 run `614ce0b3a46e4b81bfdf4324b5322ec5` completed the
primary component-document retrieval, then received HTTP 409 for its automatic
decision at checkpoint `checkpoint-2ac74834cfd92880bea30c6c`.

Read-only normal API checkpoint inspection and durable run evidence show:

- The checkpoint remains `pending`, with no actor, reason or external action.
- The run remains `awaiting_approval`; there are no `approval_decided`,
  `external_action_started` or `run_resumed` events.
- All 21 recorded input/artifact file hashes still match.
- `artifacts/research/crimp_tool.pdf` is 7,443,293 bytes with SHA-256
  `482110c8fb2102fc8534b8c0ef7df293c71e888f2bc06e7dbe6bd79d623a4eaf`.
- The actual workspace `read_reference` method rejects those unchanged bytes
  with `Choose a reference smaller than 4 MiB.` Approval `_prepare` maps this
  ValueError to `approval_stale` HTTP 409 before committing a decision.

The problem is using the document-loading size limit for an identity check.
Neither a stale artifact nor a rejected engineering result caused this failure.
The checkpoint subject digest remains
`d9d98bfd116b31f722f555d81e272056a0e421a1f3b4f3c07e44640dfe411408`.

Evidence:
`.local-run/feature-081-live/campaign-execution/harness01-003-approval-reconciliation.json`.
No approval, resume or native operation was issued during diagnosis.

## Generic repair

`WorkspaceFileUseCases.hash_reference` computes the exact SHA-256 through the
owned bounded executor without loading the whole file or decoding text.
The private `workspace_file_identity.workspace_file_sha256` helper uses:

- The existing `WorkspacePath` confined, link/reparse-rejecting resolution.
- A regular-file check and 256 MiB maximum, matching the existing file inspector's
  observation ceiling.
- 1 MiB chunks, with an additional running-byte limit to catch growth.
- Before/after handle metadata and current-path device, inode, size and
  nanosecond modification-time comparison, rejecting concurrent writes and
  replacements even when size/timestamp match.

Both approval revalidation and durable continuation restore use this private
identity API. Existing subject, input, source, binding, policy, dispatch and
required-step checks remain in place. The 4 MiB document/image loading limit and
1 MiB model-response limit remain unchanged. No new MCP tool, model file access,
schema revision or grant authority is introduced.

At `2026-09-12T18:39:54.822156+00:00`, a separate read-only probe used this actual
file service to verify all 21 original checkpoint files. The raw run stayed
byte-identical with SHA-256
`d65b24ffe34e3b5f244c1d0d1e5eb010dae6dab8a2e294f32901b739a56ae2d1`.
Proof:
`.local-run/feature-081-live/campaign-execution/harness01-003-streaming-hash-verification.json`.

## Tests and deployment boundary

Affected suites passed 62 tests with 1 skip in 29.38 seconds; Ruff passed:

```text
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_checkpoint_file_identity.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_deterministic_files.py apps/api/tests/test_workflow_integration_run_api.py apps/api/tests/test_workflow_multicheckpoint_durable_mcp.py -q --tb=short --basetemp=.local-run/feature-081-live/pytest-checkpoint-hash-final
```

The new workflow regression runs an exact pinned test MCP operation that writes
an actual binary artifact above 4 MiB in an isolated workspace. It then approves
and restores the same run through the actual bounded file service, reaches the
final output, and verifies the producing tool ran exactly once. Changing the
large artifact before decision or resume leaves the checkpoint unconsumed and
executes no later step. Additional tests cover missing/unconfined paths,
oversize files, directories, concurrent truncation and same-size/timestamp file
replacement. The one skipped test is actual symlink creation, which this Windows
test account does not permit; the existing path capability is reused unchanged.
The existing real isolated stdio MCP restart/continuation suite passes.

The live API and worker have not been restarted by this change. The original
failed decision operation, checkpoint, run record, source and grant remain
untouched. Any subsequent normal API recovery requires the controlled pause and
explicit reconciliation described by the parent campaign coordinator; the
runner's unknown-mutation protection is not weakened or reset.
