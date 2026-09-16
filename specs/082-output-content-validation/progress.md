# Progress checkpoint

**Updated:** 2026-09-16
**Phase:** Implementation active; M0–M4 complete; closure M5 remains.
**Implementation:** T001–T032 complete. T033–T034 remain. The user submitted the revised goal and authorized implementation/verification through M0–M5.

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

Complete the runnable documentation and final requirement-by-requirement closure audit in T033–T034. Complete all required examples and gates before claiming the implementation finished.

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

## M2 runtime correction evidence — 2026-09-16

- T014: `RepairFeedback` now enforces ownership and a 20-finding maximum. `process_validation/feedback.py` builds a 16-KiB-bounded packet from the exact persisted assessment, prioritizes producer-owned measured defects, carries complete-result references, and lists passing requirement constraints to preserve. The prompt frame treats findings as data and requires a complete fresh recheck.
- T015: the existing revision graph accepts one contiguous ordinary-AI text/structured producer directly owning all validator subjects, while retaining create-new CAD behavior. Tool calls, application edits, reviews, external actions, overwrite policy, unrelated subjects and arbitrary back-edges remain rejected. The canonical runner persists typed delivered feedback and revision counts, retains old attempts, invalidates the checked segment, detects identical output/defect no-progress, and releases only the current passing revision.
- T017: focused tests cover measured feedback, owner/subject identity, new attempt lineage, mixed fail/unknown behavior, evaluator error routing, unsafe/wrong targets, no progress, exhaustion, cancellation, run-history projection and existing approval-continuation/stale guards. The delivery event exposes bounded identities and budget without copying full findings into the polling projection.
- Feedback unit suite: **8 passed**. Expanded rework suite: **9 passed**. Focused design-check/runner/history selection: **104 passed**. Backend core/validator/compiler/runner/history/continuation regression set: **195 passed** using `.venv/Scripts/python.exe -m pytest ... -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-m2-backend2`.
- Ruff and `git diff --check` passed. `RepairFeedback.schema.json` was regenerated with its public `maxItems: 20` bound.

- T016: the existing validator inspector exposes the exact eligible revision target and a zero-to-three limit. It only offers the ordinary-AI producer owning every bound subject, selects one revision atomically, disconnects at zero, and clears unsafe stale targets when subject/profile ownership changes. Source/Diagram round-trip retains the standard feedback edge and limit. Existing run diagnostics now label output held, repairing output and correction budget exhausted from canonical events; polling carries bounded identities rather than findings.
- Validator settings/editor/status tests: **13 passed** within the broader frontend selection. Workflow component/observer selection: **61 passed** across five files. TypeScript build and targeted ESLint passed. Backend status/event regression selection: **71 passed**; Ruff and `git diff --check` passed.

- T018: `structured-loop.workflow.wflow` ran through the production compiler, runner, validator and `agent_adapters.generate_workflow_response` against the configured Hermes endpoint. The model produced the seeded 98 mm defect, consumed the typed measured finding, wrote a distinct 100 mm revision, passed the pinned profile and released the consumer.
- Retained evidence is under `artifacts/process-validation/structured-loop/20260916T202647Z/`: source and hash, three model-usage records, both output identities, two immutable assessments, feedback delivery, events, run log and final release note. Its manifest records every retained file by size and SHA-256; transient SQLite and nested Git state were removed after capture.
- Independent retained-evidence and saved-process checks: **12 passed** using `.venv/Scripts/python.exe -m pytest tests/external/process_validation/test_structured_loop_evidence.py packages/workspace_service/tests/test_workflow_process_validation_rework.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-m2-evidence`. Ruff and `git diff --check` passed.

M2 is complete. This evidence proves the bounded structured-output slice; it does not claim the still-open CAD correction or thermal validation demonstrations in M4.

## M3 report boundary evidence — 2026-09-16

