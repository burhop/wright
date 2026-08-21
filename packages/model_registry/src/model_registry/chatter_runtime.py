#!/usr/bin/env python3
"""Reviewed NumPy-only adapter for Wright Chatter forest packages.

Only strict JSON metadata and numeric NPZ arrays are loaded.  Pickle, estimator
objects, publisher code, and general model formats are outside this boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
import uuid
from pathlib import Path, PurePosixPath

import numpy as np

from model_registry.chatter_contracts import (
    CHATTER_ADAPTER_ID,
    CHATTER_ADAPTER_VERSION,
    CHATTER_FORMAT,
    CHATTER_TASK_ID,
    FEATURE_ORDER,
    MAX_NODES,
    MAX_OUTPUT_BYTES,
    MAX_TREES,
    PREPROCESSING_ORDER,
    result_material,
    validate_candidate_batch,
    validate_serving_metadata,
)
from model_registry.models import canonical_digest

MAX_MESSAGE = 1024 * 1024
EXPECTED_ARTIFACTS = {
    "INTERNAL-USE-NOTICE.txt",
    "evidence/conversion-parity.json",
    "model/forest.npz",
    "model/serving-metadata.json",
}
ARRAY_DTYPES = {
    "tree_offsets": np.dtype("int64"),
    "children_left": np.dtype("int32"),
    "children_right": np.dtype("int32"),
    "feature": np.dtype("int32"),
    "threshold": np.dtype("float64"),
    "leaf_class_fraction": np.dtype("float64"),
}


def _emit(
    request_id: str, result: dict | None = None, *, failure: str | None = None
) -> None:
    value = {"type": "result", "request_id": request_id, "ok": failure is None}
    if failure is None:
        value["result"] = result or {}
    else:
        value["failure"] = {"category": failure, "message": "Operation rejected"}
    sys.stdout.write(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    )
    sys.stdout.flush()


def _progress(
    request_id: str, sequence: int, phase: str, completed: int, total: int
) -> None:
    sys.stdout.write(
        json.dumps(
            {
                "type": "progress",
                "request_id": request_id,
                "sequence": sequence,
                "phase": phase,
                "completed_items": completed,
                "total_items": total,
                "message": f"{phase.title()} reviewed Chatter numeric data.",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    sys.stdout.flush()


def _target_platform() -> tuple[str, str]:
    systems = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    machines = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    return systems.get(platform.system().lower(), "unknown"), machines.get(
        platform.machine().lower(), "unknown"
    )


def _safe_path(root: Path, key: str) -> Path:
    parsed = PurePosixPath(key)
    if (
        not key
        or parsed.is_absolute()
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise ValueError("unsafe artifact path")
    value = root.joinpath(*parsed.parts).resolve()
    if root.resolve() not in value.parents:
        raise ValueError("unsafe artifact path")
    return value


def _load_json(path: Path, maximum: int) -> dict:
    raw = path.read_bytes()
    if len(raw) > maximum:
        raise ValueError("JSON artifact exceeds its byte ceiling")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("JSON artifact must be an object")
    return value


def _depth_and_reachability(
    start: int,
    end: int,
    left: np.ndarray,
    right: np.ndarray,
    feature: np.ndarray,
    maximum_depth: int,
) -> None:
    stack = [(start, 0)]
    seen: set[int] = set()
    while stack:
        node, depth = stack.pop()
        if node in seen or not start <= node < end or depth > maximum_depth:
            raise ValueError("forest topology is invalid")
        seen.add(node)
        children = (int(left[node]), int(right[node]))
        if children == (-1, -1):
            if int(feature[node]) != -2:
                raise ValueError("leaf feature marker is invalid")
            continue
        if -1 in children or int(feature[node]) not in range(len(FEATURE_ORDER)):
            raise ValueError("forest node is invalid")
        if any(child <= node or child >= end for child in children):
            raise ValueError("forest child index is invalid")
        stack.extend(((children[1], depth + 1), (children[0], depth + 1)))
    if len(seen) != end - start:
        raise ValueError("forest contains unreachable nodes")


def load_forest(root: Path) -> tuple[dict, dict[str, np.ndarray]]:
    metadata = validate_serving_metadata(
        _load_json(_safe_path(root, "model/serving-metadata.json"), 256 * 1024)
    )
    parity = _load_json(
        _safe_path(root, "evidence/conversion-parity.json"), 1024 * 1024
    )
    if parity.get("status") != "passed":
        raise ValueError("conversion parity did not pass")
    forest_path = _safe_path(root, "model/forest.npz")
    if (
        hashlib.sha256(forest_path.read_bytes()).hexdigest()
        != metadata["classifier"]["forest_sha256"]
    ):
        raise ValueError("forest digest changed")
    with np.load(forest_path, allow_pickle=False) as archive:
        if set(archive.files) != set(ARRAY_DTYPES):
            raise ValueError("forest member set is invalid")
        arrays = {name: np.asarray(archive[name]) for name in archive.files}
    if any(value.ndim != 1 for value in arrays.values()):
        raise ValueError("forest arrays must be one-dimensional")
    for name, dtype in ARRAY_DTYPES.items():
        if arrays[name].dtype != dtype:
            raise ValueError("forest dtype is invalid")
    offsets = arrays["tree_offsets"]
    node_count = int(metadata["classifier"]["node_count"])
    tree_count = int(metadata["classifier"]["tree_count"])
    if (
        not 1 <= tree_count <= MAX_TREES
        or not 1 <= node_count <= MAX_NODES
        or offsets.shape != (tree_count + 1,)
        or int(offsets[0]) != 0
        or int(offsets[-1]) != node_count
        or np.any(np.diff(offsets) <= 0)
        or any(
            arrays[name].shape != (node_count,)
            for name in ARRAY_DTYPES
            if name != "tree_offsets"
        )
    ):
        raise ValueError("forest resource declaration is invalid")
    if not np.all(np.isfinite(arrays["threshold"])) or not np.all(
        np.isfinite(arrays["leaf_class_fraction"])
    ):
        raise ValueError("forest contains non-finite values")
    if np.any(arrays["leaf_class_fraction"] < 0) or np.any(
        arrays["leaf_class_fraction"] > 1
    ):
        raise ValueError("leaf class fraction is invalid")
    for index in range(tree_count):
        _depth_and_reachability(
            int(offsets[index]),
            int(offsets[index + 1]),
            arrays["children_left"],
            arrays["children_right"],
            arrays["feature"],
            int(metadata["classifier"]["max_depth"]),
        )
    return metadata, arrays


def _preprocess(values: list[float], metadata: dict) -> np.ndarray:
    raw = dict(zip(FEATURE_ORDER, (float(item) for item in values), strict=True))
    transformed: list[float] = []
    numeric_index = 0
    means = metadata["preprocessing"]["means"]
    scales = metadata["preprocessing"]["scales"]
    log_features = set(metadata["preprocessing"]["log_features"])
    binary = set(metadata["preprocessing"]["binary_features"])
    for name in PREPROCESSING_ORDER:
        value = raw[name]
        if name in log_features:
            value = math.log1p(max(value, 0.0))
        if name not in binary:
            value = (value - float(means[numeric_index])) / float(scales[numeric_index])
            numeric_index += 1
        transformed.append(value)
    return np.asarray(transformed, dtype=np.float32)


def _score(features: np.ndarray, arrays: dict[str, np.ndarray]) -> float:
    scores: list[float] = []
    offsets = arrays["tree_offsets"]
    for tree in range(len(offsets) - 1):
        node = int(offsets[tree])
        while int(arrays["children_left"][node]) != -1:
            feature = int(arrays["feature"][node])
            node = int(
                arrays["children_left"][node]
                if features[feature] <= arrays["threshold"][node]
                else arrays["children_right"][node]
            )
        scores.append(float(arrays["leaf_class_fraction"][node]))
    result = float(np.mean(np.asarray(scores, dtype=np.float64)))
    if not math.isfinite(result) or not 0 <= result <= 1:
        raise ValueError("forest score is invalid")
    return result


def _default_evidence(metadata: dict, artifact_set_digest: str) -> dict:
    digest = str(artifact_set_digest)
    return {
        "model_id": metadata["model_id"],
        "package_revision": metadata["package_revision"],
        "variant_id": metadata["variant_id"],
        "artifact_set_digest": digest,
        "installation_digest": digest,
        "adapter_id": CHATTER_ADAPTER_ID,
        "adapter_version": CHATTER_ADAPTER_VERSION,
        "runtime_version": "numpy-compatible-1",
        "test_evidence_id": "runtime-unbound",
        "task_id": CHATTER_TASK_ID,
        "input_schema_digest": digest,
        "output_schema_digest": digest,
        "threshold": metadata["decision"]["threshold"],
    }


def predict_batch(
    value: dict, metadata: dict, arrays: dict[str, np.ndarray], evidence: dict
) -> dict:
    batch = validate_candidate_batch(value, metadata)
    threshold = float(metadata["decision"]["threshold"])
    band = float(metadata["decision"]["near_threshold_band"])
    results: list[dict] = []
    for position, candidate in enumerate(batch["candidates"]):
        values = [float(item) for item in candidate["values"]]
        score = _score(_preprocess(values, metadata), arrays)
        margin = score - threshold
        outside = any(
            raw < contract["population_min"] or raw > contract["population_max"]
            for raw, contract in zip(values, metadata["input_contract"], strict=True)
        )
        near = abs(margin) <= band
        applicability = (
            "out_of_population"
            if outside
            else ("near_threshold" if near else "in_population")
        )
        invariant_failed = any(
            item["state"] == "fail" for item in candidate["engineering_invariants"]
        )
        warnings = []
        if outside:
            warnings.append("out_of_qualification_population")
        if near:
            warnings.append("near_decision_threshold")
        if invariant_failed:
            warnings.append("engineering_invariant_failed")
        results.append(
            {
                "candidate_id": candidate["candidate_id"],
                "position": position,
                "predicted_state": "chatter" if score >= threshold else "stable",
                "chatter_score": score,
                "decision_threshold": threshold,
                "threshold_margin": margin,
                "calibration_status": "uncalibrated_model_score",
                "applicability": applicability,
                "review_required": outside or near or invariant_failed,
                "eligible_for_preference": not outside
                and not near
                and not invariant_failed,
                "warnings": warnings,
                "limitations": list(metadata["limitations"]),
            }
        )
    input_digest = canonical_digest(batch)
    result = result_material(
        results=results, model_evidence=evidence, input_digest=input_digest
    )
    encoded = json.dumps(
        result, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    if len(encoded) > min(
        MAX_OUTPUT_BYTES, int(metadata["resources"]["maximum_output_bytes"])
    ):
        raise ValueError("Chatter output exceeds its byte limit")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--artifact-root", required=True)
    root = Path(parser.parse_args().artifact_root).resolve()
    if not root.is_dir():
        return 2
    handles: dict[str, tuple[dict, dict[str, np.ndarray], str]] = {}
    for raw in sys.stdin.buffer:
        if len(raw) > MAX_MESSAGE:
            return 3
        request: dict = {}
        try:
            request = json.loads(raw)
            request_id = str(request["request_id"])
            operation = str(request["operation"])
            if operation == "health":
                system, architecture = _target_platform()
                _emit(
                    request_id,
                    {
                        "adapter_id": CHATTER_ADAPTER_ID,
                        "adapter_version": CHATTER_ADAPTER_VERSION,
                        "contract_version": "1.0",
                        "formats": [CHATTER_FORMAT],
                        "tasks": [CHATTER_TASK_ID],
                        "platforms": [system],
                        "architectures": [architecture],
                        "execution_providers": ["cpu"],
                        "maximum_message_bytes": MAX_MESSAGE,
                        "maximum_concurrency": 1,
                        "cancellation_supported": True,
                        "unload_supported": True,
                        "health": "healthy",
                        "diagnostics": {
                            "network_acquisition": False,
                            "npz_allow_pickle": False,
                            "warm_retention": False,
                        },
                    },
                )
            elif operation == "verify":
                _progress(request_id, 1, "verify", 0, 4)
                artifacts = dict(request["artifacts"])
                if set(artifacts) != EXPECTED_ARTIFACTS:
                    raise ValueError("artifact set is invalid")
                for key, expected in artifacts.items():
                    if (
                        hashlib.sha256(_safe_path(root, key).read_bytes()).hexdigest()
                        != expected
                    ):
                        raise ValueError("artifact digest changed")
                load_forest(root)
                _progress(request_id, 2, "verify", 4, 4)
                _emit(
                    request_id,
                    {
                        "verified": True,
                        "artifact_set_digest": request["artifact_set_digest"],
                        "format": request["format"],
                    },
                )
            elif operation == "load":
                _progress(request_id, 1, "load", 0, 4)
                metadata, arrays = load_forest(root)
                handle = "handle-" + uuid.uuid4().hex
                handles[handle] = (
                    metadata,
                    arrays,
                    str(request["artifact_set_digest"]),
                )
                _progress(request_id, 2, "load", 4, 4)
                _emit(
                    request_id, {"model_handle": handle, "loaded_handles": len(handles)}
                )
            elif operation == "infer":
                started = time.perf_counter()
                _progress(request_id, 1, "infer", 0, 1)
                metadata, arrays, artifact_set_digest = handles[
                    str(request["model_handle"])
                ]
                evidence = dict(
                    request.get("model_evidence")
                    or _default_evidence(metadata, artifact_set_digest)
                )
                output = predict_batch(
                    dict(request["input"]), metadata, arrays, evidence
                )
                _progress(request_id, 2, "infer", 1, 1)
                _emit(
                    request_id,
                    {
                        "model_handle": request["model_handle"],
                        "task_id": CHATTER_TASK_ID,
                        "schema_digest": request["schema_digest"],
                        "output": output,
                        "output_digest": canonical_digest(output),
                        "timing_ms": max(
                            1, math.ceil((time.perf_counter() - started) * 1000)
                        ),
                        "warnings": [],
                        "terminal_state": "succeeded",
                    },
                )
            elif operation == "unload":
                handles.pop(str(request.get("model_handle") or ""), None)
                _emit(request_id, {"remaining_handles": len(handles)})
            elif operation == "cancel":
                _emit(request_id, {"acknowledged": True})
            elif operation == "shutdown":
                handles.clear()
                _emit(request_id, {"remaining_handles": 0})
                return 0
            else:
                _emit(request_id, failure="internal_error")
        except Exception:
            _emit(
                str(request.get("request_id") or "unknown"), failure="artifact_invalid"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
