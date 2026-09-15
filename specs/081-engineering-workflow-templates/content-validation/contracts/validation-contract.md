# Independent output validation contract

**Status:** Proposed v1 contract. Commands and types in this file are targets to implement, not existing callable tools. Subject to the activation gate in [plan.md](../plan.md).

## Service boundary

The application service accepts an authorized workspace/run reference, a frozen cohort/profile digest and execution configuration for **validation readers only**. It resolves artifacts through existing workspace/run/vault services. No absolute user-supplied path or generated workflow text can authorize arbitrary file access or tool execution.

Public service operations:

- `audit_generation_cohort`: read current corpus/runtime/receipt/artifact/lifecycle facts; produce activation evidence; no workflow dispatch or campaign-state mutation.
- `lint_profiles`: validate requirements/profile schema, source locators, coverage, applicability and reader bindings.
- `validate_case`: independently inspect selected artifacts, evaluate a frozen profile and persist a validation attempt.
- `get_validation` / `list_validations`: read authorized records and currentness.
- `export_validation`: materialize structured results, RTM and test-runner views from persisted data.
- `cancel_validation`: stop owned validation work with durable cleanup and outcome reconciliation.
- `record_review`: append a decision bound to the exact validation/requirement/rubric subject through an authorized review service, then create a new immutable assessment/report revision. Derive the actor and permitted reviewer type from current authority, not a caller-supplied claim of human approval. Reuse existing review mechanisms only where their subject semantics fit; never treat execution test-auto approval as source amendment authority.

Pure evaluation is independent of HTTP and CLI. API routes, if needed for the existing workspace evidence view, use current authentication/origin/RBAC and are thin adapters. Do not introduce a new workflow execution endpoint.

## Reader request and response

A reader request identifies exact artifact IDs/digests, role/variant, explicit unit/frame context, reader version and bounded configuration. Expected engineering limits remain in the assertion layer. Geometry feature selectors may be supplied as measurement requests, never as expected-value answers.

A successful response contains measured values, units/frame, method and uncertainty, exact source refs, reader/kernel version and evidence locators. Returning only a generated summary, passing flag or source filename is insufficient.

The registry allows approved reader IDs and bounded typed parameters. It must not deserialize executable Python, shell commands or YAML object constructors from a profile. Archive readers reject traversal/links, cap expanded size and inspect content safely. Native readers use disposable confined working copies, existing application leases and exact process ownership; originals cannot be healed, saved or converted in place. Never close unrelated user documents.

Large fields are reduced from streaming/chunked reads where possible. Record exact candidate/refinement completeness and row/cell coverage. Unknown source units, missing fields or unsupported versions produce explicit non-pass states.

## Numerical and semantic rules

- Values and tolerances must be finite and physically/domain meaningful. Reject negative uncertainty/tolerance, invalid dimensions, empty arrays and incorrect axes.
- Comparisons define inclusive/exclusive bounds, absolute/relative error denominator and near-zero behavior. Case-specific model/mesh/timestep tolerances are frozen before candidate inspection.
- Use uncertainty intervals: pass only when the interval lies wholly inside acceptance; fail when wholly outside; crossing the boundary is inconclusive. For exact logical tests use exact equality.
- Compare hole/slot/mating features in the declared datum, not by arbitrary best-fit that hides reflection or orientation errors.
- A fluid domain and CAD model have different file/geometry identities. Verify the derivation and relevant geometry, boundaries, loads/materials and mesh/field associations.
- Recompute physical metrics from raw fields/time series. Synthetic fixtures and analytical baselines qualify checkers; they never replace required solver output.
- Distinguish Kelvin absolute temperatures from Celsius offsets and temperature differences. Compare thermal error on a defined rise, not arbitrary percent Celsius.
- Validate required candidate counts, variant IDs and refinement pairing. Independent lowest-feasible/all-cases decisions use the full required set.
- Existing source evidence authorizes only its actual claims; URL presence is not source support. Freeze supplier/manufacturer evidence per run. Fresh research produces a new evidence revision rather than silently changing the reference.
- The currently documented heater derivative is `wright-water-heater-v1@0.1.0` with a 2 K hysteresis assumption. At activation, verify latest authority, model equations and actual parameter readback. The input's first-target-crossing intent and post-crossing thermostat behavior must be reconciled explicitly; integrate comparison energy to the defined horizon/crossing. An analytical pre-crossing checker must not assume unverified post-crossing shutoff.

## Aggregation and traceability

