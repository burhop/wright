"""Standard-library bootstrap from a Hermes Git plugin into Wright-owned state."""

from __future__ import annotations

import json
import hashlib
import importlib.util
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import urllib.request
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence


WRIGHT_RUNTIME_VERSION = "0.1.9"
ADAPTER_PROTOCOL = "hermes-git-plugin-v1"
COMMAND_TIMEOUT_SECONDS = 600
RELEASE_MANIFEST = Path(__file__).with_name("runtime-release.json")


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
    release = _runtime_release()
    version = release["version"] if release else WRIGHT_RUNTIME_VERSION
    return (root or wright_home()) / "bootstrap" / version


def _runtime_release() -> dict[str, str] | None:
    """A generated development mirror selects one reviewed, immutable artifact."""
    if not RELEASE_MANIFEST.is_file():
        return None
    try:
        release = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
        version = release["version"]
        digest = release["sha256"]
        filename = f"wright_engineering-{version}-py3-none-any.whl"
        if (
            release["channel"] != "test"
            or not re.fullmatch(r"\d+\.\d+\.\d+\.dev\d+", version)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or not re.fullmatch(r"[0-9a-f]{40}", release["source_commit"])
            or not re.fullmatch(
                r"https://test-files\.pythonhosted\.org/packages/[0-9a-f/]+/"
                + re.escape(filename), release["url"]
            )
        ):
            raise ValueError("invalid development release identity")
        return release
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BootstrapError("runtime_release_invalid") from exc


def _runtime_environment(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    release = _runtime_release()
    if release and not env.get("WRIGHT_RUNTIME_ARTIFACT", "").strip():
        wheelhouse = root / "cache" / "testpypi" / release["sha256"]
        env.update({
            "WRIGHT_RUNTIME_VERSION": release["version"],
            "WRIGHT_RUNTIME_CHANNEL": release["channel"],
            "WRIGHT_RUNTIME_SHA256": release["sha256"],
            "WRIGHT_RUNTIME_WHEELHOUSE": str(wheelhouse),
            "WRIGHT_RUNTIME_ARTIFACT": str(
                wheelhouse / f"wright_engineering-{release['version']}-py3-none-any.whl"
            ),
        })
    return env


def _prepare_release(python: Path, env: dict[str, str]) -> None:
    release = _runtime_release()
    if not release or os.environ.get("WRIGHT_RUNTIME_ARTIFACT", "").strip():
        return
    wheel = Path(env["WRIGHT_RUNTIME_ARTIFACT"])
    wheel.parent.mkdir(parents=True, exist_ok=True)
    if not wheel.is_file() or hashlib.sha256(wheel.read_bytes()).hexdigest() != release["sha256"]:
        temporary = wheel.with_suffix(".download")
        try:
            with urllib.request.urlopen(release["url"], timeout=60) as response:
                data = response.read(64 * 1024 * 1024 + 1)
            if hashlib.sha256(data).hexdigest() != release["sha256"]:
                raise BootstrapError("runtime_release_hash_mismatch")
            temporary.write_bytes(data)
            temporary.replace(wheel)
        finally:
            temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(wheel) as archive:
        provenance = json.loads(archive.read("wright_engineering/dev-release.json"))
    if (
        provenance.get("version") != release["version"]
        or provenance.get("source_commit") != release["source_commit"]
    ):
        raise BootstrapError("runtime_release_provenance_mismatch")
    # Resolve dependencies only on PyPI, then reuse the existing offline artifact
    # handoff for both bootstrap and the contained native runtime.
    _run([
        str(python), "-m", "pip", "download", "--only-binary=:all:",
        "--index-url", "https://pypi.org/simple", "--dest", str(wheel.parent),
        f"wright-engineering[runtime] @ {wheel.as_uri()}",
    ], env=env)


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
    env = _runtime_environment(root)
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
    _bind_invoking_hermes_sdk(env)
    return env


def _bind_invoking_hermes_sdk(env: dict[str, str]) -> None:
    """Discover a complete current-profile binding, without changing Hermes."""
    explicit = (
        "WRIGHT_WORKFLOW_MODEL_TRANSPORT", "HERMES_ROLE_PYTHON",
        "HERMES_ROLE_RUNTIME_ROOT", "HERMES_ROLE_PROFILE_HOME",
    )
    if any(key in env for key in explicit) or not env.get("HERMES_HOME"):
        return
    try:
        profile = Path(env["HERMES_HOME"]).expanduser().resolve(strict=True)
        specification = importlib.util.find_spec("hermes_cli")
        if not profile.is_dir() or specification is None or not specification.origin:
            return
        runtime = Path(specification.origin).resolve().parent.parent
        required = (
            "hermes_cli/runtime_provider.py", "hermes_cli/profiles.py",
            "hermes_cli/env_loader.py", "agent/auxiliary_client.py", "hermes_constants.py",
        )
        if not Path(sys.executable).is_file() or not all((runtime / name).is_file() for name in required):
            return
    except (OSError, ImportError, ValueError):
        return
    env.update({
        "WRIGHT_WORKFLOW_MODEL_TRANSPORT": "hermes-model-sdk",
        "HERMES_ROLE_PYTHON": sys.executable,
        "HERMES_ROLE_RUNTIME_ROOT": str(runtime),
        "HERMES_ROLE_PROFILE_HOME": str(profile),
    })


def _install_target() -> tuple[str, list[str]]:
    env = _runtime_environment(wright_home())
    artifact = env.get("WRIGHT_RUNTIME_ARTIFACT", "").strip()
    if artifact:
        wheel = Path(artifact).expanduser().resolve(strict=True)
        configured = env.get("WRIGHT_RUNTIME_WHEELHOUSE", "").strip()
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
            _prepare_release(python, env)
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
