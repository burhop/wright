# Implementation Plan: Local Engineering Model Library

**Branch**: `codex/rivet-engineering-program` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/071-local-engineering-model-library/spec.md`

## Summary

Add a distinct engineering model library that lets an engineer inspect trust and compatibility, preview exact effects, acquire only pinned data artifacts, verify and activate them atomically, run typed tests through an approved runtime adapter, and expose an enabled installation to Rivet through Wright's existing workspace gateway. A new `model_registry` package owns immutable contracts, catalog policy, lifecycle state machines, source adapters, runtime ports, and stable failures. `data_vault` owns migration 16 and content-addressed storage; `workspace_service` composes use cases behind a `tool_registry` application port; FastAPI and React remain thin. Normal evidence uses tiny generated fixtures and an isolated deterministic adapter. Loop 071 must also approve and exercise one public external engineering model after Gate D records exact license, artifacts, digests, runtime, resources, limitations, and real test-vector evidence, selecting a safer replacement if PointNet cannot qualify. No weights enter Git.

## Technical Context

**Language/Version**: Python 3.11-3.14 for domain, persistence, source/runtime mediation, and API; TypeScript 6.0 and React 19 for UI; JSON/YAML for manifests

**Primary Dependencies**: Pydantic 2, jsonschema, httpx, packaging, psutil, SQLite, FastAPI, existing `tool_registry.GatewayService`, React/Vitest/Playwright, pytest; standard-library hashing, archive, path, subprocess, and atomic-file primitives. Model runtimes are separately reviewed optional adapters.

**Storage**: Additive SQLite migration 16 for snapshots, plans, operations, installations, bindings, references, and evidence; content-addressed bytes beneath the Wright-managed user data root with staging, verified, installation, export, and quarantine areas; Git stores schemas, manifests, metadata, and generated test recipes but no weights

**Testing**: pytest contract/integration/system tests; injected local HTTP/range and offline-package fixtures; isolated deterministic runtime process; GatewayService authorization/cancellation tests; Vitest; Playwright; strict docs/schema/security checks; focused loop gate followed by final `scripts/check-dev-merge.sh`

**Target Platform**: Native Windows x64, Linux x64, Linux ARM64/GB10, and currently supported macOS; Docker Linux x64/ARM64; CPU-first browser UI. Each variant declares independent platform, architecture, accelerator, and runtime compatibility.

**Project Type**: Modular local desktop/web application with Python packages, embedded persistence/file vault, thin FastAPI composition, provider-neutral gateway, React frontend, and native/Docker distribution

**Performance Goals**: List/filter 1,000 cached variants under 500 ms p95 (with a 500-entry target under 300 ms); inspect one cached package under 150 ms; create/validate a 100-file plan under one second excluding hashing/network; validate 1,000 declared artifacts under one second; observe cancellation within one second; discover an enabled capability under 300 ms; under 10% orchestration overhead excluding model load/inference

**Constraints**: Offline normal gates; no network, credentials, gated terms, paid services, proprietary apps, GPU, hardware, large downloads, global dependency changes, committed weights, or physical actuation; metadata <=64 KiB per record and evidence <=1 MiB per operation; confirmed plans set all byte ceilings; data-only formats; no pickle, repository code, native libraries, plugins, macros, shell commands, or `trust_remote_code`; all paths confined to Wright data root; model and runtime installation remain separate

**Scale/Scope**: Initial catalog with one generated Wright deterministic model, one approved public external engineering model, and representative blocked/gated/incompatible entries; at least 1,000 cached variants and up to 1,000 artifacts per package; concurrent reads and serialized mutations per package/content digest; one deterministic test adapter plus the reviewed optional `wright-neuralfoil-numpy` adapter and public extension contracts

## Constitution Check

_GATE: Passed before Phase 0 research and re-checked after Phase 1 design._

| Principle                      | Evaluation                                                                                                                                                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Modular monorepo / thin routes | PASS: `model_registry` owns the domain, `data_vault` owns state/bytes, `workspace_service` implements use cases behind a `tool_registry` application port, and routes only validate/delegate to that injected port. |
| Offline-first                  | PASS: bundled/cached inspection, import, verification, test, enablement, inference, rollback, and removal remain local.                                                                                             |
| Native and Docker distribution | PASS: contracts enter existing artifacts; payloads stay in the data root; adapters declare support independently.                                                                                                   |
| Thick base / thin code         | PASS: no model, runtime, GPU stack, compiler, or vendor dependency is added merely to pass validation.                                                                                                              |
| Manager neutrality             | PASS: Rivet and every manager reach typed model capabilities only through Wright's workspace gateway.                                                                                                               |
| Embedded state                 | PASS: migration 16 uses SQLite WAL and content uses the local vault; no server database is added.                                                                                                                   |
| Authentication / RBAC          | PASS: effects, runtime changes, workspace enablement, export, and purge use existing authenticated roles/scopes.                                                                                                    |
| Engineering isolation          | PASS: sources acquire declared bytes only; adapters are separate supervised processes with typed I/O; every LLM-facing model capability is a `BaseTool` implementation.                                             |
| UI / 3-tier tests              | PASS: tokenized primitives and patterns receive component, mocked journey, and local system coverage plus `data-testid`.                                                                                            |
| Observability                  | PASS: plan, operation, artifact, installation, adapter, binding, request, trace, test, cancellation, cleanup, and reference identities are recorded without secrets.                                                |
| Phase/manual gates             | PASS WITH RECORDED ADVANCE APPROVAL: the durable goal authorizes safe reversible choices and uninterrupted loops; Gate D is explicit and the full merge gate is deferred to program closeout.                       |
| Branch discipline              | PASS: Loop 071 keeps its numbered identity on the user-approved `codex/rivet-engineering-program`; no work targets `main`.                                                                                          |

No constitution violation requires an exception.

## Project Structure

### Documentation (this feature)

```text
specs/071-local-engineering-model-library/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- engineering-model-api.md
|   |-- gate-d-decision.md
|   |-- gateway-capability.md
|   |-- model-install-plan.schema.json
|   |-- model-operation.schema.json
|   |-- model-package.schema.json
|   |-- model-test-vector.schema.json
|   `-- runtime-adapter.md
|-- checklists/
|   |-- requirements.md
|   `-- model-library.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/model_registry/
|-- pyproject.toml
|-- src/model_registry/
|   |-- models.py
|   |-- catalog.py
|   |-- policy.py
|   |-- planning.py
|   |-- lifecycle.py
|   |-- sources.py
|   |-- runtime.py
|   |-- neuralfoil_runtime.py
|   |-- model_tool.py
|   |-- gateway_provider.py
|   |-- catalog/catalog.yaml
|   |-- catalog/neuralfoil-medium-package.json
|   `-- schemas/*.json
`-- tests/

