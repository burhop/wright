# Data model for feature 082

The [complete adopted model](../081-engineering-workflow-templates/content-validation/data-model.md) is normative for entities, keys, state transitions, aggregation, currentness, metrics and reports.

Implementation clarifications:
- Cohort/source-root authorization must support read-only source data outside the code worktree. Persist logical source identity and confined artifact locators; do not expose private host paths in ordinary views.
- ReviewRecord retains actual authority context and permitted reviewer type. The existing unauthenticated artifact-review label cannot establish human acceptance.
- AssertionResult.error must remain distinct from a measured fail across legacy adapters.
- Append-only AssessmentRevision and exact review/decision digests are mandatory; a late review creates a new report, and terminal retry creates a new attempt.
- No persisted current-result query may filter to passing rows before choosing the latest authoritative sequence.
- Units, tolerance, uncertainty and interval boundary rules remain frozen profile data; a failed comparison never rewrites them.

Ownership: pure contracts in core, persistence in data_vault, authority and orchestration in workspace_service. T006–T011 implement and test these rules.
