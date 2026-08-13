# Implementation Plan: Rivet Engineering Scenario Harness

**Branch**: `codex/rivet-engineering-program` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/070-engineering-scenario-harness/spec.md`

## Summary

Add a package-owned, versioned engineering scenario catalog on top of Loop 069's Rivet/Wright MCP gateway. Three Tier 1 examples exercise structural CAD/Python/FEA, ECAD/CAD/CFD/Python, and Grasshopper/additive/slicer/CAM chains against independent deterministic fake MCPs. A scenario service validates manifests and environment guards, starts only reviewed Rivet workflows through existing operations, normalizes bounded child artifacts, evaluates unit-aware domain assertions, persists a report linked to the existing run manifest, and projects catalog/preflight/report states through thin APIs and the existing Rivet workflow panel. Tier 2 adapters reuse the clean-container catalog process and remain explicit opt-in evidence.

## Technical Context

**Language/Version**: Python 3.11-3.14 for contracts, catalog, assertions, orchestration, persistence, and API; TypeScript 5 and React 19 for the Wright web UI; YAML/JSON for manifests and deterministic artifact fixtures

**Primary Dependencies**: Existing `workspace_service` workflow operations/runner, `tool_registry.GatewayService`, Pydantic 2, PyYAML, SQLite data-vault repositories, FastAPI, React/Vitest/Playwright, pytest; Python standard-library `zipfile`, XML, CSV, and numeric primitives for bounded format validation

**Storage**: Package resources for scenario manifests and Wright-generated fixtures; additive SQLite migration 15 for scenario run/report identity and bounded normalized assertion evidence; large/raw artifacts remain in the existing FileVault and are referenced by authorized ID and digest

**Testing**: pytest unit/contract/integration/system tests, deterministic fake MCP servers routed through the Loop 069 gateway, Vitest component/service tests, Playwright mocked and local journeys, selected opt-in clean-container MCP probes, final program `scripts/check-dev-merge.sh`

**Target Platform**: Wright native Windows x64, Linux x64, Linux ARM64/GB10, and macOS where currently supported; Docker Linux x64/ARM64; browser UI

**Project Type**: Modular monorepo local desktop/web application with Python domain services, thin FastAPI routes, a supervised Rivet Node worker, provider-neutral MCP gateway, React frontend, and native/Docker distributions

**Performance Goals**: List 100 cached scenario summaries under 300 ms; validate one manifest under 500 ms; load a 1,000-event/assertion report under one second p95 excluding child execution; deliver cancellation to an active local child within one second; clean Tier 1 residue within five seconds

**Constraints**: Offline normal tests; deterministic cross-platform output; explicit SI normalization while retaining original units; 64 KiB event and 1 MiB terminal-output ceilings; no new direct MCP path; no paid/proprietary software, credentials, network, GPU, hardware, global install, large download, or physical actuation in Tier 1; unsupported schemas and undeclared units fail closed

**Scale/Scope**: Three initial scenarios, nine requested domains, at least two independent child MCPs per scenario, approximately ten artifact/assertion plugin kinds, up to 100 catalog summaries and 1,000 report items, one optional clean-container adapter path

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Pre-design and post-design evaluation |
|-----------|----------------------------------------|
| Modular monorepo / thin routes | PASS: scenario contracts and assertions live in `core`; catalog/orchestration in `workspace_service`; persistence in `data_vault`; routes validate and delegate. |
| Offline-first | PASS: all Tier 1 workflows and fixtures are local and deterministic; Tier 2 network/install work is explicit and excluded from normal gates. |
| Native and Docker distribution | PASS: manifests/fixtures are package resources and enter the existing wheel/image; the API and UI use existing distributions. |
| Thick base / thin code | PASS: no vendor MCP or engineering application is added to the base image; Tier 2 uses disposable clean containers. |
| Manager neutrality | PASS: every scenario MCP call uses the provider-neutral Loop 069 gateway and receives no broader authority. |
| Embedded state | PASS: durable report indexes use additive SQLite migration 15; artifact bytes remain in the existing FileVault. |
| Local authentication / RBAC | PASS: listing may use existing workspace visibility; preflight/start/cancel/report access reuse authenticated session/workspace checks. |
| Engineering tool isolation | PASS: fake children are supervised fixtures; real-package probes are disposable; manifests cannot carry commands, endpoints, credentials, or host paths. |
| UI atomic design / 3-tier tests | PASS: scenario cards, preflight, assertions, and recovery extend existing components with unit, API, component, and journey coverage. |
| Observability and traceability | PASS: scenario, node, binding, call, artifact, assertion, cleanup, and trace identities remain correlated and bounded. |
| Phase isolation and manual gates | PASS WITH RECORDED ADVANCE APPROVAL: the program goal authorizes safest reversible design choices and uninterrupted loops. Loop 070 receives focused gates; the exact merge gate is deferred to program closeout after Loop 073. |
| Branch discipline | PASS: Loop 070 accumulates on `codex/rivet-engineering-program`; no work targets `main`, and `dev` is changed only after the final authoritative gate. |

No constitution violation requires a complexity exception.

## Project Structure

### Documentation (this feature)

```text
specs/070-engineering-scenario-harness/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- artifact-envelope.schema.json
|   |-- assertion-result.schema.json
|   |-- engineering-scenario-api.md
|   |-- gate-b-decision.md
|   `-- scenario-manifest.schema.json
|-- checklists/
|   |-- requirements.md
|   `-- scenario-harness.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/core/src/core/
`-- engineering_scenarios.py            # versioned domain values, limits, reason codes

packages/data_vault/src/data_vault/
|-- migrations.py                       # additive migration 15
`-- engineering_scenario_repository.py  # report identity/evidence persistence

