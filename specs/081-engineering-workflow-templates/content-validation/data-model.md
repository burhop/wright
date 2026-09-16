# Output-validation data model

**Status:** Design contract; implementation is deferred by [G0](plan.md#g0-mandatory-start-gate).

All entities carry schema versions. Canonical digests use the repository's canonical serialization, not incidental JSON whitespace. Large data remain in the vault/files; records contain bounded summaries and references. Storage and migrations belong to data-vault.

## Entities and relationships

| Entity | Required identity and content | Invariants |
|---|---|---|
| ValidationCohort | cohort ID/version, campaign ID, ordered 30 case IDs, activation evidence, input/template/definition/binding/receipt/output manifest digests per selected attempt | One selected attempt per case per frozen cohort; preserve alternative/history records; currentness is derived |
| SourceBaseline | baseline ID/version/digest; source file hashes and locators; original-to-normalized image/table relationships; authorized amendment graph | Input amendments apply narrowly; no generated claim becomes source authority |
| Requirement | ID, revision, source refs, statement, mandatory/objective/preference/assumption/deferred kind, applicability, verification dimension, method, units/frame, expected values, tolerance/uncertainty rule and rationale | Unique stable ID; explicit supersession; absence of tolerance never implies unlimited tolerance; decision objectives remain distinct from hard constraints |
| RequirementDecision | decision ID, authority/actor, exact subject digest, source conflict or applicability/tolerance disposition, rationale, timestamp | Never manufacture human approval; prior test-auto run approval does not amend the requirement baseline |
| AcceptanceProfile | ID/version/digest, source baseline, artifact-role/cardinality selectors, reader/validator identities, assertion definitions, requirement links, all-required/any-approved-alternative logic, review rubric | Case profiles contain data, not executable code; required AND checks cannot be weakened by unrelated passing checks |
| ReaderIdentity | reader/version/code digest, underlying kernel/application/tool/schema/image identities, supported formats/host, bounded resources, qualified fixture evidence | Configured operation identity is part of the measurement; unsupported formats stay explicit |
| ArtifactSubject | workflow run/workspace/case/attempt IDs, role/variant/refinement, original runtime artifact ID, relative/vault reference, source SHA-256, media/schema, byte count, producer and upstream links | Exact selected run; confined access; no hash-only equivalence claim between different representations |
| Measurement | measurement ID, artifact subject refs/digests, reader identity, observed quantities, units/frame, uncertainty/method, evidence locator and derivation edges | Independently extracted facts; expected limits never passed as substitute observations; producer booleans are claims until checked |
| AssertionResult | assertion ID/version, requirement IDs, state, expected/observed, tolerance, evidence/measurement refs, reason code, dimension (content/design/review), optional defect location | Missing/unsupported/crashed observations never pass; preserve raw and normalized values |
| RequirementResult | requirement ID/revision, applicable decision, required checks/reviews, aggregate state and reason | Aggregate on requirement identity, not number of assertions; retain justified N/A records |
| ValidationAttempt | validation ID, cohort/case identity, full subject/profile/reader-set key, lifecycle timestamps, state, result/review IDs, trace ID, environment, cleanup, final report digest | Independent of workflow run; terminal result immutable; revalidation creates an explicit new evaluation/revision or reads a verified cache |
| Finding | finding ID, validation/requirement/artifact refs, expected/observed, severity, generator/validator/source/reader classification, reproducer, remediation owner | A validator fix never rewrites the old finding; generator repair creates a separate source/output revision |
| ReviewRecord | reviewer type/identity, subject/rubric/model version, evidence locators, judgment/uncertainty and timestamp | LLM output cannot impersonate human acceptance; numerical failure cannot be overridden by a presentation score |
| AssessmentRevision | assessment ID, validation attempt ID, prior assessment ID, exact review/decision digests, derived requirement/content/design outcomes, timestamp and report digest | Append-only adjudication of retained measurements; later review never changes a finalized attempt or earlier report |

Fixture manifests additionally retain provenance, independent reference calculation/source, expected per-assertion results, deliberate defect specification and reviewer identity. They are excluded from real corpus metrics.

## State and verdict semantics

Validation lifecycle:
`queued → running → completed | blocked | cancelled | error`.

A completed validation may contain failed assertions/design requirements. Infrastructure failure is `error`; absent reader/capability is `blocked`; inadequate measurement or unresolved evidence is `inconclusive` at check level. Persist typed reasons and partial evidence before stopping.

New check states:
`pass | fail | inconclusive | blocked | not_applicable | error`.

Legacy adapter mapping is explicit:

| Source | Mapping rule |
|---|---|
| Scenario assertion pass/fail | Preserve only after independently measured observations and any uncertainty policy have been satisfied |
| Scenario assertion skip | Map to not_applicable only with an explicit applicability decision; otherwise inconclusive |
| Scenario assertion error | Keep error; never skip or pass |
| Workflow assertion inconclusive | Preserve inconclusive |
| Reader unsupported/missing | Blocked with exact format/host/schema reason |
| Measurement interval crossing an acceptance boundary | Inconclusive under the frozen measurement policy |
| No candidate satisfies a design limit | Content checks may pass; design requirement fails |

Overall content state and design-compliance state are computed separately. A false report claiming success fails content checking even if its raw data correctly show failure. Missing required reviews prevent a complete acceptance claim.

For mixed results, preserve every child state and reason. Any conclusive mandatory design failure means `compliant=false` even when other design checks are blocked or error. Separately set `evaluation_complete=false` while required measurements/reviews are unresolved. With no known failure but unresolved required checks, compliance is undetermined, not true. Apply the same known-failure/unresolved distinction within the content dimension; a CLI operational-error exit never hides an engineering failure in the report.

Resume only queued/running interrupted attempts with an unchanged full identity key and reconciled resource state. Completed, blocked, cancelled and error attempts are terminal: a retry creates a new validation ID linked to the prior attempt. Completing a later subject-bound review appends a ReviewRecord and AssessmentRevision with new report identity; existing measurements can be referenced after currentness checks without rerunning readers or mutating finalized records.

## Identity and invalidation

The evaluation key covers:
`cohort/case + input baseline + template + canonical definition + bindings + receipt snapshot + actual output manifest + requirement/profile digests + reader code/tool/schema/configuration + assertion versions + review rubric`.

Never use only scenario ID, file path, mtime or SHA of a generated summary. A semantic reader can normalize ordering while preserving source-file identity and its transform. Kernel-generated face IDs are not stable feature selectors.

Assessment/report identity also includes the exact authorized review and requirement-decision set. Current projections select the explicitly persisted supersession head for the exact current subject/profile/reader key, ordered by a monotonically assigned evaluation/assessment sequence, never by highest pass count. A newer failure, error, inconclusive or in-progress evaluation cannot be masked by an older pass. Previous verified results remain visible as historical with their own identities and status.

Any relevant input change invalidates affected current projections and cached checks. Prior attempts/reviews remain immutable. Re-hash referenced artifacts before reading and before committing a result, or use a verified immutable snapshot. If the subject changes while running, return stale-subject/inconclusive and retain the failed attempt; do not combine revisions.

## Metrics

Keep the old output-generation database/events and four counter meanings intact. Add a separately versioned validation projection with:

- Expected cohort cases (30), eligible/current selected cases and evaluation attempts.
- Cases content-verified, content-failed, inconclusive, blocked/error, pending and stale.
- Cases requirements-compliant, noncompliant and not fully determined.
- Mandatory requirements total/applicable/not-applicable, mapped, evaluated and passed.
- Required review total/completed/pending; physical validation scope if separately evidenced.

Requirements coverage counts unique requirements, not checks. Report mapped/applicable and conclusively evaluated/applicable separately. Publish the explicit N/A count and rationale; no silent denominator change. Empty applicable sets do not earn a full-compliance badge.

Historical successes and current availability are separate views. Current counts may decrease after source/reader/profile changes. Never backfill new validation into old execution events.

## Persistence and reports

Use an additive data-vault repository with unique evaluation identities, transactions, append-only event/review records and immutable terminal report digests. Reuse existing scenario repository mechanisms only where they preserve these semantics; do not pretend canonical execution is a legacy Rivet scenario.

Default generated root: `artifacts/engineering-workflow-validation/`. A dedicated `validation.sqlite3` uses the data-vault-owned schema; per-evaluation JSON/CSV/HTML/JUnit and bounded reader logs live under validation IDs. Original corpus outputs remain under their existing root and are opened read-only.

Exporters consume persisted results. CSV/HTML escape untrusted strings and protect spreadsheet formula-like cell prefixes while retaining raw canonical JSON. Public/user views use authorized artifact links and redact private host paths/credentials; local protected reproducibility records may retain necessary environment identity.
