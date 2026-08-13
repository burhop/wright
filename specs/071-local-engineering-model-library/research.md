# Research: Local Engineering Model Library

## Scope and method

Research used primary product, format, security, and standards sources plus Wright's existing gateway, capability catalog, persistence, and native-runtime code. The goal is a safe model supply chain and typed engineering capability—not a general Hugging Face browser or an in-process Python notebook.

## Decision 1: Resolve and pin immutable source identity

**Decision**: Preview may resolve a friendly model/revision name, but a confirmed plan records the full source revision, every selected path, expected size, SHA-256 digest, and aggregate maximum. Download uses only that immutable identity.

**Evidence**: Hugging Face supports exact commits in `hf_hub_download` and `snapshot_download`, cache reuse, file allow/ignore filters, offline lookup, and a dry-run view of downloads ([download guide](https://huggingface.co/docs/huggingface_hub/guides/download)). Repository metadata exposes the commit SHA, gating/private/disabled state, siblings, and file metadata ([Hub API reference](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api)).

**Rationale**: A model name or branch can move between preview and transfer. Confirmation must bind the effect, not just the label.

**Alternatives rejected**:

- Install `main` or a tag directly: mutable and not reproducible.
- Let a runtime fetch its own files: bypasses Wright's plan, checksum, storage, and audit boundary.
- Download an entire repository by default: can acquire undeclared code, history, or excess files.

## Decision 2: Treat publisher metadata as discovery evidence

**Decision**: Model cards seed task, license, limitations, training/evaluation, and publisher claims, but Wright independently validates exact artifacts, authoritative license evidence, compatibility, runtime, resources, and test vectors before approval.

**Evidence**: Hugging Face describes model cards as metadata and documentation for intended uses, limitations, training, and evaluation, including license tags or custom license links ([model cards](https://huggingface.co/docs/hub/model-cards), [model card metadata](https://huggingface.co/docs/hub/model-card-metadata)). SPDX defines machine-readable license expressions and `LicenseRef` handling ([SPDX 3.0.1 license expressions](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/)).

**Rationale**: A tag is useful discovery input but does not prove that every file is redistributable, safe to deserialize, compatible, or useful for Wright's declared task.

**Alternatives rejected**:

- Trust a license tag alone: insufficient artifact-level evidence.
- Reject any non-standard expression: custom terms can be represented as review-blocked `LicenseRef` plus evidence.
- Infer limitations from framework/task tags: those tags are too coarse for engineering units, geometry conventions, or validity ranges.

## Decision 3: Public and offline first; never accept gated terms

**Decision**: Wright may explain that content is gated or private, but never requests access, accepts terms, or discloses identity. If a user independently gains access, a new plan may reference an explicitly stored fine-grained read-only token. Tokens never enter model state, logs, evidence, runtimes, or exports.

**Evidence**: Gated access is granted per user and may share requester identity/contact with the publisher; publishers can manually approve or revoke access ([gated models](https://huggingface.co/docs/hub/models-gated)). Hugging Face recommends fine-grained tokens and distinguishes fine-grained, read, and write roles ([user access tokens](https://huggingface.co/docs/hub/security-tokens)).

**Rationale**: License/access acceptance is a personal or organizational decision outside Wright's authority. Secret references also preserve revocation and redaction.

**Alternatives rejected**:

- Automate access requests or checkbox acceptance: unauthorized external action.
- Store a token in the package/export: leaks authority and prevents safe sharing.
- Pass the token to the runtime: the runtime needs verified local bytes, not source credentials.

## Decision 4: Data-only format allowlist and explicit adapters

**Decision**: Prefer Safetensors and policy-validated ONNX. Block pickle/PyTorch `.bin`/`.pth`, joblib, source code, executable archives, native libraries, plugins, macros, and remote code as model data. A legacy format requires an explicit format/adaptor review; there is no generic bypass.

**Evidence**: Hugging Face recommends Safetensors over pickle and documents pickle scanning as defense-in-depth rather than a guarantee because pickle can execute arbitrary code ([repository security](https://huggingface.co/docs/hub/security-pickle), [Safetensors audit](https://huggingface.co/blog/safetensors-security-audit)). PyTorch warns never to load data from an untrusted source and notes that restricted loading does not eliminate denial-of-service risks ([`torch.load`](https://docs.pytorch.org/docs/stable/generated/torch.load.html)). ONNX's threat model covers traversal, links, external-data path injection, and resource exhaustion ([external-data security](https://onnx.ai/onnx/repo-docs/ExternalDataSecurity.html)); ONNX Runtime advises safe inspection/testing of untrusted models ([security guidance](https://onnxruntime.ai/docs/tutorials/web/security.html)).

**Rationale**: A model file is untrusted input. The safe default is a minimal parser/runtime surface plus strict bounds, not publisher popularity.

**Alternatives rejected**:

- Rely on malware/pickle scans: scanners cannot prove non-execution or bounded resources.
- Expose `trust_remote_code`: converts the library into a code installer.
- Convert unsafe formats inside normal install: conversion executes a parser/runtime before trust is established and changes artifact identity.

## Decision 5: Runtime is a separately approved capability

**Decision**: Model install and runtime-adapter install are separate effect plans. A package declares an exact adapter contract/version and may remain blocked until it is present. The adapter runs as a supervised local child with typed load/infer/cancel/unload messages and bounded resources/output.

**Evidence**: ONNX Runtime separates model execution from hardware Execution Providers and publishes distinct platform/provider packages ([Execution Providers](https://onnxruntime.ai/docs/execution-providers/)). This makes provider availability a deployment decision, not a property that can be inferred from a model file.

**Rationale**: Silently installing TensorFlow, PyTorch, CUDA, compilers, drivers, or services makes storage/security effects unpredictable and undermines rollback. Separate identity also makes evidence reproducible.

**Alternatives rejected**:

- Install framework dependencies during model install: hidden and often very large mutation.
- Import the framework in the API process: runtime crashes or native-library conflicts would destabilize Wright.
- Run arbitrary per-repository Python: no stable contract and an unacceptable code-execution boundary.

## Decision 6: Content-addressed, staged, atomic storage

**Decision**: Stream downloads/imports into operation-specific staging, verify exact size and SHA-256, then atomically promote immutable objects by digest. An installation is a transactional manifest/reference projection over verified content. Mutable partials, verified content, active installations, quarantine, and exports are distinct.

**Rationale**: Content addressing supports zero-byte cache reuse, deduplication, deterministic export, rollback, and safe crash recovery. Database references—not directory existence—define installation visibility.

**Alternatives rejected**:

- Store files directly in model-named folders: duplicate bytes and partial installs can appear ready.
- Hard-link user-supplied content: later mutation or link attacks can change verified content.
- Delete on uninstall unconditionally: breaks workflows, retained runs, exports, and rollback.

## Decision 7: Conservative resume and redirect policy

**Decision**: Resume only when the immutable URL/revision, strong ETag or Last-Modified validator, existing length, expected total, and `206 Content-Range` agree. Otherwise restart. Accept only HTTPS policy-approved redirects and re-evaluate credentials on host changes.

**Evidence**: HTTP Range, `If-Range`, partial responses, validators, and redirect semantics are specified by RFC 9110 ([HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)).

**Rationale**: Appending bytes from a changed representation can produce corrupt state; the final digest catches it but wastes time and complicates evidence. Credentials must not follow an unapproved host.

**Alternatives rejected**:

- Always resume by byte count: unsafe without a representation validator.
- Follow all redirects: can leak tokens or downgrade transport.
- Depend only on final hash: detects corruption too late and does not bound redirects/bytes.

## Decision 8: Gateway-mediated dynamic model capabilities

**Decision**: Add a generic `GatewayCapabilityProvider` seam. A model provider lists and calls typed namespaced capabilities only when one exact healthy installation is enabled for the immutable workspace session. GatewayService continues to apply policy, approvals, audit, bounds, cancellation, and teardown.

**Rationale**: Rivet needs to call models in workflows, but it must not receive runtime connection details or launch the adapter. This is the same authority principle established for MCPs while retaining accurate model semantics.

**Alternatives rejected**:

- Let Rivet launch/contact the runtime: duplicates lifecycle and bypasses workspace authority/audit.
- Represent a model as an MCP server row: corrupts catalog/lifecycle semantics and complicates removal/reference policy.
- Add static management tools only at API startup: installed/enabled models are dynamic and workspace-scoped.

## Decision 9: External candidate assessment

### Provisional candidate: `keras-io/PointNet`

**Exact revision**: `308acfe5d36d9bb34215d1766f13fac612abe18c`

**Positive evidence**:

- Public, ungated, enabled repository tagged Apache-2.0 and `tf-keras`.
- Model card and official Keras example describe PointNet classification over ModelNet10 point clouds ([repository](https://huggingface.co/keras-io/PointNet/tree/308acfe5d36d9bb34215d1766f13fac612abe18c), [Keras example](https://keras.io/examples/vision/pointnet/)).
- Small artifact set: `keras_metadata.pb` 227,087 bytes; `saved_model.pb` 2,086,305 bytes; variables data 3,064,233 bytes; variables index 6,215 bytes. Exact SHA-256 values are recorded in Gate D.

**Open blockers**:

- The repository has Apache metadata but no standalone license file in the selected artifact list.
- TensorFlow SavedModel is a legacy, framework-specific runtime requiring a separately approved adapter/dependency plan.
- A deterministic labelled test vector and CPU resource envelope must be produced against the exact artifact rather than inferred from the example.

**Decision**: Evaluation-only at planning time. It is useful as a realistic acquisition/trust candidate but is not installable until every Gate D blocker closes. The architecture does not depend on it.

### Alternatives assessed

- `OneScience-Group/PointNetCFD` at `b871dbaa879f2ce38a56a0f0a28fdd99444dcc2e`: blocked for the first slice because it includes required Python source and a 42.8 MB pickle-style `.pth` artifact.
- `ilessio-aiflowlab/project_sif` at `242147772e1831dfc3e6ee598e844d3d9971c5b4d`: data-only ONNX/Safetensors options but very low public maturity and insufficient independent inference/limitation evidence; defer for later review.
- `ilessio-aiflowlab/project_vidar` at `025223bffac38f738d82c2948d79c22ef8280b4d`: small data-only artifacts but similarly low maturity; defer.
- HouseCAD detector at `c71f42dcac2be377c698e43da26123b6f633d29e`: specialized ONNX candidate with insufficient first-slice evidence; defer.

## Decision 10: Deterministic first runtime

**Decision**: Generate a tiny affine-regression artifact and vectors during tests, import it through the same package/storage path, and execute it in a separate deterministic adapter process. The bundled catalog carries the recipe and expected digests for generated test fixtures, not weight bytes.

**Rationale**: This proves the complete lifecycle, typed inference, process isolation, cancellation, workspace binding, offline behavior, update/rollback, and reference-safe cleanup without a network or ML framework. It does not falsely imply that the fixture is a production engineering model.

**Alternatives rejected**:

- Commit even tiny binary weights: weakens the repository rule and makes provenance less obvious.
- Use an in-process fake: would not prove adapter supervision and late-result cancellation.
- Make external availability a normal-gate dependency: nondeterministic and incompatible with offline CI.