- T019: `ValidationReport` is a closed public `wright.process-validation-report/1` envelope containing the exact immutable assessment, digest, query-time currentness, declared scope, reader identities and one RTM row per requirement/check pair. `reporting.py` projects JSON, escaped Markdown and formula-neutralized CSV from this single object. Contract-valid pass, fail, mixed, blocked, error, stale and repair examples plus repair Markdown/CSV are published under `contracts/examples/`.
- T020: the shared service owns get, bounded finding paging, export and late review. Currentness distinguishes newer attempts, superseding review assessments, changed output revisions, mutation during validation and unavailable subjects. Review identity comes from the API control plane, applies only to an explicitly reviewable current requirement, and appends a new assessment. Existing-auth HTTP routes require the owning workspace session and engineer/admin role when enforced. MCP adds read-only get/export while retaining paged read; CLI adds get/export. Human review is not exposed to the model-facing gateway.
- T021: `contracts/report-consumer.md` publishes exact schema/version, effective-verdict rule, routes, paging, artifact references, output safety and an independent consumer recipe for the separate report branch.
- T022: tests cover shared JSON/Markdown/CSV verdicts, schema-only validation of every example, stale/latest selection, pass and changes-requested review, immutable history, cross-workspace denial, authenticated actor derivation, role denial, Markdown/HTML escaping and CSV formula neutralization.
- Combined M3/core/repository/evaluator/tool/runner/API regression selection: **124 passed**, with one existing Starlette/httpx deprecation warning, using `.venv/Scripts/python.exe -m pytest ... --basetemp=.local-run/process-validation-082/pytest-m3-combined1`. Focused schema/example/API selection: **9 passed**. Ruff and `git diff --check` passed.

M3 is complete. The report UI remains owned by the separate branch; this feature publishes its stable data and transport boundary only.

## M4 engineering reader evidence — 2026-09-16

- T023: packaged, source-pinned `parametric-drill-jig-01` and `heat-spreader-sizing-01` profiles freeze mandatory scope, subject roles, units, datum, tolerances, analytical constants, excluded scope and limitations. Profile/baseline digests are `5488f377adfa5eaea61ce4b8e299654bb74709ed313b67e8f04494bd2e4a3884` / `5fb63ff5fca47d189665efe2d22424743205a0c12812f193cd79b49fe4ebf2d8` and `28c7cbd9811fe2423715b7c485195a5cafd53cbc7118a66492fa0995036bdc82` / `3f6464140ae741a0ef9ecd8dabcde8bcbbe3cc1f9755955d7ec12b1cac89e564`. The authoring profile list is generated from these same runtime resources.
- T024/T025: `step-seat-geometry@1` reads bounded ISO-10303-21 circle placements from the exact file snapshot, rejects 2-D parameter-space circles, transforms placement origins into the frozen workpiece datum, selects the H1/H2 regions semantically and records the exact file hash and reader identity. Good, reordered/reversed-axis, arc-center, inclusive-boundary, shifted-datum, radial-clearance and missing-seat controls exercise measurements rather than parser rejection. The hash-pinned retained generated jig at attempt 012 (`2e4b9c5a137ef9d32c6ca0a4b58b4a74806bc2d94b68a6af77b496016fb6df84`) passed all six checks with H1 `(30,30)`, H2 `(170,30)` and 10.2 mm diameters.
- T026/T027: `thermal-field@1` independently parses finite coordinate/temperature CSVs, checks source dimensions, computes analytical rise and heat balance, compares bound coarse/fine lineage and derives the narrowest passing candidate from the actual bound fields. Controls cover exact references, wrong load, omitted candidate, fabricated decision, wrong unit headers, the inclusive 45 C boundary and valid-but-infeasible output. The retained attempt-008 baseline/revision coarse/fine fields and decision passed all 15 checks.
- Engineering reader qualification: **17 passed**. Full process-validation core/repository/service/tool/report/runner and engineering-reader selection: **153 passed** using `.venv/Scripts/python.exe -m pytest ... -q -p no:cacheprovider --basetemp .tmp-082-m4-regression`. Ruff, Python compileall and `git diff --check` passed.

T023–T027 are complete. At this checkpoint their reader tests alone did not claim the process demonstrations.

## M4 engineering process evidence — 2026-09-16

