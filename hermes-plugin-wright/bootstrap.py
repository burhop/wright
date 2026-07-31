"""Standard-library bootstrap from a Hermes Git plugin into Wright-owned state."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence


WRIGHT_RUNTIME_VERSION = "0.1.9"
ADAPTER_PROTOCOL = "hermes-git-plugin-v1"
COMMAND_TIMEOUT_SECONDS = 600


class BootstrapError(RuntimeError):
    pass


def wright_home() -> Path:
    configured = os.environ.get("WRIGHT_HOME", "").strip()
    root = (
        Path(configured or Path.home() / ".wright").expanduser().resolve(strict=False)
    )
    if not root.is_absolute() or root == Path(root.anchor):
        raise BootstrapError("wright_home_unsafe")
    return root


def _environment_python(environment: Path) -> Path:
    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def bootstrap_environment(root: Path | None = None) -> Path:
    return (root or wright_home()) / "bootstrap" / WRIGHT_RUNTIME_VERSION


@contextmanager
def _bootstrap_lock(root: Path, timeout: float = 120.0) -> Iterator[None]:
    lock = root / "state" / "bootstrap.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    while True:
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise BootstrapError("bootstrap_busy")
            time.sleep(0.1)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def _run(
    command: Sequence[str],
    *,
    env: dict[str, str],
    require_success: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(command),
        env=env,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
    )
    if require_success and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "")[-2000:]
        raise BootstrapError(f"bootstrap_command_failed: {detail}")
    return completed


def _child_environment(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "WRIGHT_HOME": str(root),
            "WRIGHT_MANAGER_ID": "hermes",
            "WRIGHT_MANAGER_PROTOCOL": ADAPTER_PROTOCOL,
            "WRIGHT_MANAGER_VERSION": env.get("WRIGHT_MANAGER_VERSION", "0.19.0"),
            "PYTHONNOUSERSITE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        }
    )
    env.pop("WRIGHT_REPO_DIR", None)
    env.pop("PYTHONPATH", None)
    return env


def _install_target() -> tuple[str, list[str]]:
    artifact = os.environ.get("WRIGHT_RUNTIME_ARTIFACT", "").strip()
    if artifact:
        wheel = Path(artifact).expanduser().resolve(strict=True)
        configured = os.environ.get("WRIGHT_RUNTIME_WHEELHOUSE", "").strip()
        wheelhouse = (
            Path(configured).expanduser().resolve(strict=True)
            if configured
            else wheel.parent
        )
        if not wheelhouse.is_dir():
            raise BootstrapError("runtime_wheelhouse_invalid")
        options = ["--no-index", "--find-links", str(wheelhouse)]
        return f"wright-engineering[runtime] @ {wheel.as_uri()}", options
    return f"wright-engineering[runtime]=={WRIGHT_RUNTIME_VERSION}", []


def ensure_bootstrap() -> Path:
    root = wright_home()
    environment = bootstrap_environment(root)
    python = _environment_python(environment)
    ready = environment / ".wright-bootstrap-ready"
    if python.is_file() and ready.is_file():
        return python
    with _bootstrap_lock(root):
        if python.is_file() and ready.is_file():
            return python
        if environment.exists():
            shutil.rmtree(environment)
        env = _child_environment(root)
        try:
            _run(
                [sys.executable, "-m", "venv", "--copies", str(environment)],
                env=env,
            )
            target, options = _install_target()
            _run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--only-binary=:all:",
                    target,
                    *options,
                ],
                env=env,
            )
            ready.write_text("ready\n", encoding="utf-8")
        except Exception:
            shutil.rmtree(environment, ignore_errors=True)
            raise
    return python


def _prepare_adapter_removal(plugin_root: Path | None = None) -> None:
    """Clear Windows read-only Git pack bits that Hermes 0.19 cannot remove."""
    if not _is_windows():
        return
    root = (plugin_root or Path(__file__).resolve().parent).resolve(strict=False)
    metadata = root / ".git"
    if not metadata.is_dir() or metadata.is_symlink():
        return
    try:
        for current, directories, filenames in os.walk(metadata, followlinks=False):
            current_path = Path(current)
            for name in (*directories, *filenames):
                path = current_path / name
                if not path.is_symlink():
                    path.chmod(path.stat().st_mode | stat.S_IWRITE)
    except OSError as exc:
        raise BootstrapError("adapter_removal_prepare_failed") from exc


def _is_windows() -> bool:
    return os.name == "nt"


def invoke_lifecycle(command: str, argument: str | None = None) -> dict[str, object]:
    if command not in {
        "start",
        "status",
        "doctor",
        "stop",
        "update",
        "rollback",
        "uninstall",
        "purge",
    }:
        raise BootstrapError("unsupported_lifecycle_command")
    root = wright_home()
    python = ensure_bootstrap()
    rendered = [str(python), "-m", "wright_engineering.cli", "native", command]
    if argument:
        rendered.append(argument)
    completed = _run(
        rendered,
        env=_child_environment(root),
        require_success=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise BootstrapError("lifecycle_result_invalid") from exc
    if not isinstance(payload, dict):
        raise BootstrapError("lifecycle_result_invalid")
    if command in {"uninstall", "purge"} and payload.get("ok") is True:
        shutil.rmtree(bootstrap_environment(root), ignore_errors=True)
        _prepare_adapter_removal()
    return payload
