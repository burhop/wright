# Implementation Plan: Native Engineering Process Milestone

**Branch:** `codex/079-native-process-milestone` | **Date:** 2026-09-04 | **Spec:** [spec.md](spec.md)

## Summary

Deliver native create → save → validate → execute → inspect artifact → correct and rerun, with a truthful current browser dashboard. Original 079 proposal preserved at `6daeb214`. The user's September 4 standing goal authorizes this bounded scope and prospective roadmap amendments; it is not approval of unseen exact bytes or human evidence.

## Technical Context

Python 3.11–3.14, Pydantic/FastAPI, SQLite WAL, React 19/TypeScript, pytest/Vitest/Playwright. Offline native and Docker paths use existing distribution. One Wright-owned native document; immutable 078 and Rivet formats remain unchanged. Initial scope: three deterministic development examples and one safe real local MCP integration. No arbitrary code/expressions, implicit conversions, parallel/cyclic scheduling or human-approval runtime step.

Maximum 1 MiB document, 100 steps; normal UI acceptance at 25 steps. Record 20 warm-open observations; functional deadlines gate delivery, microbenchmarks are diagnostic.

## Constitution Check

Use `.specify/memory/constitution.md` v3.1.0. API routes remain thin; core/data-vault/workspace-service own domain, persistence and application logic using the established application-service architecture. Preserve offline operation, SQLite/vault confinement, role policy, traces, UI test IDs, component/browser/system tests, native/Docker distribution and data recovery. Before implementation, independently check the completed contracts/tasks in `analysis.md`.

The user's explicit advance authority covers bounded planning decisions, implementation, dependencies after review, commits, pushes and dev PR merges. Complete planning and independent analysis first; record authority accurately rather than requiring repeated routine approval. Main/release, paid/proprietary/credentialed and physical effects remain outside scope. Human study results must be real. Historic records are immutable.

## Architecture

1. `core/native_process.py`: typed bounded document, decimal quantities, identities, strict canonical semantic digest, structure and readiness.
2. `data_vault/native_process_repository.py`: explicit BEGIN IMMEDIATE transactions, document CAS/idempotency, immutable run snapshots/events, terminal-state CAS and artifact indexes. Additive migration uses existing verified backup and truthful old-reader rejection/recovery.
3. `workspace_service/native_process_service.py`: workspace authorization and authoring/run use cases. `native_process_runtime.py`: sequential DAG and versioned operation registry, no dispatch by example/domain/vendor/UI label.
4. Staged bounded workspace artifacts with digest/size/ownership indexes. Independent assertions evaluate actual computed outputs. Distinguish fixtures, local computation and live MCP calls.
5. `native_process_mcp.py`: existing gateway policy, exact server/tool/schema binding, pre-dispatch revalidation, bounded disposable local integration.
6. The versioned process language is authoritative for AI clients, UI and runtime, as specified in [language authority](contracts/language-authority.md). Thin native API and headless CLI use the same service and validator. Frontend atomic commands/undo edit the shared definition; the replaceable canvas projects exact IDs and emits intents. Publish the same schema/operation descriptors to clients; keyboard and click alternatives are required.
7. Dashboard evolves the existing current-work supplement with separate implementation/verified/integrated evidence. Preserve old bundle support and historic readiness bytes. Separate report age from tested-code coverage.

## Project Structure

- `specs/079-wright-native-authoring/{spec,plan,research,data-model,tasks,quickstart,analysis,milestone-decision}.md` and `contracts/`
- `packages/core/src/core/native_process.py`
- `packages/data_vault/src/data_vault/{native_process_repository,native_process_artifacts}.py`
- `packages/workspace_service/src/workspace_service/{native_process_service,native_process_runtime,native_process_mcp}.py`
- `apps/api/src/api/{schemas,routers}/native_process.py`
- `apps/web/src/services/native-process.ts`, `components/native-process/`, `components/pages/NativeProcessPage.tsx`
- `src/wright_engineering/static/native-processes/`
- `tests/ui-integration/native-process.spec.ts`, `tests/e2e/test_native_process.py`, `tests/native_runtime/test_native_process_lifecycle.py`

## Delivery Sequence

Reconcile baseline/contracts/task plan/independent analysis → dashboard visibility → native model/storage/editor and early browser journey → runtime/artifacts/cancellation/recovery → exact local MCP and three examples → independent/human/packaging verification → required push/merge gates and PR integration → actual dev deployment verification and final dashboard.

Keep each PR independently useful. Dashboard can ship before native execution; do not push bookkeeping-only changes per task. Existing `.specify/extensions.yml` planning/task/analysis/implementation hooks are optional; skip redundant automatic commits and perform deliberate scoped checkpoints.

The [prospective scoped delivery rule](../../docs/programs/engineering-process-platform/coordinator-state-machine.md#prospective-native-implementation-delivery-revision-98-onward) uses the existing lifecycle and unchanged required gates for an independently reviewed implementation PR. Its exact candidate explicitly partitions implemented and pending tasks. Human study, actual deployment and final reporting remain pending until observed; scoped dev integration never implies whole-milestone acceptance.

## Verification and Recovery

Test invalid graphs/decimals/units, cross-language identity, two writers/idempotency/interrupted transactions, terminal races, output-dependent assertions, deadlines, denied scope/changed bindings, exact endpoints/undo/invalid field buffers/save conflicts and artifact recovery. Run focused tests during implementation and full required gates at candidate boundaries. Independent review binds exact commit/tree. Human study remains pending until real participants execute it. Retain upgraded DB and backups; never claim an old build opens a schema version it rejects.

## Complexity Tracking

A native runtime is necessary to replace the Rivet-specific runner. Keep it sequential and bounded. Defer an editable DSL, arbitrary expressions, automatic loops, autonomous AI authoring experience and legacy migration. Establish the official shared language/API for AI and canvas now; track migration and retirement separately from native milestone completion.
