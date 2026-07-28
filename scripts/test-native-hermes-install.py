#!/usr/bin/env python3
"""Validate one Wright wheel through a clean native Hermes lifecycle fixture."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time
from typing import Mapping, Sequence


FORBIDDEN_EXECUTABLES = frozenset(
    {"git", "docker", "node", "nodejs", "npm", "npx", "pnpm"}
)
RUNTIME_ONLY_IMPORTS = (
    "fastapi",
    "uvicorn",
    "mcp",
    "api",
    "data_vault",
    "tool_registry",
)
WHEEL_VERSION = re.compile(
    r"^wright_engineering-(?P<version>[^-]+)-[^-]+-[^-]+-[^-]+\.whl$",
    re.IGNORECASE,
)


class HarnessError(RuntimeError):
    """Raised when the clean-install acceptance contract is violated."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--previous-wheel", type=Path)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--hermes-version", default="0.19.0")
    parser.add_argument("--port", type=int)
    parser.add_argument(
        "--base-only",
        action="store_true",
        help="Run only package-plugin/base-isolation checks (not release evidence).",
    )
    return parser


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wheel_version(path: Path) -> str:
    match = WHEEL_VERSION.fullmatch(path.name)
    if match is None:
        raise HarnessError(f"not a Wright wheel: {path.name}")
    return match.group("version")


def _scripts(environment: Path) -> Path:
    return environment / ("Scripts" if os.name == "nt" else "bin")


def environment_python(environment: Path) -> Path:
    return _scripts(environment) / ("python.exe" if os.name == "nt" else "python")


