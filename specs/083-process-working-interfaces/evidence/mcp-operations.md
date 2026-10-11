# T026 — Approved MCP operations

Date: 2026-10-01. Parent milestone: `c7a1a8d5`. Branch:
`codex/083-process-working-interfaces`. This is backend operation evidence;
review/action controls and their supervised API/UI journey belong to T027/T028.
The full M0–M5 goal remains active.

## Shared mechanism

The accepted `external-action-approval` declaration supports `mcp-operation` with
an exact server, fully qualified tool name and schema digest. It remains an
Engineer review barrier. Preparation qualifies the later operation before any
upstream AI work. Connected arguments explicitly select text, JSON or an actual
workspace file; provider-qualified file arguments require the file representation.
No filename is inferred from model prose. Saved document producers, typed tool
outputs and uploaded references retain their actual file identities.

The frozen subject retains definition, immutable inputs, artifacts, destination,
resolved arguments and their digest, producer-value digests, settings and finite
operation policy. Reopening reconstructs these values from the existing durable
snapshot and actual result representations. Changed source, files, provider
schema, qualified semantics, authority or observation/cancellation tools prevent
consumption. Gateway's existing final dispatch hook rechecks tool/source/file
identities immediately before provider invocation.

Dispatch uses the existing approval lease, atomic consumption, Gateway/MCP runtime,
run recorder and async-operation monitor. It adds no executor or provider protocol.
`local_review`, the fixed enrolled `test_handoff` and historical action records
remain supported. Required provider approval strings come from existing gateway
authority; a UI approval never fabricates management credentials or grants.

## Explicit provider qualification

`wright/approved-operation` is optional Wright adapter metadata, not an MCP
standard or a claim of universal installed-server support. Its closed version-1
shape is:

```json
{
  "version": 1,
  "effect": "digital",
  "destination_argument": "destination",
  "file_arguments": ["package"],
  "status_field": "status",
  "accepted_values": ["accepted"],
  "rejected_values": ["rejected"],
  "reference_field": "operation_id"
}
```

The exact metadata is part of the existing tool schema digest and its own pinned
qualification digest. `effect` may describe digital, physical or supplier effects;
test authority admits only qualified digital operations at an enrolled exact
test destination/tool. Declared effect metadata is a capability contract, not
independent physical qualification. Physical/supplier use requires its own real
authority and qualification; this goal performs neither.

Source `approval_settings` contains `arguments`, `argument_sources`,
`destination_argument`, integer `timeout_seconds` (1–3600), `operation_policy`
and an optional confined `receipt_path`. Each dynamic argument has exactly
`source` (an actually connected address) and `representation`
(`text`, `json`, `workspace_file`). Action is exactly
`{"kind":"mcp-operation","mode":"submit"}`.

Policy has `mode` (`receipt` or `observe`), `qualification_digest` and
`profile_digest` (null for receipt). Observe mode additionally pins `tool_bindings`:
role tool basename to exact `{name, schema}`. It pins the existing
`wright/operation` profile and uses that monitor's read-only status/result and
separately authorized cancellation tools. These selections must be configured
before execution; there is no late runtime form or guessed default.

For multi-hour observation, the independently qualified `wright/operation`
metadata may explicitly include `"observation_timeout_seconds": 7200`.
The optional value must be a finite number from 0.05 to 604800 seconds (seven
days); booleans and numeric strings are invalid. Its existing schema/profile
digest must be pinned again before a changed operation can run. Ordinary step
`timeout_seconds` and approved submission `timeout_seconds` remain short finite
call budgets. Each status/result call also has that call deadline. An AI task
delegates only the explicitly bounded observation interval, then resumes the
remaining decision budget without refilling it. No model call remains pending
during observation. Profiles without the field retain their existing deadlines.
This is the existing optional Wright adapter contract, not universal MCP Tasks
support or a provider-specific implementation. Timeout, cancellation and unknown
outcomes still require reconciliation; a larger observation budget grants no
submission replay authority.