- T028: `jig-validation-loop.workflow.wflow` ran through the production compiler, canonical run recorder, real Hermes action/response generators, Wright MCP gateway, isolated FastMCP server and packaged geometry validator. The model first called `create_jig_step` with H1/H2 x positions 31/171 mm. Independent STEP readback produced two out-of-tolerance findings, the runner delivered the typed packet to `produce`, and the model called the tool again with 30/170 mm. The second STEP had a distinct subject ID and SHA-256, passed all six checks and released the consumer.
- T028: `heat-validation.workflow.wflow` copied five retained attempt-008 files into an isolated workspace without changing their source hashes, staged them through the real MCP tool, measured 15 numerical facts with `thermal-field@1`, selected `revision_60`, passed the frozen profile and released its consumer. This validates retained generation output; it does not modify or rerun the generation campaign.
- Qualifying evidence is `artifacts/process-validation/engineering/20260916T213859Z/`. Its manifest covers 35 retained files, including real tool discovery/calls, model usage, events, run logs, old/new STEP snapshots, all immutable assessments and final consumer outputs. Assessment IDs are `assessment-784aa83e624c471daf66cf8d9c2247bb` (revise), `assessment-e629d4174e524959a9191a22ba596d31` (pass) and `assessment-dadcac109d70423992bd47228ca54d45` (thermal pass).
- The saved MCP producer opts into `revision_policy=create_new_files`; compile/design checks require an MCP task, indexed expected files, one mapping for every declared file output and exact validator ownership. This permits the isolated new-file correction segment without authorizing session/application edits or arbitrary tool replay.
- Independent retained-evidence and saved-process checks: **17 passed** using `.venv/Scripts/python.exe -m pytest tests/external/process_validation/test_engineering_process_evidence.py packages/workspace_service/tests/test_workflow_process_validation_rework.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-m4-evidence-2`. Ruff and `git diff --check` passed.

T028 is complete. T029 30-pack capability reconciliation and closure tasks T030–T034 remain. Failed exploratory evidence directories are local diagnostics and are not retained as qualifying artifacts.

## M4 capability reconciliation — 2026-09-16

- T029: `coverage.json` version 2 is a deterministic packaged support map for exactly 30 canonical scenario IDs across ten families. It retains every source path, size and SHA-256 plus its source requirement and defect seeds. Regeneration from current manifests must produce the committed file byte-for-byte at the data-model level.
- Only `parametric-drill-jig-01` and `heat-spreader-sizing-01` are scenario-qualified, and only for their frozen bounded profiles. Their exact profile/baseline references, reader identities, limitations and retained evidence are pinned. The other 28 scenarios are explicitly `unsupported`; none inherits qualification from a sibling.
- Generic structured JSON/CSV/text inspection is recorded as `implemented` for the robot-diagnosis and harness families, while their pack profiles remain unsupported. Remaining gaps distinguish `planned` extensions from `unavailable` trusted readers, including slicer, CFD, FEA, native sheet-metal, electrical network/netlist, ECAD and Modelica semantics.
- `acceptance-cases.md` now lists every pack and capability state and gives extension recipes. The packaged map carries machine-readable prerequisites and steps for every capability. Status cannot advance to qualified without a frozen profile, installed reader, independent controls and linked process evidence.
- Coverage integrity suite: **4 passed** using `.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_process_validation_coverage.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-coverage-1`. Ruff and `git diff --check` passed.

M4 and T023–T029 are complete. Closure tasks T030–T034 remain; the capability map explicitly does not claim whole-design, physical or all-30 output qualification.

## M5 security boundary — 2026-09-16

- T030: service-level concurrency now proves that two simultaneous calls with the same idempotency identity execute one reader pass. The duplicate observes the single running attempt without releasing work; after completion, repeated calls return the same immutable assessment.
- Active cancellation is exercised inside a reader-owned resource scope. The resource closes, the attempt persists as terminal `cancelled`, every finding names `validation.cancelled`, and the attempt cannot be resumed as nonterminal work.
- Provider readback receives the exact trace, provider and pinned revision for both measurement and post-read stability calls. Deep nesting and entity-heavy JSON stop at declared reader budgets, persist blocked evidence, and leave source bytes unchanged. Duplicate read/report projections retain the assessment digest and expose no absolute host artifact paths.
- Following `docs/mcp-catalog/mcp-server-testing-process.md`, executable boundary tests prove that `agentcad`, `build123d`, CadQuery and OCP are absent from Wright runtime dependencies and active base/dev Docker instructions, and absent from packaged geometry/thermal reader imports. The engineering demonstration declares AgentCAD/build123d only on its selected `uv run --no-project --isolated` MCP command. T028 already retained successful direct protocol/gateway tool calls. This is reader/dependency ownership evidence; it does not label the demonstration MCP as a catalog-qualified production server.
- Full validator security boundary: **107 passed** using `.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_validation.py packages/data_vault/tests/test_process_validation_repository.py packages/workspace_service/tests/test_process_validation_subjects.py packages/workspace_service/tests/test_process_validation.py packages/workspace_service/tests/test_process_validation_security.py packages/workspace_service/tests/test_process_validation_tools.py packages/workspace_service/tests/test_process_validation_reporting.py tests/security/test_process_validation_native_boundary.py tests/security/test_canonical_workflow_security.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-security-final`. Ruff and `git diff --check` passed.

