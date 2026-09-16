# Process validation contract v1

**Status:** Proposed implementation contract; no new command or endpoint exists yet.
**Consumers:** canonical process runner, direct/CLI callers, MCP clients and the separate reporting feature.

## Operations

One application service owns these operations:

| Operation | Behavior |
|---|---|
| `evaluate(request)` | Resolve authorized bindings, evaluate or enqueue bounded readers, persist an immutable attempt/assessment and return its reference/result. Never execute the producer. |
| `get_result(id)` | Retrieve authorized persisted assessment and query-time currentness envelope. |
| `list_findings(id, cursor, limit)` | Stable, bounded pagination over the assessment's complete findings. |
| `export_result(id, format)` | JSON, Markdown or CSV traceability from that assessment; no new measurement. |
| `record_review(subject, decision)` | Accept only authority-backed subject/profile-bound review; append a new assessment. Never accept a caller's claim to be human. |

Direct Python and packaged CLI call the same service. A thin BaseTool exposes evaluation/read operations through the current Wright MCP transport, without a second daemon/executor. API reads/exports use current workspace auth/origin/RBAC. Choose exact transport names/routes at T011/T020 and publish them in the handoff. An asynchronous reader operation is not complete merely because submission succeeded.

## Request

Required: `schema_version`, `trace_id`, `workspace_id`, `invocation_id`, optional canonical `run_id/check_step_id`, `subjects[]`, pinned `profile_ref`, pinned `baseline_ref`, `idempotency_key` and bounded resource policy.

Each subject identifies producer run/step/attempt/output port and a provider-neutral result representation with immutable digest/revision. Standalone imported files have an explicit import identity/authority and no automatic rework target. Require declared output roles; never scan arbitrary neighboring directories for likely files.

A local validator process step accepts bound outputs and profile/baseline references. Its result port carries the assessment reference/check report. Pass routing releases the exact checked revision; revision routing is explicit and separately bounded. The compiler rejects incompatible bindings, missing required roles, unsupported source versions and unsafe revision paths before dispatch where possible. T010 documents the exact source grammar and migration behavior.

## Evaluation rules

1. Freeze methods, applicability and limits before inspecting the candidate. Profile changes require a new profile identity and explicit acceptance basis.
2. Measure from actual bound values/files or pinned native readback. Annotate independent measurement, native inspection, structured value, producer claim or human judgment. A lower-evidence method cannot satisfy a profile requiring stronger evidence.
3. Require finite quantities, explicit units/datum, tolerance provenance and declared operators. Normalize units/frames using recorded transforms. For bounded uncertainty, an interval wholly inside passes, wholly outside fails, and crossing a bound is inconclusive; preserve specified inclusive/exclusive boundaries.
4. Required absence, unsupported capability, malformed content and evaluator faults have distinct codes. A completed producer omitting a required file is a defect when proven from its output contract; an unavailable artifact binding is blocked.
5. Preserve known failed checks alongside unknown/error checks. No missing reader, skip, zero-row evaluation or model-authored verdict can release the process.
6. Snapshot or check subjects before/after measurement; changes invalidate the attempt's eligibility. Persist failure and error findings before stopping downstream execution.
7. Native inspection uses current confinement/lease/read-only rules. Read-only tool annotations alone do not prove semantic independence or prevent all side effects.
8. An accurate infeasibility analysis may verify content while failing design compliance. Physical validation must name actual physical evidence; otherwise it is not assessed.

## Finding and correction packet

Every non-passing mandatory check provides:
- Stable finding code/ID and check/requirement IDs.
- Subject/producer/output ownership plus a selector (JSON pointer, CSV row/column, source location, semantic feature or field region).
- Typed expected constraint and observed measurement when available; unit/frame/tolerance/uncertainty.
- Source and measured evidence references; null observation plus missing-evidence reason when unavailable.
- Category: `output_defect`, `missing_evidence`, `source_conflict`, `capability_unavailable`, `review_required`, `validator_error` or `stale_subject`.
- Readable summary, evidence-supported explanation, explicitly tentative cause where uncertain, corrective target and recheck IDs.
- Recommended action: `revise_output`, `supply_input`, `restore_capability`, `request_review`, `retry_validation` or `refresh_subject`. Recommendation is not authorization.

A repair packet includes the failing assessment/subject/profile digests, target producer, prioritized findings, passed requirements/constraints to preserve, remaining runner revision allowance and complete-result reference. Inline defaults are at most 20 findings and 16 KiB UTF-8; preserve routing/identity metadata, disclose truncation and allow paged retrieval. Persist all findings regardless of prompt size.

Artifact text and suggested causes are data, not instructions overriding requirements. No commands, arbitrary tool privileges, profile edits or approval grants belong in the correction packet. Local artifacts keep their original bytes; the producing step writes a new revision.

## Illustrative finding

This is a proposed example, **not a measured repository result**. The source jig H2 target is (170,30) mm with ±0.20 mm per axis. An illustrative observed x=169 mm should produce:

