# Gate D Decision: Wright Chatter and Model-Enabled Rivet Scenarios

**Date**: 2026-08-13
**Status**: Approved with explicit real-package qualification condition
**Gate E**: Closed

## Approved

- Private source identity pinned to `burhop/chatter` revision `4eeb36dbfede3c194c43b3d2039abd5860a675f6` and Dataset 2 SHA-256 `1d7880d3fd321a86885c825003bfc8c1ba3ccd15cf0e0e7b9c283a48b0d51d5f`.
- Conservative `LicenseRef-Wright-Internal-Chatter`, offline-only, non-redistributable treatment pending an explicit owner decision.
- Explicit trusted local retraining/export from immutable inputs; no training or conversion during installation.
- Narrow `wright-chatter-forest-npz-1.0` data-only format and separately reviewed NumPy adapter.
- `allow_pickle=False`, exact member/dtype/shape/topology/finiteness/resource validation, and no scikit-learn serving dependency.
- Parity thresholds: class agreement >=99.5%, mean score delta <=0.01, max score delta <=0.05, zero mandatory boundary class disagreement, zero split overlap, deterministic reload.
- Generated normal-gate forest and CAD/CAM fixtures; real private proof remains explicit and ignored.
- Provider-neutral gateway/Rivet evidence that distinguishes MCPs from engineering models without creating a second execution authority path.
- Advisory-only Tier-1 CAD/CAM/Chatter scenario comparing caller-supplied discrete simulated candidates.

## Not approved

- Joblib, pickle, cloudpickle, estimator object, source-code, repository, plugin, macro, native-library or `trust_remote_code` loading.
- Generic ONNX or Skops loading in this slice.
- Public redistribution, external catalog publication, license acceptance, or transfer of private source/data/model/evaluation rows.
- Dynamic feature extraction, stability-lobe interpolation, continuous optimization, training UI, production controller integration, or online monitoring.
- Any G-code, controller instruction, feed/spindle override, axis movement, physical actuation, or claim of real-world safety probability/certification.

## Real-package approval condition

No exact Chatter package is `approved`, `ready`, or enabled until a local qualification run binds all source, data, membership, recipe, environment, exporter, artifact, package, adapter and vector identities and every parity/boundary requirement passes. A generated fixture proves implementation only and must never be presented as real Chatter qualification.

## Rollback

Disable the workspace model binding and scenario, revoke active run authority, remove the package reference, uninstall the revision, and purge only after reference/lease checks. Retained run evidence remains inspectable. No source data or private serving payload is deleted by Wright unless the user separately authorizes removal from the user-owned output location.
