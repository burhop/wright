# Workflow Recovery Regression Entry Point

These commands are the deterministic local verification path for the workflow
authoring and recovery fixes. They use mocked or disposable services only; no
engineering MCP, CAD, CFD, solver, printer, or vendor operation is dispatched.

## Frontend contract

```sh
cd apps/web
bun run test --run \
  src/prototypes/workflow-recovery/mcp-discovery.spec.tsx \
  src/prototypes/workflow-recovery/mcp-server-blocks.spec.ts \
  src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx \
  src/components/pages/WorkflowRecoveryPage.spec.tsx
bun run build
```

## API contract

Run from the repository root with the locked workspace environment. The
`PYTHONPATH` makes the checked-out workspace packages authoritative instead of
requiring installed editable copies.

```sh
export PYTHONPATH=apps/api/src:packages/agent_adapters/src:packages/core/src:packages/tool_registry/src:packages/data_vault/src:packages/model_registry/src:packages/workspace_service/src
export UV_CACHE_DIR=/tmp/wright-uv-cache

uv run --project apps/api python -m pytest apps/api/tests/test_workflow_sources_api.py -q
uv run --project apps/api python -m pytest apps/api/tests/test_engineering_workflow_template_api.py -q
uv run --project apps/api python -m pytest apps/api/tests/test_engineering_scenario_api.py -q
uv run --project apps/api python -m pytest apps/api/tests/test_workflow_integration_run_api.py -q

PYTHONPATH=packages/core/src:packages/data_vault/src:packages/workspace_service/src \
  uv run --project apps/api python -m pytest \
  packages/workspace_service/tests/test_executor.py \
  packages/workspace_service/tests/test_workflow_external_action_execution.py \
  packages/workspace_service/tests/test_workflow_approval_execution.py -q
```

Run the files separately. In the managed Python 3.13 environment, a single
combined `TestClient` invocation can stall before the first request even when
the individual integration slice is green; that is an environment/test-harness
condition, not a product pass. Capture the individual exit codes and report a
stall rather than retrying indefinitely.

The API tests use temporary workspaces, stubbed model responses, and fixed test
destinations. A green result is not evidence that a live engineering service
is qualified.

## Served browser evidence

Start a disposable frontend with the recovery surface explicitly enabled:

```sh
cd apps/web
VITE_WRIGHT_WORKFLOW_RECOVERY=1 bun run dev -- --host 127.0.0.1 --port 5173
```

In another shell, run Chromium with the managed-host flag required by this
environment:

```sh
PLAYWRIGHT_BASE_URL=http://127.0.0.1:5173 \
PLAYWRIGHT_CHROMIUM_ARGS=--no-sandbox \
bunx playwright test \
  tests/ui-integration/workflow-recovery.spec.ts \
  tests/ui-integration/engineering-workflow-templates.spec.ts \
  tests/ui-integration/workflow-recovery-accessibility.spec.ts \
  tests/ui-integration/workflow-recovery-evidence.spec.ts \
  --project=chromium
```

The evidence test retains the reviewed canvas screenshot in
`artifacts/qa/workflow-recovery-20260918/canvas-readiness.png`. Stop the local
Vite process after the run. If the host cannot bind loopback or Chromium
requires sandbox override, report those as environment conditions rather than
changing the product or claiming a browser run occurred.
