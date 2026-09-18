# Wright Luna QA Batch

Date: 2026-09-18

Scope: bounded, low-cost QA of the workflow editor and live-run readiness experience. Live model, CAD, solver, printer, MCP execution and paid workflow calls were disabled.

## Baseline and Environment

- Checkout: `/home/burhop/repos/wright`, branch `dev`.
- Pre-existing user change preserved: `docs/architecture/beta-readiness-and-architecture-analysis.md`.
- Isolated browser server: Vite on `http://127.0.0.1:5197`, with process-definition, workflow-composer and workflow-recovery flags enabled.
- Existing Playwright harness: `playwright.config.ts`, one Chromium worker, mocked/local test state.
- The repository dependency tree was incomplete in this checkout. The cached dependency tree from `/tmp/wright-083-workflow-trace-review` was overlaid into untracked `node_modules`; no tracked dependency files were changed.
- Python service tests were not runnable in the base interpreter because `opentelemetry` was absent. `uv run --all-packages` was also blocked by a read-only UV cache. Catalog inspection below used the repository YAML parser path and did not execute engineering work.

## Results Matrix

| Evidence level | Result | What it proves |
| --- | --- | --- |
| Focused Vitest | Passed: 26 files / 269 tests | Workflow recovery state, services, readiness UI contracts and editor components |
| Focused Playwright | Passed: 15 / 15 | Normal workspace Workflows entry, template selection, blank editor, save/reopen, connections, deletion, MCP binding, readiness messaging and responsive containment |
| Catalog readiness inventory | Passed: 10 / 10 catalog entries inspected | Current declared readiness and blockers, without starting a run |
| Offline result packet | Passed: ZIP contents and principal assets inspected | Existing packet is portable and includes report/evidence, PDFs, CAD geometry and CFD visualizations |
| Real engineering execution | Not run | Deliberately excluded to avoid AI/CAD/solver/printer side effects |
| Python service regression suite | Blocked by environment | Missing `opentelemetry`; no product conclusion inferred |

## Catalog Readiness

All ten packaged templates are currently blocked from ordinary live execution. Three are declared `setup_required`; seven are `reference`. Their declared blockers are:

- Printed replacement part: image-to-mesh, slicer and Bambu P1S transfer qualification.
- Raspberry Pi enclosure: AgentCAD D001 and Foam-Agent D040 qualification.
- Sheet-metal supplier handoff: current Solid Edge and supplier-preview qualification.
- Lightweight equipment bracket: bracket geometry and CalculiX D034 clean-environment qualification.
- Sensor-interface PCB: pinned KiCad DRC protocol repair and qualification.
- Parametric drill jig: complete jig and optional DFM D037 qualification.
- Robot tracking diagnosis: numeric messages, alignment, plotting and recovery qualification.
- Heat-spreader sizing: dimensional thermal problem and CAD handoff qualification.
- Sensor-fan harness: beta access, credentials and Splice CAD D031 qualification.
- Water-heater sizing: Modelica D035 qualification; only the approved bounded kit is eligible after qualification.

This is a template/readiness inventory, not a claim that every example dataset was discovered. The requested approximately 30 examples were not present as a single inventory in this checkout and should be audited from the campaign publisher separately.

## Fixes Made

`tests/ui-integration/workflow-recovery.spec.ts` had two stale assumptions:

1. A component-expansion test captured `sha256:calculating` before the semantic digest settled. It now waits for a real SHA-256 digest before comparing identity.
2. A layout-only save expected the semantic revision to advance. It now asserts `layout_revision` advances while `definition_revision` and the semantic revision remain unchanged, matching the workflow layout contract.

These are regression-test repairs, not changes to production workflow semantics.

## Remaining Issues

1. The ten packaged templates need maintainer-owned qualification and tool setup before live runs can be considered runnable. The user cannot fix this by changing an input prompt.
2. The Python test environment needs its reviewed runtime dependencies restored, especially `opentelemetry`, before the service suite can provide a green result.
3. The 30-example campaign needs a publisher-level inventory with per-example template revision, readiness, tool bindings, qualification state and first blocker.

## Reproduction

Focused UI gate, with an isolated Vite server already running:

```text
PLAYWRIGHT_BASE_URL=http://127.0.0.1:5197 node node_modules/playwright/cli.js test tests/ui-integration/workflow-recovery.spec.ts tests/ui-integration/workflow-recovery-bindings.spec.ts tests/ui-integration/engineering-workflow-templates.spec.ts --project=chromium --workers=1
```

Expected result: `15 passed`.

Focused component gate:

```text
npm run test --workspace=web -- src/prototypes/workflow-recovery src/services/workspace-service.spec.ts src/prototypes/workflow-recovery/EngineeringTemplateDialog.spec.tsx --maxWorkers=1
```

Expected result: `26 passed`, `269 passed`.

The browser tests use mocked or local state. They do not prove that CAD, CFD, KiCad, Modelica, Bambu or other external engineering workflows execute successfully.
