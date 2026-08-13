# Gate D Decision: Model Supply Chain and Runtime Boundary

**Decision date**: 2026-08-13

**Authority**: Advance authorization in the Wright Engineering Capability Program goal

**Outcome**: **PASSED — NEURALFOIL MEDIUM APPROVED; POINTNET REMAINS EVALUATION-ONLY**

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

## Rejected baseline: `keras-io/PointNet`

### Recorded source identity

- Repository: `keras-io/PointNet`
- Full revision: `308acfe5d36d9bb34215d1766f13fac612abe18c`
- Source state observed during research: public, ungated, enabled, `tf-keras`, Apache-2.0 metadata
- Declared task: PointNet classification over ModelNet10 point clouds

### Candidate artifact facts

| Path                                      |   Bytes | SHA-256                                                            |
| ----------------------------------------- | ------: | ------------------------------------------------------------------ |
| `keras_metadata.pb`                       |  227087 | `49de5bb4c0894223b551f658c63a0930b52be488419c2927ea9c7f25ced26822` |
| `saved_model.pb`                          | 2086305 | `2924bd9cb2435445398f8e86ebc2522df96251b6f9b4dd73e695bd89e24a6411` |
| `variables/variables.data-00000-of-00001` | 3064233 | `15d3ba92731f58a4f88938b6fc84f034be34b7dcf5dffeebe287a0bf1a40479c` |
| `variables/variables.index`               |    6215 | `87a5668ed6f992d2233dba73419abda6a51fd6b4c484f69b02e27fddb5e708d7` |

These are research observations to be independently verified by the source adapter before use. README/history/image files are not implicitly selected.

### Closed condition

PointNet remains `needs_review` / evaluation-only. It was not selected for the first approved external package because the legacy TensorFlow SavedModel boundary, missing standalone selected-artifact license, undeclared label/vector material, and disproportionate runtime footprint did not close safely. It may become `approved` only when a future implementation evidence record proves all of the following against the exact revision and bytes:

1. authoritative Apache-2.0 license/attribution evidence is sufficient for local use and the chosen export/redistribution projection despite no standalone license file in the selected model artifact set;
2. the four selected files are sufficient and no repository code, plugin, macro, native artifact, hidden download, unsafe deserializer, or undeclared file is required;
3. a separately planned, installed, and conformance-tested TensorFlow SavedModel adapter supports the artifact on a declared CPU platform without mutating Wright's base environment;
4. exact download, installed-disk, RAM, load-time, inference-time, and output limits are measured conservatively;
5. input point count/order/type/normalization, coordinate convention, output label order, confidence semantics, intended use, and limitations are explicit;
6. real deterministic labelled test vectors pass repeatedly offline against the downloaded artifact, with exact input/output digests and declared tolerance;
7. cancellation, bad input, resource rejection, adapter crash, unload, and cleanup paths pass with no late success or residue hidden;
8. cache reuse transfers zero bytes and uninstall/purge preserve all declared references.

No general contract was weakened to admit PointNet. NeuralFoil was selected as the safer replacement.

## Approved external package: `neuralfoil-medium`

### Primary-source identity

