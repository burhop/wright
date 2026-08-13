# Data Model: Chatter and Model-Enabled Rivet Scenarios

## 1. Chatter source record

Discovery-only catalog record for the private source before a serving package exists.

| Field | Type | Rules |
| --- | --- | --- |
| `model_id` | string | `wright-chatter-internal`; stable catalog identity |
| `owner` | string | Wright project support boundary; not a public license grant |
| `source_revision` | 40-char digest | Exact private Git revision |
| `dataset_digest` | SHA-256 | Exact immutable Dataset 2 bytes |
| `membership_digest` | SHA-256 or absent | Exact reviewed split membership; absent blocks conversion approval |
| `recipe_id` / `recipe_digest` | string / SHA-256 | Exact training/preprocessing/parameter contract |
| `terms` | object | Internal-use, offline-only, non-redistributable |
| `evidence` | facet states | Source/data may be cached; serving/runtime/test absent until qualification |
| `blockers` | bounded list | Missing local conversion, terms decision, incompatible runtime, or stale evidence |

The source record is never installable. It must not contain source rows, host paths, credentials, model bytes, or an artifact digest guessed before conversion.

## 2. Chatter serving metadata

Semantic declaration paired with one numeric forest artifact.

| Field | Type | Rules |
| --- | --- | --- |
| `format_version` | const `wright-chatter-forest-npz-1.0` | Adapter allowlist key |
| `model_id` / `package_revision` / `variant_id` | identity | Must match package manifest |
| `source` | identity object | Source revision, dataset, membership, recipe, environment, exporter, and qualification identities; no downstream evidence digest |
| `input_contract` | ordered feature list | Exactly 37 unique features; name, meaning, unit, allowed origins, contract bounds, population bounds |
| `preprocessing` | object | Exact transform output order, log/binary partitions, imputation constants, means, scales, numeric precision |
| `classifier` | object | Binary Random Forest; class order `[0,1]`; tree/node/depth ceilings; forest array digest |
| `decision` | object | Chatter class `1`, threshold, `>=` rule, near-threshold band, score label `uncalibrated` |
| `resources` | object | Artifact/RAM/load/inference/output/batch ceilings |
| `limitations` | list | Simulated population, no calibration, no stability interpolation, no machine authority |
| `metadata_digest` | SHA-256 | Canonical digest excluding itself |

### Forest numeric arrays

`forest.npz` contains only allowlisted fixed numeric arrays:

- `tree_offsets`: `int64`, length `tree_count + 1`, first 0, final `node_count`, strictly increasing.
- `children_left`, `children_right`: `int32`, length `node_count`; both `-1` for a leaf, otherwise valid globally rebased child indexes inside the same tree.
- `feature`: `int16` or `int32`, length `node_count`; split nodes reference the transformed feature range.
- `threshold`: finite `float64`, length `node_count`; meaningful only for split nodes.
- `leaf_class_fraction`: finite `float64`, shape `(node_count, 2)`; leaf rows are non-negative and sum to one within tolerance.

Semantic validation requires one reachable acyclic root per tree, no cross-tree edge, no orphan, depth no greater than 25, 1-500 trees, at most 1,000,000 nodes, and no unexpected archive member or object dtype.

## 3. Conversion parity evidence

Immutable proof that a locally produced serving package is equivalent enough to the trusted evaluator.

| Field | Type | Rules |
| --- | --- | --- |
| `evidence_id` / `schema_version` | identity | Stable and versioned |
| `source_identity` | object | Source, dataset, membership, recipe, environment and trusted evaluator identities |
| `serving_identity` | object | Exporter, metadata, forest, pre-package material, adapter and runtime identities |
| `population` | object | Frozen partition/count/digest facts, never rows or feature values |
| `metrics` | object | Class agreement, mean/max absolute score delta, reload delta, counts |
| `boundary_results` | list | Vector identity, source/serving class, score delta, mandatory flag, pass/fail |
| `checks` | bounded list | Structure, order, finiteness, unit, malformed, resource and cancellation predicates |
| `material_digest` | SHA-256 | Deterministic evidence only |
| `observation_digest` | SHA-256 | Timing, observed resources, host/toolchain diagnostics |
| `status` | enum | `passed`, `failed`, `blocked` |

`passed` requires class agreement >=0.995, mean delta <=0.01, max delta <=0.05, reload delta within declared tolerance, zero group overlap, and every mandatory boundary/check pass. Digest construction is acyclic: serving metadata and forest are finalized first; parity evidence binds those plus a pre-package material digest that excludes parity evidence; the final package manifest then binds metadata, forest, and parity evidence as exact artifacts.

## 4. Cutting candidate batch

Typed request produced by simulated CAM or a caller.

| Field | Type | Rules |
| --- | --- | --- |
| `schema_version` | const `1.0` | Exact task contract |
| `feature_order` | const array | Exact 37-name order |
| `units` | const array | Exact unit corresponding to every ordered name |
| `candidates` | array | 1-100 items, stable order and unique identities |
| `batch_provenance` | object | Simulation-only producer/tool/artifact/schema identities |

