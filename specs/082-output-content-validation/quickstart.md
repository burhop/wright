# Future-agent quickstart

**Code worktree**: `D:/repos/wright/.local-run/output-content-validation`
**Branch**: `codex/082-output-content-validation`
**Base**: `86ee835974970cd05913b58e306e537f6dfaf181`, fetched merged dev.
**Start**: [ready-to-paste /goal](implementation-goal.md).

## Read order

1. [progress.md](progress.md), [spec.md](spec.md), [plan.md](plan.md), [tasks.md](tasks.md).
2. Repository AGENTS.md and `.specify/memory/constitution.md`.
3. [research.md](research.md), [data-model.md](data-model.md), [contract](contracts/validation-contract.md), [acceptance cases](acceptance-cases.md); read their incorporated 081 sources.
4. Current [campaign execution state](../081-engineering-workflow-templates/dataset-campaign/execution-state.md), [campaign plan](../081-engineering-workflow-templates/dataset-campaign/plan.md), [native lifecycle contract](../081-engineering-workflow-templates/dataset-campaign/contracts/native-application-lifecycle.md), subsequent closeout evidence and selected bindings.
5. [Modelica contract](../081-engineering-workflow-templates/dataset-campaign/modelica-selected-kit.md), [heat inspection](../081-engineering-workflow-templates/dataset-campaign/heat-native-result-inspection.md), [jig center guidance](../081-engineering-workflow-templates/dataset-campaign/jig-circle-center-guidance.md) and current pack amendments.
6. Before UI work, `docs/contributing/workflow-ui-integration.md`; before native reader qualification, `docs/mcp-catalog/mcp-server-testing-process.md`.

## First actions

Confirm branch, feature selector and dirty work in this worktree. Do not switch branches in the original shared checkout. Review [readiness evidence](evidence/readiness-2026-09-16.json); it is a dated preliminary failure, not current authority or a complete cohort audit.

T001 must verify full G0 before T002 or validation implementation. When blocked, record exact facts and leave deferred without taking over generation. The current generation status CLI writes; direct source readers and read-only WAL-aware SQLite access are the initial audit method.

Once approved and eligible, perform the 74 tasks. The first useful slice is T001–T015. Family tasks are five-step A–E chains; each E needs actual retained artifacts. Treat task descriptions and the adopted design as joint acceptance criteria.

## Concurrent task isolation

Separate worktrees allow distinct branches and files, but do not isolate external runtimes automatically. Use this worktree's own validation state and temporary copies. Record distinct API/frontend ports and writable runtime/data roots. Treat the original corpus/runtime as authorized read-only sources. Serialize shared native resources and record exact owned processes/leases. No global cleanup, application takeover or branch switching in another task.

A future fetch/rebase is not required merely because dev advances. If integration is needed, preserve this branch's commits and recheck source/profile/runtime identities; do not silently redefine the frozen cohort.

## Verification

The CLI and validator tests are planned files. After T010 exists, inspect its real `--help` before using the target commands. Service operations and exit semantics are in the contract.

Suggested focused checks once implemented:
```powershell
uv run python scripts/run_engineering_content_validation.py --help
uv run python -m pytest packages/core/tests/test_engineering_output_validation.py
uv run python -m pytest packages/data_vault/tests/test_engineering_validation_repository.py
uv run python -m pytest tests/test_engineering_content_validation_campaign.py
```

Use repository suite-isolation conventions when combining packages. Add family/native checks and UI component/mock/served-system checks at their tasks. Exact required push/merge gates come from current contributor runbooks, not this example list.

## Progress discipline

Update progress.md after material results, including exact subject/version, evidence paths, relevant commands, failures and next task. Preserve terminal evidence. Classify faults as source, generator, reader, oracle or report before changing code. Do not widen tolerances. At milestone review gates, show concrete tested evidence and observe current human authority.

No goal, monitor, workflow, reader implementation, push or deployment was started by preparing this handoff.