- Repository and immutable revision: [`peterdsharpe/NeuralFoil@bb8a775199d1dafb5f410e68e027ba6eca1af9bc`](https://github.com/peterdsharpe/NeuralFoil/tree/bb8a775199d1dafb5f410e68e027ba6eca1af9bc).
- Release identity: NeuralFoil 0.3.3, as declared by the exact revision's [`pyproject.toml`](https://github.com/peterdsharpe/NeuralFoil/blob/bb8a775199d1dafb5f410e68e027ba6eca1af9bc/pyproject.toml) and the publisher's [PyPI project](https://pypi.org/project/neuralfoil/0.3.3/).
- License: the exact revision's [MIT `LICENSE.txt`](https://github.com/peterdsharpe/NeuralFoil/blob/bb8a775199d1dafb5f410e68e027ba6eca1af9bc/LICENSE.txt), copyright 2023-2023 Peter Sharpe. No external acceptance or access request is required.
- Engineering basis: the publisher describes NeuralFoil as a physics-informed airfoil aerodynamics surrogate trained on nearly eight million XFoil runs, with pure NumPy runtime inference; the [official paper](https://arxiv.org/abs/2503.16323) documents the model and validation context.
- Test authority: the exact revision's [`test_golden_values.py`](https://github.com/peterdsharpe/NeuralFoil/blob/bb8a775199d1dafb5f410e68e027ba6eca1af9bc/tests/test_golden_values.py) publishes the fixed Kulfan input and cross-platform-tolerant medium-model outputs used by Wright.

### Selected artifact boundary

Only these three immutable public files are model-package artifacts. The raw-source bytes, not a line-ending-converted checkout, are authoritative.

| Path                                  |  Bytes | SHA-256                                                            |
| ------------------------------------- | -----: | ------------------------------------------------------------------ |
| `LICENSE.txt`                         |   1074 | `f3a3857f0bfab1733bcea48be8b6f1ad2c43176f855362cdd6c334a360a93450` |
| `model/nn-medium.npz`                 | 103467 | `6cae229ce9ab9df0c3c68a1a441fae529a78481409d6b3ac4baf17ee58715952` |
| `model/scaled_input_distribution.npz` |   7696 | `63a33149c902ad01ecf537dd2d127d9e7ffbf86527893f4dc76f25f7087a3573` |

Total acquisition and installed-content ceiling: **112,237 bytes**. No `.py`, `.pth`, training log, repository archive, native library, executable, plugin, or mutable tag is selected. In particular, the publisher repository's PyTorch training checkpoints are prohibited and excluded.

### Runtime and vector decision

The separately reviewed `wright-neuralfoil-numpy` adapter version `1.0.0` implements only the published direct-Kulfan encode, medium MLP, symmetry, confidence, and coefficient decode boundary. It:

- requires the optional `engineering-models` NumPy extra instead of mutating the base runtime;
- reads the two selected NPZ artifacts with `allow_pickle=False` and exact key/shape/finite-number checks;
- does not import or execute the NeuralFoil repository, AeroSandbox, PyTorch, training code, or remote code;
- accepts one bounded 8+8-weight Kulfan case and returns only confidence, `CL`, `CD`, `CM`, and upper/lower transition locations;
- runs behind Wright's isolated stdio supervisor and Gateway capability provider with no source credential or workspace authority.

The official golden vector at alpha 5 degrees and Reynolds number 1,000,000 passed at relative tolerance `1e-6`. Wright and the official PyPI 0.3.3 runtime independently returned the same values:

| Output                |               Observed |
| --------------------- | ---------------------: |
| `analysis_confidence` |   `0.9557118377834403` |
| `CL`                  |   `1.1033280967904384` |
| `CD`                  | `0.009198824384558149` |
| `CM`                  | `-0.11059803045101073` |
| `Top_Xtr`             |  `0.25054349678066945` |
| `Bot_Xtr`             |   `0.9648784090579786` |

The model remains an XFoil surrogate, not certification evidence. Confidence is not a calibrated error probability. Wright intentionally excludes coordinate fitting, AeroSandbox extensions, compressibility, post-stall, and control-surface features from this first adapter.

### Gate D result

`neuralfoil-medium` is approved as the first public external engineering-model package. Approval is for the exact revision, selected bytes, Wright adapter version, schema, resource ceiling, limitations, and mandatory vector only. Hosts without the optional NumPy runtime show the approved package as incompatible/runtime-missing rather than offering installation. Full lifecycle evidence is recorded in `docs/model-evidence/external-model-validation-2026-08-13.md`.

## Rollback

The model-library feature can be disabled at API composition, navigation, and gateway-provider registration. Existing conversational model setup, MCP catalog/server management, GatewayService MCP tools, and Rivet MCP workflows continue unchanged. Migration 16 and verified content may remain inert for forward compatibility; destructive schema rollback is not required. Uncommitted opt-in external bytes remain under `.local-run/` and are removed through their bounded test cleanup.

## Gate result rationale

The provider-neutral architecture, deterministic fixture, and selected NeuralFoil package are sufficiently specified, reversible, offline-testable, and consistent with the Wright constitution. PointNet remains outside the approved boundary. Gate D is closed for Loop 071 without granting authority to any other third-party model, runtime, or artifact.