packages/data_vault/src/data_vault/
|-- migrations.py
|-- model_repository.py
`-- model_artifact_store.py

packages/workspace_service/src/workspace_service/
`-- engineering_model_service.py

packages/tool_registry/src/tool_registry/
|-- gateway_ports.py
|-- model_library_port.py
`-- gateway_service.py

apps/api/src/api/
|-- schemas/engineering_models.py
|-- routers/engineering_models.py
`-- composition.py

apps/web/src/
|-- components/models/
|-- components/pages/EngineeringModelLibraryPage.tsx
|-- services/engineering-model-service.ts
|-- App.tsx
`-- **/*.spec.tsx

tests/e2e/test_engineering_model_library.py
tests/external/test_neuralfoil_external_model.py
tests/compatibility/test_engineering_model_compatibility.py
tests/packaging/test_engineering_model_package.py
tests/security/test_engineering_model_distribution.py
tests/ui-integration/engineering-model-library.spec.ts
docs/models/local-engineering-models.md
docs/model-evidence/external-model-validation-2026-08-13.md
docs/engineering-capability-program-progress.md
```

**Structure Decision**: Create `model_registry` rather than place specialized models in conversational provider setup or the MCP catalog. It supplies dependency-inverted source, persistence, storage, runtime, and gateway ports. `data_vault` implements local state and bytes; `workspace_service` binds authenticated use cases behind a `tool_registry` application port; `tool_registry` also accepts a generic capability provider so enabled models use the same workspace, policy, audit, result-bound, and cancellation boundary as MCP tools without pretending to be MCP servers. The LLM-facing projection wraps each enabled task in a `BaseTool` implementation before producing its `GatewayTool` view.

## Phase 0 Research Decisions

Details and primary sources are in [research.md](research.md).

