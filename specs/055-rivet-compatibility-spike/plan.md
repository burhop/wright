# Implementation Plan: Rivet Compatibility Spike

**Branch**: `055-rivet-compatibility-spike` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/055-rivet-compatibility-spike/spec.md`

**Parent**: `054-rivet-workflow-integration` at `21d2982` (`docs: plan incremental Rivet integration`)

## Summary

Run a controlled, feature-disabled compatibility experiment before adopting Rivet in production. The slice will select an immutable candidate baseline, build its editor and Node runtime reproducibly, exercise a non-production fixture, trace all host/persistence/native assumptions, test the official external-call and remote-debugger seams, deny runtime downloads, inventory supply-chain risk, and publish a versioned go/conditional-go/no-go decision.

The spike creates no production routes, packages, database migrations, workspace files, UI tab, or governed engineering-tool implementation. Its only durable deliverables are isolated test harness/fixture assets and the evidence needed for the next slices to accept, constrain, or reject Rivet.

## Technical Context

**Language/Version**: Python >=3.11 for Wright harness/verification; TypeScript/Node candidate selected by the spike (upstream manifest currently records Node 20.4); Wright TypeScript ~6.0 and React 19 remain untouched

**Primary Dependencies**: Git, Node package manager/version required by the selected Rivet pin, upstream `@ironclad/rivet-core` and `@ironclad/rivet-node`, a local static-file server/test browser, existing Wright Workspace Surface and process-supervisor contracts; all added only in an isolated development fixture

**Storage**: Read-only/downloaded upstream source plus `integrations/rivet/spike/` build metadata and fixture assets; evidence documents and checksum/license inventories under this slice; no SQLite migration, vault record, or user workspace content

**Testing**: Shell/PowerShell reproducibility scripts; Node-level fixture tests; static asset manifest/network-denial checks; pytest contract tests only if the harness needs typed Wright boundary checks; optional Playwright smoke for a built editor; source/package/license/SBOM scans

**Target Platform**: Development proof on Windows first, with portable scripted inspection and explicit Linux/macOS/Docker/unverified matrix entries; not a production support claim

**Project Type**: Experimental compatibility harness and documentation slice that consumes, but does not modify, the Wright application

**Performance Goals**: Record editor build duration, output bytes, warm fixture start time, runtime memory/process observations, and cancellation latency; no product performance claim is made by this slice

**Constraints**: No production imports/routes/schema/UI; no real user workspaces, engineering tools, credentials, or secrets; no browser-profile persistence as test authority; no direct MCP authorization; no runtime CDN/package/plugin download on supported fixture path; all source/package/build inputs pinned and checksummed

**Scale/Scope**: One upstream candidate and one fallback candidate at most; one small fixture project; one isolated editor build; one Node runner path; one host-operation seam; one remote-debugger attempt; browser and local-runner evidence only

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle | Design evidence | Gate |
|---|---|---|
| Strictly typed FastAPI and modular boundaries | The spike changes no production application boundary. Any optional harness-to-Wright check uses a narrow contract fixture only; no route business logic is added. | PASS |
| Offline-first | The explicit network-denial trial, asset manifest, package cache recording, and no-runtime-download gate test the constitutional requirement before adoption. | PASS |
| Production distribution and native/Docker parity | This slice makes no support claim. Its matrix distinguishes demonstrated Windows proof from Docker/Linux/macOS evidence required later. | PASS |
| Embedded storage and file vault | No durable user data or new store is introduced. Experimental inputs and evidence remain repository assets. | PASS |
| Local authentication and RBAC | The fixture uses mock host operations and no real principal, credential, or engineering tool. It cannot establish production authorization. | PASS |
| UI atomic design and test pyramid | The upstream editor is treated as isolated active content. The spike uses a minimal smoke test only; Wright UI components are not changed. | PASS |
| Structured observability | Scripts emit redacted structured evidence with source, command, version, checksum, environment, timestamp, result, and limitation. | PASS |
| Phase isolation and branch discipline | All work stays on `055-rivet-compatibility-spike`; no implementation begins until the human approves this plan; later feature slices consume only documented conclusions. | PASS |

Post-design re-check: the contracts preserve all constitutional boundaries. No exception or complexity justification is required.

## Research Decisions

1. **Use a source commit and lockfile as the unit of compatibility.** Published Rivet editor, core, and Node package versions can diverge. The spike chooses an immutable source revision, records package resolutions and build-output checksums, and never treats a tag or `latest` as sufficient proof.
2. **Use the Node executor as the execution candidate.** The documented Node API exposes `runGraphInFile`, abort signals, process events, external functions, and remote debugging. The browser executor is inspected only to identify editor limitations, not accepted as Wright's production runner.
3. **Treat editor host adaptation as a first-class compatibility test.** The decisive evidence is whether IO, dataset, native API, plugin registration, and debugger configuration can be injected per editor/workspace instance. A global mutable provider is not acceptable.
4. **Prove the official external-call seam before designing a plugin.** External calls are the smallest documented host bridge. A Wright plugin is considered only if evidence shows it is needed for safe typed UX or discovery and can be bundled/allowlisted without new authority.
5. **Use a network-denied fixture, not a claim based on a lockfile.** The build and runtime process must capture attempted requests and prove every allowed dependency is prepackaged.
6. **Keep experimental work physically and logically isolated.** `integrations/rivet/spike/` holds scripts, fixture, lock metadata, patch application, and generated manifests. It is excluded from production packaging and user flows until a later slice deliberately adopts selected assets.
7. **Fail closed on missing evidence.** Any mandatory capability without repeatable proof is classified unresolved/blocked. A conditional-go names its required enforcement in the next owning slice; it never silently becomes support.

Detailed sources and alternatives are in [research.md](./research.md).

## Project Structure

### Documentation (this feature)

```text
specs/055-rivet-compatibility-spike/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- checklists/
|   |-- requirements.md
|   |-- integration.md
|   |-- runtime.md
|   `-- security.md
|-- contracts/
|   |-- compatibility-evidence-contract.md
|   |-- go-no-go-contract.md
|   `-- upstream-baseline-contract.md
`-- tasks.md                    # generated only after human plan approval
```

