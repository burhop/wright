# Progress checkpoint

**Updated:** 2026-09-16
**Phase:** Implementation active; M0 foundations complete, M1 next.
**Implementation:** T001–T006 complete. T007–T034 remain. The user submitted the revised goal and authorized implementation/verification through M0–M5.

## Current objective

Build a runtime process validator with evidence-backed findings that a producing AI can act on, bounded correction/revalidation, and readable results for the separate reporting branch.

The [scope amendment](scope-amendment.md) and [saved goal](implementation-goal.md) make the change explicit. Submitting the goal approves replacing global all-30 readiness with per-subject checks and the first three capability slices. Planning is not activation.

## Workspace and history

Use `D:/repos/wright` on `codex/082-output-content-validation`. The earlier branch/dev recovery is complete; no further recovery task is implied. Previous planning documents are retained in Git history at `0a48f88f`.

The dated [readiness snapshot](evidence/readiness-2026-09-16.json) recorded 24/30 outputs during earlier planning. It is not a current audit and does not gate the revised runtime implementation. The 081 analysis remains valuable source material; its old activation/dashboard scope is superseded on approval of the revised goal.

## Reviewed and prepared

- Reviewed earlier 081/082 plans, source-derived acceptance cases and current constitution.
- Located existing canonical CAD design-check and feedback/revision mechanisms; identified their non-CAD restrictions and revision identity gaps.
- Prepared runtime service, per-subject readiness, typed findings, bounded repair and report-consumer contracts.
- Preserved all-30 capability mapping with a bounded initial structured/CAD/numerical delivery.
- Replaced the 74-task campaign/UI plan with 34 tasks: setup 2, foundations 4, US1 7, US2 5, US3 4, US4 7, closure 5.
- Updated spec, plan, research, data model, contract, acceptance map, quickstart, goal, managed AGENTS reference and checklist.
- Kept report application/UI ownership in the other branch; only process authoring/status integration is planned here.
- Verified document links, sequential task IDs/counts, the 30 distinct source manifest IDs and whitespace; see [planning review](evidence/planning-review-2026-09-16.md).

## Next action

Implement T007–T009: behavioral evaluator tests, structured readers and the application service over the new contracts/repository. Then connect the canonical validator mode and tools (T010–T013), followed by the actual correction loop. Publish the report contract early. Complete all required demonstrations and gates before claiming the implementation finished.

Implementation progress entries should state completed task IDs, exact files/commands, evidence paths, blockers and next work. Nothing in this checkpoint claims a measured output pass, live process demonstration or human engineering acceptance.

## M0 implementation evidence — 2026-09-16

- T001: [runtime integration](evidence/runtime-integration.md) records the existing canonical compiler/scheduler, MCP composition, packaged resource paths and isolated runtime roots. Prerequisite/checklist checks passed (19/19); optional pre-commit hook skipped because tracked work was clean.
- T002: `scripts/build_process_validation_coverage.py` generated 30 unique source inventories with per-file hashes, requirement/defect seeds and planned capabilities. Structured demonstration requirements were frozen before evaluation and copied into runtime resources.
- T003: `core/process_validation.py` adds versioned source/profile/subject/request/measurement/check/finding/assessment/feedback/review models, canonical identities and conservative aggregation. Five generated JSON schemas are in `contracts/schemas/`; packaged profile validates against the exported schema.
- T004: `data_vault/process_validation_repository.py` adds workspace-scoped SQLite WAL attempts, immutable terminal results, latest-attempt projection, idempotency, cancellation/resume and append-only subject-bound review. Review cannot remove measured checks or apply to a superseded attempt.
- T005: subject resolver reuses a new public wrapper over the existing pinned-directory bounded file reader. Exact hash and runtime binding checks, unchanged-output recheck, reader capability/method/format identity, cancellation/deadline/entity bounds and native-readback extension contracts are implemented. Native reader qualification remains T024–T028/T030, not claimed here.
- T006: runtime profile loader validates closed schemas and pinned digests, using packaged resources or confined workspace files. Missing registered reader support produces an explicit blocked capability result.

Validation commands used `.venv/Scripts/python.exe` with `-p no:cacheprovider` and unique `--basetemp=.local-run/process-validation-082/...` directories. The shared old pytest cache is not writable; using a private test root avoids changing it.

- Core/repository focused tests: **32 passed**.
- Workspace profile/subject tests: **13 passed**.
- Existing source-store bounded-read/confinement regression selection: **9 passed, 2 skipped** (host symlink support), 49 deselected.
- Ruff check passed on all new Python files; formatter applied.
- Exported JSON schemas, packaged profile schema and all 30 source inventory records verified.

Initial test-first core collection failed as expected before the new model existed. The first repository test command failed because its private parent directory did not exist; creating that parent resolved setup, then all tests passed. No process/solver/AI demonstration has run yet. No pushes or merges.
