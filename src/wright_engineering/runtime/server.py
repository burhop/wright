"""Packaged Wright API/UI bootstrap for the isolated runtime process."""

from __future__ import annotations

import hashlib
import os
from importlib.resources import files
from pathlib import Path
from typing import Any, MutableMapping

from .layout import NativeLayout


class ServerBootstrapError(RuntimeError):
    pass


def packaged_static_path() -> Path:
    candidate = Path(str(files("wright_engineering.static").joinpath("web")))
    if not (candidate / "index.html").is_file():
        raise ServerBootstrapError("packaged_ui_missing")
    return candidate


def prepare_runtime_environment(
    layout: NativeLayout,
    *,
    static_path: Path | None = None,
    bind_host: str = "127.0.0.1",
    port: int = 8000,
    environment: MutableMapping[str, str] | None = None,
) -> dict[str, str]:
    layout.ensure()
    static = (static_path or packaged_static_path()).resolve(strict=False)
    if not (static / "index.html").is_file():
        raise ServerBootstrapError("packaged_ui_missing")
    values = {
        "WRIGHT_NATIVE_RUNTIME": "1",
        "WRIGHT_DATA_ROOT": str(layout.data),
        "DATABASE_PATH": str(layout.data / "wright.db"),
        "FRONTEND_DIST_DIR": str(static),
        "WRIGHT_WORKSPACE_ROOT": str(layout.workspaces),
        "WRIGHT_WORKSPACES_DIR": str(layout.workspaces),
        "WRIGHT_LOG_DIR": str(layout.logs),
        "WRIGHT_BIND_HOST": bind_host,
        "WRIGHT_ALLOWED_ORIGINS": ",".join(
            dict.fromkeys(
                (
                    f"http://{bind_host}:{port}",
                    f"http://127.0.0.1:{port}",
                    f"http://localhost:{port}",
                )
            )
        ),
    }
    target_environment = os.environ if environment is None else environment
    target_environment.update(values)
    return values


def runtime_identity_payload() -> dict[str, Any]:
    challenge = os.environ.get("WRIGHT_RUNTIME_CHALLENGE", "")
    if not challenge:
        raise ServerBootstrapError("runtime_challenge_missing")
    return {
        "product": "wright",
        "pid": os.getpid(),
        "runtime_id": os.environ.get("WRIGHT_RUNTIME_ID", ""),
        "instance_id": os.environ.get("WRIGHT_RUNTIME_INSTANCE_ID", ""),
        "operation_id": os.environ.get("WRIGHT_RUNTIME_OPERATION_ID", ""),
        "challenge_hash": hashlib.sha256(challenge.encode("utf-8")).hexdigest(),
    }


def serve(
    *,
    host: str,
    port: int,
    data_root: Path,
    static_path: Path | None = None,
) -> None:
    layout = NativeLayout.from_wright_home(data_root.parent)
    if data_root.resolve(strict=False) != layout.data:
        raise ServerBootstrapError("data_root_outside_layout")
    prepare_runtime_environment(
        layout, static_path=static_path, bind_host=host, port=port
    )
    import uvicorn

    uvicorn.run("api.main:app", host=host, port=port, log_config=None)
