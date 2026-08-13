#!/usr/bin/env python3
"""Reviewed NumPy adapter for the NeuralFoil medium data-only model.

The numerical encode/network/decode equations follow NeuralFoil 0.3.3 by
Peter Sharpe and R. John Hansman, used under the MIT license. This adapter
loads only caller-verified NPZ arrays with pickle disabled; it does not import
or execute the NeuralFoil repository or its PyTorch training checkpoints.
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

MAX_MESSAGE = 1024 * 1024
EXPECTED_ARTIFACTS = {
    "LICENSE.txt",
    "model/nn-medium.npz",
    "model/scaled_input_distribution.npz",
}
EXPECTED_WEIGHT_SHAPES = {
    "net.0.weight": (64, 25),
    "net.0.bias": (64,),
    "net.2.weight": (64, 64),
    "net.2.bias": (64,),
    "net.4.weight": (64, 64),
    "net.4.bias": (64,),
    "net.6.weight": (64, 64),
    "net.6.bias": (64,),
    "net.8.weight": (198, 64),
    "net.8.bias": (198,),
}
EXPECTED_DISTRIBUTION_SHAPES = {
    "mean_inputs_scaled": (25,),
    "cov_inputs_scaled": (25, 25),
    "inv_cov_inputs_scaled": (25, 25),
}


def emit(
    request_id: str, result: dict | None = None, *, failure: str | None = None
) -> None:
    value = {"type": "result", "request_id": request_id, "ok": failure is None}
    if failure is None:
        value["result"] = result or {}
    else:
        value["failure"] = {"category": failure, "message": "Operation rejected"}
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def progress(request_id: str, sequence: int, phase: str, completed: int) -> None:
    value = {
        "type": "progress",
        "request_id": request_id,
        "sequence": sequence,
        "phase": phase,
        "completed_items": completed,
        "total_items": 3,
        "message": f"{phase.title()} reviewed NeuralFoil model data.",
    }
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def target_platform() -> tuple[str, str]:
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


def safe_path(root: Path, key: str) -> Path:
    parsed = PurePosixPath(key)
    if (
        not key
        or parsed.is_absolute()
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise ValueError
    value = root.joinpath(*parsed.parts).resolve()
    if root.resolve() not in value.parents:
        raise ValueError
    return value


def load_npz(path: Path, shapes: dict[str, tuple[int, ...]]) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        if set(archive.files) != set(shapes):
            raise ValueError
        values = {key: np.asarray(archive[key]) for key in archive.files}
    if any(values[key].shape != shape for key, shape in shapes.items()):
        raise ValueError
    if any(value.dtype.kind not in {"f", "i", "u"} for value in values.values()):
        raise ValueError
    if any(not np.all(np.isfinite(value)) for value in values.values()):
        raise ValueError
    return values


def load_model(root: Path) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    weights = load_npz(safe_path(root, "model/nn-medium.npz"), EXPECTED_WEIGHT_SHAPES)
    distribution = load_npz(
        safe_path(root, "model/scaled_input_distribution.npz"),
        EXPECTED_DISTRIBUTION_SHAPES,
    )
    return weights, distribution


def _number(value: object) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError
    return result


def _input(value: object) -> tuple[np.ndarray, float]:
    if not isinstance(value, dict):
        raise ValueError
    required = {
        "upper_weights",
        "lower_weights",
        "leading_edge_weight",
        "te_thickness",
        "alpha_deg",
        "reynolds_number",
        "n_crit",
        "xtr_upper",
        "xtr_lower",
    }
    if set(value) != required:
        raise ValueError
    upper = value["upper_weights"]
    lower = value["lower_weights"]
    if not isinstance(upper, list) or not isinstance(lower, list):
        raise ValueError
    if len(upper) != 8 or len(lower) != 8:
        raise ValueError
    alpha = _number(value["alpha_deg"])
    reynolds = _number(value["reynolds_number"])
    n_crit = _number(value["n_crit"])
    xtr_upper = _number(value["xtr_upper"])
    xtr_lower = _number(value["xtr_lower"])
    if reynolds <= 0 or not 0 <= xtr_upper <= 1 or not 0 <= xtr_lower <= 1:
        raise ValueError
    angle = np.deg2rad(alpha)
    rows = [
        *(_number(item) for item in upper),
        *(_number(item) for item in lower),
        _number(value["leading_edge_weight"]),
        _number(value["te_thickness"]) * 50,
        math.sin(2 * angle),
        math.cos(angle),
        1 - math.cos(angle) ** 2,
        (math.log(reynolds) - 12.5) / 3.5,
        (n_crit - 9) / 4.5,
        xtr_upper,
        xtr_lower,
    ]
    return np.asarray([rows], dtype=np.float64), reynolds


def _network(x: np.ndarray, weights: dict[str, np.ndarray]) -> np.ndarray:
    result = x.T
    layers = (0, 2, 4, 6, 8)
    for index, layer in enumerate(layers):
        result = weights[f"net.{layer}.weight"] @ result + weights[
            f"net.{layer}.bias"
        ].reshape((-1, 1))
        if index != len(layers) - 1:
            result = result / (1 + np.exp(-result))
    return result.T


def _distance(x: np.ndarray, distribution: dict[str, np.ndarray]) -> np.ndarray:
    delta = x - distribution["mean_inputs_scaled"].reshape((1, -1))
    return np.sum(delta @ distribution["inv_cov_inputs_scaled"] * delta, axis=1)


def predict(
    value: object,
    weights: dict[str, np.ndarray],
    distribution: dict[str, np.ndarray],
) -> dict[str, float]:
    x, _ = _input(value)
    y = _network(x, weights)
    y[:, 0] -= _distance(x, distribution) / 50

    flipped = x.copy()
    flipped[:, :8] = -x[:, 8:16]
    flipped[:, 8:16] = -x[:, :8]
    flipped[:, 16] = -x[:, 16]
    flipped[:, 18] = -x[:, 18]
    flipped[:, 23] = x[:, 24]
    flipped[:, 24] = x[:, 23]
    y_flipped = _network(flipped, weights)
    y_flipped[:, 0] -= _distance(flipped, distribution) / 50
    y_unflipped = y_flipped.copy()
    y_unflipped[:, 1] = -y_flipped[:, 1]
    y_unflipped[:, 3] = -y_flipped[:, 3]
    y_unflipped[:, 4] = y_flipped[:, 5]
    y_unflipped[:, 5] = y_flipped[:, 4]

    fused = (y + y_unflipped) / 2
    fused[:, 0] = 1 / (1 + np.exp(-np.clip(fused[:, 0], -700, 700)))
    fused[:, 4:6] = np.clip(fused[:, 4:6], 0, 1)
    output = {
        "analysis_confidence": float(fused[0, 0]),
        "cl": float(fused[0, 1] / 2),
        "cd": float(np.exp((fused[0, 2] - 2) * 2)),
        "cm": float(fused[0, 3] / 20),
        "top_xtr": float(fused[0, 4]),
        "bottom_xtr": float(fused[0, 5]),
    }
    if not all(math.isfinite(item) for item in output.values()):
        raise ValueError
    return output


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--artifact-root", required=True)
    root = Path(parser.parse_args().artifact_root).resolve()
    if not root.is_dir():
        return 2
    handles: dict[str, tuple[dict[str, np.ndarray], dict[str, np.ndarray]]] = {}
    for raw in sys.stdin.buffer:
        if len(raw) > MAX_MESSAGE:
            return 3
        request: dict = {}
        try:
            request = json.loads(raw)
            request_id = str(request["request_id"])
            operation = str(request["operation"])
            if operation == "health":
                system, architecture = target_platform()
                emit(
                    request_id,
                    {
                        "adapter_id": "wright-neuralfoil-numpy",
                        "adapter_version": "1.0.0",
                        "contract_version": "1.0",
                        "formats": ["numpy-npz"],
                        "tasks": ["airfoil_aerodynamics"],
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
                        },
                    },
                )
            elif operation == "verify":
                progress(request_id, 1, "verify", 0)
                artifacts = dict(request["artifacts"])
                if set(artifacts) != EXPECTED_ARTIFACTS:
                    raise ValueError
                for key, expected in artifacts.items():
                    if (
                        hashlib.sha256(safe_path(root, key).read_bytes()).hexdigest()
                        != expected
                    ):
                        raise ValueError
                load_model(root)
                progress(request_id, 2, "verify", 3)
                emit(
                    request_id,
                    {
                        "verified": True,
                        "artifact_set_digest": request["artifact_set_digest"],
                        "format": request["format"],
                    },
                )
            elif operation == "load":
                progress(request_id, 1, "load", 0)
                handle = "handle-" + uuid.uuid4().hex
                handles[handle] = load_model(root)
                progress(request_id, 2, "load", 3)
                emit(
                    request_id, {"model_handle": handle, "loaded_handles": len(handles)}
                )
            elif operation == "infer":
                progress(request_id, 1, "infer", 0)
                started = time.perf_counter()
                weights, distribution = handles[str(request["model_handle"])]
                output = predict(request["input"], weights, distribution)
                timing_ms = max(1, math.ceil((time.perf_counter() - started) * 1000))
                progress(request_id, 2, "infer", 3)
                emit(
                    request_id,
                    {
                        "model_handle": request["model_handle"],
                        "task_id": "airfoil_aerodynamics",
                        "schema_digest": request["schema_digest"],
                        "output": output,
                        "output_digest": hashlib.sha256(
                            json.dumps(
                                output, sort_keys=True, separators=(",", ":")
                            ).encode()
                        ).hexdigest(),
                        "timing_ms": timing_ms,
                        "warnings": [],
                        "terminal_state": "succeeded",
                    },
                )
            elif operation == "unload":
                handles.pop(str(request.get("model_handle") or ""), None)
                emit(request_id, {"remaining_handles": len(handles)})
            elif operation == "cancel":
                emit(request_id, {"acknowledged": True})
            elif operation == "shutdown":
                handles.clear()
                emit(request_id, {"remaining_handles": 0})
                return 0
            else:
                emit(request_id, failure="internal_error")
        except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
            emit(
                str(request.get("request_id") or "unknown"), failure="artifact_invalid"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