Each mandatory requirement enumerates all necessary checks and reviews. All must pass for that requirement to pass. Alternative verification routes are allowed only if explicitly defined in the reviewed profile, with selection evidence. A global average or weighted LLM score cannot mask a failed hard requirement.

Any known mandatory failure keeps the relevant content/design result failed, while a separate evaluation-complete flag remains false if another necessary check errors, blocks or awaits review. Retain both facts and all child reasons; operational CLI precedence does not override requirement verdicts. With no known failure and unresolved checks, the result is undetermined. Test these mixed combinations explicitly.

Late reviews append records and a new AssessmentRevision referencing unchanged measurements and their current subject. Include review/decision digests in the new report key and reject stale subjects/rubrics. Never reopen a finalized report. Independent fixture/rubric review may be performed by a separately recorded competent checker or agent when its defined criteria permit; only explicitly human-required judgments need a human decision.

RTM rows include requirement/source revision and locator, method/check version, expected/tolerance, observed/units, actual artifact/measurement link, state, reason, review and current/stale indicator. Test the RTM against source inventory and persisted results. Do not allow orphan hard requirements, stale evidence, missing dependencies or invented N/A.

Canonical JSON is authoritative. CSV/HTML are generated views. JUnit XML distinguishes failed engineering checks from reader/framework errors and includes typed blocked/inconclusive/N/A reasons as properties; any skipped representation remains non-pass in the application summary and CLI exit code.

## Proposed CLI

Target script: `scripts/run_engineering_content_validation.py`.

```text
audit-generation --inputs <generation-input-root> --campaign-state <existing-state-root> --runtime-state <authorized-runtime-reference> --output <new-start-gate-json>
lint-profiles --profiles <validation-profile-root> --cohort <frozen-cohort-json>
validate --cohort <frozen-cohort-json> --profiles <validation-profile-root> --state <separate-validation-root> (--case <exact-case-id> | --all) [--resume <validation-id>]
status --state <separate-validation-root> [--cohort <cohort-id>]
report --state <separate-validation-root> --cohort <cohort-id> --output <confined-report-root>
record-review --state <separate-validation-root> --validation <validation-id> --expected-subject-digest <digest> --decision <allowed-review-decision> --rationale-file <confined-text-file>
```

Commands must be idempotent where appropriate, validate roots and fail before reader dispatch when G0/cohort/profile identities are not valid. `audit-generation` writes only the requested new validation evidence; `status` is read-only. No command submits a printer/supplier action or regenerates a workflow.

`record-review` uses the current authenticated/authorized reviewer context and the frozen rubric's allowed decisions; no `--actor human` bypass is permitted. It writes an append-only review/adjudication, not an execution approval. `--resume` is valid only for a queued/running interrupted attempt with unchanged identities and reconciled resources. Retrying a terminal attempt creates a new linked ID. Current reports follow the persisted latest authoritative evaluation/assessment sequence, including non-pass results; an older pass cannot win by filtering out newer failures.

Exit convention:

| Code | Meaning |
|---|---|
| 0 | Requested operation completed, and for validate all required content/design/review checks in scope passed |
| 1 | At least one conclusive content or design failure; evidence retained |
| 2 | Invalid request/profile/cohort or framework/reader error |
| 3 | Deferred G0, blocked/inconclusive/stale subject or pending mandatory review |
| 130 | Cancelled, with partial/cleanup evidence |

If outcomes mix, priority is framework error → unresolved/blocked → conclusive failure → pass; detailed per-case dispositions always remain available. The original execution receipt is untouched regardless of validation exit code.

## Compatibility and acceptance tests

Prove:

1. Old campaign receipts/configuration/history still load with unchanged execution and zero-content-validation semantics.
2. Adding requirement profiles outside generation packs does not change their fingerprints or grants.
3. New validation attempts cannot change workflow run status, approvals, template readiness or public qualification.
4. `pass/fail/skip/error` legacy states are bridged explicitly; unsupported skip is never accepted.
5. Same-run/cross-representation evidence is verified by actual hashes and semantic derivation; stale/cross-run artifacts fail before acceptance.
6. Candidate reports and all generated RTM formats reconcile, including no-feasible-design, partial review and reader-error cases.
7. Reader cancellation/restart cannot mutate originals or replay unknown native operations.
8. All 30 current cases and their required parts/variants receive a disposition. A missing adapter means unfinished implementation where that adapter is in scope.
9. Mixed fail/blocked/error results preserve known failures and separate evaluation completeness. Late reviews reject stale subjects, append report revisions and cannot impersonate a human or alter finalized evidence. Terminal retries use new IDs; current projections never hide newer non-pass results behind an older pass.
