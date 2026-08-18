# Tasks: Windows MCP Qualification

**Input**: Design documents from `specs/074-windows-mcp-qualification/`

**Tests**: Required. Real MCP execution is never part of the normal test suite;
tests use only local fakes and disposable process fixtures.

**Organization**: Tasks are grouped by user story. Any task that can touch a
real package, endpoint, Wright registration, or process is sequential and must
respect the fixed server order.

## Phase 1: Setup

**Purpose**: Establish schemas, fixed recipe identities, and isolated evidence
locations before any executor exists.

- [x] T001 Add package copies of the reviewed recipe and evidence schemas in `packages/tool_registry/src/tool_registry/catalog/windows-qualification-recipe.schema.json` and `packages/tool_registry/src/tool_registry/catalog/windows-qualification-evidence.schema.json`
- [x] T002 Add seven ordered declarative recipe records with no arbitrary shell strings in `packages/tool_registry/src/tool_registry/catalog/windows-qualification-recipes.yaml`
- [x] T003 Add transient qualification guards to `.gitignore` so `.local-run/`, downloaded sources, caches, package roots, and disposable workspaces remain untracked while dated redacted evidence remains committable

---

## Phase 2: Foundational Models and Policy

**Purpose**: Build the fail-closed vocabulary and validation boundary required
by every story.

- [x] T004 [P] Add failing model tests for the seven stage results, eight unique stages, digest limits, no-problems claim rule, and bounded evidence in `packages/tool_registry/tests/test_windows_qualification_models.py`
- [x] T005 Implement strict allowlist/order, recipe, safety, stage, evidence, run, and summary models in `packages/tool_registry/src/tool_registry/windows_qualification_models.py`
- [x] T006 [P] Add failing recipe tests for exact-ID allowlisting, structured operation kinds, pinned identities, destination policy, safe-probe policy, and shell-string rejection in `packages/tool_registry/tests/test_windows_qualification_recipes.py`
- [x] T007 Implement schema-backed recipe loading, canonical digests, semantic validation, and exact-ID denial in `packages/tool_registry/src/tool_registry/windows_qualification_recipes.py`
- [x] T008 [P] Add catalog contract tests for optional signed Windows qualification summaries and claim validation in `packages/tool_registry/tests/test_windows_qualification_projection.py`
- [x] T009 Extend catalog and capability detail contracts with the bounded Windows qualification projection in `packages/tool_registry/src/tool_registry/catalog_models.py` and `packages/tool_registry/src/tool_registry/capability_models.py`

**Checkpoint**: No executable operation can be represented for a non-allowlisted
server, and every recipe/evidence document is bounded and schema-valid.

---

## Phase 3: User Story 1 - Safely qualify an approved server (Priority: P1)

**Goal**: Enforce source/safety decisions, bounded native Windows operations,
process-tree ownership, and cleanup before exposing any real runner.

**Independent Test**: A non-allowlisted fixture request reaches none of the
source, network, installer, subprocess, onboarding, gateway, or cleanup side-
effect seams; allowlisted local fixtures demonstrate timeouts and cleanup.

### Tests for User Story 1

- [x] T010 [P] [US1] Add local helper-process fixtures for clean start, stdout contamination, oversized output, hang, child process, malformed protocol, and clean shutdown in `packages/tool_registry/tests/fixtures/windows_qualification/`
- [x] T011 [P] [US1] Add failing native executor tests for no-shell launch, per-stage timeout, byte ceiling, process-tree cleanup, allowed roots/destinations, and residue detection in `packages/tool_registry/tests/test_windows_qualification_executor.py`
- [x] T012 [P] [US1] Add failing orchestration tests for preflight refusal, external-boundary continuation, stage independence, cleanup-on-error, and no side-effect before allowlist in `packages/tool_registry/tests/test_windows_qualification_service.py`
- [x] T013 [P] [US1] Add failing CLI tests for preview purity, native-Windows enforcement, safe root validation, ordered-only `qualify-all`, and infrastructure exit semantics in `packages/tool_registry/tests/test_windows_qualification_cli.py`

### Implementation for User Story 1

- [x] T014 [US1] Implement injected native Windows operations, bounded stream capture, process-tree shutdown, residue snapshots, and cleanup in `packages/tool_registry/src/tool_registry/windows_qualification_executor.py`
- [x] T015 [US1] Implement safety-decision enforcement, eight-stage orchestration, checkpoint continuation, installed/action ledgers, and cleanup finalization in `packages/tool_registry/src/tool_registry/windows_qualification_service.py`
- [x] T016 [US1] Implement preview, one-server, and fixed-order operator commands without arbitrary command input in `packages/tool_registry/src/tool_registry/windows_qualification_cli.py`

