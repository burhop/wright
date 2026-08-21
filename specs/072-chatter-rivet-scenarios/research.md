# Research: Chatter and Model-Enabled Rivet Scenarios

## Scope and method

Research covered the immutable private Chatter source, current Data Vault qualification evidence, Wright's Loop 069-071 gateway/Rivet/scenario/model seams, and primary scikit-learn and NumPy documentation. The selected design minimizes trusted code, keeps all normal gates offline, and separates a real private-model qualification from generated CI evidence.

## Decision 1: Treat the source as private internal evidence

**Decision**: Pin `burhop/chatter` at `4eeb36dbfede3c194c43b3d2039abd5860a675f6`, Dataset 2 at SHA-256 `1d7880d3fd321a86885c825003bfc8c1ba3ccd15cf0e0e7b9c283a48b0d51d5f`, and the Data Vault feature-095 CPU recipe: the exact 37-feature order, `GroupShuffleSplit(test_size=0.2, random_state=42)` by `dataset_id`, 96/24 train/validation groups with zero overlap, training-only preprocessing, and Random Forest `n_estimators=500`, `max_depth=25`, `min_samples_split=10`, `min_samples_leaf=5`, `max_features=sqrt`, `class_weight=balanced`, `criterion=gini`. The deterministic split identities are emitted and frozen by qualification. Label the resulting package `LicenseRef-Wright-Internal-Chatter`, `offline_only`, and redistribution prohibited until an owner decision supplies broader terms.

**Rationale**: The authenticated source is private and reports no license metadata or license/notice file. The README and model card describe a simulated CNC chatter classifier and explicitly limit real-time/real-sensor applicability. “Our model” is enough to continue local internal qualification, not enough to grant public redistribution.

**Evidence**:

- Private source: `https://github.com/burhop/chatter/tree/4eeb36dbfede3c194c43b3d2039abd5860a675f6`
- Data Vault qualification: `D:/repos/data_vault/specs/095-chatter-model-building-vertical-slice/`
- Frozen real-data evidence: `D:/repos/data_vault/specs/095-chatter-model-building-vertical-slice/evidence/gb10-real-data-proof.json`
- Current parity contract: `D:/repos/data_vault/tests/live_integration/model_builder/test_chatter_parity.py`

**Alternatives rejected**:

- Public catalog package: no redistribution grant.
- Gated web acquisition: unnecessary and privacy-widening for a user-owned local source.
- Invented license or attribution: unsupported by evidence.

## Decision 2: Retrain explicitly; never load Joblib in Wright

**Decision**: The trusted qualification command retrains the exact deterministic recipe from immutable local Dataset 2 bytes and exports a separate serving representation. Wright installation and runtime never load the existing Joblib/pickle pipeline, contact Data Vault, or install converter dependencies.

**Rationale**: The source saves `model.joblib` and `scaler.joblib`. scikit-learn states that pickle-family loading can execute arbitrary code and generally requires the training environment. Retraining from immutable reviewed inputs avoids treating a serialized Python object as a package boundary and supplies exact conversion evidence.