1. Pin every remote model to a full immutable revision and declare every file, size, SHA-256 digest, media type, and role. Mutable aliases can resolve a new preview but never survive confirmation.
2. Treat model-card metadata as discovery evidence, not installation authority. Gate D independently approves license/attribution, actual files, format, adapter/runtime, resources, limitations, and vectors.
3. Accept only reviewed data-only formats. Safetensors and strictly validated ONNX are preferred; legacy framework data needs an explicit adapter decision. Pickle-family files, source archives, native code, and remote code are blocked.
4. Keep model packages and runtime adapters on separate plans. A model may depend on a verified adapter identity but cannot install packages, drivers, compilers, services, containers, or global settings.
5. Use staged content-addressed storage: partial state is untrusted, verified objects are immutable by digest, activation is an atomic manifest/reference update, and purge is reference/lease guarded.
6. Resume HTTP only when validators and declared identity make the range safe; otherwise restart. Offline archives receive identical path, declaration, size, digest, license, compatibility, and vector checks.
7. Expose models as typed namespaced Wright capabilities through a generic gateway provider. Runtime processes stay private; managers and Rivet never receive their endpoint, token, command, or handle.
8. Start with a generated affine test model/adapter for exhaustive normal-gate coverage. Keep `keras-io/PointNet` at revision `308acfe5d36d9bb34215d1766f13fac612abe18c` evaluation-only because its standalone license evidence, legacy TensorFlow SavedModel boundary, resource footprint, and vectors did not close safely. Approve `neuralfoil-medium` only at immutable revision `bb8a775199d1dafb5f410e68e027ba6eca1af9bc`, with three exact MIT/NPZ artifacts and the separately reviewed optional `wright-neuralfoil-numpy` adapter.

## Phase 1 Design

### Catalog and trust

- A bundled release catalog contains bounded manifests and evidence references. Package identity is `(model_id, package_revision, variant_id, manifest_digest)`.
- JSON Schema plus semantic validation enforces unique identities, SPDX-compatible license evidence, exact artifacts, safe formats, platform/resources, typed contracts, deterministic vectors, and known adapters.
- Readiness is computed as `approved`, `needs_review`, `gated_external_action`, `incompatible`, `deprecated`, `withdrawn`, or `blocked`. Every evidence facet is labelled bundled/cached/live/stale/partial/absent.
- Refresh creates a candidate snapshot and cannot mutate an active snapshot, installation, or confirmed plan.

### Planning, acquisition, and activation

- Plan creation performs compatibility, resource, license, source, storage, reference, and runtime preflight and returns exact upper-bound effects and blockers. Confirmation binds a principal to one expiring plan digest.
- Remote acquisition permits policy-approved HTTPS sources/redirects, stages only declared relative files, streams within limits, verifies SHA-256, and promotes by digest only after all checks.
- Resumption requires the same immutable revision, strong validator, and correct `206 Content-Range`; otherwise it restarts. Credentials remain opaque secret references outside model state.
- Offline import rejects absolute/traversing/duplicate paths, links, nested archives, executable bits, undeclared files, unsafe formats, and excess expansion. Export contains deterministic manifest/artifacts/evidence but no secrets, authority, host paths, private data, or disallowed redistribution.
- Visibility changes only in an atomic transaction referencing already verified objects. Failed/cancelled updates preserve the active healthy revision.

### Runtime and gateway capability

- An adapter advertises versioned tasks, schemas, formats, platforms, and resources and implements health, artifact verification, load, typed inference, progress, cancel, unload, and shutdown over a bounded local protocol.
- The supervisor enforces deadlines, output ceilings, clean environment, and residue reporting. Inputs and outputs are schema-checked; non-finite/oversized results fail closed; process exit alone is never engineering evidence.
- Mandatory vectors pass before readiness/enablement. Vector contracts include deterministic seed, material limitations exercised, input/output schema digests, units/coordinates where applicable, and bounded expectations. A separately launched deterministic adapter proves process mediation and cancellation without adding an ML framework.
- A generic `GatewayCapabilityProvider` lists only workspace-enabled healthy exact `BaseTool` bindings using `wright_model__<model-id>__<task>`. GatewayService continues to own workspace immutability, policy/review/approval, audit, result bounds, request cancellation, and session close.

### Lifecycle and recovery

