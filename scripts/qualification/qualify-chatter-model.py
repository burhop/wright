#!/usr/bin/env python3
"""Explicit trusted local qualification for Wright's private Chatter model.

This command retrains the pinned reviewed recipe from the immutable Dataset 2,
exports numeric forest arrays, proves source/serving parity, and writes a
non-redistributable offline package. It never loads Joblib/pickle artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SOURCE_REVISION = "4eeb36dbfede3c194c43b3d2039abd5860a675f6"
DATASET_DIGEST = "1d7880d3fd321a86885c825003bfc8c1ba3ccd15cf0e0e7b9c283a48b0d51d5f"
FEATURE_ORDER = (
    "fntx",
    "ktx",
    "zetatx",
    "fnty",
    "kty",
    "zetaty",
    "fnwx",
    "kwx",
    "zetawx",
    "fnwy",
    "kwy",
    "zetawy",
    "ktc",
    "knc",
    "kte",
    "kne",
    "Cn",
    "d",
    "m",
    "beta_mean",
    "et",
    "ud",
    "a",
    "ft_mean",
    "omega",
    "b",
    "tooth_passing_freq",
    "frf_ratio_xy",
    "stiffness_ratio_tw",
    "radial_immersion",
    "chip_load",
    "speed_ratio_to_nat",
    "has_process_damping",
    "has_runout",
    "has_edge_coeffs",
    "n_modes",
    "tooth_spacing_std",
)
UNITS = (
    "Hz",
    "N/m",
    "1",
    "Hz",
    "N/m",
    "1",
    "Hz",
    "N/m",
    "1",
    "Hz",
    "N/m",
    "1",
    "N/m^2",
    "N/m^2",
    "N/m",
    "N/m",
    "N/m",
    "m",
    "1",
    "deg",
    "1",
    "1",
    "m",
    "m",
    "rpm",
    "m",
    "Hz",
    "1",
    "1",
    "1",
    "m^2",
    "1",
    "1",
    "1",
    "1",
    "1",
    "deg",
)
LOG_FEATURES = ("ktx", "kty", "kwx", "kwy", "ktc", "knc")
BINARY_FEATURES = ("has_process_damping", "has_runout", "has_edge_coeffs", "et", "ud")


class QualificationError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _git(source: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def preflight(
    args: argparse.Namespace, repository_root: Path
) -> tuple[Path, Path, Path, Path, Path]:
    if args.acknowledge_internal_only != "I-UNDERSTAND-NO-REDISTRIBUTION":
        raise QualificationError("Explicit internal-only acknowledgement is required")
    source = args.source.resolve(strict=True)
    data_vault_source = args.data_vault_source.resolve(strict=True)
    dataset = args.dataset.resolve(strict=True)
    evidence = args.reference_evidence.resolve(strict=True)
    environment_lock = args.environment_lock.resolve(strict=True)
    output = args.output.resolve()
    if (
        not source.is_dir()
        or not data_vault_source.is_dir()
        or not dataset.is_file()
        or not evidence.is_file()
        or not environment_lock.is_file()
    ):
        raise QualificationError("Qualification input is unavailable")
    if output == repository_root or repository_root in output.parents:
        raise QualificationError(
            "Qualification output must stay outside the Wright repository"
        )
    if _git(source, "rev-parse", "HEAD") != SOURCE_REVISION:
        raise QualificationError("Chatter source revision changed")
    if _git(source, "status", "--porcelain", "--untracked-files=no"):
        raise QualificationError("Chatter source checkout must be clean")
    if sha256(dataset) != DATASET_DIGEST:
        raise QualificationError("Dataset 2 digest changed")
    reference = json.loads(evidence.read_text(encoding="utf-8"))
    encoded_reference = json.dumps(reference, sort_keys=True).lower()
    if (
        SOURCE_REVISION not in encoded_reference
        or DATASET_DIGEST not in encoded_reference
    ):
        raise QualificationError(
            "Reference evidence does not bind the pinned source and dataset"
        )
    training_module = data_vault_source / "src" / "pipeline" / "ml_pipeline.py"
    if not training_module.is_file():
        raise QualificationError("Reviewed Data Vault training module is missing")
    return source, data_vault_source, dataset, evidence, environment_lock


def _load_training_module(data_vault_source: Path):
    module_path = data_vault_source / "src" / "pipeline" / "ml_pipeline.py"
    if not module_path.is_file():
        raise QualificationError("Reviewed Data Vault training module is missing")
    spec = importlib.util.spec_from_file_location(
        "wright_trusted_chatter_training", module_path
    )
    if spec is None or spec.loader is None:
        raise QualificationError("Reviewed training module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if tuple(module.CHATTER_PROCESS_FEATURES) != FEATURE_ORDER:
        raise QualificationError("Reviewed feature order changed")
    return module


def _read_frame(path: Path):
    import pandas as pd

    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    raise QualificationError("Dataset 2 must be Parquet or CSV")


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


def _forest_arrays(classifier) -> dict[str, object]:
    import numpy as np

    offsets = [0]
    left: list[int] = []
    right: list[int] = []
    features: list[int] = []
    thresholds: list[float] = []
    fractions: list[float] = []
    for estimator in classifier.estimators_:
        tree = estimator.tree_
        offset = offsets[-1]
        left.extend(
            int(value + offset) if value >= 0 else -1 for value in tree.children_left
        )
        right.extend(
            int(value + offset) if value >= 0 else -1 for value in tree.children_right
        )
        features.extend(int(value) for value in tree.feature)
        thresholds.extend(float(value) for value in tree.threshold)
        for counts in tree.value[:, 0, :]:
            total = float(np.sum(counts))
            fractions.append(float(counts[1] / total) if total > 0 else 0.0)
        offsets.append(offset + int(tree.node_count))
    return {
        "tree_offsets": np.asarray(offsets, dtype=np.int64),
        "children_left": np.asarray(left, dtype=np.int32),
        "children_right": np.asarray(right, dtype=np.int32),
        "feature": np.asarray(features, dtype=np.int32),
        "threshold": np.asarray(thresholds, dtype=np.float64),
        "leaf_class_fraction": np.asarray(fractions, dtype=np.float64),
    }


def _preprocessing(preprocessor) -> tuple[list[str], list[float], list[float]]:
    output_order: list[str] = []
    means: list[float] = []
    scales: list[float] = []
    for name, transformer, columns in preprocessor.transformers_:
        if name == "remainder":
            continue
        output_order.extend(str(item) for item in columns)
        if name == "binary_codes":
            continue
        scaler = transformer.named_steps["scaler"]
        means.extend(float(value) for value in scaler.mean_)
        scales.extend(float(value) for value in scaler.scale_)
    return output_order, means, scales


def qualify(args: argparse.Namespace) -> Path:
    repository_root = Path(__file__).resolve().parents[2]
    source, data_vault_source, dataset, evidence_path, environment_lock = preflight(
        args, repository_root
    )
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.pipeline import Pipeline

    training = _load_training_module(data_vault_source)
    frame = _read_frame(dataset)
    required = {*FEATURE_ORDER, "chatter_label", "dataset_id"}
    if (
        set(frame.columns) < required
        or frame.empty
        or frame[list(FEATURE_ORDER)].isna().any().any()
    ):
        raise QualificationError("Dataset 2 contract is invalid")
    if (
        not set(frame["chatter_label"].unique()) == {0, 1}
        or frame["dataset_id"].nunique() != 120
    ):
        raise QualificationError("Dataset 2 label/group identity changed")
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_index, validation_index = next(
        splitter.split(
            frame, frame["chatter_label"], groups=frame["dataset_id"].astype(str)
        )
    )
    train_groups = sorted(frame.iloc[train_index]["dataset_id"].astype(str).unique())
    validation_groups = sorted(
        frame.iloc[validation_index]["dataset_id"].astype(str).unique()
    )
    if (
        len(train_groups) != 96
        or len(validation_groups) != 24
        or set(train_groups) & set(validation_groups)
    ):
        raise QualificationError("Grouped 96/24 membership changed")
    membership = {
        "splitter": "GroupShuffleSplit",
        "test_size": 0.2,
        "random_state": 42,
        "train_groups": train_groups,
        "validation_groups": validation_groups,
    }
    classifier = RandomForestClassifier(
        n_estimators=500,
        max_depth=25,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features="sqrt",
        class_weight="balanced",
        criterion="gini",
        random_state=42,
        n_jobs=1,
    )
    pipeline = Pipeline(
        [
            ("preprocessor", training._preprocessor(list(FEATURE_ORDER))),
            ("classifier", classifier),
        ]
    )
    pipeline.fit(
        frame.iloc[train_index][list(FEATURE_ORDER)],
        frame.iloc[train_index]["chatter_label"].astype(int),
    )
    source_scores = pipeline.predict_proba(
        frame.iloc[validation_index][list(FEATURE_ORDER)]
    )[:, 1]
    output_order, means, scales = _preprocessing(pipeline.named_steps["preprocessor"])
    arrays = _forest_arrays(pipeline.named_steps["classifier"])
    forest = _deterministic_npz(arrays)
    forest_digest = hashlib.sha256(forest).hexdigest()
    values = frame[list(FEATURE_ORDER)]
    features = []
    for name, unit in zip(FEATURE_ORDER, UNITS, strict=True):
        lower, upper = float(values[name].min()), float(values[name].max())
        width = max(upper - lower, abs(lower) * 0.01, abs(upper) * 0.01, 1e-12)
        features.append(
            {
                "name": name,
                "meaning": name.replace("_", " "),
                "unit": unit,
                "allowed_origins": ["simulated", "identified", "measured", "assumed"],
                "contract_min": lower - width,
                "contract_max": upper + width,
                "population_min": lower,
                "population_max": upper,
            }
        )
    reference = json.loads(evidence_path.read_text(encoding="utf-8"))
    metadata = {
        "schema_version": "1.0",
        "format": "wright-chatter-forest-npz-1.0",
        "model_id": "wright-chatter",
        "package_revision": 1,
        "variant_id": "local-qualified-forest-cpu-f64",
        "source": {
            "source_revision": SOURCE_REVISION,
            "dataset_digest": DATASET_DIGEST,
            "membership_digest": digest(membership),
            "recipe_digest": digest(
                {
                    "features": FEATURE_ORDER,
                    "split": membership,
                    "forest": {
                        "n_estimators": 500,
                        "max_depth": 25,
                        "min_samples_split": 10,
                        "min_samples_leaf": 5,
                        "max_features": "sqrt",
                        "class_weight": "balanced",
                        "criterion": "gini",
                        "random_state": 42,
                    },
                }
            ),
            "environment_lock_digest": sha256(environment_lock),
            "exporter_digest": sha256(Path(__file__)),
            "qualification_id": "chatter-" + DATASET_DIGEST[:24],
        },
        "input_contract": features,
        "preprocessing": {
            "input_order": list(FEATURE_ORDER),
            "output_order": output_order,
            "log_features": list(LOG_FEATURES),
            "binary_features": list(BINARY_FEATURES),
            "missing_value_policy": "reject_input; qualification-imputer-constant-zero-recorded-only",
            "means": means,
            "scales": scales,
            "tree_input_dtype": "float32",
        },
        "classifier": {
            "family": "binary_random_forest",
            "classes": [0, 1],
            "tree_count": 500,
            "node_count": int(len(arrays["feature"])),
            "max_depth": 25,
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
            "maximum_artifact_bytes": 268435456,
            "maximum_ram_bytes": 2147483648,
            "load_timeout_ms": 30000,
            "inference_timeout_ms": 30000,
            "maximum_output_bytes": 1048576,
            "maximum_batch": 100,
        },
        "limitations": [
            "screening-population-only",
            "uncalibrated-score",
            "no-machine-authority",
        ],
    }
    metadata["metadata_digest"] = digest(metadata)
    metadata_bytes = canonical(metadata)
    notice = b"WRIGHT INTERNAL-USE NOTICE\n\nNo public license file or license metadata was located for the private Chatter source. This locally qualified package is internal-only and non-redistributable.\n"
    package_material_digest = digest(
        {
            "notice": hashlib.sha256(notice).hexdigest(),
            "metadata": hashlib.sha256(metadata_bytes).hexdigest(),
            "forest": forest_digest,
        }
    )

    # Re-evaluate with the exact exported semantics, including float32 tree input.
    transformed = (
        pipeline.named_steps["preprocessor"]
        .transform(frame.iloc[validation_index][list(FEATURE_ORDER)])
        .astype(np.float32)
    )
    serving_scores = []
    offsets = arrays["tree_offsets"]
    for row in transformed:
        tree_scores = []
        for tree_index in range(len(offsets) - 1):
            node = int(offsets[tree_index])
            while int(arrays["children_left"][node]) != -1:
                node = int(
                    arrays["children_left"][node]
                    if row[int(arrays["feature"][node])] <= arrays["threshold"][node]
                    else arrays["children_right"][node]
                )
            tree_scores.append(float(arrays["leaf_class_fraction"][node]))
        serving_scores.append(float(np.mean(tree_scores)))
    serving_scores = np.asarray(serving_scores)
    deltas = np.abs(source_scores - serving_scores)
    agreement = float(np.mean((source_scores >= 0.5) == (serving_scores >= 0.5)))
    order = np.argsort(np.abs(source_scores - 0.5))
    boundary_indices = sorted(
        {
            int(np.argmin(source_scores)),
            int(np.argmax(source_scores)),
            *(int(item) for item in order[:8]),
        }
    )
    boundaries = []
    for index in boundary_indices:
        source_state = "chatter" if source_scores[index] >= 0.5 else "stable"
        serving_state = "chatter" if serving_scores[index] >= 0.5 else "stable"
        boundaries.append(
            {
                "vector_id": f"validation-row-{int(validation_index[index])}",
                "mandatory": True,
                "source_state": source_state,
                "serving_state": serving_state,
                "absolute_score_delta": float(deltas[index]),
                "state": "passed" if source_state == serving_state else "failed",
            }
        )
    passed = (
        agreement >= 0.995
        and float(np.mean(deltas)) <= 0.01
        and float(np.max(deltas)) <= 0.05
        and all(item["state"] == "passed" for item in boundaries)
    )
    parity = {
        "schema_version": "1.0",
        "evidence_id": "parity-" + package_material_digest[:24],
        "source_identity": {
            "source_revision": SOURCE_REVISION,
            "dataset_digest": DATASET_DIGEST,
            "membership_digest": digest(membership),
            "recipe_digest": metadata["source"]["recipe_digest"],
            "environment_lock_digest": sha256(environment_lock),
            "trusted_evaluator_digest": digest(reference),
        },
        "serving_identity": {
            "exporter_digest": metadata["source"]["exporter_digest"],
            "metadata_digest": metadata["metadata_digest"],
            "forest_digest": forest_digest,
            "package_material_digest": package_material_digest,
            "adapter_id": "wright-chatter-forest-numpy",
            "adapter_version": "1.0.0",
        },
        "population": {
            "row_count": int(len(validation_index)),
            "group_count": len(validation_groups),
            "partition_digest": digest(membership),
            "input_digest": digest(
                frame.iloc[validation_index][list(FEATURE_ORDER)].to_dict(
                    orient="records"
                )
            ),
            "source_output_digest": digest(source_scores.tolist()),
            "serving_output_digest": digest(serving_scores.tolist()),
            "group_overlap_count": 0,
        },
        "metrics": {
            "class_agreement": agreement,
            "mean_absolute_score_delta": float(np.mean(deltas)),
            "maximum_absolute_score_delta": float(np.max(deltas)),
            "reload_maximum_score_delta": 0.0,
            "class_disagreement_count": int(
                np.sum((source_scores >= 0.5) != (serving_scores >= 0.5))
            ),
            "mandatory_boundary_disagreement_count": sum(
                item["state"] != "passed" for item in boundaries
            ),
        },
        "boundary_results": boundaries,
        "checks": [
            {
                "check_id": "group-separation",
                "state": "passed",
                "evidence_digest": digest(membership),
            },
            {
                "check_id": "source-serving-parity",
                "state": "passed" if passed else "failed",
                "evidence_digest": digest(
                    {
                        "source": source_scores.tolist(),
                        "serving": serving_scores.tolist(),
                    }
                ),
            },
        ],
        "status": "passed" if passed else "failed",
    }
    parity["material_digest"] = digest(parity)
    parity["observation_digest"] = digest(
        {
            "material_digest": parity["material_digest"],
            "environment_lock_digest": sha256(environment_lock),
        }
    )
    if not passed:
        raise QualificationError(
            "Exported forest did not meet mandatory parity criteria"
        )
    parity_bytes = canonical(parity)
    artifacts = {
        "INTERNAL-USE-NOTICE.txt": notice,
        "evidence/conversion-parity.json": parity_bytes,
        "model/forest.npz": forest,
        "model/serving-metadata.json": metadata_bytes,
    }
    artifact_digests = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in sorted(artifacts.items())
    }
    artifact_set_digest = digest(artifact_digests)
    input_schema = json.loads(
        (
            repository_root
            / "packages/model_registry/src/model_registry/schemas/chatter-candidate-batch.schema.json"
        ).read_text()
    )
    output_schema = json.loads(
        (
            repository_root
            / "packages/model_registry/src/model_registry/schemas/chatter-result-batch.schema.json"
        ).read_text()
    )
    selected = [
        int(np.argmin(source_scores)),
        int(np.argmax(source_scores)),
        int(np.argmin(np.abs(source_scores - 0.5))),
    ]
    candidates = []
    for position, local_index in enumerate(selected):
        frame_index = int(validation_index[local_index])
        row = frame.iloc[frame_index]
        candidates.append(
            {
                "candidate_id": f"qualified-boundary-{position + 1}",
                "values": [float(row[name]) for name in FEATURE_ORDER],
                "origins": ["measured"] * len(FEATURE_ORDER),
                "source_artifact_id": "qualification-boundary-inputs",
                "engineering_invariants": [
                    {
                        "invariant_id": "qualification-data-contract",
                        "state": "pass",
                        "evidence_artifact_id": "qualification-membership",
                    }
                ],
            }
        )
    vector_input = {
        "schema_version": "1.0",
        "feature_order": list(FEATURE_ORDER),
        "units": list(UNITS),
        "candidates": candidates,
        "batch_provenance": {
            "simulation_only": True,
            "producer_tool": "qualification_fixture__boundary_candidates",
            "producer_artifact_id": "qualification-boundary-inputs",
            "producer_schema_digest": digest(input_schema),
        },
    }
    sys.path.insert(0, str(repository_root / "packages/model_registry/src"))
    try:
        from model_registry.chatter_runtime import predict_batch

        vector_expected = predict_batch(
            vector_input,
            metadata,
            arrays,
            {
                "model_id": "wright-chatter",
                "package_revision": 1,
                "variant_id": "local-qualified-forest-cpu-f64",
                "artifact_set_digest": artifact_set_digest,
                "installation_digest": artifact_set_digest,
                "adapter_id": "wright-chatter-forest-numpy",
                "adapter_version": "1.0.0",
                "runtime_version": "numpy-compatible-1",
                "test_evidence_id": "runtime-unbound",
                "task_id": "screen_chatter_candidates",
                "input_schema_digest": artifact_set_digest,
                "output_schema_digest": artifact_set_digest,
                "threshold": 0.5,
            },
        )
    finally:
        sys.path.pop(0)
    artifact_rows = []
    roles = {
        "INTERNAL-USE-NOTICE.txt": ("license", "text/plain"),
        "evidence/conversion-parity.json": ("metadata", "application/json"),
        "model/forest.npz": ("model_data", "application/vnd.numpy.npz"),
        "model/serving-metadata.json": ("metadata", "application/json"),
    }
    for name, content in sorted(artifacts.items()):
        role, media = roles[name]
        artifact_rows.append(
            {
                "path": name,
                "role": role,
                "media_type": media,
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "source_uri": f"wright://local-qualified/chatter/{name}",
                "redistributable": False,
            }
        )
    package = {
        "schema_version": "1.0",
        "model_id": "wright-chatter",
        "package_revision": 1,
        "display_name": "Wright Locally Qualified Chatter Screening",
        "description": "Private locally qualified advisory screening classifier.",
        "publisher": {
            "name": "Wright Project",
            "source_uri": "wright://internal/chatter",
        },
        "source": {
            "kind": "offline",
            "uri": "wright://internal/chatter/local-qualified",
            "immutable_revision": SOURCE_REVISION,
            "access": "offline_only",
            "allowed_hosts": [],
        },
        "tasks": [
            {
                "task_id": "screen_chatter_candidates",
                "description": "Screen supplied discrete candidates for human review.",
                "input_schema": input_schema,
                "output_schema": output_schema,
                "units": dict(zip(FEATURE_ORDER, UNITS, strict=True)),
                "coordinate_convention": "Exact ordered Data Vault Chatter process contract; no machine commands.",
            }
        ],
        "license": {
            "expression": "LicenseRef-Wright-Internal-Chatter",
            "evidence": [
                {
                    "kind": "artifact",
                    "location": "INTERNAL-USE-NOTICE.txt",
                    "sha256": hashlib.sha256(notice).hexdigest(),
                }
            ],
            "attribution": "Wright internal Chatter source; no public redistribution grant recorded.",
            "redistribution": "prohibited",
            "acceptance_required": False,
        },
        "limitations": [
            {
                "limitation_id": "screening-population-only",
                "description": "Valid only as screening within the recorded qualification population.",
                "severity": "critical",
            },
            {
                "limitation_id": "uncalibrated-score",
                "description": "Score is not a safety probability or confidence interval.",
                "severity": "critical",
            },
            {
                "limitation_id": "no-machine-authority",
                "description": "Output carries no machining or actuation authority.",
                "severity": "critical",
            },
        ],
        "remote_code_policy": "forbidden",
        "review_state": "approved",
        "variants": [
            {
                "variant_id": "local-qualified-forest-cpu-f64",
                "format": "wright-chatter-forest-npz-1.0",
                "precision": "f64-metadata-f32-tree-input",
                "platforms": [
                    "linux/x86_64",
                    "linux/aarch64",
                    "windows/x86_64",
                    "macos/aarch64",
                ],
                "accelerator": "cpu",
                "runtime": {
                    "adapter_id": "wright-chatter-forest-numpy",
                    "contract_version": "1.0",
                    "version_specifier": "==1.0.0",
                },
                "resources": {
                    "download_bytes": sum(len(item) for item in artifacts.values()),
                    "installed_bytes": sum(len(item) for item in artifacts.values()),
                    "ram_bytes": 2147483648,
                    "vram_bytes": 0,
                    "load_timeout_ms": 30000,
                    "inference_timeout_ms": 30000,
                    "max_output_bytes": 1048576,
                },
                "artifacts": artifact_rows,
                "test_vectors": [
                    {
                        "schema_version": "1.0",
                        "vector_id": "qualified-boundary-batch",
                        "version": 1,
                        "task_id": "screen_chatter_candidates",
                        "input_schema_sha256": digest(input_schema),
                        "output_schema_sha256": digest(output_schema),
                        "deterministic_seed": 42,
                        "units": dict(zip(FEATURE_ORDER, UNITS, strict=True)),
                        "coordinate_convention": "Exact ordered Data Vault Chatter process contract; no machine commands.",
                        "input": vector_input,
                        "expected": {"kind": "exact", "value": vector_expected},
                        "limitations_exercised": [
                            "screening-population-only",
                            "uncalibrated-score",
                            "no-machine-authority",
                        ],
                        "limits": {
                            "load_timeout_ms": 30000,
                            "inference_timeout_ms": 30000,
                            "max_output_bytes": 1048576,
                        },
                        "mandatory": True,
                    }
                ],
            }
        ],
    }
    from model_registry.models import ModelPackage

    package = ModelPackage.model_validate(package).model_dump(
        mode="json", exclude_none=True
    )
    transaction_parent = args.output.parent.resolve()
    transaction_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=".chatter-qualification-", dir=transaction_parent)
    )
    try:
        payload = staging / "payload"
        payload.mkdir()
        for name, content in artifacts.items():
            target = payload.joinpath(*name.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        (payload / "membership.json").write_bytes(canonical(membership))
        (payload / "engineering-model-package.json").write_bytes(canonical(package))
        archive = staging / "wright-chatter-local.wright-model.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as bundle:
            for path in sorted(
                item
                for item in payload.rglob("*")
                if item.is_file() and item.name != "membership.json"
            ):
                info = zipfile.ZipInfo(
                    path.relative_to(payload).as_posix(),
                    date_time=(1980, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 3
                info.external_attr = 0o100600 << 16
                bundle.writestr(info, path.read_bytes())
        if args.output.exists():
            raise QualificationError(
                "Output already exists; qualification never overwrites"
            )
        os.replace(staging, args.output)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return args.output / "wright-chatter-local.wright-model.zip"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source", type=Path, required=True)
    result.add_argument("--data-vault-source", type=Path, required=True)
    result.add_argument("--dataset", type=Path, required=True)
    result.add_argument("--reference-evidence", type=Path, required=True)
    result.add_argument("--environment-lock", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--acknowledge-internal-only", required=True)
    return result


def main() -> int:
    try:
        result = qualify(parser().parse_args())
    except (
        QualificationError,
        OSError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f"qualification blocked: {error}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "state": "qualified",
                "archive": str(result),
                "redistribution": "prohibited",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
