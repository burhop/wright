# Data model: process validation v1

This is the active model for the revised [plan](plan.md). Earlier 081 cohort entities are useful for later batch evaluation, not mandatory runtime objects.

## Entities and identity

| Entity | Required information and relationships |
|---|---|
| RequirementBaseline | Version/digest, source artifact hashes and locators, atomic requirement IDs, authorized amendments, unresolved decisions. Frozen before assessment. |
| ValidationProfile | ID/version/digest, supported subject kinds, required output roles, required checks, scope, comparison/uncertainty rules, capability needs, qualitative rubric and correction policy. |
| SubjectBinding | Workspace/run/producer-step/output-port, producer attempt, EngineeringResult ID, representation, value/file digest or pinned provider revision, permitted locator, input revisions. A result ID without a revision is insufficient. |
| ValidationRequest | Schema version, trace ID, validator invocation/check step, subject set, pinned profile/baseline, authority context, idempotency key and resource budget. Authority is supplied by the service boundary, never trusted from model text. |
| ReaderIdentity | Reader/version/configuration digest, native tool/schema/host identity where applicable, qualified formats, resource limits and evidence method. |
| Measurement | ID, subject, selector/location, typed value/unit/frame, uncertainty, method, evidence artifact/hash and provenance. |
| CheckResult | ID/version, requirement IDs, mandatory/applicability classification, expected constraint, measurement IDs, state, findings and scope. |
| Finding | Stable code/ID, requirement/check IDs, state/severity/category, subject and owner, expected/observed, evidence/source refs, diagnosis certainty, correction target, recheck IDs, repair eligibility and readable explanation. |
| ValidationAttempt | Immutable request identity, lifecycle/events, timestamps, reader identities, measurements/checks/findings, attempt sequence and terminal reason. |
| Assessment | Immutable ID/digest, attempt reference, review decision digests, summary dimensions, requirement dispositions, limitations, report projection references. |
| RepairFeedback | Assessment/subject/profile identity, target producer, failing findings, constraints to preserve, acceptance targets, complete-result reference and truncation metadata. Not an execution grant. |
| RevisionState | Runner-owned authorized target, limit, consumed revisions, delivered feedback, before/after subjects, rejected attempts, invalidated dependent results and stop reason. |
| ReviewDecision | Exact subject/profile/requirement/assessment, authenticated authority and actor type, rationale/evidence, time and decision. Append-only. |
| ReportEnvelope | Contract version, assessment and subject identity, currentness as of a stated time, supersession links, summary, findings, measurements, RTM rows and rendered Markdown reference. |

Inline structured values use a specified canonical JSON encoding before hashing; reject nonfinite numeric values and record encoding version. Raw text/file bytes use their actual bytes. Provider revision plus readback/snapshot digest is required where available; an unstable live resource cannot earn a durable pass.

An idempotency key is scoped to the workspace and invocation. Repeating the same key with identical normalized request returns the same attempt; changed inputs with that key produce a conflict. A new terminal evaluation uses a new attempt even for unchanged output. A cache may reuse qualified measurements under all matching identities, but never silently replace the latest attempt with an older successful assessment.

## States

**Attempt lifecycle:** queued → running → completed / blocked / error / cancelled. Completed describes execution of the evaluation, not design success. Resume an interrupted nonterminal attempt only with unchanged identities and owned resources; otherwise retain it and start a new attempt.

**Check state:** pass / fail / blocked / inconclusive / error / not_applicable. Not applicable requires a source-backed reason; missing support is blocked. Inconclusive covers uncertainty/ambiguous evidence, error covers evaluator faults, fail covers evidenced requirement violations.

**Summary dimensions:**
- `content_verified`: true/false/null for the declared content-check scope.
- `requirements_compliant`: true/false/null for the declared design-requirement scope.
- `evaluation_complete`: all applicable mandatory checks and reviews have conclusive dispositions.
- `physical_validation`: explicit evidence/scope or `not_assessed`.
- `release_eligible`: all applicable mandatory obligations for this gate passed, the scope is nonempty, no required source decision is unresolved and subject identity is current.

Known failure keeps the associated compliance dimension false even if another check is blocked/error. Missing evidence without known failure leaves it null. Aggregate mandatory checks with AND; do not average scores or treat an empty check list as a pass. Warnings are visible but do not change a mandatory check's status.

`pass / revise / needs_input / error` are process dispositions, distinct from check states. Revise is a recommendation only until the runner verifies target, authority, unchanged baseline, remaining budget and safe replay. Any required evaluator error holds release and requires a validator repair/retry; it is not a design defect.

## Revision and currentness

An assessment never changes. A new output revision or later authorized review creates new linked evidence/assessment. Currentness is a query-time envelope with `as_of`, selected subject revision, latest authoritative attempt/assessment, stale reason and superseded IDs. Stored historical report snapshots remain snapshots.

Choose latest authoritative sequence for the selected subject/check/profile, including queued/running/error attempts. Never select only passing rows first. Revalidate all mandatory checks in the selected profile after a correction, not just the defect that triggered it. Recheck dependent profiles if their bound output changed.

Revision budget and no-progress fingerprint survive restart. Prior output and requirement identities remain in history. Feedback records the producer attempt that consumed it; a correction is not inferred from an AI claim.
