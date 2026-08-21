# Implementation Plan: Windows MCP Qualification

**Branch**: `codex/074-windows-mcp-qualification` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/074-windows-mcp-qualification/spec.md`

## Summary

Add a native-Windows qualification path beside Wright's existing clean-Linux
container validator. The new path is governed by an immutable seven-server
allowlist and declarative pinned recipes, performs a source and safety decision
before any executable action, records eight independent qualification stages,
and always attempts bounded process cleanup and residue comparison. Evidence is
written as redacted JSON and Markdown under a dated Windows directory and a
small evidence-backed summary is projected into the catalog/UI. Real execution
is operator-invoked; normal regression tests use only local fakes. Qualification
then proceeds through the seven approved servers in order, with unavailable,
archived, commercial-host, OAuth, subscription, and unsafe boundaries preserved
as factual results instead of optimistic compatibility claims.

## Technical Context

**Language/Version**: Python 3.11-3.14 for recipes, orchestration, MCP probes,
evidence, and CLI; TypeScript 6.0 and React 19 for the catalog projection

**Primary Dependencies**: Pydantic 2, jsonschema, httpx/httpx-sse, psutil,
existing `tool_registry` validation/onboarding/gateway services, Python
standard-library subprocess/hash/path/tempfile facilities, React Testing
Library/Vitest. No MCP-specific package becomes a Wright dependency.

**Storage**: Declarative recipes and schemas in Git; dated redacted evidence in
`docs/mcp-catalog/evidence/windows-qualification-2026-08-13/`; isolated package
and runtime state beneath `.local-run/windows-mcp-qualification/` and the OS
temporary root; current catalog summaries in the bundled YAML. No credentials,
downloaded repositories, package caches, executable content, or real CAD files
enter Git.

**Testing**: pytest contract/unit/integration tests with fake executors, fake
local MCP clients, temporary directories, deterministic process fixtures, and
denied network; Vitest component coverage for separate Windows stages and stale
evidence; opt-in native Windows qualification; final `scripts/check-dev-merge.sh`

**Target Platform**: Native Windows 11 x86_64 is the only real qualification
target in this loop. Other platforms retain their independent evidence. The
existing clean-container validator remains authoritative for Linux containers.

**Project Type**: Modular monorepo with a Python domain/CLI, FastAPI projection,
React catalog UI, packaged native runtime, and provider-neutral MCP gateway

**Performance Goals**: Fail a denied identifier before any executor seam in
under 50 ms; validate a recipe/evidence document under 100 ms; apply timeouts
per stage; terminate a timed-out fixture process tree within 10 seconds; keep
captured output per stage at or below 64 KiB and one evidence document below
1 MiB; render the qualification summary with the existing detail dialog budget

**Constraints**: Exactly seven approved server IDs; no administrator access,
credentials, OAuth completion, subscription/license acceptance, commercial
host installation, global Python/Node/PATH/registry/service/startup mutation,
security-control changes, real engineering document mutation, undocumented
network destinations, destructive tools, arbitrary-code safe probes, physical
actuation, or non-allowlisted executable action. Preserve unrelated working
changes; no merge, push, PR, release, or publication.

**Scale/Scope**: Seven recipes, eight stage names, seven result values, one
native executor, one evidence writer/matrix, one catalog projection, and fake
coverage for every gate/failure class. This loop is qualification infrastructure
and evidence only; it does not become a general package manager.

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Pre-design finding | Post-design evidence |
|---|---|---|
| Modular monorepo / thin routes | Pass: qualification remains in `tool_registry`; the UI consumes an existing capability projection. | Pass: contracts keep recipes, execution, evidence, and projection separate; no route business logic is added. |
| Offline-first | Pass: real network qualification is explicitly operator-invoked, while normal tests and cached evidence remain offline. | Pass: fake recipes cover all gates without network; remote evidence degrades honestly when not refreshed. |
| Native and Docker distribution | Pass: native Windows evidence is distinct from clean-container evidence. | Pass: the Windows executor does not change the Docker base or infer cross-platform support. |
| Thick base / thin code | Pass: selected MCPs stay isolated optional test material. | Pass: no MCP package or commercial host is added to Wright dependencies or base images. |
| Manager-neutral runtime | Pass: qualification and gateway checks target Wright contracts, not a specific agent manager. | Pass: Rivet-visible discovery is verified only through the provider-neutral Wright gateway. |
| Embedded state | Pass: recipes/evidence are files and current runtime validation continues to use embedded SQLite. | Pass: no server database or external state service is introduced. |
| Security and RBAC | Pass: the CLI is operator-invoked and real onboarding retains its approval/confirmation boundary. | Pass: hard allowlist, structured operations, network allowlist, redaction, bounded execution, and cleanup fail closed. |
| Engineering tooling protocol | Pass: this feature validates MCP servers; it does not create an LLM engineering tool outside gateway contracts. | Pass: no GUI-only agent execution path or physical actuation is added. |
| Three-tier UI testing | Pass: the small interactive projection receives component coverage and existing page journeys remain the integration tier. | Pass: UI changes use existing components/tokens/test IDs; fixture and live evidence claims remain distinct. |
| Observability | Pass: evidence records stable digests/timings/reasons without secrets or raw command authority. | Pass: schemas impose byte bounds and redaction; audit ledgers prove allowed actions and cleanup. |
| Phase isolation/manual gates | Pass by explicit durable user approval to run the complete Spec Kit and ordered qualification loops unattended. | Pass: the user pre-approved safe reversible stage advancement and required automatic continuation on external blockers. |
| Branch discipline | Pass: work is isolated on `codex/074-windows-mcp-qualification`; no `main` action is authorized. | Pass: feature artifacts and implementation remain on the dedicated branch without merge/push/PR. |

No constitution violation requires an exception.

## Project Structure

### Documentation (this feature)

```text
specs/074-windows-mcp-qualification/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- windows-qualification-cli.md
|   |-- windows-qualification-evidence.schema.json
|   |-- windows-qualification-projection.md
|   `-- windows-qualification-recipe.schema.json
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/tool_registry/src/tool_registry/
|-- windows_qualification_models.py
|-- windows_qualification_recipes.py
|-- windows_qualification_executor.py
|-- windows_qualification_service.py
|-- windows_qualification_writer.py
|-- windows_qualification_cli.py
|-- capability_models.py
|-- capability_views.py
|-- catalog_models.py
`-- catalog/
    |-- engineering-catalog.yaml
    |-- windows-qualification-recipes.yaml
    |-- windows-qualification-evidence.schema.json
    `-- windows-qualification-recipe.schema.json

packages/tool_registry/tests/
|-- fixtures/windows_qualification/
|-- test_windows_qualification_models.py
|-- test_windows_qualification_recipes.py
|-- test_windows_qualification_executor.py
|-- test_windows_qualification_service.py
|-- test_windows_qualification_writer.py
|-- test_windows_qualification_cli.py
`-- test_windows_qualification_projection.py

