# Implementation Plan: Chatter and Model-Enabled Rivet Scenarios

**Branch**: `codex/rivet-engineering-program` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/072-chatter-rivet-scenarios/spec.md`

## Summary

Add a private, offline-only Chatter package path and a deterministic model-enabled CNC scenario without teaching Rivet about Chatter. An explicit opt-in qualification command retrains the exact reviewed Data Vault recipe from immutable local Dataset 2 bytes, exports only bounded numeric Random Forest and preprocessing arrays, proves source-versus-serving parity, and creates a non-redistributable Wright offline model archive plus evidence outside Git. The existing model library imports, verifies, tests, enables, and invokes that archive through a new `wright-chatter-forest-numpy` adapter. The generic gateway exposes the enabled task beside MCP tools. The scenario harness adds provider-neutral capability evidence, deterministic CAD and simulated CAM fixtures, a model result/report contract, and one Tier-1 Rivet graph. Normal gates use a tiny generated Chatter-shaped forest; the real private package is exercised only by an explicit ignored qualification test. No workflow produces machine instructions or physical action.

## Technical Context

**Language/Version**: Python 3.11-3.14 for contracts, conversion, model runtime, gateway, scenario orchestration, API, and tests; TypeScript 6.0 and React 19 for UI; JSON/YAML/NPZ for versioned declarations and data-only arrays

**Primary Dependencies**: Existing Pydantic 2, jsonschema, NumPy, SQLite, FastAPI, `model_registry`, `data_vault`, `tool_registry.GatewayService`, Rivet worker/bridge, React/Vitest/Playwright, pytest; scikit-learn/pandas/pyarrow only in the explicitly selected trusted qualification environment, never in normal installation or serving

**Storage**: Existing model content-addressed store, installation/evidence/binding tables, workflow/scenario repositories, and Run Manifest records; private source data, qualification environments, conversion output, packages, and scratch remain under ignored caller-owned paths; Git stores only schemas, metadata, generator recipes, tiny generated fixtures, and expected predicates

**Testing**: pytest contract/unit/integration/system/security/packaging tests; generated Random Forest/fixture MCP doubles; real Rivet worker and Wright gateway tests; opt-in ignored local Chatter qualification test; Vitest and mocked Playwright accessibility/responsive journeys; final program gate remains deferred until Loop 073

**Target Platform**: CPU-only native Windows x64, Linux x64, Linux ARM64/GB10, and supported macOS plus Docker Linux x64/ARM64. The private package declares exact compatible platforms and adapter version; unsupported hosts stay inspectable but blocked.

**Project Type**: Modular local desktop/web application with Python packages, embedded persistence/file vault, thin FastAPI composition, provider-neutral gateway, isolated Rivet worker, React UI, and native/Docker packaging

**Performance Goals**: Chatter batch of 1-100 candidates under 3 seconds p95 cold on reference CPU; scenario preflight under 1 second p95; deterministic scenario under 30 seconds p95; cancellation delivered under 1 second and owned cleanup under 5 seconds or explicit residue; bounded report/evidence under 2 MiB

**Constraints**: Offline normal gates; no credentials, paid services, proprietary apps, GPU, hardware, large downloads, unsafe deserialization, remote code, global environment mutation, committed private data/model payloads, executable machine instructions, or physical actuation. Exact input order, units, finite values, source identity, artifact digests, threshold, adapter, vector evidence, resources, and policy are fail-closed.

**Scale/Scope**: One private Chatter source record; one locally produced package revision with 37 process features, two classes, 500-tree ceiling, 1,000,000-node ceiling, 256 MiB artifact ceiling, and batches of 1-100 candidates; one generated normal-gate package; one CAD/CAM/model Tier-1 scenario; provider-neutral extensions that support later models without model-ID branches

## Constitution Check

_GATE: Passed before Phase 0 research and re-checked after Phase 1 design._

| Principle | Evaluation |
| --- | --- |
| Modular monorepo / thin routes | PASS: `model_registry` owns the Chatter format/runtime, `workspace_service` owns use cases and scenario composition, `tool_registry` owns the gateway seam, and routes remain validation/delegation only. |
| Offline-first | PASS: imported package inspection, testing, binding, inference, scenario execution, evidence, comparison, disable, and removal work air-gapped. |
| Native and Docker distribution | PASS: only adapter code/contracts ship; private weights and data remain user-owned content outside distributions. |
| Thick base / thin code | PASS: no scikit-learn, converter, CAD/CAM host, GPU stack, or MCP-specific host software is added to the production base merely for validation. |
| Manager neutrality | PASS: Rivet and every manager see only gateway tool contracts; model processes, MCP endpoints, and reusable authority remain private to Wright. |
| Embedded state | PASS: existing SQLite WAL repositories and Wright file vault retain state/evidence; no server database is added. |
| Authentication / RBAC | PASS: existing effect-plan, import, enable, workflow review, approval, and run authority boundaries remain authoritative. |
| Engineering isolation | PASS: the model task is a `BaseTool` gateway capability; CAD/CAM fixtures are code-driven MCPs; the adapter is a supervised bounded process. |
| UI / 3-tier tests | PASS: generic scenario/model patterns gain component, mocked page-journey, and local system tests with stable test IDs. |
| Observability | PASS: package, adapter, binding, candidate, node, child call, result, cancellation, cleanup, and artifact identities are correlated without private rows, scores tied to source rows, secrets, paths, or payload bytes. |
| Phase/manual gates | PASS WITH RECORDED ADVANCE APPROVAL: the durable program goal authorizes uninterrupted reversible loops; Gate D is recorded and the exact-tree dev gate remains deferred to Loop 073. |
| Branch discipline | PASS: Loop 072 retains its numbered feature identity on the user-approved `codex/rivet-engineering-program`; no work targets `main`. |

No constitution violation requires an exception.

## Project Structure

### Documentation (this feature)

```text
specs/072-chatter-rivet-scenarios/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- chatter-candidate-batch.schema.json
|   |-- chatter-result-batch.schema.json
|   |-- chatter-serving-metadata.schema.json
|   |-- conversion-parity-evidence.schema.json
|   |-- model-enabled-scenario.md
|   |-- run-manifest-provider-evidence.md
|   `-- gate-d-chatter-decision.md
|-- checklists/
|   |-- requirements.md
|   |-- chatter-trust-and-security.md
|   |-- scenario-engineering.md
|   `-- usability-and-recovery.md
`-- tasks.md
```