def clean_child_environment(
    *, plugin_environment: Path, hermes_home: Path, port: int
) -> dict[str, str]:
    keep = {
        key: value
        for key, value in os.environ.items()
        if key
        in {
            "COMSPEC",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "TMPDIR",
            "LANG",
            "LC_ALL",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
        }
    }
    keep.update(
        {
            "PATH": str(_scripts(plugin_environment)),
            "HERMES_HOME": str(hermes_home),
            "HERMES_VERSION_OVERRIDE": "0.19.0",
            "HERMES_PLUGIN_INSTALL_CAPABILITY": "python-distribution-v1",
            "WRIGHT_NATIVE_PORT": str(port),
            "PYTHONNOUSERSITE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        }
    )
    for forbidden in ("PYTHONPATH", "WRIGHT_REPO_DIR", "VIRTUAL_ENV"):
        keep.pop(forbidden, None)
    return keep


def assert_forbidden_tools_inaccessible(environment: Mapping[str, str]) -> None:
    for executable in FORBIDDEN_EXECUTABLES:
        if shutil.which(executable, path=environment.get("PATH", "")):
            raise HarnessError(f"forbidden executable is reachable: {executable}")


def assert_source_isolation(
    *, cwd: Path, sys_path: Sequence[str], repository_root: Path
) -> None:
    root = repository_root.resolve(strict=False)
    if cwd.resolve(strict=False).is_relative_to(root):
        raise HarnessError("lifecycle working directory is inside the source checkout")
    for value in sys_path:
        if value and Path(value).resolve(strict=False).is_relative_to(root):
            raise HarnessError("installed interpreter leaked the source checkout")


class CommandAudit:
    def __init__(self) -> None:
        self.executables: list[str] = []
        self.forbidden: set[str] = set()

    def _record(self, executable: str | Path) -> None:
        name = Path(executable).name.lower()
        stem = Path(name).stem
        self.executables.append(name)
        if name in FORBIDDEN_EXECUTABLES or stem in FORBIDDEN_EXECUTABLES:
            self.forbidden.add(name)

    def run(
        self,
        command: Sequence[str | Path],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float = 600,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        rendered = [str(item) for item in command]
        self._record(rendered[0])
        process = subprocess.Popen(
            rendered,
            cwd=cwd,
            env=dict(env),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            if time.monotonic() >= deadline:
                process.kill()
                raise HarnessError(f"command timed out: {Path(rendered[0]).name}")
            try:
                import psutil

                for child in psutil.Process(process.pid).children(recursive=True):
                    try:
                        self._record(child.exe())
                    except (psutil.Error, OSError):
                        continue
            except (ImportError, OSError):
                pass
            time.sleep(0.01)
        stdout, stderr = process.communicate()
        completed = subprocess.CompletedProcess(
            rendered, process.returncode, stdout, stderr
        )
        if self.forbidden:
            raise HarnessError(
                "forbidden executable was invoked: " + ", ".join(sorted(self.forbidden))
            )
        if check and completed.returncode:
            bounded = (completed.stderr or completed.stdout or "")[-3000:]
            raise HarnessError(f"command failed ({Path(rendered[0]).name}): {bounded}")
        return completed


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _result(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    for line in reversed(completed.stdout.splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise HarnessError("native command did not return machine-readable JSON")


def _require_ok(result: dict[str, object], command: str) -> None:
    if result.get("ok") is not True:
        raise HarnessError(f"native {command} failed: {result.get('code')}")


def _artifact_environment(
    environment: Mapping[str, str], wheel: Path, *, channel: str = "local_candidate"
) -> dict[str, str]:
    updated = dict(environment)
    updated.update(
        {
            "WRIGHT_RUNTIME_ARTIFACT": str(wheel.resolve()),
            "WRIGHT_RUNTIME_VERSION": wheel_version(wheel),
            "WRIGHT_RUNTIME_CHANNEL": channel,
            "WRIGHT_RUNTIME_SHA256": sha256_file(wheel),
        }
    )
    return updated


def _native_command(
    audit: CommandAudit,
    python: Path,
    command: str,
    *,
    cwd: Path,
    env: Mapping[str, str],
    argument: str | None = None,
    check: bool = True,
) -> dict[str, object]:
    args: list[str | Path] = [python, "-m", "wright_engineering.cli", "native", command]
    if argument:
        args.append(argument)
    return _result(audit.run(args, cwd=cwd, env=env, check=check))


def _install_plugin_fixture(
    audit: CommandAudit,
    plugin_python: Path,
    wheel: Path,
    wheelhouse: Path,
    *,
    cwd: Path,
    env: Mapping[str, str],
) -> None:
    audit.run(
        [
            plugin_python,
            "-m",
            "pip",
            "install",
            "--no-index",
            "--only-binary=:all:",
            "--find-links",
            wheelhouse,
            wheel,
        ],
        cwd=cwd,
        env=env,
    )


def _verify_base_plugin(
    audit: CommandAudit,
    plugin_python: Path,
    *,
    cwd: Path,
    env: Mapping[str, str],
    repository_root: Path,
) -> dict[str, object]:
    probe = """
import importlib.metadata, json, pathlib, sys
class Context:
    def __init__(self): self.commands=[]; self.hooks=[]
    def register_command(self, **kwargs): self.commands.append(kwargs['name'])
    def register_hook(self, **kwargs): self.hooks.append(kwargs['name'])
entries = [e for e in importlib.metadata.entry_points(group='hermes_agent.plugins') if e.name == 'wright']
assert len(entries) == 1
ctx = Context(); entries[0].load()(ctx)
runtime_only = {'fastapi','uvicorn','mcp','api','data_vault','tool_registry'}
assert runtime_only.isdisjoint(sys.modules)
print(json.dumps({'commands':ctx.commands,'hooks':ctx.hooks,'sys_path':sys.path}))
"""
    completed = audit.run([plugin_python, "-I", "-c", probe], cwd=cwd, env=env)
    payload = json.loads(completed.stdout.splitlines()[-1])
    assert_source_isolation(
        cwd=cwd, sys_path=payload["sys_path"], repository_root=repository_root
    )
    if payload["commands"] != ["wright"]:
        raise HarnessError("Hermes discovered an invalid Wright entry point")
    return payload


def _copy_wheelhouse(source: Path, destination: Path, wheels: Sequence[Path]) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    for item in source.iterdir():
        if item.is_file() and item.suffix.lower() in {".whl", ".zip"}:
            shutil.copy2(item, destination / item.name)
    for item in wheels:
        target = destination / item.name
        if not target.exists():
            shutil.copy2(item, target)


def run_harness(args: argparse.Namespace) -> dict[str, object]:
    repository_root = Path(__file__).resolve().parents[1]
    wheel = args.wheel.resolve(strict=True)
    previous = args.previous_wheel.resolve(strict=True) if args.previous_wheel else None
    if not args.base_only and previous is None:
        raise HarnessError("full lifecycle evidence requires --previous-wheel")
    if previous is not None and wheel_version(previous) == wheel_version(wheel):
        raise HarnessError("previous stable wheel must have a different version")

    hermes_home = args.hermes_home.resolve(strict=False)
    if hermes_home.exists():
        raise HarnessError("Hermes test home must start absent")
    test_root = hermes_home.parent / f".{hermes_home.name}-acceptance"
    if test_root.exists():
        raise HarnessError("acceptance boundary must start absent")
    test_root.mkdir(parents=True)
    cwd = test_root / "source-isolated-cwd"
    cwd.mkdir()
    plugin_environment = test_root / "hermes-plugin-environment"
    local_wheelhouse = test_root / "wheelhouse"
    _copy_wheelhouse(
        args.wheelhouse.resolve(strict=True),
        local_wheelhouse,
        [item for item in (wheel, previous) if item is not None],
    )
    candidate = local_wheelhouse / wheel.name
    predecessor = local_wheelhouse / previous.name if previous else None
    port = args.port or _free_port()
    audit = CommandAudit()

    bootstrap_env = os.environ.copy()
    bootstrap_env.pop("PYTHONPATH", None)
    bootstrap_env.pop("WRIGHT_REPO_DIR", None)
    audit.run(
        [sys.executable, "-m", "venv", "--copies", plugin_environment],
        cwd=cwd,
        env=bootstrap_env,
    )
    plugin_python = environment_python(plugin_environment)
    environment = clean_child_environment(
        plugin_environment=plugin_environment,
        hermes_home=hermes_home,
        port=port,
    )
    environment["HERMES_VERSION_OVERRIDE"] = args.hermes_version
    assert_forbidden_tools_inaccessible(environment)
    _install_plugin_fixture(
        audit,
        plugin_python,
        candidate,
        local_wheelhouse,
        cwd=cwd,
        env=environment,
    )
    base_probe = _verify_base_plugin(
        audit,
        plugin_python,
        cwd=cwd,
        env=environment,
        repository_root=repository_root,
    )
    base_inventory = audit.run(
        [plugin_python, "-m", "pip", "freeze", "--all"],
        cwd=cwd,
        env=environment,
    ).stdout.splitlines()
    if any(
        item.lower().startswith(name + "==")
        for item in base_inventory
        for name in RUNTIME_ONLY_IMPORTS
    ):
        raise HarnessError("runtime dependency leaked into Hermes base environment")

    lifecycle: list[str] = ["install"]
    if args.base_only:
        return {
            "schema_version": 1,
            "status": "passed",
            "mode": "base-only",
            "platform": f"{platform.system().lower()}-{platform.release()}",
            "architecture": platform.machine().lower(),
            "source_isolation": True,
            "forbidden_executables": sorted(audit.forbidden),
            "base_inventory": sorted(base_inventory),
            "entry_point": base_probe,
            "lifecycle": lifecycle,
        }

    external_workspace = test_root / "external-workspace"
    external_workspace.mkdir()
    external_sentinel = external_workspace / "must-survive.txt"
    external_sentinel.write_text("external\n", encoding="utf-8")

    initial = predecessor or candidate
    active_environment = _artifact_environment(environment, initial)
    start = _native_command(
        audit, plugin_python, "start", cwd=cwd, env=active_environment
    )
    _require_ok(start, "start")
    lifecycle.append("start")
    status = _native_command(
        audit, plugin_python, "status", cwd=cwd, env=active_environment
    )
    _require_ok(status, "status")
    lifecycle.append("status")
    doctor = _native_command(
        audit, plugin_python, "doctor", cwd=cwd, env=active_environment
    )
    _require_ok(doctor, "doctor")
    lifecycle.append("doctor")

    with ThreadPoolExecutor(max_workers=2) as pool:
        concurrent = list(
            pool.map(
                lambda name: _native_command(
                    audit,
                    plugin_python,
                    name,
                    cwd=cwd,
                    env=active_environment,
                    check=False,
                ),
                ("start", "status"),
            )
        )
    if not any(item.get("ok") is True for item in concurrent):
        raise HarnessError("concurrent session probe produced no successful result")

    data_root = hermes_home / "wright" / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    preserved = data_root / "preserved-by-uninstall.txt"
    preserved.write_text("keep\n", encoding="utf-8")

    candidate_environment = _artifact_environment(environment, candidate)
    update = _native_command(
        audit,
        plugin_python,
        "update",
        argument=wheel_version(candidate),
        cwd=cwd,
        env=candidate_environment,
    )
    _require_ok(update, "update")
    lifecycle.append("update")
    rollback = _native_command(
        audit, plugin_python, "rollback", cwd=cwd, env=candidate_environment
    )
    _require_ok(rollback, "rollback")
    lifecycle.append("rollback")
    update_again = _native_command(
        audit,
        plugin_python,
        "update",
        argument=wheel_version(candidate),
        cwd=cwd,
        env=candidate_environment,
    )
    _require_ok(update_again, "update")

    stop = _native_command(
        audit, plugin_python, "stop", cwd=cwd, env=candidate_environment
    )
    _require_ok(stop, "stop")
    lifecycle.append("stop")
    restart = _native_command(
        audit, plugin_python, "start", cwd=cwd, env=candidate_environment
    )
    _require_ok(restart, "restart")

    uninstall = _native_command(
        audit, plugin_python, "uninstall", cwd=cwd, env=candidate_environment
    )
    _require_ok(uninstall, "uninstall")
    lifecycle.append("uninstall")
    if not preserved.is_file() or not external_sentinel.is_file():
        raise HarnessError("default uninstall removed user or external data")
    audit.run(
        [plugin_python, "-m", "pip", "uninstall", "-y", "wright-engineering"],
        cwd=cwd,
        env=environment,
    )
    _install_plugin_fixture(
        audit,
        plugin_python,
        candidate,
        local_wheelhouse,
        cwd=cwd,
        env=environment,
    )
    reinstall = _native_command(
        audit, plugin_python, "start", cwd=cwd, env=candidate_environment
    )
    _require_ok(reinstall, "reinstall")
    if not preserved.is_file():
        raise HarnessError("reinstall did not preserve Wright data")
    _require_ok(
        _native_command(
            audit, plugin_python, "stop", cwd=cwd, env=candidate_environment
        ),
        "stop",
    )

    preview = _native_command(
        audit,
        plugin_python,
        "purge",
        cwd=cwd,
        env=candidate_environment,
        check=False,
    )
    confirmation = str(dict(preview.get("details", {})).get("confirmation_code", ""))
    if not confirmation:
        raise HarnessError("purge did not disclose a confirmation-bound scope")
    purge = _native_command(
        audit,
        plugin_python,
        "purge",
        argument=confirmation,
        cwd=cwd,
        env=candidate_environment,
    )
    _require_ok(purge, "purge")
    lifecycle.append("purge")
    if data_root.exists() or not external_sentinel.is_file():
        raise HarnessError("purge boundaries did not match Wright-owned data")

    runtime_inventory = sorted(
        item.name
        for runtime_python in (hermes_home / "wright" / "runtimes").glob(
            "*/Scripts/python.exe" if os.name == "nt" else "*/bin/python"
        )
        for item in [runtime_python]
    )
    return {
        "schema_version": 1,
        "status": "passed",
        "mode": "candidate-fixture",
        "platform": f"{platform.system().lower()}-{platform.release()}",
        "architecture": platform.machine().lower(),
        "python": platform.python_version(),
        "hermes_version": args.hermes_version,
        "hermes_capability": "python-distribution-v1",
        "candidate": {
            "filename": candidate.name,
            "version": wheel_version(candidate),
            "sha256": sha256_file(candidate),
        },
        "previous_stable": {
            "filename": predecessor.name,
            "version": wheel_version(predecessor),
            "sha256": sha256_file(predecessor),
        },
        "source_isolation": True,
        "forbidden_executables": sorted(audit.forbidden),
        "observed_executables": sorted(set(audit.executables)),
        "base_inventory": sorted(base_inventory),
        "runtime_inventory_after_purge": runtime_inventory,
        "lifecycle": lifecycle,
        "data_preserved_on_uninstall": True,
        "purge_exact": True,
        "external_workspace_preserved": True,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        evidence = run_harness(args)
    except (HarnessError, OSError, subprocess.SubprocessError) as exc:
        print(f"native Hermes acceptance failed: {exc}", file=sys.stderr)
        return 1
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
