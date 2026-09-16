# Future-agent quickstart

**Workspace:** `D:/repos/wright`
**Branch:** `codex/082-output-content-validation`
**Start:** [ready-to-paste /goal](implementation-goal.md)
**Scope:** Runtime validator, AI correction loop and report data contract.

## Read order

1. [progress.md](progress.md), [scope-amendment.md](scope-amendment.md), [spec.md](spec.md), [plan.md](plan.md), [tasks.md](tasks.md).
2. Repository AGENTS.md and `.specify/memory/constitution.md`.
3. [research.md](research.md), [data-model.md](data-model.md), [validation contract](contracts/validation-contract.md), [acceptance cases](acceptance-cases.md).
4. Earlier [30-pack engineering seeds](../081-engineering-workflow-templates/content-validation/acceptance-cases.md), jig center guidance and heat native-result notes linked from the acceptance file.
5. Before editor changes, `docs/contributing/workflow-ui-integration.md`; before native reader qualification, `docs/mcp-catalog/mcp-server-testing-process.md`.

The old 081 and prior 082 campaign plans are historical references. The submitted revised goal explicitly replaces their all-30 implementation activation gate. Check each bound subject's readiness when evaluating it. Do not spend this implementation run recovering the corpus or auditing other branches.

## First useful result

T001–T013 add a local process validator and durable evidence. T014–T018 prove the repair loop. Start with an ordinary AI task producing structured output so MCP/native dependencies do not block the core behavior. Then publish the report contract and complete the real jig/heat slices.

Current design checks are CAD/MCP-only; do not assume generic repair already works. Extend existing compilation, feedback, revision checkpoints and invalidation deliberately. Existing run:task:port result IDs need attempt/revision/hash binding before a verdict is durable.

Runtime profiles belong in the packaged service, not only under tests. Test fixtures and saved demonstrations remain separate from the original generation packs.

## Demonstration isolation

Use `artifacts/process-validation/` with distinct runtime/data roots and free ports. Reuse source artifacts read-only. Native readers use owned sessions or confined copies under existing lifecycle rules. Do not borrow another task's database, overwrite its artifacts or kill its services.

Use a real configured AI for correction acceptance, save feedback consumption and new output evidence, and label controlled initial defects. If a needed credential/reader is unavailable, record a precise blocker while completing independent work. A mock is useful test evidence, not a substitute for required live demonstration.

## Commands after implementation

No new validator command exists yet. T011 adds the proposed packaged entry point:

```powershell
uv run python -m workspace_service.process_validation_cli --help
uv run python -m pytest packages/core/tests/test_process_validation.py
uv run python -m pytest packages/data_vault/tests/test_process_validation_repository.py
uv run python -m pytest packages/workspace_service/tests/test_workflow_process_validation.py
uv run python -m pytest packages/workspace_service/tests/test_workflow_process_validation_rework.py
```

Confirm actual CLI help and repository suite isolation before use. Add reader/security/report/UI tests at their tasks. Exact push/merge/release gates remain in the contributor runbooks if those actions are separately authorized.

## Report branch handoff

Publish contract schemas and representative records, JSON/Markdown/RTM projections, exact read/export operations and `contracts/report-consumer.md`. Keep the consumer independent of validator internals and engineering tool availability. Preserve explicit scope, currentness and evidence links. Do not edit the other branch or create its report UI.

## Progress and completion

All 34 tasks must be complete for this goal. Record each milestone's evidence in progress.md; distinguish code implemented, process demonstrated, design compliant and human accepted. The saved goal, when submitted verbatim, supplies implementation authority across the listed milestones; it does not authorize external actions or invent engineering review decisions.

No goal, workflow, solver or implementation was started by saving this handoff.
