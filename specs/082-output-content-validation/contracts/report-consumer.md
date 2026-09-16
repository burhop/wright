# Report consumer handoff

The reporting branch consumes `wright.process-validation-report/1`. It does not
import validator implementation modules, invoke readers, or rerun an assessment.
The authoritative schema is
[`schemas/ValidationReport.schema.json`](schemas/ValidationReport.schema.json).
Breaking changes require a new report schema major version; additive optional
fields may extend version 1.

## Authoritative identity and verdict

`assessment_digest` is the SHA-256 of the embedded `assessment` under
`wright-json-v1` canonical encoding. The embedded assessment retains its pinned
profile, baseline, subjects, measurements, checks, findings, review IDs and
summary. A consumer must treat the effective release verdict as:

```text
currentness.is_current AND assessment.summary.release_eligible
```

A historical pass remains visible but must not be presented as the current
release decision. `currentness` names the selected and latest attempt and
assessment, a supersession chain when reviews were appended, an `as_of` time,
and one closed stale reason. Query the endpoint again when live currentness is
required; exported files are snapshots.

`scope.requirement_ids` is the complete baseline scope declared by the profile.
`excluded_scope`, `limitations`, and `physical_validation` must remain visible.
Do not infer validation of excluded work or turn `not_assessed` into a pass.

## Traceability rows

`traceability[]` contains one row for every requirement/check pair in the pinned
profile. Each row carries source references, requirement text and scope, check
method and reader, expected constraint, observed value/unit/frame, status,
evidence references, exact subject/output revision, producer identity, findings,
and recommended action. Multiple rows may refer to the same requirement. Keep
all rows; do not average or collapse conflicting states.

The typed assessment remains the source of truth. JSON, Markdown, and RTM CSV
are generated from the same `ValidationReport`; they do not independently infer
verdicts. Representative pass, fail, mixed, blocked, error, stale, and repair
records are in [`examples/`](examples/). `repair.report.md` and
`repair.rtm.csv` are projections of `repair.report.json`.

## Authenticated operations

All HTTP operations use the existing Wright control-plane authentication and
require an engineer or administrator when authentication is enforced. Every
operation also requires the owning `session_id`; a foreign workspace receives a
not-found response without assessment content.

| Operation | HTTP contract |
|---|---|
| Get report | `GET /api/workspace/process-validations/{assessment_id}?session_id={session}` |
| Page findings | `GET /api/workspace/process-validations/{assessment_id}/findings?session_id={session}&cursor=0&limit=20` |
| Export | `GET /api/workspace/process-validations/{assessment_id}/export?session_id={session}&format=json|markdown|csv` |
| Record review | `POST /api/workspace/process-validations/{assessment_id}/reviews` with `session_id`, `requirement_id`, `decision`, `rationale`, and nonempty `evidence_refs` |

Finding pages contain at most 20 findings and 64 KiB of inline finding data.
Follow `next_cursor` until null. A report or JSON export contains the complete
assessment. Export responses use `Cache-Control: no-store`, a fixed safe
filename, and `X-Content-Type-Options: nosniff`.

The review route derives `actor_id` and `authority_ref` from the authenticated
request. The body cannot assert reviewer identity. A decision applies only to a
current assessment and a baseline requirement explicitly marked for review. It
appends a new assessment and leaves the original unchanged. Re-fetch the
returned assessment/report before presenting a current verdict.

The existing gateway exposes `wright_validation__get`,
`wright_validation__read` (paged findings), and `wright_validation__export` as
read-only operations alongside evaluation. Human review is intentionally absent
from the model-facing gateway. The packaged CLI provides `get`, `read`, and
`export`; authenticated human review remains a control-plane operation.

## Rendering and links

Artifact references are opaque, authorized identifiers such as
`wright://workspace/...`; never rewrite them into host filesystem paths. Resolve
them through the owning workspace service when a future report UI adds link
handling. Show unresolved references as text rather than guessing a path.

Treat all requirement text, findings, explanations and evidence labels as
untrusted display data. The supplied Markdown projection escapes Markdown/HTML
metacharacters. The CSV projection prefixes formula-leading cells with an
apostrophe and uses RFC-compatible quoting. A custom consumer must apply
equivalent protections.

Use the following independent compatibility check in the report branch:

1. Load `ValidationReport.schema.json` with a Draft 2020-12 JSON Schema library.
2. Validate every `*.report.json` example without importing Wright Python code.
3. Assert the effective verdict from currentness and summary.
4. Reconcile every RTM status and assessment digest with the JSON traceability
   rows.
5. Render unknown additive fields without failure and reject an unknown
   `schema_version`.