T030 is complete. Installed wheel/offline/native/Docker boundary verification remains T031; served workspace authoring verification remains T032.

## M5 installed and Docker distribution — 2026-09-16

- T031: a fresh 806-member `wright_engineering-0.1.9-py3-none-any.whl` includes all validator contracts, repository/service/readers, CLI/gateway adapters and structured/jig/heat/coverage resources. Its local qualifying build SHA-256 is `7b47c4f61ac576dbd4b9ee33ab3febf39063554485fd51874929fa1470e846c2`.
- An isolated `python -I` smoke imported Wright modules only from the extracted wheel, blocked network and child-process APIs, loaded all three profiles plus coverage v2, ran the real CLI into SQLite, and retrieved the same assessment through the installed gateway provider. Distribution suite: **2 passed in 9.79s** using `.venv/Scripts/python.exe -m pytest tests/packaging/test_process_validation_distribution.py -q -p no:cacheprovider --basetemp=.local-run/process-validation-082/pytest-distribution-final`.
- Docker Server 28.5.1 ran the same installed wheel read-only under `wright-dev-gate:e2f018eb` / image `sha256:fc11b351d5f6ac259a8f64b6f9669f8b73d26d806cd39f3fc3241e9d7f1db3f8` (`linux/amd64`, Python 3.13.15), with `--network none` and no repository mount. The packaged service loaded structured/jig/heat profiles and produced a release-eligible offline assessment.
- [Distribution evidence](evidence/distribution.md) records exact commands, results and boundaries. Existing Hatch recursive package inclusion and console metadata were sufficient. No MCP-specific dependency or host software was added to the wheel or base image.

At this checkpoint, T031 was complete; served authoring/run evidence and final documentation/audit remained.

## M5 served authoring and run evidence — 2026-09-16

- T032: the existing workspace Workflow/Workflows surface now carries each validator event's authorized workspace-relative `assessment_path` into the run timeline. Live streams and recovered run summaries expose an **Open validation assessment** action while rejecting absolute, parent-relative and malformed paths. The existing held, repairing and exhausted status presentation remains the source of run-state language.
- Component coverage verifies packaged profile selection, subject/revision authoring, save/source round-trip, Undo/Redo, read-only behavior, status labels, safe assessment paths and reopening a held run's exact assessment. Focused frontend selection: **21 passed** across four files.
- `tests/ui-integration/process-validation.spec.ts` enters through the normal workspace **Workflows** control, opens the validator inspector, verifies its pinned profile, connected subject, producer correction target and two-revision budget, then consumes mocked canonical NDJSON for a measured 98 mm defect, delivered feedback, corrected revision and passing recheck. Both immutable assessment links are visible. The new test and the existing workspace-entry regression passed together in served Chromium: **2 passed**.
- `tests/e2e/test_process_validation.py` executes the saved structured process through the canonical runner with deterministic model responses, producing a real fail → typed feedback → corrected pass loop. It then reads both immutable assessments, paged actionable findings, human-readable Markdown and RTM CSV through the FastAPI workspace routes: **1 passed**. This test uses a narrowly monkeypatched safe-path resolver because the managed pytest root is inside the source checkout; the production path guard remains covered by T030.
- `npm run build --prefix apps/web`, Prettier, Ruff and `git diff --check` passed. The known Vite native-config/chunk-size notices and Starlette/httpx deprecation warning remain unrelated.

T032 is complete. T033 runnable documentation and T034 final completion audit remain.