- Durable idempotent operations cover plan, acquire/import, verify, install, test, enable, update, rollback, disable, uninstall, purge, export, cleanup, failure, and cancellation.
- References cover installed packages, active revisions, bindings, reviewed workflows, retained runs, exports, operations, and leases. Uninstall may retain referenced cache content; purge requires zero references and leases.
- Startup reconciles database and storage: partials remain untrusted, missing content blocks readiness, unknown bytes are quarantined, and interrupted activation follows the committed transaction.
- Update comparison includes license, artifacts, runtime, contracts, units/coordinates, resources, vectors, limitations, and redistribution. Rollback reuses verified cache but re-tests the exact adapter/environment.

### API, UI, and tests

- Thin `/api/v1/engineering-models` routes expose catalog/detail, plan/confirm, operation/progress/cancel, test, workspace enable/disable, update/rollback, export/import, uninstall/purge, references, and evidence by delegating immediately to the injected `tool_registry` application port.
- A dedicated Engineering Models page remains separate from `/setup/model`, leads with task/readiness/license/resources/runtime/evidence/limitations, previews every effect, reports exact blockers/recovery, and stays useful offline. Generated fixtures also show their exact generator recipe, inputs, constraints, and resulting manifest/artifact digests; external artifacts show source/provenance rather than a fictitious generator.
- Tests cover contracts, paths/formats/limits, sources/resume/redirects, CAS/concurrency/crash recovery, lifecycle/update/rollback/references, adapter verification/progress/failures/cancellation, gateway isolation/authority/BaseTool conformance, structured logs/traces, UI states/accessibility, and bounded opt-in external evidence.

### Bounded record and deterministic evidence policy

- Catalog/package/plan/operation/evidence records are capped at 64 KiB unless the public contract sets a smaller limit; validation evidence and exports have an independent 1 MiB metadata ceiling; general API/log records never embed model payload bytes.
- Arrays are bounded at: 1,000 variants per benchmark snapshot, 1,000 artifacts per package, 128 blockers/effects, 32 tasks/vectors/platforms, 64 limitations/units, and 1,000 durable references. User-facing page sizes are capped at 100 and progress/event history at 1,000 entries.
- Strings use field-specific schema limits, with 128-byte identities, 512-byte relative paths, 1,000-byte safe messages/limitations, 2,048-byte source locations, and 4,096-byte descriptions/attribution as maxima. Typed input/output and adapter control messages have explicit encoded-byte limits before parsing.
- A `material_evidence_digest` covers deterministic identities, input/output digests, predicates, and outcomes. Timing, observed resources, timestamps, trace IDs, and host diagnostics live in a separate observation projection/digest so repeated supported CPU runs can have identical material evidence within declared tolerances.
- Structured `structlog` events and OpenTelemetry spans cover source acquisition, database/storage transitions, adapter verify/load/infer/unload, gateway calls, cancellation, cleanup, and failures. Every span carries the existing trace identity and only bounded redacted attributes.

## Gate D Decision

[Gate D](contracts/gate-d-decision.md) approves the provider-neutral contracts, content-addressed storage, strict data-only policy, separate adapter lifecycle, deterministic runtime slice, gateway mediation, UI/API design, and `neuralfoil-medium` as the first public external package. Approval is limited to immutable revision `bb8a775199d1dafb5f410e68e027ba6eca1af9bc`, the exact selected MIT license and two NPZ artifacts, the published golden vector, and `wright-neuralfoil-numpy` adapter version `1.0.0`. The adapter uses `allow_pickle=False`, executes no publisher code, and remains an optional NumPy runtime rather than a model-plan side effect. PointNet remains evaluation-only. No remote code, gated terms, or model weights enter Git.

## Post-design Constitution Re-check

All pre-design passes remain valid: models are separate from conversational and MCP catalogs; routes stay thin; state remains embedded; runtimes are private and supervised; Rivet calls only through the workspace gateway; dependencies and artifacts are never silently installed; normal gates stay offline and payload-free; physical actuation remains outside Gate E.

## Complexity Tracking

No exception is required. The new package is justified because engineering-model identity, artifact trust, installation, runtime, and test semantics are neither MCP-server semantics nor conversational-provider configuration. A generic gateway-provider seam is smaller and safer than representing installed models as fake MCP servers.