**Checkpoint**: User Story 1 passes entirely offline with local fixtures and the
real CLI remains opt-in.

---

## Phase 4: User Story 2 - Understand what works on this computer (Priority: P2)

**Goal**: Present source, package/registration, startup, protocol, host/backend, Wright setup,
gateway, cleanup, and staleness separately in the MCP Server Library.

**Independent Test**: Fixture evidence with a passed MCP package/protocol and a
missing commercial host renders “MCP server installed; host app needed,” not
`Incompatible`, and remote endpoints are described as registrations.

### Tests for User Story 2

- [x] T017 [P] [US2] Add failing capability-view tests for current/stale summary projection, remote registration semantics, host-required partials, and evidence digest binding in `packages/tool_registry/tests/test_windows_qualification_projection.py`
- [x] T018 [P] [US2] Add failing React tests for the eight concise source/package/startup/protocol/host/Wright/gateway/cleanup groups, validation date, stale message, evidence reference, accessible structure, and semantic wording in `apps/web/src/components/tools/WindowsQualificationSummary.spec.tsx`
- [x] T019 [P] [US2] Extend capability detail integration tests with Windows qualification rendering and absence behavior in `apps/web/src/components/tools/CapabilityLibrary.spec.tsx`

### Implementation for User Story 2

- [x] T020 [US2] Project validated Windows summaries from catalog entries in `packages/tool_registry/src/tool_registry/capability_views.py`
- [x] T021 [US2] Add the tokenized accessible qualification summary component in `apps/web/src/components/tools/WindowsQualificationSummary.tsx`
- [x] T022 [US2] Integrate the Windows summary into the capability detail dialog without reintroducing a single ambiguous compatibility badge in `apps/web/src/components/tools/CapabilityDetails.tsx`

**Checkpoint**: Engineers can identify every relevant Windows boundary from one
detail view without reading raw evidence.

---

## Phase 5: User Story 3 - Reproduce and audit qualification (Priority: P3)

**Goal**: Produce redacted, bounded, reproducible per-server evidence and
consolidated audit ledgers.

**Independent Test**: Fixture qualification writes schema-valid JSON/Markdown,
a complete matrix, progress record, install/cleanup ledgers, and empty non-
allowlist proof without leaking secrets, private paths, commands, or raw output.

### Tests for User Story 3

- [x] T023 [P] [US3] Add failing writer tests for schema validation, redaction, atomic checkpoints, eight-stage matrix completeness, installed/cleanup ledgers, and empty non-allowlist proof in `packages/tool_registry/tests/test_windows_qualification_writer.py`
- [x] T024 [P] [US3] Add staleness tests for source, package, tool schema, machine, credential binding, and maximum age in `packages/tool_registry/tests/test_windows_qualification_models.py`

### Implementation for User Story 3