### Source Code (repository root)

```text
packages/model_registry/src/model_registry/
|-- chatter_runtime.py
|-- chatter_contracts.py
|-- generated.py
|-- runtime.py
|-- policy.py
|-- catalog/catalog.yaml
`-- schemas/*.json

packages/model_registry/tests/
|-- test_chatter_runtime.py
|-- test_chatter_contracts.py
|-- test_chatter_generated.py
`-- test_chatter_security.py

packages/core/src/core/rivet_mcp.py
packages/core/tests/test_rivet_mcp_contracts.py

packages/workspace_service/src/workspace_service/
|-- engineering_model_service.py
|-- rivet_capabilities.py
|-- rivet_evidence.py
|-- workflow_runner.py
|-- engineering_scenario_catalog_service.py
|-- engineering_scenario_artifacts.py
|-- engineering_scenario_assertions.py
|-- engineering_scenario_service.py
`-- engineering_scenario_catalog/
    |-- contracts/*.json
    |-- scenarios/chatter-candidate-review.yaml
    |-- fixtures/chatter-candidate-review.json
    `-- workflows/chatter-candidate-review.rivet-project

packages/tool_registry/src/tool_registry/
|-- gateway_models.py
`-- gateway_service.py

scripts/qualification/
`-- qualify-chatter-model.py

apps/api/src/api/
|-- schemas/workspace.py
`-- routers/workspace.py

apps/web/src/
|-- components/chat/RivetScenarioLibrary.tsx
|-- components/chat/RivetScenarioReport.tsx
|-- services/workspace-service.ts
`-- **/*.spec.tsx

