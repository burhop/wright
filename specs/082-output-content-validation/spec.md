# Feature Specification: Process Output Validator

**Branch:** `codex/082-output-content-validation`
**Updated:** 2026-09-16
**Status:** Revised planning package; implementation not started
**Input:** Validate what a previous process step produced, return actionable feedback to its producing AI, and supply human-readable evidence to a separate reporting feature.

## Scope and authority

The [scope amendment](scope-amendment.md) proposes replacing the earlier all-30 campaign gate and report-UI scope. Submitting the revised goal approves this change. The 30 input packs inform reusable capabilities. Version 1 delivers a running process capability with structured-output, CAD and numerical examples; remaining family-specific readers form an explicit extension backlog.

A validator checks a declared output and requirement scope. It does not infer that the whole process or physical product is valid. MCP and non-MCP producers and readers use the same contracts.

## User Scenarios & Testing

### User Story 1 — Check a previous step inside a process (Priority: P1)

An author connects an output to a process check, selects a requirement profile, and connects downstream work to the check's accepted outcome.

**Independent test:** Run a saved canonical process with a non-MCP producer, validator and downstream consumer. A correct structured result proceeds; a wrong value, missing required field or stale subject prevents release.

**Acceptance scenarios:**
1. Given a completed producer step, when its declared output is checked, then evaluation binds the exact producer attempt and output revision even while the rest of the process is incomplete.
2. Given a required native reader is unavailable, when the check runs, then it identifies the missing capability and holds downstream work.
3. Given no MCP dependency in the profile, when checking text, structured values or local files, then the process evaluates them locally.
4. Given an MCP caller, when it invokes the validator with authorized bindings, then the same service and verdict semantics apply.

### User Story 2 — Correct a failed output using the findings (Priority: P1)

The producing AI receives evidence-backed correction instructions, creates a new revision and submits that revision for the same checks.

**Independent test:** A process produces an intentionally defective structured output; a real configured AI consumes its correction packet, creates a corrected revision, and the validator releases the consumer only after a pass. Repeat with a CAD-producing AI/MCP task.

**Acceptance scenarios:**
1. Given a measured defect, when feedback is delivered, then it includes requirement/check IDs, expected/observed values, tolerance, units/frame, evidence location, affected producer/output and an acceptance target.
2. Given a permitted revision path, when correction succeeds, then old failures remain in history and the new result references the new output revision.
3. Given only missing evidence with no repairable defect, a required evaluator fault, repeated unchanged output or exhausted revision budget, when the check cannot finish, then it stops automatic repair with a precise next action.
4. Given multiple producing steps, when feedback is assembled, then findings identify their owners; only an explicitly configured safe revision target may run automatically.

### User Story 3 — Reuse the result in user reports (Priority: P1)

A report author consumes stable validation records containing readable explanations and a requirements traceability matrix without rerunning measurements.

**Independent test:** Consume exported JSON using only the published schema and render the supplied Markdown/traceability rows. Every displayed verdict and measurement reconciles with the stored result, including failed and incomplete checks.

**Acceptance scenarios:**
1. Given a failed dimension, when rendered, then a user sees the requirement, observed dimension, allowed range, evidence-supported diagnosis and next action.
2. Given a newer incomplete or failed revision, when reporting current status, then an older pass stays historical and cannot mask it.
3. Given an honestly infeasible design, when assessed, then valid analysis and noncompliant design remain distinct.
4. Given a required human judgment, when no authorized decision exists, then the result identifies pending review; an AI summary cannot substitute for it.

### User Story 4 — Reuse engineering checks across output families (Priority: P2)

An author selects reusable geometry, structured-data or numerical checks and supplies source-backed requirements instead of writing one validator per workflow.

**Independent test:** Demonstrate the same engine on a non-MCP structured output, drill-jig geometry and heat-spreader results. Independently known good, alternative and targeted bad outputs exercise the intended checks.

**Acceptance scenarios:**
1. Given jig seat coordinates, when measured from actual geometry, then checks use the workpiece datum, circular center and specified per-axis tolerances.
2. Given heat-spreader candidates, when evaluated, then actual field/energy/refinement evidence is checked against independent calculations; a generator success report is insufficient.
3. Given an unsupported family-specific check, when requested, then it returns a capability-specific blocked result, never a placeholder pass.
4. Given any of the 30 source packs, when reviewing the capability inventory, then required capabilities and implemented/planned support are explicit.

### Edge cases