### Experimental Source Only (created after approval)

```text
integrations/rivet/spike/
|-- README.md                   # no-production-use warning and reproduce entry point
|-- baseline/                   # immutable source/package/lock/patch metadata
|-- fixture/                    # minimal project and mock host operation
|-- scripts/                    # build, probe, offline, inventory, clean commands
|-- reports/                    # generated ignored output; committed summaries only
`-- tests/                      # deterministic compatibility assertions

tests/contract/rivet_spike/     # only if a Wright boundary fixture is needed
tests/ui-integration/rivet_spike/ # only if the static-editor smoke needs Playwright
```

**Structure Decision**: Experimental code lives under `integrations/rivet/spike/`, not under any production package. It may consume public Wright contracts for inspection but does not alter `core`, `workspace_service`, `tool_registry`, `data_vault`, `apps/api`, `apps/web`, Docker, native packaging, or release manifests. Promotion to production must occur in a later, separately approved owning slice.

## Delivery Phases

1. **Baseline acquisition**: Select primary and fallback candidates from immutable upstream sources; capture source/package/lockfile/checksum/license inputs and verify the build instructions in a clean location.
2. **Editor host-seam probe**: Build/serve the candidate editor at a non-root path; trace project/dataset/native/persistence/plugin/debugger initialization; identify injection seam or minimal patch; record prohibited behavior.
3. **Runner and bridge probe**: Run the fixture using the Node executor; capture process events, abort/cancel behavior, external-call request/response, and remote-debugger connection/rejection behavior using mock host operations only.
4. **Offline and supply-chain probe**: Run with package/CDN/plugin downloads denied; capture requests; generate asset, checksum, size, license, vulnerability, platform, and maintenance inventory.
5. **Decision and handoff**: Publish the compatibility matrix, evidence record, risk register, go/conditional-go/no-go decision, rollback/cleanup proof, and exact constraints for the persistence, runner, and editor-adapter slices.

Each phase is independently repeatable. A failed phase stops the candidate and records the failure; it does not expand production scope to work around it.

## Verification Strategy

- **Reproducibility**: Two clean executions from recorded inputs; exact source/package/build checksums; patch applies cleanly or fails explicitly; generated reports contain environment versions.
- **Editor**: Static asset loading from a non-root base path; no implicit Tauri dependency; inventory of file picker, IndexedDB, global-directory, local-storage, native API, plugin, and network behavior; IO/dataset/native injection per instance/workspace test.
- **Runner**: Fixture executes via `@ironclad/rivet-node`; events are captured; `AbortSignal`/cancellation is attempted and timed; external call uses a mock Wright bridge; remote debugger connects only through a generated test endpoint and stale/cross-fixture attempts are rejected where protocol exposes identity.
- **Offline**: Build and fixture execution with outbound package/CDN/plugin/font/telemetry requests denied and logged; asset manifest supports independent inspection.
- **Supply chain**: License notices, direct/transitive package inventory, known vulnerability report, checksums, bundle size, native build/runtime prerequisites, and ownership/update procedure.
- **Isolation**: Search/diff proves no production package, route, schema, Docker image, or user-facing feature is introduced; fixture contains no secret, real credential, or live tool call.
- **Decision quality**: Every umbrella compatibility question maps to an evidence item, disposition, risk, and next owner; unsupported contexts are named rather than inferred.

## Documentation and Evidence

The committed evidence bundle includes the selected source and package identities, build/fixture commands, exact versions, hashes, request log, output manifest, license/SBOM inventory, test logs, matrix, risk register, external-call/plugin decision, upgrade/fork policy, and go/no-go record. Generated bulky artifacts are reproducible and referenced by digest rather than committed indiscriminately. All evidence uses mock data and redacts any environment-specific paths/tokens.

## Planning Gate

This design is ready for a human decision when the specification, research, data model, three contracts, quickstart, and security/runtime/integration checklists contain no unresolved marker; all experimental boundaries are isolated; and the only next action is to generate tasks and run the approved spike. Stop here for human approval before creating `tasks.md`, downloading/building upstream code, or adding any fixture/script implementation.
