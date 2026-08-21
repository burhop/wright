#!/usr/bin/env python3
"""Deterministic stdio engineering-model adapter used only by Wright tests.

The fixture intentionally uses only the Python standard library. It never acquires
content or imports code from the supplied artifact directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import threading
import time
import uuid
from pathlib import Path, PurePosixPath

MAX_MESSAGE = 1024 * 1024
_write_lock = threading.Lock()
_cancelled: dict[str, threading.Event] = {}
_handles: dict[str, tuple[float, float]] = {}
_stopping = threading.Event()


def _target_platform() -> tuple[str, str]:
    systems = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    machines = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }
    return (
        systems.get(platform.system().lower(), "unknown"),
        machines.get(platform.machine().lower(), "unknown"),
    )


def _emit(value: dict) -> None:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    with _write_lock:
        sys.stdout.write(encoded + "\n")
        sys.stdout.flush()


def _result(request_id: str, result: dict) -> None:
    _emit({"type": "result", "request_id": request_id, "ok": True, "result": result})


def _failure(request_id: str, category: str, message: str) -> None:
    _emit(
        {
            "type": "result",
            "request_id": request_id,
            "ok": False,
            "failure": {"category": category, "message": message},
        }
    )


def _progress(request_id: str, sequence: int, phase: str, completed: int) -> None:
    _emit(
        {
            "type": "progress",
            "request_id": request_id,
            "sequence": sequence,
            "phase": phase,
            "completed_items": completed,
            "total_items": 2,
            "message": f"{phase.title()} deterministic model.",
        }
    )


def _safe_path(root: Path, key: str) -> Path:
    parsed = PurePosixPath(key)
    if (
        not key
        or parsed.is_absolute()
        or any(part in {"", ".", ".."} for part in parsed.parts)
    ):
        raise ValueError("artifact key is unsafe")
    candidate = root.joinpath(*parsed.parts).resolve()
    if root.resolve() not in candidate.parents:
        raise ValueError("artifact key is unsafe")
    return candidate


def _verify_artifacts(root: Path, artifacts: dict[str, str]) -> None:
    for key, expected in artifacts.items():
        path = _safe_path(root, key)
        if not path.is_file():
            raise FileNotFoundError(key)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("artifact digest mismatch")


def _coefficients(root: Path) -> tuple[float, float]:
    path = _safe_path(root, "model/coefficients.json")
    value = json.loads(path.read_text(encoding="utf-8"))
    if set(value) != {"offset", "scale"}:
        raise ValueError("coefficient document is invalid")
    offset = float(value["offset"])
    scale = float(value["scale"])
    if not math.isfinite(offset) or not math.isfinite(scale):
        raise ValueError("coefficient document is invalid")
    return offset, scale


def _work(root: Path, request: dict) -> None:
    request_id = str(request.get("request_id") or "")
    operation = str(request.get("operation") or "")
    fault = str(request.get("fault_profile") or "")
    cancelled = _cancelled.setdefault(request_id, threading.Event())
    try:
        if fault == "crash":
            os._exit(23)
        if operation == "health":
            system, architecture = _target_platform()
            descriptor = {
                "adapter_id": "wright-deterministic",
                "adapter_version": "1.0.0",
                "contract_version": "1.0",
                "formats": ["wright-affine-json"],
                "tasks": ["predict"],
                "platforms": [system],
                "architectures": [architecture],
                "execution_providers": ["cpu"],
                "input_schema_dialects": [
                    "https://json-schema.org/draft/2020-12/schema"
                ],
                "output_schema_dialects": [
                    "https://json-schema.org/draft/2020-12/schema"
                ],
                "maximum_message_bytes": MAX_MESSAGE,
                "maximum_concurrency": 1,
                "cancellation_supported": True,
                "unload_supported": True,
                "health": "healthy",
                "diagnostics": {"network_acquisition": False},
            }
            if fault == "bad_identity":
                descriptor["adapter_version"] = "9.9.9"
            _result(request_id, descriptor)
            return
        if operation == "verify":
            _progress(request_id, 1, "verify", 0)
            _verify_artifacts(root, dict(request.get("artifacts") or {}))
            _coefficients(root)
            _progress(request_id, 2, "verify", 2)
            _result(
                request_id,
                {
                    "verified": True,
                    "artifact_set_digest": request["artifact_set_digest"],
                    "format": request["format"],
                },
            )
            return
        if operation == "load":
            _progress(request_id, 1, "load", 0)
            values = _coefficients(root)
            handle = "handle-" + uuid.uuid4().hex
            _handles[handle] = values
            _progress(request_id, 2, "load", 2)
            _result(
                request_id, {"model_handle": handle, "loaded_handles": len(_handles)}
            )
            return
        if operation == "infer":
            handle = str(request.get("model_handle") or "")
            if handle not in _handles:
                _failure(request_id, "inference_failed", "Model handle is unavailable")
                return
            _progress(request_id, 1, "infer", 0)
            if fault in {"slow", "late", "late_short", "progress_forever"}:
                iterations = 2 if fault == "late_short" else 200
                for index in range(iterations):
                    if fault == "progress_forever":
                        _progress(request_id, index + 2, "infer", 0)
                    if cancelled.is_set() and fault not in {"late", "late_short"}:
                        _failure(request_id, "cancelled", "Inference was cancelled")
                        return
                    time.sleep(0.01)
            if cancelled.is_set() and fault not in {"late", "late_short"}:
                _failure(request_id, "cancelled", "Inference was cancelled")
                return
            if fault == "bad_progress":
                _emit(
                    {
                        "type": "progress",
                        "request_id": request_id,
                        "sequence": 1,
                        "phase": "infer",
                        "message": "token=forbidden",
                    }
                )
            input_value = dict(request.get("input") or {})
            x = float(input_value["x"])
            offset, scale = _handles[handle]
            output = {"y": offset + scale * x}
            if fault == "nonfinite":
                output = {"y": float("nan")}
            elif fault == "oversized":
                output = {"y": offset + scale * x, "padding": "x" * 100_000}
            _progress(request_id, 2, "infer", 2)
            _result(
                request_id,
                {
                    "model_handle": handle,
                    "task_id": "predict",
                    "schema_digest": request["schema_digest"],
                    "output": output,
                    "output_digest": hashlib.sha256(
                        json.dumps(
                            output, sort_keys=True, separators=(",", ":")
                        ).encode()
                    ).hexdigest(),
                    "timing_ms": 1,
                    "warnings": [],
                    "terminal_state": "succeeded",
                },
            )
            return
        if operation == "unload":
            _handles.pop(str(request.get("model_handle") or ""), None)
            _result(request_id, {"remaining_handles": len(_handles)})
            return
        _failure(request_id, "internal_error", "Unsupported operation")
    except FileNotFoundError:
        _failure(request_id, "artifact_missing", "Declared artifact is unavailable")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        _failure(request_id, "artifact_invalid", "Declared artifact is invalid")
    finally:
        _cancelled.pop(request_id, None)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--artifact-root", required=True)
    args = parser.parse_args()
    root = Path(args.artifact_root).resolve()
    if not root.is_dir():
        return 2
    for raw in sys.stdin.buffer:
        if len(raw) > MAX_MESSAGE:
            return 3
        try:
            request = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return 4
        operation = str(request.get("operation") or "")
        if operation == "cancel":
            target = str(request.get("target_request_id") or "")
            if target in _cancelled:
                _cancelled[target].set()
            _result(str(request.get("request_id") or ""), {"acknowledged": True})
            continue
        if operation == "shutdown":
            _stopping.set()
            for event in tuple(_cancelled.values()):
                event.set()
            _handles.clear()
            _result(str(request.get("request_id") or ""), {"remaining_handles": 0})
            return 0
        threading.Thread(target=_work, args=(root, request), daemon=True).start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
