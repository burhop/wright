# Runtime integration baseline

Recorded 2026-09-16 at implementation start after explicit approval of M0–M5.

## Existing extension points

- Canonical source compiler and scheduler: `packages/workspace_service/src/workspace_service/workflow_source_execution.py` (`PromptStep`, `PromptWorkflow`, compilation, `_execution_snapshot`, prompt feedback and revision scheduling).
- Existing check validation: `workflow_design_check.py` (`inspect_verdict`, `validate_rework`). Currently restricted to one preceding create-new/indexed CAD producer and read-only CAD/MCP inspection. Add a separate typed local-validator mode; preserve legacy behavior.
- Result identity: `workflow_results.py` (`EngineeringResult`, `Representation`, `Provenance`). A run/task/port identity needs producer-attempt and content revision binding for validation.
- Durable run projection: `workflow_run_record.py`; preserve existing `design_revision` invalidation and publish persisted verification/diagnostic evidence before a failed gate stops execution.
- Native readback: `workflow_mcp_execution.py` and `workflow_async_operations.py`; read-only annotations, pinned subject, terminal materialization and owned leases remain controlling.
- Tool interface: `packages/core/src/core/tools.py` provides BaseTool/ToolContext. `packages/tool_registry/src/tool_registry/mcp_server.py` exposes the existing GatewayService. `apps/api/src/api/mcp_transport.py` binds authenticated workspace/session transport. T011 must inject the application-owned validator through this existing composition boundary; tool_registry must not import workspace_service.
- Workspace routes: `apps/api/src/api/routers/workspace.py`; keep business logic in workspace_service and preserve current security dependencies.
- Authoring: `apps/web/src/prototypes/workflow-recovery/` model, recovery-dsl, canonical-wire, command-system and existing option controls. Follow the reviewed editor integration runbook before edits; preserve source/diagram round-trip and normal workspace entry.

## Package/storage/test conventions

- Python >=3.11; current local `.venv/Scripts/python.exe` has Pydantic 2.13.4 and pytest. No new dependency is required for initial contracts/structured readers.
- Root wheel includes the core, data_vault and workspace_service package roots. Hatch includes non-Python resources below them; T031 must verify the actual built wheel includes validation profiles.
- Existing data-vault `connect_state_db` owns SQLite WAL, busy timeout, foreign keys and read-only connections. Add validation tables under a unique prefix; no separate database server.
- Existing `.gitignore` and `.dockerignore` cover Python/Node builds, caches, secrets and databases. Add only feature-specific generated evidence ignore rules when needed.
- Run focused package tests with the existing virtual environment and explicit paths. Do not combine incompatible package conftest scopes without the repository's suite isolation.

## Demonstration isolation

Use `artifacts/process-validation/` for retained test/demo evidence and `.local-run/process-validation-082/` for private runtime data, process handles and credentials. Allocate free ports when a service is needed; no existing process is terminated or adopted. Original generation corpus is a read-only source. No new runtime/solver was started during this baseline review.

## Spec Kit checks

The prerequisite command resolves feature 082. Requirements checklist: 19 complete,
0 incomplete. Implementation is explicitly authorized across M0–M5. The optional
pre-implementation `/speckit-git-commit` hook is skipped because tracked state was
clean; focused local commits will preserve completed work.
