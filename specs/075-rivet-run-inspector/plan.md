# Implementation Plan: Rivet Run Inspector

**Branch**: `codex/075-rivet-run-inspector` | **Date**: 2026-08-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/075-rivet-run-inspector/spec.md`

## Summary

Replace the direct Rivet canvas's 220-character terminal banner with a first-class, collapsible bottom Run Inspector. The implementation will project one authoritative inspection snapshot from existing SQLite run/event records, MCP child-call evidence, manifests, artifacts, and terminal outputs; preserve bounded redacted intermediate results at the gateway boundary; restore active and recent runs after refresh; provide deterministic diagnostics and safe full rerun; and extend the trusted Rivet editor bridge with presentation-only node execution states and focus. Existing run, cancel, options, save-before-run, lint, and evidence-export contracts remain intact.

## Technical Context

**Language/Version**: Python 3.11-3.14 for persistence, domain projection, and FastAPI; TypeScript 6.0 and React 19 for the workspace UI; TypeScript/Node.js for the pinned Rivet runner and editor wrapper

**Primary Dependencies**: FastAPI, Pydantic 2, embedded SQLite repositories, existing `workspace_service` workflow runner/operations/evidence modules, React, React Testing Library/Vitest, Playwright, the pinned Rivet 2 editor artifact, and the existing exact-origin `postMessage` bridge. No new runtime dependency is required.

**Storage**: Existing `workspace_workflow_runs`, `workspace_workflow_run_events`, `workspace_workflow_child_calls`, and run-manifest/approval tables in the embedded Wright SQLite database. Existing JSON columns retain bounded result projections. No second history store or external database is added.

**Testing**: pytest for repository, runner, evidence, projection, and API contracts; React Testing Library/Vitest for inspector states and interactions; mocked Playwright journeys in `tests/ui-integration/`; one local FastAPI/Rivet fixture smoke in `tests/e2e/`; pinned editor build/manifest verification; final `scripts/check-dev-merge.sh` before merge

**Target Platform**: Wright web UI and packaged native/Docker workspace UI on Windows, Linux, and macOS; offline local execution remains supported

**Project Type**: Modular monorepo with Python domain services and thin FastAPI routes, React workspace UI, embedded SQLite data vault, and a pinned patched Rivet editor/runner integration

**Performance Goals**: Reflect received execution updates in the UI within 1 second; poll active local runs at 500 ms with one aggregated request; restore an active run within 3 seconds after refresh; render at most 64 KiB or 200 rows initially for any expanded result; return at most 20 recent runs by default and 50 by request; keep inspection responses within the existing 2 MiB evidence ceiling

**Constraints**: Offline-first; no raw secrets, authority tokens, OAuth values, or unredacted MCP payloads in UI/history/export; preserve immutable run/revision identity and generation-checked cancellation; support older run records with missing optional evidence; do not add unconditional partial retry; do not scrape Rivet DOM; preserve unrelated dirty work; no merge, push, publication, or release without separate authorization

**Scale/Scope**: One current/selected run, up to 50 recent summaries, up to 256 run events and 1000 evidence records, up to 512 canvas node-state overlays, complete retained final outputs up to the existing 1 MiB limit, and bounded intermediate result projections per child call

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Pre-design finding | Post-design evidence |
|---|---|---|
| Modular monorepo / thin routes | Pass: run aggregation belongs in `workspace_service`; API routes only validate scope and project typed responses. | Pass: [run-inspector-api.md](contracts/run-inspector-api.md) defines a thin route over one domain inspection projection. |
| Offline-first | Pass: the inspector consumes local persisted state and requires no cloud service. | Pass: all normal tests use local fixtures; no model, OAuth, or external MCP dependency is introduced. |
| Native and Docker distribution | Pass: the UI and shared runtime contracts apply to both packaged native and Docker profiles. | Pass: no profile-specific execution path is added; required Rivet feature flags remain part of existing launch-profile verification. |
| Thick base / thin code | Pass: this feature adds no MCP or CAD host package to a base image. | Pass: result inspection reuses existing gateway evidence and artifacts only. |
| Manager-neutral runtime | Pass: workflow run state is independent of Hermes, Codex, OpenClaw, or the provider/model selected behind Wright. | Pass: no direct Rivet-to-provider/model wiring is added. |
| Embedded state | Pass: current SQLite records already contain the authoritative run/event/evidence data. | Pass: [data-model.md](data-model.md) extends repository projections and existing JSON evidence without a second store. |
| Security and RBAC | Pass: existing workspace/session scoping, authority boundaries, and artifact authorization remain in force. | Pass: [result-projection.md](contracts/result-projection.md) applies redaction before persistence/copy/export and exposes only non-reusable trace identities. |
| Engineering tooling protocol | Pass: this is observability for code-driven Rivet/MCP execution, not a GUI-only agent tool. | Pass: execution remains through existing runner and gateway contracts; the iframe receives presentation state only. |
| UI atomic design | Pass: new primitives/components/patterns will use existing design tokens. | Pass: plan separates status/result primitives, step/result components, and the composed inspector; no hardcoded parallel design system is introduced. |
| Tier 1 component tests | Pass: inspector state and interaction matrix is directly testable. | Pass: component coverage includes default, running, success, failure, cancellation, empty, large, redacted, and historical states. |
| Tier 2 UI integration | Pass: run, refresh, history, keyboard, and output journeys are page-level behaviors. | Pass: a mocked Playwright journey is explicitly included under `tests/ui-integration/workspace-surfaces/`. |
| Tier 3 system E2E | Pass: one local runner/API inspection smoke can verify the full parsing path. | Pass: the quickstart includes a focused `tests/e2e/test_rivet_run_inspector.py` gate without external MCP dependencies. |
| Test IDs | Pass: every interactive inspector control can receive a stable test ID. | Pass: API/UI contracts and tasks will require IDs for toggle, tabs, results, steps, history, copy/export, focus, cancel, and rerun controls. |
| Observability / traceability | Pass: runs, manifests, child calls, and events already carry run and trace correlations. | Pass: the inspection model completes projection of existing trace/timestamp fields and keeps exact reason codes in expandable details. |
| UI transparency | Pass: the feature's purpose is to expose run decisions, outputs, evidence, and limits. | Pass: diagnostics, completeness, redaction, truncation, artifacts, revision, and technical evidence are all explicit in the design. |
| Phase isolation / manual gates | Pass: the feature specification was explicitly approved before planning. | Pass: implementation remains blocked until this plan and subsequent task generation receive their required human approvals. |
| Branch discipline | Pass: work is isolated on `codex/075-rivet-run-inspector`. | Pass: all design artifacts target the feature branch; no `main`, merge, or release action is authorized. |

No constitution violation requires an exception.

## Project Structure

### Documentation (this feature)

```text
specs/075-rivet-run-inspector/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- editor-run-state-bridge.md
|   |-- result-projection.md
|   `-- run-inspector-api.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md                 # Generated by /speckit-tasks after plan approval
```