tests/e2e/test_chatter_model_scenario.py
tests/external/test_chatter_local_qualification.py
tests/compatibility/test_chatter_compatibility.py
tests/packaging/test_chatter_distribution.py
tests/security/test_chatter_boundaries.py
tests/ui-integration/chatter-rivet-scenario.spec.ts
docs/models/chatter-local-model.md
docs/rivet/model-enabled-scenarios.md
docs/engineering-capability-program-progress.md
```

**Structure Decision**: Extend the generic model-library, gateway, Rivet binding, and scenario contracts. Chatter-specific numeric semantics live only in `model_registry` and the explicit qualification script. The generic runner, gateway, scenario orchestration, and UI receive provider-neutral metadata and never branch on the Chatter model ID. The Loop 069 `capability-binding.schema.json` and `run-manifest.schema.json` version-1 resources remain byte-for-byte immutable; new `capability-binding-v2.schema.json` and `run-manifest-v2.schema.json` resources make MCP versus engineering-model identity explicit, while version-aware readers preserve prior evidence.

## Phase 0 Research Decisions

Details and primary sources are in [research.md](research.md).

1. Treat the private `burhop/chatter` revision and immutable Data Vault dataset/membership/evaluation records as internal source evidence, not redistribution authority. Until an owner decision exists, package terms are `LicenseRef-Wright-Internal-Chatter`, offline-only, export-prohibited.
2. Never load the existing Joblib/pickle artifact in Wright. The explicit qualification command retrains the exact reviewed recipe from immutable bytes and exports a narrow data-only forest representation; normal installation only imports/verifies that output.
3. Prefer `wright-chatter-forest-npz` over generic ONNX or Skops. It represents only ordered preprocessing constants and binary decision-tree arrays required for this one reviewed classifier family, loads with `allow_pickle=False`, and has semantic/shape/resource validators.
4. Reproduce scikit-learn semantics deliberately: ordered ColumnTransformer output, `log1p(max(x,0))`, training means/scales, float32 tree input, `<=` split traversal, per-leaf class fractions, forest mean score, class order `[0,1]`, and `score >= threshold` as chatter.
5. Bind parity evidence to source revision, data and membership digests, recipe/environment/exporter identities, serving bytes, frozen rows, boundary vectors, class agreement, per-row score deltas, and reload determinism. Aggregate success cannot override a mandatory boundary disagreement.
6. Use one cold bounded batch per gateway call. Existing model runtime admission, deadlines, cancellation, unload, shutdown, and reservation cleanup are sufficient; run-scoped warm reuse is deferred.
7. Use a list of 37 named feature records, not an unordered JSON object, so feature order, unit, origin, finiteness, and duplication are independently validated. Results call the numeric output an uncalibrated chatter score.
8. Add a generic `provider_kind` plus provider-specific evidence projection to Rivet bindings/Run Manifest. MCPs remain MCPs; installed models remain engineering-model capabilities even though both use one gateway call path.
9. Add a Tier-1 `chatter-candidate-review` graph with deterministic CAD context, simulated CAM candidate generation, and one model capability. It compares only supplied discrete candidates, rejects failed invariants/near-threshold/out-of-population cases, and emits advisory evidence with no G-code or machine authority.
10. Use generated forest arrays and fixture MCPs for normal gates. The private real-model qualification and scenario proof are ignored, explicit, local-only, bounded, and required for real deployment evidence rather than ordinary CI.

## Phase 1 Design

### Trusted qualification and package

- The bundled catalog adds a non-installable private Chatter source record showing exact source/data/recipe identities, limitations, absent local payload state, and recovery instructions. It contains no artifact digest guessed before conversion.
- `qualify-chatter-model.py` requires explicit source, Dataset 2, membership/evidence, output, and environment-lock inputs. It checks clean source revision and every supplied digest, imports only reviewed local Data Vault training code in the trusted environment, trains deterministically, exports validated numeric arrays, runs source/serving parity, and creates a Wright offline package. It never contacts a cloud service or writes inside the repository by default.
- The package declares source access `offline_only`, internal terms, redistribution prohibited, the exact conversion and artifact identities, `remote_code_policy=forbidden`, adapter `wright-chatter-forest-numpy`, CPU resources, supported platforms, limitations, candidate contract, and mandatory vectors. Because no upstream public license file or license metadata exists, qualification emits and binds an `INTERNAL-USE-NOTICE.txt` artifact that records that absence and the conservative local policy; it is policy evidence, not a publisher license grant. Digests form a one-way chain: metadata/forest/notice, then parity evidence, then the final manifest/archive.
- Private packages cannot use ordinary export. Packaging/distribution tests reject dataset, Joblib/pickle, serving NPZ, offline archives, caches, qualification environments, and model payload signatures from Git/wheels/sdists/native/Docker layers.

### Serving format and adapter

- `serving-metadata.json` contains format/schema versions, 37 ordered input features with units/origins/ranges, transformed order, log/binary partitions, imputation policy, means/scales, class order, threshold, near-threshold band, training-population bounds, numeric rules, source/conversion identities, and forest-array digest. It contains no downstream parity or final-package digest.
- `forest.npz` contains fixed numeric dtypes only: tree offsets, globally rebased left/right children, feature indexes, thresholds, and normalized two-class leaf values. Loader uses `allow_pickle=False`, bounded headers/bytes, exact allowlisted members, and validation of topology, reachability, indexes, finite values, class fractions, tree/node counts, and metadata digest.
- The adapter accepts 1-100 exact candidate records, validates order/name/unit/origin/range/finite values, transforms in declared order, casts the tree matrix to float32, traverses each tree, averages chatter-class leaf fractions, and returns deterministic per-candidate results. It never imports scikit-learn or executes source code.
- Out-of-contract input fails the call. In-range but outside the recorded training population returns `out_of_population`; scores in the declared band return `near_threshold`; neither is eligible for preference. The threshold rule is explicit and the score is always labelled uncalibrated.

### Provider-neutral Rivet evidence

- Capability Binding version 2 gains versioned provider evidence whose `kind` is `mcp` or `engineering_model`. The version-1 class/schema/resource and its server-shaped fields remain readable and byte-stable. Version-aware construction writes version 2 for new review, digests the provider evidence, and treats an old reviewed binding as legacy evidence rather than silently reinterpreting it.
- MCP evidence contains server/tool/revision/schema/validation identities. Model evidence contains model/package/variant/artifact-set/installation/adapter/runtime/test/workspace-binding/task/schema/threshold/resource identities. Gateway discovery supplies the evidence; workflow selection cannot invent or override it.
- New `run-manifest-v2.schema.json` and `capability-binding-v2.schema.json` resources record provider evidence per binding and child call. Restart/reproduction comparison treats provider material as deterministic and timing/resources/trace observations as non-material. The Loop 069 version-1 schema files remain byte-for-byte unchanged and supported for prior inspection/comparison; new reviews and runs write version 2 and select their exact schema by the declared version.
- Cancellation remains authority-first and provider-neutral: the gateway sends cancel to active MCP or model providers, discards late completion, then closes the session and records residue state.

### Scenario graph and report

- Scenario manifest version 1.1 adds domain `model`, capability `provider_kind`, model evidence requirements, candidate/report artifact kinds, and a `chatter_advisory` assertion plugin registered through the existing duplicate-safe extension seam. The Loop 070 version 1.0 schema/resource stays byte-for-byte available; catalog validation selects the schema by the declared version.
- Deterministic CAD fixture emits workpiece/tool envelope and invariant facts. Deterministic simulated CAM fixture emits three or more fully typed candidate batches and non-model invariants but no G-code. The model node receives exactly that artifact's candidate list.
- The advisory normalizer correlates candidate IDs and child receipts, excludes failed invariants and non-applicable model results, and chooses at most one lowest-score discrete candidate for human review. It never labels a candidate safe, interpolates a stability region, or creates new parameters.
- The report includes all candidates, model results, selected-for-review/rejected reasons, invariant outcomes, units, simulation-only/calibration/applicability/limitations notices, exact provider/artifact/workflow evidence, cleanup, and reproducibility. It rejects commands, endpoints, credentials, host paths, authority, private rows, and payload bytes.

### API, UI, and recovery

- Existing thin scenario endpoints return the extended generic preflight/report shapes. Preflight names the capability kind, readiness facts, required versus available resources, stale identities, and stable recovery actions.
- The scenario library shows CAD/CAM/model composition and blocks start until exact review. The report presents the simulation-only banner, uncalibrated score/threshold/margin, applicability, invariant failures, selected-for-review status, evidence, and cleanup. Status never relies on color alone.
- Missing package, failed vectors, stale binding, incompatible host, insufficient resources, crash, timeout, cancellation, and residue use stable provider-neutral categories and recovery steps. A failed/cancelled run cannot publish an advisory result.
- Keyboard, focus, 320 CSS pixel, 200% zoom, cancel, retry, evidence, comparison, and export journeys receive component and Playwright coverage with no serious/critical accessibility findings.

### Bounded records and deterministic evidence

- Candidate batch: 1-100 candidates, exactly 37 features each, identities <=128 bytes, units/origins from fixed enums, finite float64 JSON values, encoded request <=512 KiB. Adapter output <=1 MiB and scenario report/evidence <=2 MiB.
- Forest: exactly two classes, 1-500 trees, 1-1,000,000 total nodes, max depth 25, artifact <=256 MiB, metadata <=1 MiB, finite float64 preprocessing/threshold/leaf arrays, int32 topology/index arrays, no object/string arrays in NPZ.
- Material digests cover workflow/scenario/provider/package/adapter/vector/fixture/schema/input/result/assertion/artifact identities and numeric values. Timestamps, trace/request IDs, observed memory/timing, and host diagnostic text are observations and cannot change material reproduction claims.
- Structured events and spans include bounded scenario/run/node/provider/call/candidate/result/cancellation/cleanup identities. They exclude candidate feature values, private-row scores, model arrays, source locations on disk, credentials, commands, and reusable authority.

## Gate D Chatter Decision

[Gate D](contracts/gate-d-chatter-decision.md) approves the internal-only source record, explicit local retraining/export boundary, narrow `wright-chatter-forest-npz` representation, NumPy adapter, parity criteria, generated normal-gate fixtures, generic provider evidence, and advisory-only scenario design. Approval does not grant public redistribution, does not approve Joblib/pickle/Skops/generic ONNX loading, and does not authorize a real model package until its exact local conversion evidence passes. Gate E remains closed: no model or scenario output may generate or execute machine instructions or physical action.

## Post-design Constitution Re-check

All pre-design passes remain valid after the contracts: private data/model bytes remain outside Git and distributions; installation does not train or deserialize code; runtime mediation remains Wright-owned and manager-neutral; MCP and model calls share gateway authority without identity conflation; state is embedded; normal tests are offline and generated; routes/UI remain generic; and physical actuation is structurally forbidden.

## Complexity Tracking

No exception is required. A narrow Chatter forest adapter is smaller and safer than adding a generic arbitrary-model loader or a serving framework. Versioned provider evidence is required because preserving the legacy fiction that every gateway capability is an MCP server would make review and reproduction misleading.