```json
{
  "schema_version": "wright.process-validation/1",
  "finding_id": "finding-jig-h2-x",
  "code": "geometry.position.out_of_tolerance",
  "check_id": "seat-center-x",
  "requirement_ids": ["jig.h2.position.x"],
  "state": "fail",
  "severity": "error",
  "category": "output_defect",
  "subject_ref": "subject-jig-producer-attempt-1",
  "owner": {"step_id": "create_jig", "output_port": "model", "attempt": 1},
  "selector": {"kind": "semantic_feature", "feature": "H2.bushing_seat", "quantity": "center.x"},
  "expected": {"operator": "within", "target": 170.0, "absolute_tolerance": 0.20, "inclusive": true},
  "observed": {"value": 169.0, "unit": "mm", "frame": "workpiece_datum", "measurement_ref": "measurement-h2-x"},
  "source_refs": ["source-holes-csv:row-H2:x_mm"],
  "evidence_refs": ["measurement-h2-x"],
  "summary": "H2 seat center is 1.00 mm too far left.",
  "explanation": "Measured x=169.00 mm; the allowed interval is 169.80–170.20 mm in the workpiece datum.",
  "correction": {
    "action": "revise_output",
    "target_step_id": "create_jig",
    "target": "Move the H2 seat center to x=170.00 mm in the workpiece datum.",
    "preserve_requirement_ids": ["jig.h2.position.y", "jig.seat.diameter"],
    "recheck_ids": ["seat-center-x", "seat-center-y", "seat-diameter"]
  }
}
```

The containing result resolves subject/measurement/source refs to their exact artifact hashes, reader method and locators. Do not invent a native topology ID or assert a root cause unsupported by measurements.

Readable projection: **H2 seat position — Fail.** Expected x=170.00±0.20 mm; measured 169.00 mm in the workpiece datum. Correct the H2 seat position, retain its required y-coordinate and seat diameter, then recheck the complete profile. Evidence: the linked measurement and source CSV row.

## Process and repair semantics

- `pass`: current subject, complete mandatory scope and all applicable mandatory checks pass; release that revision.
- `revise`: at least one evidenced, safely correctable defect and a permitted revision target; no automatic execution from direct tool calls.
- `needs_input`: unmet prerequisite, uncertain evidence, pending review, no safe route, no progress or exhausted budget; hold with precise next action.
- `error`: evaluator/infrastructure fault; hold and retain engineering findings already established.

A known defect alongside missing evidence stays noncompliant/incomplete. It may use an independently safe configured revision route, but unresolved checks remain mandatory and prevent pass. A required evaluator error prevents producer repair until the validator fault is addressed.

Version 1 supports one explicit producer/check revision segment and 0–3 revisions, default 0. Never infer arbitrary back-edges. Persist counts/feedback/no-progress identity across restart; stop on unchanged subject/defects, cycle, changed source basis or unsafe side effects. Preserve old failures. Revalidate every mandatory profile check on the new revision. Approval-bound downstream work remains governed by existing policies.

## Reporting branch boundary

The report envelope contains:
- Contract version, assessment ID/digest, attempt ID and trace/run/check identifiers.
- Subject/baseline/profile/reader identities and immutable evidence references.
- Scope: requirement IDs covered, explicitly excluded items and physical-model limitations.
- Summary dimensions from [data-model.md](../data-model.md), counts by state and process disposition.
- Full findings/measurements or stable paged references.
- RTM rows: requirement ID/text/source → check/method → expected/observed/unit → status → evidence → producer/output revision → action.
- Readable Markdown using the same values/IDs, not independently inferred verdicts.
- Currentness envelope with `as_of`, selected/latest revision, stale reason and supersession references.

Schema major versions change for breaking changes; additive optional fields preserve v1 consumers. Unknown versions fail explicitly. Provide representative pass/fail/mixed/blocked/error/stale/repair examples and consumer tests. Markdown escapes untrusted content; CSV neutralizes formula injection. Export stable authorized artifact references, not private absolute host paths.

Publish JSON/Markdown as existing verification/diagnostic results/events. The other branch owns report layout, report UI and aggregation into user deliverables. It must not need validator-private imports, a running solver or a new evaluation to render a stored result.

## CLI and operational failures

Proposed packaged entry point: `python -m workspace_service.process_validation_cli`, with evaluate/get/export/profile-list operations; confirm actual help after implementation. Exit 0 means conclusive pass, 1 measured noncompliance, 2 invalid request/evaluator failure, 3 held/blocked/inconclusive/stale, 130 cancellation. Mixed precedence: 2 > 3 > 1 > 0; detailed fields retain all facts.

For MCP, distinguish transport/tool execution error from a successfully returned failing assessment. No success flag at the transport level means a design passed. Validate duplicate-key conflicts, subject confinement, authorization, cancellation, paging and currentness consistently across adapters.
