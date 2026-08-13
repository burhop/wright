# Implementation Plan: Engineering Capability Program Hardening

**Branch**: `codex/rivet-engineering-program` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/073-program-hardening/spec.md`

## Summary

Close the Wright Engineering Capability Program with one coherent, locally
operable experience: engineers can discover a capability, enable it, preflight
and run a Rivet scenario, understand failures, and deliberately export a
bounded diagnostic snapshot without exposing proprietary inputs or reusable
authority. Harden the current native and Docker state boundaries with seeded
upgrade/rollback/persistence evidence, align the shipped runtime compatibility
contract with the current data schema, add component/UI/system journey
coverage, and make every deterministic regression found here part of the
authoritative development merge gate. This loop does not publish a release or
add any physical actuation.

## Technical Context

**Language/Version**: Python 3.11-3.14; TypeScript 6.0; React 19

**Primary Dependencies**: FastAPI, Pydantic 2, SQLite, existing
`workspace_service`, `tool_registry`, `model_registry`, Wright native lifecycle,
Docker Compose, React Testing Library/Vitest, Playwright 1.62, Axe

**Storage**: Existing embedded SQLite data-vault migrations and native manifest
store; content-addressed catalog/model caches; structured local filesystem
vault; Docker named volumes. Diagnostic preview grants are deliberately
process-local, bounded, expiring, single-use records and are invalid after
restart.

**Testing**: pytest component/contract/integration/system suites; Vitest React
component tests; mocked and live Playwright journeys; Axe accessibility checks;
native artifact lifecycle/rehearsal tests; Docker manifest/volume contract tests

**Target Platform**: Exact-evidence support claims for Windows x86_64, Linux
x86_64, Linux arm64, macOS x86_64, and macOS arm64; Docker Linux x86_64 and
arm64. This Windows host may produce only Windows-local evidence; other targets
remain fixture/contract evidence unless their exact CI or host run exists.

**Project Type**: Modular monorepo with FastAPI backend, React web UI, packaged
native runtime, and Docker appliance

**Performance Goals**: Diagnostic preview p95 <= 500 ms for bounded fixture
state; export p95 <= 1 second and <= 2 MiB; progress/status changes visible
within 1 second; keyboard recovery requires no pointer-only action; deterministic
normal test suites require no network, credentials, GPU, proprietary host, or
paid service.

**Constraints**: Offline first; no automatic diagnostic upload; no raw prompts,
model features, environment values, credentials, private paths, artifact bodies,
commands, child-tool arguments, or reusable authority; no MCP-specific host
software in the base image; no remote-code execution; no model weights; no
physical actuation; preserve/quarantine newer incompatible data rather than
delete or misrepresent it; release rehearsal only, no publication.

**Scale/Scope**: Six completed program loops (068-073), four deterministic
multi-domain scenarios, the bundled capability and model catalogs, all current
data migrations through schema 16, native and Docker state roots, five public
platform/architecture claims, one reusable diagnostics panel, and one complete
cross-feature engineering journey.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Pre-design finding | Post-design evidence |
|---|---|---|
| Strict FastAPI/modular boundaries | Pass: routes will adapt HTTP only and delegate to `workspace_service`. | Pass: `contracts/support-diagnostics-api.md` keeps projection, redaction, scope, and grant logic in the service package. |
| Offline first | Pass: all normal behavior uses local persisted state and bundled snapshots. | Pass: diagnostics never upload; upgrade and journey acceptance runs with network denied. |
| Native/Docker distribution | Pass: exact artifact evidence and persistence are in scope; no release publication. | Pass: compatibility/persistence contracts bind evidence to artifact digest, platform, architecture, and storage roots. |
| Thick base/thin code | Pass: no new MCP host software or vendor dependency. | Pass: Docker design tests named-volume contracts only and keeps selected MCP validation outside the base. |
| Manager-neutral runtime | Pass: state and diagnostics live below manager adapters. | Pass: no Hermes-, Codex-, or OpenClaw-specific diagnostic semantics. |
| Embedded state | Pass: existing SQLite/file stores remain authoritative. | Pass: no service database; process-local export grants require no migration. |
| Security/RBAC | Pass: workspace/principal scope and explicit confirmation are mandatory. | Pass: export digest, one-use grant, expiry, redaction, and inert attachment rules are contractual. |
| Engineering tooling | Pass: no new engineering executor or GUI-only agent tool. | Pass: feature adds support projection and validation only; BaseTool contracts are unchanged. |
| Three-tier UI testing | Pass: component, mocked UI, and live system coverage planned. | Pass: `contracts/engineering-journey.md` maps every journey step to all applicable tiers. |
| Observability | Pass: stable reason/provider/trace digests are retained without sensitive payloads. | Pass: diagnostic snapshot schema permits safe correlation only and forbids unbounded log bodies. |
| Phase isolation/manual gates | Pass by explicit user authorization to run the overnight loops on the shared integration branch. | Pass: planning/design remains separately reviewable in `specs/073-program-hardening`; no `main` or release action is authorized. |

No constitutional violation requires a complexity exception.

## Project Structure

### Documentation (this feature)

```text
specs/073-program-hardening/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- compatibility-evidence.schema.json
|   |-- engineering-journey.md
|   |-- state-inventory.schema.json
|   |-- support-diagnostic-snapshot.schema.json
|   `-- support-diagnostics-api.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
apps/api/src/api/
|-- main.py
`-- routers/support_diagnostics.py

