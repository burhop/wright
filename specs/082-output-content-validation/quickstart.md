# Implementation and operator quickstart

**Workspace:** `D:/repos/wright`

**Branch:** `codex/082-output-content-validation`

**Approved goal:** [implementation-goal.md](implementation-goal.md)

**Product guide:** [Process Output Validation](../../docs/workflows/process-output-validation.md)

## Current state

T001–T033 are implemented and recorded in [progress.md](progress.md). The runtime validator, bounded correction, report contract, structured/CAD/thermal demonstrations, security/distribution gates, authoring controls, run diagnostics, assessment links and runnable operator documentation exist. T034 final audit/closure is the remaining plan task at this checkpoint.

The validator is a process step that checks one or more exact upstream output revisions. It is not a final QA campaign. The 30 input packs define a capability map; only the explicitly frozen and demonstrated slices are qualified.

## Read order

1. [progress.md](progress.md), [scope-amendment.md](scope-amendment.md), [spec.md](spec.md), [plan.md](plan.md), and [tasks.md](tasks.md).
2. Repository `AGENTS.md` and `.specify/memory/constitution.md`.
3. The [product guide](../../docs/workflows/process-output-validation.md), [source contract](contracts/process-source.md), [report consumer contract](contracts/report-consumer.md), and [acceptance cases](acceptance-cases.md).
4. [research.md](research.md), [data-model.md](data-model.md), and [validation contract](contracts/validation-contract.md) when changing internals.
5. Before editor changes, `docs/contributing/workflow-ui-integration.md`; before native reader qualification, `docs/mcp-catalog/mcp-server-testing-process.md`.

The earlier 081 analysis is reference material. Its all-30 activation gate and report-UI scope are superseded. Do not restart branch recovery, take over the generation campaign, or claim unsupported scenario qualification.

## Inspect the installed profiles

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
uv run python -m workspace_service.process_validation_cli --help
uv run python -m workspace_service.process_validation_cli profile `
  --profile structured-demo
uv run python -m workspace_service.process_validation_cli profile `
  --profile parametric-drill-jig-01
uv run python -m workspace_service.process_validation_cli profile `
  --profile heat-spreader-sizing-01
```

The profile operation prints the exact profile and baseline references needed in process source. Runtime profiles live in the packaged service. Test fixtures and demonstrations remain separate from original generation packs.

## Run the offline CLI example

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
$root = ".local-run/process-validation-example"
uv run python examples/process-output-validation/prepare_example.py `
  --workspace $root --length-mm 100

$result = uv run python -m workspace_service.process_validation_cli evaluate `
  --workspace $root --workspace-id validator-example `
  --db "$root/validation.sqlite3" --request request.json `
  --profile structured-demo | ConvertFrom-Json

uv run python -m workspace_service.process_validation_cli export `
  --workspace $root --workspace-id validator-example `
  --db "$root/validation.sqlite3" `
  --assessment $result.assessment_id --format markdown
```

The preparer registers an exact producer output before evaluation; the CLI does not accept an unregistered caller claim as canonical output. Use `--length-mm 98` for a measured noncompliant result. The full `get`, paged `read`, Markdown and RTM/CSV commands are in the product guide.

## Reproduce isolated demonstrations

The structured correction demonstration needs the configured Hermes-compatible model endpoint:

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
uv run python scripts/run_process_validation_structured_loop.py `
  --output-dir artifacts/process-validation/structured-loop/<new-UTC-run-id>
```

The engineering demonstration also starts its explicitly isolated MCP dependencies and copies retained heat inputs read-only:

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
uv run python scripts/run_process_validation_engineering.py `
  --output-dir artifacts/process-validation/engineering/<new-UTC-run-id>
```

Both commands refuse to overwrite their output root. Use a distinct runtime/data root and do not borrow another task's database, service, or port. These live demonstrations are already retained and independently verified; rerun them only when their runtime path changes or new evidence is required.

## Focused verification

```powershell
$env:UV_CACHE_DIR = ".local-run/uv-cache"
uv run pytest `
  packages/core/tests/test_process_validation.py `
  packages/data_vault/tests/test_process_validation_repository.py `
  packages/workspace_service/tests/test_process_validation.py `
  packages/workspace_service/tests/test_workflow_process_validation.py `
  packages/workspace_service/tests/test_workflow_process_validation_rework.py `
  packages/workspace_service/tests/test_process_validation_reporting.py `
  tests/e2e/test_process_validation.py -q

npm run test --prefix apps/web -- --run `
  src/prototypes/workflow-recovery/validation-run-status.spec.ts `
  src/prototypes/workflow-recovery/WorkflowRunObserverIntegration.spec.tsx `
  src/prototypes/workflow-recovery/ValidatorBlockEditor.spec.tsx `
  src/prototypes/workflow-recovery/validation-settings.spec.ts

npm run build --prefix apps/web

$env:WRIGHT_PLAYWRIGHT_PORT = "5186"
node node_modules/@playwright/test/cli.js test `
  tests/ui-integration/process-validation.spec.ts `
  tests/ui-integration/workflow-composer.spec.ts `
  --project=chromium --workers=1
```

Use a private `--basetemp` if the host's shared pytest cache is not writable. The exact distribution and Docker commands/results are in [distribution.md](evidence/distribution.md). Retained-evidence verifiers are under `tests/external/process_validation/`.

## Report branch handoff

The other branch consumes `wright.process-validation-report/1` and must not import validator internals or rerun readers. It should validate the published schema and examples, calculate the effective verdict as `currentness.is_current AND assessment.summary.release_eligible`, preserve all RTM rows and scope limitations, and resolve evidence only through authorized workspace operations. The complete boundary is [contracts/report-consumer.md](contracts/report-consumer.md).

## Completion rule

All T001–T034 requirements, artifacts, examples and gates must be supported by current evidence before marking the goal complete. Distinguish implemented code, demonstrated process behavior, qualified reader scope, report compatibility, and human or physical acceptance. Push, merge and release remain separately authorized and governed by their contributor runbooks.
