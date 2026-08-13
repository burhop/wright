# Gate D Decision: Model Supply Chain and Runtime Boundary

**Decision date**: 2026-08-13

**Authority**: Advance authorization in the Wright Engineering Capability Program goal

**Outcome**: **APPROVED WITH A CLOSED EXTERNAL-MODEL CONDITION**

## Approved for implementation

1. A separate `model_registry` domain package and dedicated Engineering Models UI, distinct from conversational model setup and the MCP catalog.
2. Versioned model package, variant, artifact, install-plan, operation, test-vector, runtime-adapter, evidence, reference, and workspace-binding contracts.
3. Full immutable revision pinning plus explicit selected paths, byte sizes, SHA-256 digests, license/attribution, typed task schemas, resources, limitations, and test vectors.
4. A strict data-only policy. Pickle-family files, repository/source code, native libraries, executables, macros, plugins, shell commands, and remote-code execution remain blocked without a future separate governance change.
5. Staged, bounded, content-addressed acquisition/import; digest verification; atomic activation; cache deduplication; crash reconciliation; quarantine; leases; and reference-safe uninstall/purge.
6. Separate runtime-adapter lifecycle. Model installation cannot implicitly add a framework, driver, compiler, service, container, or global dependency.
7. A supervised typed adapter protocol with resource admission, schema validation, deadlines, cancellation, late-result suppression, unload/shutdown, and residue evidence.
8. A generic GatewayCapabilityProvider so Rivet and other reviewed workspace clients can discover/call exact enabled model tasks only through GatewayService policy, approval, audit, bounds, cancellation, and immutable workspace binding.
9. A generated deterministic affine fixture and separate test adapter for complete offline normal-gate lifecycle evidence. The fixture is generated in temporary test state; no weights are committed.
10. Candidate and blocked catalog entries that honestly explain missing license/runtime/evidence, incompatible hardware, gated/private access, or unsafe files without presenting them as ready.

## Prohibited by this decision

- Downloading a mutable branch/tag after confirmation.
- Running a repository install script or `trust_remote_code`.
- Loading pickle, `.pth`, joblib, or equivalent executable deserialization as approved model data.
- Passing source tokens to runtimes or persisting them in model state/evidence/export.
- Accepting gated terms, requesting access, purchasing service, or installing global/runtime dependencies as part of a model plan.
- Exposing runtime commands, endpoints, file paths, process handles, or direct connections to Rivet.
- Treating model-card tags, malware scans, process exit zero, or one variant's evidence as readiness proof.
- Deleting content with an active installation, binding, workflow, retained run, export, operation, evidence, or lease reference.
- Adding model weights to Git or making external downloads part of normal gates.

## External candidate: `keras-io/PointNet`

### Recorded source identity

- Repository: `keras-io/PointNet`
- Full revision: `308acfe5d36d9bb34215d1766f13fac612abe18c`
- Source state observed during research: public, ungated, enabled, `tf-keras`, Apache-2.0 metadata
- Declared task: PointNet classification over ModelNet10 point clouds

### Candidate artifact facts

| Path | Bytes | SHA-256 |
|------|------:|--------|
| `keras_metadata.pb` | 227087 | `49de5bb4c0894223b551f658c63a0930b52be488419c2927ea9c7f25ced26822` |
| `saved_model.pb` | 2086305 | `2924bd9cb2435445398f8e86ebc2522df96251b6f9b4dd73e695bd89e24a6411` |
| `variables/variables.data-00000-of-00001` | 3064233 | `15d3ba92731f58a4f88938b6fc84f034be34b7dcf5dffeebe287a0bf1a40479c` |
| `variables/variables.index` | 6215 | `87a5668ed6f992d2233dba73419abda6a51fd6b4c484f69b02e27fddb5e708d7` |

These are research observations to be independently verified by the source adapter before use. README/history/image files are not implicitly selected.

### Closed condition

PointNet remains `needs_review` / evaluation-only. It may become `approved` only when an implementation evidence record proves all of the following against the exact revision and bytes:

1. authoritative Apache-2.0 license/attribution evidence is sufficient for local use and the chosen export/redistribution projection despite no standalone license file in the selected model artifact set;
2. the four selected files are sufficient and no repository code, plugin, macro, native artifact, hidden download, unsafe deserializer, or undeclared file is required;
3. a separately planned, installed, and conformance-tested TensorFlow SavedModel adapter supports the artifact on a declared CPU platform without mutating Wright's base environment;
4. exact download, installed-disk, RAM, load-time, inference-time, and output limits are measured conservatively;
5. input point count/order/type/normalization, coordinate convention, output label order, confidence semantics, intended use, and limitations are explicit;
6. real deterministic labelled test vectors pass repeatedly offline against the downloaded artifact, with exact input/output digests and declared tolerance;
7. cancellation, bad input, resource rejection, adapter crash, unload, and cleanup paths pass with no late success or residue hidden;
8. cache reuse transfers zero bytes and uninstall/purge preserve all declared references.

If any condition cannot be met safely and proportionately, PointNet remains blocked or is replaced by a better public data-only candidate. No general contract may be weakened to admit it.

## Rollback

The model-library feature can be disabled at API composition, navigation, and gateway-provider registration. Existing conversational model setup, MCP catalog/server management, GatewayService MCP tools, and Rivet MCP workflows continue unchanged. Migration 16 and verified content may remain inert for forward compatibility; destructive schema rollback is not required. Uncommitted opt-in external bytes remain under `.local-run/` and are removed through their bounded test cleanup.

## Gate result rationale

The provider-neutral architecture and deterministic slice are sufficiently specified, reversible, offline-testable, and consistent with the Wright constitution. Approving them allows implementation without granting authority for an inadequately evidenced third-party runtime. The closed condition is a trust boundary, not an optional follow-up.
