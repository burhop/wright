"""Small deterministic generated artifacts used by Wright's normal model gates."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from importlib.resources import files

from .models import ModelPackage, canonical_digest, canonical_json


def affine_artifacts(package: ModelPackage) -> dict[str, bytes]:
    """Regenerate the reviewed affine fixture and verify every declared identity."""

    if package.model_id != "wright-affine-test":
        raise ValueError("The package has no built-in deterministic generator")
    coefficients = {"offset": 1.0, "scale": 2.0}
    values = {
        "LICENSE": b"MIT License\n\nCopyright Wright Project contributors.\n",
        "model/coefficients.json": canonical_json(coefficients).encode("utf-8"),
        "tests/predict-two-input.json": canonical_json({"x": 2.0}).encode("utf-8"),
        "tests/predict-two-expected.json": canonical_json({"y": 5.0}).encode("utf-8"),
    }
    declarations = {
        item.path: item for variant in package.variants for item in variant.artifacts
    }
    if set(values) != set(declarations):
        raise ValueError("Generated artifact declarations changed")
    for path, value in values.items():
        declaration = declarations[path]
        if (
            len(value) != declaration.size
            or hashlib.sha256(value).hexdigest() != declaration.sha256
        ):
            raise ValueError("Generated artifact identity changed")
    return values


def _deterministic_npz(arrays: dict[str, object]) -> bytes:
    import numpy as np

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, value in sorted(arrays.items()):
            member = io.BytesIO()
            np.lib.format.write_array(member, np.asarray(value), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, member.getvalue())
    return output.getvalue()


def _chatter_documents() -> tuple[dict, dict[str, bytes]]:
    """Build a tiny redistributable proof forest, never a real Chatter payload."""

    import numpy as np

    from .chatter_contracts import (
        CHATTER_ADAPTER_ID,
        CHATTER_ADAPTER_VERSION,
        CHATTER_FORMAT,
        CHATTER_TASK_ID,
        FEATURE_ORDER,
        FEATURE_UNITS,
        LOG_FEATURES,
        BINARY_FEATURES,
        PREPROCESSING_ORDER,
    )
    from .chatter_runtime import predict_batch

    forest = _deterministic_npz(
        {
            "tree_offsets": np.asarray([0, 3, 6], dtype=np.int64),
            "children_left": np.asarray([1, -1, -1, 4, -1, -1], dtype=np.int32),
            "children_right": np.asarray([2, -1, -1, 5, -1, -1], dtype=np.int32),
            "feature": np.asarray([0, -2, -2, 0, -2, -2], dtype=np.int32),
            "threshold": np.asarray(
                [5.0, -2.0, -2.0, 5.0, -2.0, -2.0], dtype=np.float64
            ),
            "leaf_class_fraction": np.asarray(
                [0.0, 0.1, 0.9, 0.0, 0.1, 0.9], dtype=np.float64
            ),
        }
    )
    forest_digest = hashlib.sha256(forest).hexdigest()
    meanings = {name: name.replace("_", " ") for name in FEATURE_ORDER}
    binary = set(BINARY_FEATURES)
    features = []
    for name, unit in zip(FEATURE_ORDER, FEATURE_UNITS, strict=True):
        if name in binary:
            contract_min, contract_max, population_min, population_max = (
                0.0,
                2.0,
                0.0,
                2.0,
            )
        else:
            contract_min, contract_max, population_min, population_max = (
                -1e15,
                1e15,
                -1e9,
                1e9,
            )
        features.append(
            {
                "name": name,
                "meaning": meanings[name],
                "unit": unit,
                "allowed_origins": ["simulated", "identified", "measured", "assumed"],
                "contract_min": contract_min,
                "contract_max": contract_max,
                "population_min": population_min,
                "population_max": population_max,
            }
        )
    metadata = {
        "schema_version": "1.0",
        "format": CHATTER_FORMAT,
        "model_id": "wright-chatter-generated-test",
        "package_revision": 1,
        "variant_id": "generated-forest-cpu-f64",
        "source": {
            "source_revision": "4eeb36dbfede3c194c43b3d2039abd5860a675f6",
            "dataset_digest": "1d7880d3fd321a86885c825003bfc8c1ba3ccd15cf0e0e7b9c283a48b0d51d5f",
            "membership_digest": canonical_digest({"fixture": "generated-membership"}),
            "recipe_digest": canonical_digest({"fixture": "two-stump-forest"}),
            "environment_lock_digest": canonical_digest(
                {"fixture": "numpy-contract-1"}
            ),
            "exporter_digest": canonical_digest(
                {"fixture": "wright-generated-exporter-1"}
            ),
            "qualification_id": "generated-normal-gate-only",
        },
        "input_contract": features,
        "preprocessing": {
            "input_order": list(FEATURE_ORDER),
            "output_order": list(PREPROCESSING_ORDER),
            "log_features": list(LOG_FEATURES),
            "binary_features": list(BINARY_FEATURES),
            "missing_value_policy": "reject_input; qualification-imputer-constant-zero-recorded-only",
            "means": [0.0] * 32,
            "scales": [1.0] * 32,
            "tree_input_dtype": "float32",
        },
        "classifier": {
            "family": "binary_random_forest",
            "classes": [0, 1],
            "tree_count": 2,
            "node_count": 6,
            "max_depth": 1,
            "forest_member": "model/forest.npz",
            "forest_sha256": forest_digest,
            "arrays": {
                "tree_offsets": "int64",
                "children_left": "int32",
                "children_right": "int32",
                "feature": "int32",
                "threshold": "float64",
                "leaf_class_fraction": "float64",
            },
        },
        "decision": {
            "positive_class": 1,
            "threshold": 0.5,
            "comparison": "score_greater_than_or_equal_is_chatter",
            "near_threshold_band": 0.05,
            "score_semantics": "mean_tree_leaf_chatter_fraction",
            "calibration_status": "uncalibrated_model_score",
        },
        "resources": {
            "maximum_artifact_bytes": 2 * 1024 * 1024,
            "maximum_ram_bytes": 256 * 1024 * 1024,
            "load_timeout_ms": 5000,
            "inference_timeout_ms": 3000,
            "maximum_output_bytes": 1024 * 1024,
            "maximum_batch": 100,
        },
        "limitations": [
            "generated-proof-only",
            "uncalibrated-screening",
            "no-machine-authority",
        ],
    }
    metadata["metadata_digest"] = canonical_digest(metadata)
    metadata_bytes = canonical_json(metadata).encode()
    notice = (
        "WRIGHT INTERNAL-USE NOTICE\n\n"
        "This generated normal-gate package is not the private Chatter model. "
        "No public license file or license metadata was located for the private source. "
        "The real local qualification is conservatively internal-only and non-redistributable.\n"
    ).encode()
    material_digest = canonical_digest(
        {
            "notice": hashlib.sha256(notice).hexdigest(),
            "metadata": hashlib.sha256(metadata_bytes).hexdigest(),
            "forest": forest_digest,
        }
    )
    source = {
        "source_revision": metadata["source"]["source_revision"],
        "dataset_digest": metadata["source"]["dataset_digest"],
        "membership_digest": metadata["source"]["membership_digest"],
        "recipe_digest": metadata["source"]["recipe_digest"],
        "environment_lock_digest": metadata["source"]["environment_lock_digest"],
        "trusted_evaluator_digest": canonical_digest(
            {"fixture": "generated-evaluator"}
        ),
    }
    parity = {
        "schema_version": "1.0",
        "evidence_id": "generated-normal-gate-parity",
        "source_identity": source,
        "serving_identity": {
            "exporter_digest": metadata["source"]["exporter_digest"],
            "metadata_digest": metadata["metadata_digest"],
            "forest_digest": forest_digest,
            "package_material_digest": material_digest,
            "adapter_id": CHATTER_ADAPTER_ID,
            "adapter_version": CHATTER_ADAPTER_VERSION,
        },
        "population": {
            "row_count": 2,
            "group_count": 2,
            "partition_digest": canonical_digest({"fixture": ["stable", "chatter"]}),
            "input_digest": canonical_digest({"fixture": "inputs"}),
            "source_output_digest": canonical_digest({"fixture": "source-output"}),
            "serving_output_digest": canonical_digest({"fixture": "serving-output"}),
            "group_overlap_count": 0,
        },
        "metrics": {
            "class_agreement": 1.0,
            "mean_absolute_score_delta": 0.0,
            "maximum_absolute_score_delta": 0.0,
            "reload_maximum_score_delta": 0.0,
            "class_disagreement_count": 0,
            "mandatory_boundary_disagreement_count": 0,
        },
        "boundary_results": [
            {
                "vector_id": "generated-stable",
                "mandatory": True,
                "source_state": "stable",
                "serving_state": "stable",
                "absolute_score_delta": 0.0,
                "state": "passed",
            },
            {
                "vector_id": "generated-chatter",
                "mandatory": True,
                "source_state": "chatter",
                "serving_state": "chatter",
                "absolute_score_delta": 0.0,
                "state": "passed",
            },
        ],
        "checks": [
            {
                "check_id": "generated-data-only",
                "state": "passed",
                "evidence_digest": material_digest,
                "message": "Tiny generated proof; not real qualification evidence.",
            }
        ],
        "status": "passed",
    }
    parity["material_digest"] = canonical_digest(parity)
    parity["observation_digest"] = canonical_digest(
        {"material_digest": parity["material_digest"], "host": "generated"}
    )
    parity_bytes = canonical_json(parity).encode()
    artifacts = {
        "INTERNAL-USE-NOTICE.txt": notice,
        "evidence/conversion-parity.json": parity_bytes,
        "model/forest.npz": forest,
        "model/serving-metadata.json": metadata_bytes,
    }
    artifact_digests = {
        name: hashlib.sha256(value).hexdigest()
        for name, value in sorted(artifacts.items())
    }
    artifact_set_digest = canonical_digest(artifact_digests)
    input_schema = json.loads(
        files("model_registry.schemas")
        .joinpath("chatter-candidate-batch.schema.json")
        .read_text(encoding="utf-8")
    )
    output_schema = json.loads(
        files("model_registry.schemas")
        .joinpath("chatter-result-batch.schema.json")
        .read_text(encoding="utf-8")
    )
    values = [0.0] * len(FEATURE_ORDER)
    vector_input = {
        "schema_version": "1.0",
        "feature_order": list(FEATURE_ORDER),
        "units": list(FEATURE_UNITS),
        "candidates": [
            {
                "candidate_id": "generated-stable",
                "values": values,
                "origins": ["simulated"] * len(FEATURE_ORDER),
                "source_artifact_id": "generated-candidates",
                "engineering_invariants": [
                    {
                        "invariant_id": "fixture-clearance",
                        "state": "pass",
                        "evidence_artifact_id": "generated-cad-context",
                    }
                ],
            }
        ],
        "batch_provenance": {
            "simulation_only": True,
            "producer_tool": "fixture_cam__generate_candidates",
            "producer_artifact_id": "generated-candidates",
            "producer_schema_digest": canonical_digest(input_schema),
        },
    }
    expected = predict_batch(
        vector_input,
        metadata,
        {
            "tree_offsets": np.asarray([0, 3, 6], dtype=np.int64),
            "children_left": np.asarray([1, -1, -1, 4, -1, -1], dtype=np.int32),
            "children_right": np.asarray([2, -1, -1, 5, -1, -1], dtype=np.int32),
            "feature": np.asarray([0, -2, -2, 0, -2, -2], dtype=np.int32),
            "threshold": np.asarray(
                [5.0, -2.0, -2.0, 5.0, -2.0, -2.0], dtype=np.float64
            ),
            "leaf_class_fraction": np.asarray(
                [0.0, 0.1, 0.9, 0.0, 0.1, 0.9], dtype=np.float64
            ),
        },
        {
            "model_id": metadata["model_id"],
            "package_revision": 1,
            "variant_id": metadata["variant_id"],
            "artifact_set_digest": artifact_set_digest,
            "installation_digest": artifact_set_digest,
            "adapter_id": CHATTER_ADAPTER_ID,
            "adapter_version": CHATTER_ADAPTER_VERSION,
            "runtime_version": "numpy-compatible-1",
            "test_evidence_id": "runtime-unbound",
            "task_id": CHATTER_TASK_ID,
            "input_schema_digest": artifact_set_digest,
            "output_schema_digest": artifact_set_digest,
            "threshold": 0.5,
        },
    )
    artifact_rows = []
    roles = {
        "INTERNAL-USE-NOTICE.txt": ("license", "text/plain"),
        "evidence/conversion-parity.json": ("metadata", "application/json"),
        "model/forest.npz": ("model_data", "application/vnd.numpy.npz"),
        "model/serving-metadata.json": ("metadata", "application/json"),
    }
    for path, value in sorted(artifacts.items()):
        role, media_type = roles[path]
        artifact_rows.append(
            {
                "path": path,
                "role": role,
                "media_type": media_type,
                "size": len(value),
                "sha256": artifact_digests[path],
                "source_uri": f"wright://generated/chatter/{path}",
                "redistributable": False,
            }
        )
    package = {
        "schema_version": "1.0",
        "model_id": metadata["model_id"],
        "package_revision": 1,
        "display_name": "Wright Generated Chatter Contract Model",
        "description": "Tiny deterministic forest that exercises Chatter contracts without private model or dataset bytes.",
        "publisher": {
            "name": "Wright Project",
            "source_uri": "https://github.com/burhop/wright",
        },
        "source": {
            "kind": "offline",
            "uri": "wright://generated/chatter-contract",
            "immutable_revision": "generated-fixture-revision-1",
            "access": "offline_only",
            "allowed_hosts": [],
        },
        "tasks": [
            {
                "task_id": CHATTER_TASK_ID,
                "description": "Screen supplied discrete simulated cutting candidates for human review.",
                "input_schema": input_schema,
                "output_schema": output_schema,
                "units": dict(zip(FEATURE_ORDER, FEATURE_UNITS, strict=True)),
                "coordinate_convention": "Feature values use the exact ordered Data Vault Chatter process contract; no machine coordinates or commands are accepted.",
            }
        ],
        "license": {
            "expression": "LicenseRef-Wright-Internal-Chatter",
            "evidence": [
                {
                    "kind": "artifact",
                    "location": "INTERNAL-USE-NOTICE.txt",
                    "sha256": artifact_digests["INTERNAL-USE-NOTICE.txt"],
                }
            ],
            "attribution": "Wright-generated contract proof. The private Chatter source has no public redistribution grant recorded.",
            "redistribution": "prohibited",
            "acceptance_required": False,
        },
        "limitations": [
            {
                "limitation_id": "generated-proof-only",
                "description": "This tiny forest proves contracts only and is not the real Chatter classifier.",
                "severity": "critical",
            },
            {
                "limitation_id": "uncalibrated-screening",
                "description": "Scores are uncalibrated screening outputs, not safety probabilities or guarantees.",
                "severity": "critical",
            },
            {
                "limitation_id": "no-machine-authority",
                "description": "Results select only supplied candidates for human review and carry no machining authority.",
                "severity": "critical",
            },
        ],
        "remote_code_policy": "forbidden",
        "review_state": "approved",
        "variants": [
            {
                "variant_id": metadata["variant_id"],
                "format": CHATTER_FORMAT,
                "precision": "f64-metadata-f32-tree-input",
                "platforms": [
                    "linux/x86_64",
                    "linux/aarch64",
                    "windows/x86_64",
                    "macos/aarch64",
                ],
                "accelerator": "cpu",
                "runtime": {
                    "adapter_id": CHATTER_ADAPTER_ID,
                    "contract_version": "1.0",
                    "version_specifier": "==1.0.0",
                },
                "resources": {
                    "download_bytes": sum(len(value) for value in artifacts.values()),
                    "installed_bytes": sum(len(value) for value in artifacts.values()),
                    "ram_bytes": 256 * 1024 * 1024,
                    "vram_bytes": 0,
                    "load_timeout_ms": 5000,
                    "inference_timeout_ms": 3000,
                    "max_output_bytes": 1024 * 1024,
                },
                "artifacts": artifact_rows,
                "test_vectors": [
                    {
                        "schema_version": "1.0",
                        "vector_id": "generated-stable-batch",
                        "version": 1,
                        "task_id": CHATTER_TASK_ID,
                        "input_schema_sha256": canonical_digest(input_schema),
                        "output_schema_sha256": canonical_digest(output_schema),
                        "deterministic_seed": 0,
                        "units": dict(zip(FEATURE_ORDER, FEATURE_UNITS, strict=True)),
                        "coordinate_convention": "Feature values use the exact ordered Data Vault Chatter process contract; no machine coordinates or commands are accepted.",
                        "input": vector_input,
                        "expected": {"kind": "exact", "value": expected},
                        "limitations_exercised": [
                            "generated-proof-only",
                            "uncalibrated-screening",
                            "no-machine-authority",
                        ],
                        "limits": {
                            "load_timeout_ms": 5000,
                            "inference_timeout_ms": 3000,
                            "max_output_bytes": 1024 * 1024,
                        },
                        "mandatory": True,
                    }
                ],
            }
        ],
    }
    return package, artifacts


def generated_chatter_package() -> ModelPackage:
    document, _ = _chatter_documents()
    return ModelPackage.model_validate(document)


def chatter_fixture_artifacts(package: ModelPackage) -> dict[str, bytes]:
    document, artifacts = _chatter_documents()
    expected = ModelPackage.model_validate(document)
    if package.digest != expected.digest:
        raise ValueError("Generated Chatter package identity changed")
    return artifacts


__all__ = ["affine_artifacts", "chatter_fixture_artifacts", "generated_chatter_package"]