apps/web/src/
|-- components/support/SupportDiagnosticsPanel.tsx
|-- components/chat/RivetScenarioReport.tsx
|-- components/pages/ToolRegistryPage.tsx
|-- components/pages/EngineeringModelLibraryPage.tsx
`-- services/workspace-service.ts

packages/workspace_service/src/workspace_service/
|-- support_diagnostics.py
|-- support_diagnostic_service.py
|-- engineering_scenario_service.py
`-- engineering_model_service.py

packages/data_vault/src/data_vault/
`-- migrations/

src/wright_engineering/
|-- compatibility.json
`-- runtime/
    |-- diagnostics.py
    |-- migrations.py
    `-- state.py

docker/
|-- image-family.yaml
`-- container-manifest.mcp.md

tests/
|-- program_hardening/
|-- native_runtime/
|-- e2e/
`-- ui-integration/engineering-program-journey.spec.ts

docs/
|-- getting-started/
|-- operations/engineering-support-diagnostics.md
|-- testing/engineering-program-usability.md
`-- engineering-capability-program-progress.md

scripts/check-dev-merge.sh
```

**Structure Decision**: Extend existing packages and UI surfaces. The reusable
safe diagnostic projection belongs in `workspace_service`; the API router stays
thin, and the React panel is composed into existing capability, model, and Rivet
surfaces. Native compatibility continues to use the packaged JSON contract and
runtime migration manager. Deterministic hardening tests receive a named suite
so the authoritative gate can expose them early while the full suite remains the
backstop.

## Design Sequence

1. Define the safe diagnostic vocabulary, recursive redaction boundary, state
   inventory, compatibility evidence, preview/export grant, and complete journey
   contracts before changing runtime behavior.
2. Add failing tests for adversarial diagnostic material, principal/workspace
   isolation, digest/expiry/single-use behavior, current-schema compatibility,
   predecessor-state migration, newer-state quarantine, native persistence, and
   Docker named-volume declarations.
3. Implement the service and thin API, then compose the reusable UI panel into
   the existing engineering journey with stable loading, progress, failure,
   recovery, keyboard, reflow, zoom, and reduced-motion states.
4. Exercise component, mocked UI integration, and real local system tiers plus a
   human-repeatable walkthrough; record exact evidence level rather than
   upgrading fixture/contract checks into platform support claims.
5. Add the new deterministic hardening slice to `scripts/check-dev-merge.sh`,
   run non-publishing native/release rehearsals, update operations/install/
   rollback/uninstall/offline documentation, and close the program progress log.

## Complexity Tracking

No violations.