packages/workspace_service/src/workspace_service/
|-- engineering_scenario_catalog.py     # resource loading and manifest validation
|-- engineering_scenario_assertions.py  # registry and domain assertion plugins
|-- engineering_scenario_artifacts.py   # normalization, unit/coordinate enforcement
|-- engineering_scenario_service.py     # preflight/start/evaluate/compare orchestration
`-- engineering_scenario_catalog/
    |-- catalog.yaml
    |-- NOTICE.md
    |-- scenarios/*.yaml
    |-- workflows/*.rivet-project
    `-- fixtures/**/*.json|csv|3mf

apps/api/src/api/
|-- schemas/workspace.py                # scenario request/response projections
`-- routers/workspace.py                # thin scenario endpoints

apps/web/src/
|-- components/chat/RivetScenarioLibrary.tsx
|-- components/chat/RivetScenarioReport.tsx
|-- components/chat/RivetWorkflowsPanel.tsx
|-- services/workspace-service.ts
`-- **/*.spec.tsx

packages/workspace_service/tests/
|-- test_engineering_scenario_catalog.py
|-- test_engineering_scenario_assertions.py
|-- test_engineering_scenario_service.py
`-- fixtures/engineering_mcp_server.py

packages/data_vault/tests/
apps/api/tests/
tests/e2e/test_rivet_engineering_scenarios.py
tests/ui-integration/rivet-engineering-scenarios.spec.ts
docs/rivet/engineering-scenarios.md
docs/mcp-catalog/mcp-server-testing-process.md
docs/engineering-capability-program-progress.md
```

**Structure Decision**: Extend the existing workflow/gateway and data-vault packages rather than create another runner or test application. Scenario code owns only catalog, preflight, artifact normalization, assertions, and report projection; Loop 069 remains authoritative for MCP discovery, binding, review, execution, approvals, cancellation, and child lifecycle.

## Phase 0 Research Decisions

The primary-source evidence and alternatives are in [research.md](research.md). The resulting choices are:

1. Use a compact Wright schema vocabulary for artifacts rather than embed full vendor formats. Preserve source media/schema/version, unit and coordinate declarations, upstream hashes, and a bounded payload/vault reference.
2. Normalize comparable numeric values to SI dimensions while retaining original values/units. Reject absent or dimensionally incompatible units; never infer millimetres versus metres.
3. Validate format-specific invariants at useful seams: KiCad board header/dimensions/layers/nets, FEA/CFD convergence and input correlation, Grasshopper data-tree topology, 3MF package/unit/mesh/build relationships, and static RS274-style CAM modal safety.
4. Implement assertions behind a stable registry keyed by artifact kind and assertion kind. Unknown schema/plugin versions fail closed, so future domains do not require edits to the scenario runner.
5. Model deterministic fake engineering applications as distinct MCP servers, not in-process return stubs. Tests drive namespace-qualified discovery and calls through the real Wright gateway and run-bound Rivet provider.
6. Package only small Wright-generated fixtures with explicit provenance. Third-party samples require source, license, redistribution, and modification records.
7. Classify scenarios as Tier 1 deterministic/offline, Tier 2 disposable clean-container public MCP, or Tier 3 credentialed/proprietary/manual. Environment guards run before installation or child startup.

## Phase 1 Design

### Catalog and validation

- A catalog index points to immutable manifest resources. Loading validates the JSON Schema plus cross-field rules: unique IDs, supported versions, at least two capabilities for Tier 1, declared resource/safety/cleanup/provenance, known artifact and assertion plugins, graph node coverage, and no child connection material.
- Manifest digests use canonical JSON after YAML parsing. Catalog summaries expose only bounded user-facing metadata; the full manifest is available for preflight.
- The initial scenarios are `structural-bracket`, `electronics-enclosure-cooling`, and `parametric-manufacturing`. Each has a purpose-built Rivet project with static namespace-qualified MCP tool calls and no model-provider node.

### Preflight and execution

- Preflight resolves the scenario workflow and delegates capability discovery/binding preview to existing `WorkspaceWorkflowOperations`. It produces `ready`, `blocked`, or `skipped` with exact capability, schema, tier, platform, resource, and safety reasons.
- Starting a scenario calls the existing reviewed workflow start path with an immutable scenario context (manifest ID/digest, seed, assertion-set digest). It never supplies direct MCP configuration or bypasses review/approval.
- The scenario service observes the durable run manifest. Terminal child outputs marked as scenario artifacts are normalized, stored/linked through authorized vault references, and evaluated. Cancellation continues to use the existing workflow cancellation path and late-result boundary.

### Artifacts, units, and assertions

- An artifact envelope has a 1.x schema, domain/kind, source schema, producer node/call, upstream digests, content digest, original units/coordinate system, bounded inline structured content or vault reference, and validation state.
- A small dimensional unit table covers length, area, volume, mass, time, temperature (absolute and delta), angle, force, pressure/stress, velocity, power, energy, and dimensionless values. Canonical comparisons use SI and `Decimal` where source precision matters.
- Core assertions cover schema, presence, finite numbers, exact/range/tolerance/relational checks and source correlation. Domain plugins add mesh, ECAD, solver convergence, data-tree, 3MF/slicer, and static CAM rules.
- Assertions return `pass`, `fail`, `skip`, or `error`; failures carry stable categories and bounded observations. A tool success never implies engineering success.

### Persistence and evidence

- Migration 15 adds `engineering_scenario_runs` keyed to the existing workflow run and `engineering_scenario_assertions` keyed to one scenario run. It stores exact identities, bounded normalized observations, report digest/state, and cleanup metadata, not raw artifacts or authority.
- Final report generation is idempotent. Startup can rebuild a missing report from a terminal run manifest and package-owned manifest/fixtures; a material identity mismatch is reported rather than guessed.
- Comparison operates on exact identity/digest sets and assertion results. Export omits raw paths, credentials, authority, and proprietary payloads.

### UI

- The existing Rivet tab gains a scenario-library section with domain chips, tier/resource/duration text, readiness, participating capabilities, and a review action.
- Preflight shows blockers before start. The report groups nodes/capabilities, artifacts, and assertions and always provides text status, expected/observed values, units, and recovery.
- Existing workflow cards and run history remain unchanged when the user does not open scenarios.

### Test strategy

- Unit/contract tests validate schema versions, manifest digests, unit dimensions/conversions, bounds/tolerances, all plugin kinds, untrusted payload limits, license/provenance requirements, and environment classification.
- Integration tests start multiple distinct fake MCP child processes, bind/review one scenario graph, run it through the injected Rivet provider and Wright gateway, then assert artifacts, progress, report persistence, cancellation, and zero residual child receipt after denial/cancellation.
- Negative tests cover missing/ambiguous/stale capability, wrong units, malformed schema, invalid mesh/ECAD/package/tree, non-convergence, unsafe CAM intent, oversize/secret/script/path payloads, and unsupported versions.
- UI tests cover library, blocked preflight, running/cancelled, passing/failing assertion, responsive/keyboard, and evidence export journeys.
- Tier 2 runs only through explicit clean-container commands and records partial/blocked evidence separately from normal tests.

## Gate B Decision

[Gate B](contracts/gate-b-decision.md) is approved under the program goal's advance authority: package-owned versioned manifests; three deterministic multi-MCP scenarios; SI-aware artifact normalization; plugin assertions; existing gateway/run authority only; additive report persistence; existing Rivet panel extension; explicit Tier 2 clean-container adapter. Rollback disables scenario endpoints/UI and leaves ordinary workflows and Loop 069 MCP execution intact.

## Post-design Constitution Re-check

The Phase 1 contracts preserve every pre-design PASS. In particular, the harness does not become an MCP manager or solver, routes remain thin, durable state remains SQLite/FileVault, normal tests stay offline and deterministic, vendor software is not added to base images, child output is untrusted and bounded, and Gate E remains closed to physical actuation.

## Complexity Tracking

No constitution violation requires an exception. Domain assertions are plugins because nine artifact families have materially different invariants; the registry is smaller and safer than conditional logic in the runner and allows later domains without expanding gateway authority.
