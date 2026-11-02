# Producer Evidence Contract

**Status**: Implemented feature-083 consumer envelope for authorized workflow and
validation producers.

## Ownership

| Concern                                                                                                   | Owner                                                         |
| --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Requirement derivation and validation, engineering checks, acceptance thresholds, correctness conclusions | Existing workflow and validation producers                    |
| Input and requirement approval decisions                                                                  | Existing user-approval components                             |
| Existing execution, retries, branch selection, and tool operations                                        | Existing runtime                                              |
| Incremental capture additions required to preserve report history                                         | Feature 083 through narrow runtime hooks                      |
| Evidence indexing, navigation, result presentation, report projection, ZIP export                         | Feature 083                                                   |
| Schema, identity, link, and byte-integrity checks for report data                                         | Feature 083; these do not establish engineering correctness   |

## Producer Envelope

The implemented envelope accepts `schema_version`, `evidence_id`, `producer`,
`producer_version`, `producer_record_id`, `run_id`, `kind`, `recorded_at`,
`subjects`, `statement`, `recorded_outcome`, `supporting_refs`, and optional
`supersedes_id`. Workspace scope comes from the authenticated session rather
than a producer-asserted field. Producer identity is stable across retries.

Subjects identify the appropriate `occurrence_id`, `artifact_version_id` and content digest, `requirement_id` and revision, input baseline digest, or run-level scope. A validation of one artifact must never apply automatically to later iterations. An unavailable subject mapping stays explicit until an exact mapping can be made.

`statement` and `outcome` are producer-authored, with the original producer vocabulary retained. An optional display label must not change the meaning. Include links to full machine-readable results and human-readable reports when available. Later corrections use `supersedes` references; ingest does not overwrite the original claim.

## Evidence Kinds

| Kind        | Additional fields requested where applicable                                                                                             |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Requirement | Requirement ID/revision, statement, source document revision and location, acceptance criterion, scope                                   |
| Approval    | Actor, time, decision, approved subject ID/revision/digest, rationale/reference                                                          |
| Assumption  | Statement, applicable scope, source or decision reference, units if relevant                                                             |
| Decision    | Recorded choice, concise recorded rationale, considered alternatives if recorded, evidence references, actor/tool                        |
| Validation  | Check ID/version, checked subject, criterion/threshold, recorded result and units, outcome, tool/version/configuration, result documents |

Domain-specific detail remains in namespaced metadata or linked evidence documents. Examples include mesh sizes and element counts, convergence studies, boundary conditions, materials, solver settings, coordinate systems, CAD tolerances, PCB design-rule/connection reports, slicer settings, and dimensional tables. Feature 083 displays such data; it does not prescribe new domain checks or interpret their adequacy.

## Runtime Capture Hooks

The report needs run-start definition/layout and input bindings; step-start occurrence with actual resolved prompt/context references; explicit traversal with producer/consumer occurrences and transferred versions; tool/result events; artifact publication before overwrite; and terminal/error/checkpoint events. Preserve exact recorded prompts where available under current credential handling, not private internal model reasoning.

Shared changes to `workflow_run_record.py`, `workflow_source_execution.py`, `workflow_results.py`, and affected repositories must preserve their established ownership. Prefer additive hooks or a single adapter maintained in the owning layer. Do not independently migrate the same table or introduce competing result-ID schemes.

## Consumption Rules

1. Report generation reads records without invoking validators or execution.
2. Run completion never synthesizes validation or human approval.
3. Missing evidence appears only in the relevant expanded detail as unavailable/not recorded; it is not a new top-level concern or an implicit pass.
4. Failed validation is shown exactly as supplied. If the runtime records it as a blocker/error, the run header can show that recorded state. Trace does not independently block a completed workflow.
5. Superseded checks remain linked to their original subjects. Conflicting producer records stay attributable rather than being silently reconciled by Trace.
6. Late validation creates a new report evidence revision. An already exported ZIP retains its original evidence cutoff.

## Contract Acceptance

Use recorded or explicitly synthetic envelopes to cover two artifacts with the same filename and different hashes, two requirement revisions with different approvals, a corrected validation record, a run-level check, a failed check, an unsupported producer schema, and a record whose artifact is unavailable. Verify navigation and identity association only. The engineering validator's own test suite establishes correctness.

No change to feature-081 deferred validation's assignment or G0 gate follows from this contract.