### Source Code (repository root)

```text
packages/core/src/core/
`-- rivet_mcp.py                         # Optional bounded child result evidence

packages/data_vault/src/data_vault/
|-- workflow_runs.py                     # timestamps, trace, recent-run query
`-- rivet_mcp_repository.py               # persisted safe child result projection

packages/data_vault/tests/
|-- test_data_vault_workflow_runs.py
`-- test_rivet_run_manifest.py

packages/workspace_service/src/workspace_service/
|-- workflow_runner.py                   # safe terminal output, truthful timestamps
|-- workflow_operations.py               # scoped history/inspection entry points
|-- rivet_gateway_bridge.py              # retain sanitized intermediate result
|-- rivet_evidence.py                    # redaction/result projection
`-- workflow_inspection.py               # step reduction, diagnostics, completeness

packages/workspace_service/tests/
|-- test_workflow_runner.py
|-- test_workflow_operations.py
|-- test_rivet_gateway_bridge.py
|-- test_rivet_run_evidence.py
`-- test_workflow_inspection.py

apps/api/src/api/
|-- schemas/workspace.py                 # typed summaries and inspection response
`-- routers/workspace.py                 # thin recent/inspection GET routes

apps/api/tests/
|-- test_rivet_mcp_run_api.py
`-- test_workflow_run_inspection_api.py