apps/web/src/components/tools/
|-- CapabilityDetails.tsx
|-- WindowsQualificationSummary.tsx
`-- WindowsQualificationSummary.spec.tsx

docs/mcp-catalog/
|-- mcp-server-setup-recipes.md
|-- testing-problem-log.md
`-- evidence/windows-qualification-2026-08-13/
    |-- qualification-matrix.md
    |-- progress-log.md
    |-- installed-items.json
    |-- cleanup-ledger.json
    |-- non-allowlist-proof.json
    `-- <server-id>-windows-qualification.{json,md}
```

**Structure Decision**: Keep the current generic validation path intact and add
a Windows-specific bounded qualification domain because its safety, install,
process, residue, and evidence stages are materially richer than a protocol-only
container probe. Catalog models own only the small signed projection; full
operator evidence remains in dated documentation. The service accepts explicit
ports for source inspection, package preparation, MCP probing, Wright
onboarding/gateway validation, residue snapshots, and cleanup so deterministic
tests never touch the network or install software.

## Design Sequence

1. Define strict recipe/evidence models, fixed allowlist/order, stage/result
   vocabulary, current/stale identity binding, size limits, and signed catalog
   projection.
2. Add failing tests for non-allowlist denial before all side-effect seams,
   malformed/unsafe recipes, redaction, output bounds, timeout/process-tree
   cleanup, residue detection, remote/local semantics, host-required partials,
   evidence staleness, matrix completeness, and UI wording.
3. Implement structured recipe loading, source/safety decision enforcement, the
   injected orchestration service, native Windows executor, writer, CLI, and
   catalog projection; keep all real actions opt-in.
4. Research and qualify each approved server in the mandated order, stopping a
   server at the first safety or prerequisite boundary, checkpointing evidence,
   cleaning up, and continuing.
5. Reconcile catalog/UI claims to saved evidence, update setup/problem docs,
   run focused offline tests and the development merge gate, verify zero live
   processes and isolated residue, and report exact Windows claims.

## Complexity Tracking

No violations.