- [x] T025 [US3] Implement atomic JSON/Markdown evidence, matrix, progress, installed-items, cleanup, and non-allowlist writers in `packages/tool_registry/src/tool_registry/windows_qualification_writer.py`
- [x] T026 [US3] Add the documented operator workflow and evidence interpretation guide in `docs/mcp-catalog/windows-mcp-qualification.md`
- [x] T027 [US3] Create the dated matrix/progress/ledger scaffolds in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/qualification-matrix.md`, `progress-log.md`, `installed-items.json`, `cleanup-ledger.json`, and `non-allowlist-proof.json`

**Checkpoint**: Offline fixtures prove evidence is bounded, redacted, complete,
and stale-safe.

---

## Phase 6: User Story 4 - Finish the ordered qualification run (Priority: P4)

**Goal**: Research, safely classify, and attempt every permitted stage for the
seven approved servers in the exact order, saving and cleaning after each.

**Independent Test**: Seven dated evidence pairs and one consolidated matrix
show honest terminal classifications and an empty non-allowlist action ledger.

### Safety and qualification checkpoints

- [x] T028 [US4] Record pinned source/safety decisions for all seven approved identities before executable action in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/safety-preflight.md`
- [x] T029 [US4] Qualify `brep-mcp`, save `brep-mcp-windows-qualification.json` and `.md`, clean owned state, and checkpoint the matrix/progress ledgers in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`
- [x] T030 [US4] Qualify `solid-edge-mcp-burhop`, save its JSON/Markdown source or safety boundary, clean owned state, and checkpoint the matrix/progress ledgers in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`
- [x] T031 [US4] Qualify `aps-mcp-server-nodejs`, save its JSON/Markdown archive or safety boundary, clean owned state, and checkpoint the matrix/progress ledgers in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`
- [x] T032 [US4] Qualify `autodesk-product-help-mcp`, save its JSON/Markdown registration/protocol/safe-probe/Wright evidence, clean owned state, and checkpoint the matrix/progress ledgers in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`
- [x] T033 [US4] Qualify `autodesk-fusion-desktop-mcp`, save its JSON/Markdown built-in host boundary, clean owned state, and checkpoint the matrix/progress ledgers in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`
- [x] T034 [US4] Qualify `autodesk-fusion-data-mcp`, save its JSON/Markdown OAuth/remote boundary, clean owned state, and checkpoint the matrix/progress ledgers in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`
- [x] T035 [US4] Qualify `onshape-labs-featurescript-mcp`, save its JSON/Markdown preview/subscription boundary, clean owned state, and checkpoint the matrix/progress ledgers in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`
- [x] T036 [US4] Reconcile all seven catalog Windows claims and signed qualification summaries to saved evidence in `packages/tool_registry/src/tool_registry/catalog/engineering-catalog.yaml`
- [x] T037 [US4] Update exact attempt recipes and chronological problems in `docs/mcp-catalog/mcp-server-setup-recipes.md` and `docs/mcp-catalog/testing-problem-log.md`

**Checkpoint**: Every approved server has a current evidence pair and factual
terminal classification; no other MCP was installed, connected, launched, or
executed.

---

## Phase 7: Polish and Cross-Cutting Verification

**Purpose**: Close regression, catalog, UI, cleanup, and authoritative gate
requirements without merging or publishing.

- [x] T038 [P] Run focused offline `tool_registry` Windows qualification and catalog tests and record exact results in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/progress-log.md`
- [x] T039 [P] Run focused React qualification/detail tests and record exact results in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/progress-log.md`
- [x] T040 Validate both JSON schemas, all seven evidence files, recipe identities, catalog summaries, and evidence digests in `packages/tool_registry/tests/test_windows_qualification_writer.py`
- [x] T041 Verify all owned MCP/process trees are stopped, `.local-run/` and downloads remain untracked, residue is cleaned, and the non-allowlist ledger remains empty in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/cleanup-ledger.json`
- [x] T042 Run `scripts/check-dev-merge.sh` without merging and record a precise host-limitation note for any genuinely unavailable gate in `docs/mcp-catalog/evidence/windows-qualification-2026-08-13/progress-log.md`
- [x] T043 Update the program progress record with the Windows qualification outcome and unresolved risks in `docs/engineering-capability-program-progress.md`
- [x] T044 Re-run the Spec Kit consistency review, mark all completed tasks, and verify `AGENTS.md` still points to `specs/074-windows-mcp-qualification/plan.md`

---

## Dependencies and Execution Order

- Phase 1 -> Phase 2 -> User Story 1 is the safety-critical sequence.
- User Story 2 and User Story 3 may proceed after foundational contracts, but
  both must finish before real catalog summaries are reconciled.
- User Story 4 is strictly sequential: T028 -> T029 -> T030 -> T031 -> T032 ->
  T033 -> T034 -> T035 -> T036 -> T037.
- Every server task saves evidence, cleans owned state, and checkpoints before
  the next server starts.
- Phase 7 starts only after all seven terminal classifications exist.

## Parallel Opportunities

- T004, T006, and T008 affect separate test files after schemas exist.
- T010-T013 define separate fixture/executor/service/CLI failures before the
  corresponding implementation.
- T017-T019 cover backend projection, component behavior, and page integration
  in separate files.
- T023 and T024 cover writer and currency behavior independently.
- T038 and T039 may run concurrently only after implementation/evidence edits
  stop; real server qualification tasks never run in parallel.

## Implementation Strategy

1. **MVP**: Finish Phases 1-3. This alone delivers a safe exact-ID native
   qualification boundary with no real MCP action in tests.
2. Add the user-facing projection and auditable writers.
3. Perform the seven-server loop with safety-first early terminal results.
4. Reconcile claims and run focused then authoritative gates.

## Format Validation

All tasks use the required checkbox, sequential task ID, optional `[P]`, required
user-story label within story phases, action, and concrete file path.