Each candidate contains:

- `candidate_id`: unique bounded identity.
- `values`: exactly 37 finite JSON numbers in declared order.
- `origins`: exactly 37 values from `simulated`, `identified`, `measured`, or `assumed`.
- `source_artifact_id`: authorized producing artifact.
- `engineering_invariants`: bounded pass/fail facts with evidence references; never machine commands.

Contract-bound violations fail the complete model call. Population-bound violations are valid inputs but yield explicit `out_of_population` applicability.

## 5. Chatter result batch

Deterministic model output preserving candidate order.

Each result contains:

- candidate identity and position;
- predicted state `stable` or `chatter`;
- `chatter_score`, exact threshold, and signed `score - threshold` margin;
- calibration status fixed to `uncalibrated_model_score`;
- applicability `in_population`, `near_threshold`, or `out_of_population`;
- `review_required` and `eligible_for_preference` flags;
- bounded warning and limitation identifiers;
- exact package/variant/artifact/installation/adapter/runtime/test/task/schema/threshold evidence.

The batch carries input/output/material digests. It contains no input feature values, private source row identity, host path, credential, model array, or runtime authority.

## 6. Provider evidence

Provider-neutral identity block attached to each reviewed Rivet capability binding and Run Manifest entry.

It is written only by Capability Binding and Run Manifest version 2. The Loop 069 version-1 schemas and records remain immutable legacy MCP-shaped evidence; readers select the exact schema by declared version and never infer model identity for version 1.

### Common fields

`schema_version`, `provider_kind`, `provider_id`, `capability_id`, `capability_digest`, `schema_digest`, `validation_evidence_id`, `binding_digest`, and `resource_class`.

### MCP provider

`provider_kind=mcp` plus server identity/revision, tool name, validation evidence and workspace grant.

### Engineering model provider

`provider_kind=engineering_model` plus model/package/variant/artifact-set, installation, adapter/runtime, mandatory-test evidence, task, threshold and workspace model-binding identities.

The union is discriminated and closed. A model cannot populate MCP fields or vice versa. Any provider material change invalidates the reviewed binding.

## 7. Chatter scenario manifest

Version 1.1 scenario declaration extending the existing generic manifest.

| Field | Rules |
| --- | --- |
| `domains` | Includes `cad`, `cam`, and `model` |
| `capabilities` | One deterministic CAD MCP, one simulated CAM MCP, one exact engineering-model tool; each declares `provider_kind` |
| `candidate_contract` | Exact batch schema and producer/consumer nodes |
| `artifacts` | CAD context, candidate batch, model result, advisory report |
| `assertions` | Geometry/tool reach/force/clearance, candidate correlation, applicability, advisory safety, provenance, cleanup |
| `environment` | Tier 1: no network, credentials, proprietary app, GPU, hardware, large download |
| `safety` | `physical_actuation=false`, `static_outputs_only=true`, no executable machine instructions |

## 8. Chatter advisory report

Bounded immutable scenario outcome.

| Field | Type | Rules |
| --- | --- | --- |
| Scenario/workflow identities | object | Manifest, graph, workflow, review, binding-set and policy digests |
| `candidate_outcomes` | list | Correlated model result plus every non-model invariant and rejection reason |
| `selected_for_review` | identity or null | At most one discrete eligible candidate; never called safe/recommended for machining |
| `notices` | fixed object | Simulation-only, uncalibrated score, applicability, limitations, human review, no machine authority |
| `provider_evidence` | list | Exact MCP and model blocks |
| `artifacts` / `assertions` | bounded lists | Authorized digests and pass/fail facts |
| `cleanup` | object | Clean or possible residue plus recovery |
| `material_digest` | SHA-256 | Stable reproduction material |
| `observations` | object | Non-material timing/resource/trace facts |

No report is published for a failed or cancelled model call. A candidate is ineligible when any required invariant fails, applicability is not `in_population`, or threshold review is required.

## 9. State transitions

### Real package qualification

```text
source-record
  -> qualification-running
  -> conversion-failed | parity-failed | package-produced
  -> imported
  -> verified
  -> tested
  -> ready
  -> enabled
```

Every transition binds the exact prior identities. A change creates a fresh qualification/package revision; it never updates an active revision in place.

### Scenario

```text
catalogued
  -> prepared
  -> preflight-blocked | reviewed
  -> running
  -> cancelling -> cancelled-clean | cancelled-residue
  -> failed
  -> passed
```

Only `passed` may contain a complete advisory report. Cancellation revokes authority before provider cancellation and ignores late completion.

## 10. Identity and comparison policy

Material comparison includes source, package, adapter, vector, provider, schema, workflow, scenario, fixture, candidate input, result, assertion, artifact, and policy digests. Timing, observed resource consumption, trace/request IDs, timestamps, and host diagnostic text are non-material observations. Any missing or changed material identity makes exact reproduction false and requires review.
