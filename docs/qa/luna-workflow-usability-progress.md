# Luna Workflow Usability Progress

Started: 2026-09-18 13:40 UTC
Earliest completion: 2026-09-18 14:40 UTC

## Acceptance checklist

- [x] Known template readiness is visible before Run, with owner and next action.
- [ ] Missing input, missing binding, unavailable MCP, host-software failure, and template qualification are distinct states. Missing input, missing binding, MCP availability, and template qualification are now represented; host-software failure is categorized when returned by the run API, but still needs a dedicated backend readiness probe.
- [x] Executable blocks and inspectors show editable, persisted tool/server bindings.
- [ ] Blank creation, authoring, connections, persistence, delete, undo/redo, duplicate-run prevention, rejected starts, failure, and cancellation are verified.
- [ ] Focused component/API/Playwright checks pass, including narrow-screen and failure states. Component/build/lint and focused served Chromium checks pass; API pytest is blocked by the environment's missing `opentelemetry` dependency.
- [x] Normal workspace Workflow/Workflows entry is browser-verified and the served URL is recorded: `http://127.0.0.1:5197/workspace/ws-recovery?workflow=canonical` under the test fixture.

## Evidence

- Existing production changes include a compact Run readiness summary and focused component coverage.
- Source readiness is now authoritative: `GET /api/workspace/workflow-sources/readiness` reads stored template provenance and calls the same catalog readiness service used by the run gate.
- Executable canvas cards now expose their saved binding or `Not bound`; the inspector remains the edit surface.
- MCP task readiness checks the enabled workspace tool inventory and reports unavailable/check-unavailable separately from missing binding.
- Backend run errors retain their error code and are categorized as template qualification, MCP/tool, host application, model service, or output capture failures.
- Existing QA report: `docs/qa/wright-luna-ui-qa-2026-09-18.md`.
- Live engineering, paid model, CAD, solver, printer, and engineering MCP execution remain disabled.

## Process execution improvements

1. **Persist template provenance with every instantiated workflow** — implemented and now exposed through a source-readiness read that shares the run gate's catalog authority.
2. **Expose structured preflight for host software and MCP adapters** — next process change. The UI currently reports the honest boundary (`preflight required`) and categorizes returned failures, but it cannot know host software health before Wright provides a non-executing probe.
3. **Record tool inventory/availability at run start** — next process change. The editor can compare a binding with the current enabled-tool inventory, but the run event contract should record the checked server, tool, host version, and probe result.
4. **Keep rejection separate from execution evidence** — partially implemented. Known template qualification failures are blocked before prompt capture; backend error codes are preserved. Add a durable `preflight_rejected` event/result state when the host contract is extended.
5. **Keep artifact and visual evidence in the workflow result contract** — follow-up for the result-package/report work; this Luna pass does not activate deferred all-30 output validation.
6. **Capture engineering-facing evidence at production time** — CAD previews, input drawings/PDF page images, CFD field plots, mesh/solver settings, support/toolpath views, and the exact command or prompt that produced researched evidence. A report cannot reconstruct these reliably from filenames or byte counts later.
7. **Make every activity contract input → ordered operation → output** — persist consumed inputs, the human-readable operation sequence, tool/server/version, selected pass or elapsed time, and produced artifacts as first-class run data. Do not make engineers open a settings dump to discover process meaning.
8. **Package supporting context by role** — distinguish required inputs, retained references, and incidental supporting files in the result packet; show the relevant visual inline and explain why it was used.
9. **Use a dedicated visual-result contract for geometric and simulation outputs** — expose a 3D viewer or stable preview for CAD/mesh outputs and useful CFD plots when available; suppress duplicate recolors and empty toolpath projections instead of presenting them as evidence.
10. **Preserve provenance for every visual** — record whether an image came from an input file, a tool result, a browser/web search, or a generated preview, together with the producing activity and the prompt/command that created it.
11. **Capture dependency edges as report data** — input-to-activity and activity-to-activity links, including the dependency type and artifact identity, must survive packaging so the report can render arrows instead of reconstructing a disconnected list of cards.
12. **Record measurement semantics, not raw storage facts** — replace byte-count-only observations with named units, tolerances, test method, pass/fail interpretation, and the artifact or image that supports the claim.

