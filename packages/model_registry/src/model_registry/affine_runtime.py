#!/usr/bin/env python3
"""Reviewed stdio adapter for Wright's generated affine validation package."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import uuid
from pathlib import Path, PurePosixPath

MAX_MESSAGE = 1024 * 1024


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
        "total_items": 2,
        "message": f"{phase.title()} deterministic model.",
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


def coefficients(root: Path) -> tuple[float, float]:
    value = json.loads(
        safe_path(root, "model/coefficients.json").read_text(encoding="utf-8")
    )
    if set(value) != {"offset", "scale"}:
        raise ValueError
    offset, scale = float(value["offset"]), float(value["scale"])
    if not math.isfinite(offset) or not math.isfinite(scale):
        raise ValueError
    return offset, scale


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--artifact-root", required=True)
    root = Path(parser.parse_args().artifact_root).resolve()
    if not root.is_dir():
        return 2
    handles: dict[str, tuple[float, float]] = {}
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
                    },
                )
            elif operation == "verify":
                progress(request_id, 1, "verify", 0)
                for key, expected in dict(request["artifacts"]).items():
                    path = safe_path(root, key)
                    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                        raise ValueError
                coefficients(root)
                progress(request_id, 2, "verify", 2)
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
                handles[handle] = coefficients(root)
                progress(request_id, 2, "load", 2)
                emit(
                    request_id, {"model_handle": handle, "loaded_handles": len(handles)}
                )
            elif operation == "infer":
                progress(request_id, 1, "infer", 0)
                offset, scale = handles[str(request["model_handle"])]
                output = {"y": offset + scale * float(request["input"]["x"])}
                progress(request_id, 2, "infer", 2)
                emit(
                    request_id,
                    {
                        "model_handle": request["model_handle"],
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