apps/web/src/
|-- components/common/
|   `-- RunStateBadge.tsx                # token-driven accessible primitive
|-- components/workflows/
|   |-- RivetRunInspector.tsx            # composed bottom inspector pattern
|   |-- RivetRunInspector.spec.tsx
|   |-- RivetRunResult.tsx               # typed result presentation/actions
|   |-- RivetRunStepList.tsx             # ordered accessible execution steps
|   `-- rivet-run-inspector.css
|-- components/surfaces/
|   |-- DirectRivetSurface.tsx            # host layout, reattachment, iframe sync
|   `-- DirectRivetSurface.spec.tsx
|-- hooks/
|   `-- useRivetRunInspection.ts          # polling, event cursor, history selection
`-- services/
    |-- workspace-service.ts              # typed client contract
    `-- workspace-service.spec.ts

integrations/rivet/editor/
|-- wrapper/WrightEditorBridge.tsx        # protocol v3 message validation
|-- patches/rivet2-run-state-overlay.patch
|-- scripts/build-rivet2.mjs
|-- manifest.json
`-- dist/                                 # verified rebuilt pinned artifact

tests/ui-integration/workspace-surfaces/
`-- rivet-run-inspector.spec.ts

tests/e2e/
`-- test_rivet_run_inspector.py

docs/
|-- rivet-workflows.md
`-- rivet/mcp-gateway.md
```

**Structure Decision**: Keep execution and evidence ownership in the existing data-vault and workspace-service modules. Add one focused `workflow_inspection.py` projector so run-state reduction, diagnostics, redaction completeness, and backward compatibility are independently testable. The FastAPI router stays thin. The React layer uses a shared hook plus small result/step components composed into the bottom inspector. Canvas node state crosses only the existing trusted bridge and is implemented in the maintained Rivet source patch before the pinned artifact is rebuilt.

## Design Sequence

1. Add failing repository/domain tests for running timestamps, trace projection, bounded recent history, safe oversized outputs, redaction, old records, and child-call result summaries.
2. Implement the result projector and extend existing run/child-call persistence without adding a parallel store; ensure persistence limits cannot turn an otherwise successful run into an unexplained failure.
3. Add the deterministic inspection reducer for progress, steps, outputs, diagnostics, completeness, and full-rerun eligibility; expose scoped recent-run and inspection methods from workflow operations.
4. Add Pydantic contracts and thin recent-run/inspection endpoints, preserve all existing start/cancel/history/evidence routes, and cover access scoping and `no-store` behavior.
5. Add frontend types/client methods and a polling/reattachment hook that uses an event cursor, stops at terminal state, tolerates transient errors, and never starts a run on refresh.
6. Build the token-driven bottom inspector with summary, Outputs, Steps, Diagnosis/Details, and History views; include keyboard navigation, copy/export/artifact actions, explicit empty/truncated/redacted states, and failure auto-open.
7. Extend the exact-origin editor protocol and maintained Rivet patch for bounded node state/focus, cover malformed/missing-node behavior, rebuild the pinned artifact, and verify manifest/hash integrity.
8. Integrate with `DirectRivetSurface`, replacing the 220-character banner while preserving immediate Run, separate Run Options, cancel, lint, and save-before-run behavior.
9. Add Tier 1 component tests, Tier 2 mocked Playwright journeys, Tier 3 local system smoke, and documentation; run focused gates first and the development merge gate only after the feature stabilizes.

## Complexity Tracking

No violations.