Finite decimal arguments use the existing validation JSON canonicalizer for the
new MCP-operation subject/digests. Historical aliases retain their original
strict integer JSON hashes. Credentials/payment fields, nonfinite values,
depth and subject-size limits remain rejected. No global canonical JSON contract
or historical digest was changed.

## Receipts and uncertainty

- Qualified structured rejection records `not_dispatched`; MCP `isError` or an
  exception alone does not prove rejection before effects.
- Acceptance records `dispatched` with an exact provider reference before
  observation. Receipt mode establishes submission acceptance, not job completion.
- Observe mode records submitted, actual working/completed state and collected
  results through the existing monitor. Accepted submission cannot release later
  work unless the declared observation and receipt delivery complete.
- Requested cancellation and the provider's actual cancellation outcome are
  separate. Interrupting observation without that control is not cancellation.
- Disconnect, timeout, unrecognized response, missing reference or unfinished
  consumed action blocks repeat submission. No retry loop or guessed success exists.
- An optional indexed JSON receipt is an actual verified file with exact run,
  checkpoint, action, subject, provider and digest provenance; it becomes the
  existing `external_action_receipt` result. A publication collision holds the
  consumed operation for reconciliation and cannot resubmit it.

The conservative final-hook race test retains consumed unknown state even though
its controlled gateway proves zero provider calls. It does not invent a general
transport guarantee after consumption.

## Checked scope and remaining work

44 new tests pass using actual source storage, compilation, file publication,
SQLite checkpoint/claim persistence, existing runtime/approval/recorder/monitor
code and a controlled nonphysical gateway. They cover qualification, earlier
readiness failure, exact file/destination/argument pins, decimal/sensitive/finite
values, stale provider/status bindings, final dispatch freshness, acceptance,
explicit rejection with/without MCP `isError`, uncertain outcomes, same-run
duplicate resume, actual receipt files, accepted-before-observed-completion,
monitor disconnect and explicit confirmed cancellation. An actual private enrolled
policy derives `integration_test:083-private-unit` and labels the digital receipt;
the same policy mechanism rejects a physical-qualified provider before AI/effects.
These are synthetic model/provider/reviewer unit fixtures. They do not prove live
MCP connectivity, engineering correctness, human acceptance or physical behavior.

Final current-code regression verification: **652 passed**, no skips, 74.64 s;
two existing TestClient warnings. This covers 37 backend/API/core/storage modules,
including source/approval/v2-v3 continuation, supervised input, unattended model
policy, 082 validation/rework, operation monitoring/cancellation and integration
authority. A separate **62 passed** (13.00 s) covers the 44 operation tests plus
real GatewayService/approval-policy/capability-provider regressions. These suites
overlap; their totals must not be added.

The actual GatewayService final-hook test changes an artifact during application
startup and confirms its lifecycle never calls the provider. Current-tool
qualification is repeated in that final hook after startup may refresh catalog
definitions. Freshness tests and conservative unknown state retain one-shot
consumption across the boundary.

Exact commands, log hashes, 14 recorded unit-run/checkpoint subjects, artifact
hashes and preservation checks are retained in
[checked scope](../../../artifacts/process-interfaces/083/20261001-t026-operations/checked-scope.json).
Ten original prototype hashes, three protected campaign hashes, two mixed API
deltas and both approved feature-context files match their baselines. Focused
Ruff and whitespace checks pass. No owned server was started; all test handles
are terminal. No push/merge/release or hardware/supplier submission occurred.
Earlier preliminary runs include fixture construction/signature/field mistakes
and a pre-final 649-pass regression run; they are not the final checked code state.
The subsequent 651-pass run also predates the final current-tool guard/test.
Existing TestClient deprecation warnings remain unchanged.

No frontend/package/generated-schema files changed in this task. The previous
T025 browser/build evidence does not qualify the upcoming review/action UI.
T021, T027/T028 and all default-model UI authoring, live engineering, migration,
installed native/Docker and M5 completion evidence remain required.
