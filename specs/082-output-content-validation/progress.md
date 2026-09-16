# Progress checkpoint

**Updated:** 2026-09-16
**Phase:** Implementation active; M1 implementation and focused checks complete; M2 bounded correction next.
**Implementation:** T001–T013 complete. T014–T034 remain. The user submitted the revised goal and authorized implementation/verification through M0–M5.

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

Implement typed bounded feedback and the safe generic correction loop (T014–T018). Publish the report contract early. Complete all required demonstrations and gates before claiming the implementation finished.

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

## M1 evaluator evidence — 2026-09-16

- T007–T009: `process_validation/readers/structured.py`, `evaluation.py` and `service.py` inspect real inline values and bounded JSON/CSV/text files, compare independent observations, and finalize immutable assessments. Registered engineering numeric predicates are reused after observation. Units, finite values, uncertainty intervals and exact selectors are preserved.
- `test_process_validation.py` adds 26 behavioral cases covering passing alternatives/boundaries, defects, malformed/ambiguous JSON, missing fields, stale snapshots, unsupported readers, evaluator errors, cancellation, mixed outcomes, units, uncertainty, CSV rows and source fixtures.
- Findings distinguish expected units/frame from observed units/frame. Mutation during inspection retains measured facts, marks `subject_current=false`, and adds a readiness finding; it cannot release downstream work. A newer unfinished/failed attempt prevents an older passing invocation from becoming current.
- Structured profile version 2 adds explicit required-length presence and required-identity coverage discovered during missing-field controls. The source baseline/digest and engineering limits remain unchanged.
- Core/repository/subject/evaluator suite: **71 passed** using `.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_validation.py packages/data_vault/tests/test_process_validation_repository.py packages/workspace_service/tests/test_process_validation_subjects.py packages/workspace_service/tests/test_process_validation.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-validation-5`.
- Ruff check and formatter passed on changed Python files. Updated contract schemas exported with `scripts/export_process_validation_schemas.py`.

These checks establish evaluator behavior, not a running AI repair demonstration. Canonical runner/tool/UI integration and real demonstrations remain open.

## M1 backend integration evidence — 2026-09-16

- T010: closed `ValidatorConfiguration` / profile locations and exact input-role bindings compile as ordinary canonical tasks. Profile/baseline pins are checked before execution. Approval edges use existing ordering. Invalid/missing pins, unbound or duplicate subjects, collections, mixed MCP settings and unsafe policies are rejected. Grammar is in `contracts/process-source.md`.
- T011: `ValidationApplication`, `ProcessValidationTool` (BaseTool), `ProcessValidationGatewayProvider` and packaged `wright-process-validate` CLI reuse the evaluator. Registered through the existing gateway capability-provider interface in API composition; no extra daemon or transport. Real GatewayService policy/schema/audit dispatch is exercised. A measured fail is returned data; invalid caller authority is a tool error.
- T013: the canonical runner records exact completed producer outputs, executes the local validator without a model call, writes immutable assessment evidence before a held gate, and releases the consumer only after a current pass. Tests prove ordinary producer/check/consumer execution, missing capability, no-subject blocked evidence and direct/tool/read parity. Existing result roles/events and run-history projection are reused.
- Raw inline response encoding preserves original UTF-8 bytes, so duplicate JSON members are visible to the reader instead of being lost during an adapter parse. Empty available-subject sets yield mandatory missing-role findings. Runner output registration is immutable and workspace/producer-attempt scoped; external callers cannot claim a canonical gate stream.
- Core/repository/readers/tools/compiler/runner/design-check/run-history/resume suite: **181 passed** with `.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_validation.py packages/data_vault/tests/test_process_validation_repository.py packages/workspace_service/tests/test_process_validation_subjects.py packages/workspace_service/tests/test_process_validation.py packages/workspace_service/tests/test_process_validation_tools.py packages/workspace_service/tests/test_workflow_process_validation.py packages/workspace_service/tests/test_workflow_source_execution.py packages/workspace_service/tests/test_workflow_design_check.py packages/workspace_service/tests/test_workflow_run_resume_record.py packages/workspace_service/tests/test_workflow_run_history.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-m1-1`.
- Reviewed the required workflow integration runbook, recovered 080 north-star/plan and `image-redesign-delivery.json` before authoring edits. Preserve the existing canvas/inspector/source/command seam. Browser evidence for this feature remains T032.
- API composition and authenticated MCP transport regression suite: **7 passed**, one existing Starlette/httpx deprecation warning, with `.venv/Scripts/python.exe -m pytest apps/api/tests/test_workspace_composition.py apps/api/tests/test_mcp_transport.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-api-m1-1`. Ruff passed; seven public contract schemas exported.

Still open: authoring T012; bounded feedback/rework and real AI demonstration M2; readable exports/review routes M3; actual CAD/thermal readers and demonstrations M4; native/Docker/browser gates M5. Current backend tests do not establish these claims.

## M1 authoring integration evidence — 2026-09-16

- T012: added Review → Validate output to the existing palette/inspector. Profile selection loads generated pins from the same packaged profiles; subject controls connect exact producer outputs and retain compatible port types. The existing command, Source/Diagram, Undo/Redo and save/reopen paths are preserved. Technical references stay in disclosure. No report dashboard was added.
- `validation-settings.ts`, `ValidatorBlockEditor.tsx`, generated `validation-profiles.json`, and corresponding tests own the new controls. Existing `authoring-objects.ts`, `recovery-authoring.ts`, `recovery-dsl.ts`, `canonical-wire.ts` and `WorkflowRecoveryConcept.tsx` extend the accepted model. No model/command schema replacement was needed: validation is serialized JSON internally and a documented object in public source.
- First authoring tests caught the existing nonempty deterministic instructions rule and canonical JSON ordering. The validator now carries descriptive instructions (never executed as a prompt) and uses the established stable-value canonicalizer. Test controls were corrected to use an actual distinct producer and history-origin Undo/Redo commands.
- **139 frontend tests passed** across the new settings/component tests, existing editor, authoring/source/instruction/command tests and workspace reopen suite. Command: `node ../../node_modules/vitest/vitest.mjs run src/prototypes/workflow-recovery/validation-settings.spec.ts src/prototypes/workflow-recovery/ValidatorBlockEditor.spec.tsx src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx src/prototypes/workflow-recovery/authoring-objects.spec.ts src/prototypes/workflow-recovery/recovery-authoring.spec.ts src/prototypes/workflow-recovery/recovery-instruction-fields.spec.ts src/prototypes/workflow-recovery/command-system.spec.ts src/components/pages/WorkflowRecoveryReopen.spec.tsx`, from `apps/web`.
- TypeScript build check (`node node_modules/typescript/bin/tsc -b --pretty false`) and targeted ESLint passed. Python compiler/design-check regression selection: **73 passed** under `.local-run/process-validation-082/pytest-authoring-1`; Ruff passed. The existing Vite native-config warning remains unrelated.
- Use installed local Node entry points for checks. The runtime fallback `pnpm exec` unexpectedly attempted installation, moved two local dependencies, and hit restricted network access. That owned process was stopped; the exact two moved directories were restored within `apps/web/node_modules`, and checks ran against the existing installation. No dependency/package version change was intended or needed.

This is implementation/component evidence. Served workspace entry, responsive/visual evidence and installed native/Docker qualification remain M5; real AI repair and CAD/heat demonstrations remain M2/M4. No claim of user visual acceptance or full corpus validation.