- Unsaved structured values, multiple files/parts, foreign-run evidence and provider resources with no stable revision.
- Output changes during inspection; canceled/crashed native reader; concurrent duplicate requests.
- Empty evidence, unsupported formats, nonfinite numbers, ambiguous units/datums and uncertainty crossing a threshold.
- A failed requirement alongside a blocked check; informative warnings versus mandatory failures.
- Mixed-producer findings, unsafe side effects, source conflicts and input changes during rework.
- Feedback containing artifact-sourced instructions, excessive text, credentials or untrusted paths.
- Direct invocation with no configured revision route: return feedback without scheduling work.

## Requirements

- **FR-001:** Invoke validation as a canonical process check and through direct service/MCP interfaces; do not require the entire process or 30-case corpus to finish.
- **FR-002:** Bind immutable producer attempt, output port, representation/revision/hash, baseline, profile and reader identities. Check readiness per subject.
- **FR-003:** Version source-backed requirements, methods, tolerances and applicability independently of generated outputs. Record scope and unresolved requirements explicitly.
- **FR-004:** Compose registered readers/checks by capability; case IDs select data rather than runtime branches. Package runtime resources outside test-only directories.
- **FR-005:** Measure actual files/values or pinned native readback. Record method/evidence strength; a summary cannot prove unobserved geometry or physics.
- **FR-006:** Return typed findings with expected/observed constraints, evidence selectors, ownership, correction target, routing category and readable explanation.
- **FR-007:** Preserve pass/fail/blocked/inconclusive/error/justified-not-applicable states and separate content verification, design compliance, evaluation completeness and physical evidence.
- **FR-008:** Gate downstream work on a conclusive current pass for the entire declared mandatory scope; informational checks cannot hide mandatory omissions.
- **FR-009:** Route feedback to a configured upstream producer and support bounded safe revision followed by revalidation. Preserve satisfied constraints; never weaken the profile automatically.
- **FR-010:** Persist revision budgets, feedback, attempts and invalidation across resume. Stop on no progress, stale identity, unknown side effects or exhausted budget.
- **FR-011:** Keep validation read-only. The runner owns authorized producer execution; no evaluator edits originals, reruns manufacturing, submits orders or invents approval.
- **FR-012:** Publish versioned JSON, readable Markdown and requirements traceability rows from the same immutable assessment; provide read/export operations for the reporting branch.
- **FR-013:** Preserve historical assessments, fail-closed currentness and genuine reviewer identity; late authorized review creates a new assessment.
- **FR-014:** Demonstrate structured-output, drill-jig and heat-spreader capabilities with real process evidence; map all 30 packs to capabilities without claiming all are implemented.
- **FR-015:** Qualify checks with valid, alternative, defect and boundary controls; verify confinement, error routing and existing process compatibility.
- **FR-016:** Preserve offline operation where dependencies permit, package boundaries, tracing, auth/RBAC, native resource ownership and established process authoring.
- **FR-017:** Make configuration and results accessible in existing process authoring/run surfaces; keep the separate report application out of this feature.

## Key Entities

Validation request, subject binding, requirement baseline/profile, reader identity, measurement, check result, finding, repair feedback, immutable attempt, assessment, report projection and subject-bound review decision. See [data-model.md](data-model.md).

## Success Criteria

- **SC-001:** A saved producer → validator → consumer process runs; valid output releases exactly its validated revision and invalid/unknown output does not.
- **SC-002:** Real AI correction demonstrations succeed for non-MCP structured output and a CAD/MCP producer; wrong → findings → new revision → pass is retained, and bounded-stop behavior is proven.
- **SC-003:** Every non-passing mandatory check has a source/evidence-linked finding and usable disposition; findings are readable without internal implementation knowledge.
- **SC-004:** JSON, Markdown and traceability agree by assessment ID/digest and currentness; a consumer can use them without importing validator internals.
- **SC-005:** Three initial capability slices are verified, all 30 packs are accounted for, and unsupported capabilities never pass.
- **SC-006:** Existing design-check/review and authoring remain functional; focused contract/runtime/native tests and applicable three-tier UI checks pass.
- **SC-007:** Original artifacts remain unchanged, prior failures stay accessible, and retries cannot reset correction budgets or reuse stale passes.

## Assumptions and exclusions

Implementation does not start in this planning task. Use isolated demonstration runs; do not take over the generation campaign. Full 30-case evaluation, all specialized readers, arbitrary graph rewinds, a new report UI, physical qualification and publication are later work. The first automatic revision segment contains one safe producer and its validator; other affected owners receive findings and require an explicit later run or future supported route.
