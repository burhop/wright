# Local Engineering Models

Wright's Engineering Models library manages small deterministic fixtures and reviewed local engineering-model data packages. It is separate from conversational model setup and from the MCP catalog. Rivet never receives a runtime command, process handle, endpoint, host path, or reusable authority: a tested model becomes a typed workspace capability only through Wright's existing governed Gateway.

## Trust boundary

A package is data and metadata, not an installer. It may declare exact model data, license/attribution, deterministic test inputs, and expected results. It cannot install Python packages, drivers, compilers, services, containers, plugins, macros, native libraries, or remote code. Runtime adapters have a separate review and lifecycle.

Normal validation is offline and CPU-first. It requires no credential, paid service, proprietary application, GPU, hardware, license acceptance, or physical actuation. Model weights and downloaded model repositories stay outside Git under Wright's owned data root or an ignored `.local-run/` probe root.

## First reviewed external model

The first approved public package is `neuralfoil-medium`, pinned to [`peterdsharpe/NeuralFoil@bb8a775199d1dafb5f410e68e027ba6eca1af9bc`](https://github.com/peterdsharpe/NeuralFoil/tree/bb8a775199d1dafb5f410e68e027ba6eca1af9bc). It estimates bounded subsonic airfoil coefficients from direct eight-weight-per-side Kulfan parameters. The package selects only the MIT license, 103,467-byte medium NPZ weights, and 7,696-byte scaled-input distribution. Wright does not select or execute the repository source, PyTorch `.pth` training checkpoints, AeroSandbox extensions, or any mutable revision.

The adapter requires the separately chosen NumPy runtime extra:

```console
pip install "wright-engineering[engineering-models]"
```

Without that extra, the catalog entry remains inspectable but reports `runtime_missing`; installing a model never installs NumPy implicitly. The adapter uses `np.load(..., allow_pickle=False)`, exact array keys and shapes, finite-number checks, a private artifact copy, bounded JSON stdio, deadlines, cancellation, and cleanup. Gate D provenance, digests, limitations, and official golden-vector values are recorded in `specs/071-local-engineering-model-library/contracts/gate-d-decision.md` and the [external validation evidence](../model-evidence/external-model-validation-2026-08-13.md).

NeuralFoil is a physics-informed surrogate primarily trained against XFoil, not certification-grade CFD or experimental evidence. `analysis_confidence` is an out-of-distribution indicator, not a calibrated probability of accuracy. The first Wright adapter deliberately excludes coordinate fitting, compressibility, post-stall, and control-surface features.

## Author a package

Start from the versioned JSON contracts in `packages/model_registry/src/model_registry/schemas/` and the generated affine example in `packages/model_registry/src/model_registry/catalog/`. A package identity is the exact tuple of model ID, package revision, variant ID, and manifest digest. Never change an existing revision in place.

Each package must declare:

- an immutable publisher/source revision and access state;
- complete SPDX-compatible license evidence, attribution, redistribution state, and any external acceptance requirement;
- typed analysis-only tasks with bounded JSON input/output schemas, units, and coordinate convention where material;
- one or more independently compatible variants with reviewed data-only format, exact platform/architecture/provider requirements, and bounded disk/RAM/VRAM/time/output resources;
- every artifact path, role, media type, exact byte size, SHA-256 digest, immutable source, and redistribution flag;
- material limitations and mandatory deterministic vectors that exercise them;
- an exact compatible adapter contract/version and declarative expected predicates.

Approved package artifacts are limited to reviewed data-only formats. ONNX and Safetensors are the general preferred formats; `wright-affine-json` exists only for Wright's tiny deterministic fixture. Pickle-family files, framework checkpoints that execute code, Python/source archives, native libraries, executables, plugins, macros, scripts, and `trust_remote_code` are prohibited.

## Generate fixtures without weights

Tests must generate tiny model bytes from explicit constants beneath a caller-owned temporary directory. Generate the manifest and artifacts together, compute sizes and SHA-256 digests from the resulting bytes, and use fixed ZIP timestamps, ordering, permissions, and compression. Do not copy a public model's weights into a fixture and do not commit generated archives.

The generated affine fixture is the reference pattern: coefficients are canonical JSON, input and expected output are canonical JSON, the license is a tiny text artifact, and the adapter is deterministic. The richer fault adapter is test-only and is not registered in production.

## Public extension registries

`model_registry.extensions` exposes duplicate-safe registries for packages, source adapters, runtime adapters, and declarative predicates. Registration never replaces an existing identity. A package is accepted only after static conformance proves its license linkage, paths/formats, source adapter, exact adapter version/capabilities, task/vector schema digests, limitations, and predicate identities.

Use model-specific code only inside a separately reviewed source or runtime adapter. Do not add model IDs or special cases to `EngineeringModelService`, the HTTP routes, Rivet, or the Gateway.

## Validate locally

Static package validation reads one bounded local JSON manifest. It does not contact its source or acquire content:

```console
uv run wright models validate-catalog path/to/engineering-model-package.json
```

Static adapter validation reads a declaration but does not start its command:

```console
uv run wright models validate-adapter path/to/adapter.json
```

Both commands return bounded JSON with `passed`, a stable identity, findings, recovery guidance, and a deterministic report digest. A passing static result is not permission to run or install the adapter.

For full conformance, use `run_package_conformance` with bytes produced by a deterministic local fixture generator. It additionally rejects undeclared artifacts and size/digest changes. Runtime conformance uses the supervised private protocol and generated artifacts only after the adapter itself has been reviewed.

## Adapter review

An adapter registration declares an exact adapter and contract version, formats, tasks, platforms, architectures, execution providers, message ceiling, and a private command. Reviewers must verify health identity, artifact verification, load/infer schemas, monotonic redacted progress, deadlines, cancellation, late-result suppression, unload, shutdown, and residue cleanup.

The supervisor launches adapters with an isolated interpreter, minimal environment, private read-only artifact copy, bounded JSON stdio, absolute deadlines, and an owned scratch directory. Adapters do not receive source credentials or Wright workspace authority. A process exit is not engineering evidence; every mandatory vector must pass and be durably linked to the exact installation, artifact set, adapter version, schemas, seed, units/coordinates, limitations, and environment policy.

## License and redistribution review

Install eligibility and export eligibility are separate. A package may be inspectable while download, install, or export remains blocked. Before approval, record the authoritative license source, exact license artifact/digest, attribution, whether acceptance is required, and whether every artifact is redistributable. Private/gated sources and any non-redistributable artifact fail deterministic export.

Offline export contains only the public manifest and declared redistributable artifacts. It excludes secrets, credentials, private paths, host diagnostics, runtime commands, bindings, workspace authority, and model payloads not explicitly declared for redistribution. Re-import performs the same path, size, digest, license, format, and undeclared-file checks as acquisition.

## Update, rollback, and removal

Revision comparison covers license, redistribution, artifacts, adapter, schemas, units, coordinates, resources, vectors, and limitations. A successor does not replace the working revision until its exact artifacts and standard vectors pass; activation is transactional. Rollback reuses verified cached bytes but invalidates prior readiness and requires a fresh standard test in the current adapter/environment.

Disable first removes workspace use. Uninstall removes active visibility while retaining verified bytes needed by workflows, runs, evidence, or exports. Purge is available only after uninstall and only when no active durable reference, other installation, or unexpired runtime lease holds the content. The preview reports exact reclaimable bytes. References may be explicitly detached or archived; Wright never silently breaks reproducibility.

## Rivet use

After installation and mandatory testing, an engineer explicitly enables one task for one workspace. Wright projects it as `wright_model__<model-id>__<task>` with exact binding, installation, adapter, evidence, schema, and policy digests. Rivet discovers and calls that tool through the same short-lived run-bound Gateway used for MCP capabilities. Cancellation and session close flow back through Wright to the private adapter supervisor.

Physical actuation remains outside the model capability gate. Model tasks may analyze or recommend engineering results, but they cannot command a spindle, printer, robot, PLC, motor, heater, extruder, or machine axis.