## Current work

1. Inspect authoritative template provenance/readiness and the served checkout. (done)
2. Close the gap between template readiness and the editor's pre-run display. (done for catalog-backed templates)
3. Verify task binding persistence and recovery behavior. (canvas visibility, editor controls, MCP-focused tests, and existing persistence journeys verified; broader binding journey remains)
4. Run focused regression and browser checks; record blockers separately. (done for the served web path; API collection remains environment-blocked)

## Verification ledger

- `bun run build` passed for the web application after the readiness and binding changes.
- `bun run lint` passed with zero errors; nine pre-existing hook-dependency warnings remain outside this focused change.
- Focused workflow recovery component suite passed: 43 tests.
- Workspace service contract suite passed: 50 tests, including categorized run failures and source-readiness requests.
- Combined recovery/canvas/MCP/service regression pass passed: 110 tests across 4 files.
- Full web Vitest run reached 970 passed tests across 152 files. One-worker mode reproduces an unrelated `ChatLayout.spec.tsx` environment-teardown RPC error (`onUserConsoleLog` pending); the same suite passes cleanly with two workers. Park the one-worker harness issue separately.
- Related MCP, application-task, observer, canvas, and template suites passed: 61 tests.
- Served Chromium checks passed in bounded groups for the normal workspace entry, blank template creation, persistence, bindings, deletion, readiness, and responsive behavior.
- Full focused served Chromium journey set passed: 15/15 tests through the normal Workspace/Workflows entry.
- Final served Chromium trace pass passed template creation/readiness and responsive production-readiness journeys; traces are under `test-results/playwright/`.
- `python -m compileall` passed for the API changes.
- Added API coverage for the hand-authored `not_template` and missing-source `404` readiness cases; execution of the Python suite remains environment-blocked.
- API pytest remains blocked by the checkout environment: required API packages are unavailable and the UV cache is read-only.
- The full web run's single teardown error is separate from the changed workflow/page suites, which pass independently; investigate the ChatLayout console-log hook in a separate cleanup task.
- No live CAD, CFD, model, printer, or MCP execution was started.
- Readiness now excludes human-review and supported AI-capable blocks from missing-binding warnings; only deterministic/MCP execution steps are treated as requiring an execution binding.
- Canvas cards now show the concrete persisted binding ID for ordinary tasks and the server/tool pair for MCP-backed tasks.
- Readiness recognizes both current `mcp-tool` and legacy `mcp-task` authoring representations.
- Categorized run failures now include an accountable owner even when an older host envelope omits a correction.

Focused repeatable web regression command:

```text
bun run test -- src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.spec.tsx src/services/workspace-service.spec.ts --pool=forks --maxWorkers=1
```

Served UI verification command:

```text
PLAYWRIGHT_BASE_URL=http://127.0.0.1:5197 node node_modules/playwright/cli.js test tests/ui-integration/workflow-recovery.spec.ts tests/ui-integration/engineering-workflow-templates.spec.ts --project=chromium --workers=1 --grep "fresh|readiness|binding|blank"
```

## Blockers and next actions

- Python API pytest cannot collect in this checkout: the base invocation lacks the API package path, the package-path invocation lacks `agent_adapters`, and the reviewed environment also lacks `opentelemetry`; `uv` is unable to use its read-only cache. Re-run `uv run pytest -q apps/api/tests/test_engineering_workflow_template_api.py` in a normal development environment.
- Host-software failure needs a real preflight/readiness contract rather than being inferred from a generic run failure. Parked for the next runtime contract pass: owner is Wright runtime/integration maintainers; next action is a non-executing host/MCP probe that records capability, host version, tool identity, and blocker before prompt dispatch.