**Primary source**: [scikit-learn model persistence](https://scikit-learn.org/stable/model_persistence.html)

**Alternatives rejected**:

- Joblib/pickle: arbitrary-code boundary and version coupling.
- Cloud/MLflow conversion: violates offline/private/bounded requirements.
- Training during install: makes package identity non-deterministic and silently expands effects.

## Decision 3: Use a narrow numeric NPZ format, not generic ONNX or Skops

**Decision**: Define `wright-chatter-forest-npz-1.0`: one strict JSON metadata file plus one NPZ containing only fixed numeric arrays for a binary Random Forest. Load with `allow_pickle=False`; reject unexpected members, object arrays, unsafe dtypes, invalid topology, non-finite values, and resource excess.

**Rationale**: NumPy documents that `allow_pickle=False` avoids object unpickling and recommends it for security/portability. ONNX would add a broad interpreter/runtime and can represent arbitrary computations; scikit-learn recommends sandboxing ONNX against computation/memory exploits. Skops restores Python estimator objects and a same-version serving environment. The selected classifier needs only a few explicit arrays and equations.

**Primary sources**:

- [NumPy `load`](https://numpy.org/doc/stable/reference/generated/numpy.load.html)
- [NumPy file I/O guidance](https://numpy.org/doc/stable/user/how-to-io.html)
- [scikit-learn model persistence and ONNX security](https://scikit-learn.org/stable/model_persistence.html)

**Alternatives rejected**:

- Generic ONNX: wider operator/runtime attack and resource surface than this use case needs.
- Skops: still reconstructs a Python object graph and couples serving to scikit-learn.
- Safetensors: good tensor container but no standard tree topology/metadata semantics; NPZ is already supported by the reviewed model library and NumPy adapter pattern.
- JSON-only trees: unnecessarily large and slow for hundreds of trees.

## Decision 4: Encode exact preprocessing and forest semantics

**Decision**: Export the ordered 37-feature contract, the ColumnTransformer output order, six log-feature and five binary-feature partitions, imputation constants, StandardScaler means/scales, class order `[0,1]`, float32 tree input behavior, split topology/thresholds, normalized leaf class fractions, and decision threshold. Serving follows `left if x <= threshold`, averages tree chatter-class fractions, and classifies `chatter` when `score >= threshold`.

**Rationale**: Data Vault's reviewed pipeline uses `log1p(max(x,0))`, training-only StandardScaler, and ordered ColumnTransformer concatenation. scikit-learn documents `z=(x-u)/s`, the output concatenation order, its float32 tree input conversion, tree structure arrays, and Random Forest probability as the mean of per-tree leaf class fractions.

**Primary sources**:

- [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [ColumnTransformer](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html)
- [RandomForestClassifier probability semantics](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html)
- [Decision tree structure arrays](https://scikit-learn.org/stable/auto_examples/tree/plot_unveil_tree_structure.html)

**Alternatives rejected**:

- Reimplementing feature extraction from machine/tool configuration: widens the first slice and can silently change training semantics.
- Relying on dictionary insertion order: too weak for a safety-relevant feature contract.
- Majority votes only: differs from scikit-learn's mean probability semantics.

## Decision 5: Freeze conversion parity and boundary evidence

**Decision**: Bind source revision, dataset/membership/recipe/environment/exporter identities and serving artifact digest into one parity record. Compare trusted and serving outputs on the frozen qualification population plus explicit stable, chatter, threshold-adjacent, malformed, range, order, unit, resource, and cancellation vectors. Require >=99.5% class agreement, mean absolute score delta <=0.01, max delta <=0.05, reload determinism, and zero mandatory boundary class disagreement.

**Rationale**: Aggregate agreement can hide a safety-relevant boundary regression. Per-row delta facts and mandatory vectors make the conversion falsifiable and ensure an exporter/runtime change becomes a new reviewed revision.

**Evidence**: Data Vault feature 095 records the selected 80/20 recipe, 96/24 group counts, zero overlap, real metrics, and known first-row score in `D:/repos/data_vault/specs/095-chatter-model-building-vertical-slice/evidence/gb10-real-data-proof.json`. Data Vault's later generic model-builder parity test independently supplies the accepted score-delta/reload gates; its separate config-matched membership is not substituted for the selected package recipe.

**Alternatives rejected**:

- Metrics-only approval: does not prove serving equivalence.
- Random samples only: can miss deterministic boundary regressions.
- Exact byte equality across retraining environments: too strict for separately evidenced toolchain changes and not a substitute for output parity.

## Decision 6: One cold batch per model gateway call

**Decision**: Accept 1-100 candidates per call and use the existing model runtime lifecycle: verify, load, infer, unload, and shutdown. Do not retain a warm Chatter process across calls in this loop.

**Rationale**: Batching amortizes load while preserving existing resource admission, request cancellation, session close, and cleanup. Warm reuse would add lease expiry, stale binding, multi-run resource, and restart complexity before measured evidence justifies it.

**Alternatives rejected**:

- One process per candidate: needless repeated load cost.
- Run-global singleton: over-broad lifetime and resource ownership.
- Direct in-process evaluation in the gateway: weakens runtime isolation/cancellation.

## Decision 7: Make units, order, origin, and score semantics explicit

**Decision**: A candidate contains an ordered list of 37 records with exact feature name, finite numeric value, unit, and origin (`simulated`, `identified`, `measured`, or `assumed`). Results preserve order and return `stable|chatter`, `chatter_score`, threshold, signed margin, `uncalibrated`, applicability, warnings, and evidence. Near-threshold or out-of-population results require review and cannot be preferred.

**Rationale**: A JSON object cannot reliably express a deliberate positional contract to a reviewer. Named list entries make duplicates, reorderings, wrong units, and origin mismatches visible. The Random Forest score is a model output, not a calibrated real-world safety probability.

**Alternatives rejected**:

- Calling the output confidence/probability of safety: unsupported calibration claim.
- Accepting partial/defaulted features: hides assumptions and changes inference.
- Continuous stability interpolation: outside the model's evidence and requested safety scope.

## Decision 8: Record provider kind without splitting execution paths

**Decision**: Extend capability binding and Run Manifest evidence with `provider_kind` and a versioned provider-specific identity block. MCP blocks retain server/tool/validation facts; engineering-model blocks retain model/package/variant/artifact/installation/adapter/test/task/threshold/resource facts. Both remain ordinary gateway capabilities to Rivet.

The Loop 069 version-1 JSON Schema resources remain byte-for-byte immutable. Loop 072 adds separate Capability Binding and Run Manifest version-2 resources and version-aware readers; it does not replace the archived v1 contracts or silently upgrade prior evidence.

**Rationale**: Loop 071 already provides a generic `GatewayCapabilityProvider`; the existing Rivet discovery and call path works for model tools. The missing piece is truthful evidence: `wright-models` must not be presented to an engineer as an MCP server. A generic evidence union preserves one authority/cancellation path without identity conflation.

**Alternatives rejected**:

- Direct Rivet-to-model process connection: leaks lifecycle/endpoints and bypasses Wright review.
- Fake MCP server identity: misleading provenance and recovery.
- Chatter-specific runner node: breaks extensibility and collision safety.

## Decision 9: Build an advisory-only CAD/CAM/model scenario

**Decision**: Add `chatter-candidate-review`, a Tier-1 graph with deterministic CAD context MCP, simulated CAM candidate MCP, and the enabled model capability. It evaluates exactly the returned discrete candidates, carries all non-model invariants forward, and may select one lowest-score eligible candidate only “for human review.”

**Rationale**: This is the smallest multi-domain workflow that proves model capabilities compose with MCPs. Static CAD and simulated CAM fixtures keep normal gates proprietary-free. Selection remains subordinate to geometry/tool reach/force/clearance facts and never becomes a machine prescription.

**Alternatives rejected**:

- G-code generation or controller integration: Gate E prohibits physical actuation and executable machine instructions.
- Real CAM/CAD in normal gates: proprietary and host-dependent.
- Ranking every numerically scored candidate: would hide failed invariants or applicability warnings.

## Decision 10: Separate generated CI proof from real private proof

**Decision**: Normal tests generate a tiny Chatter-shaped forest and deterministic CAD/CAM artifacts under temporary directories. A separately selected ignored test performs real local conversion/import/test/bind/Rivet/report lifecycle using caller-supplied ignored paths. Distribution scans prove neither payload enters Git or shipped artifacts.

**Rationale**: Normal gates must be fast, offline, reproducible, and redistributable; the real package is private and potentially tens of megabytes. The same public contracts and adapter are exercised in both paths, so the generated proof is meaningful without claiming real-model qualification.

**Alternatives rejected**:

- Committing a reduced private forest: still a private model payload and not exact evidence.
- Skipping normal model-enabled scenario coverage: would make the generic path fragile.
- Making real qualification mandatory in CI: requires unavailable private inputs and a training environment.
