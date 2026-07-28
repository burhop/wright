#!/usr/bin/env python3
"""Verify published Wright artifacts through a released package-capable Hermes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time
from typing import Mapping, Sequence

from release.hermes_capability import require_released_package_capability


FORBIDDEN = {"git", "docker", "node", "nodejs", "npm", "npx", "pnpm"}
LIFECYCLE = (
    "install",
    "start",
    "status",
    "doctor",
    "stop",
    "update",
    "rollback",
    "uninstall",
    "purge",
)


def _run(
    command: Sequence[str | Path],
    *,
    env: Mapping[str, str],
    cwd: Path,
    timeout: float = 600,
) -> subprocess.CompletedProcess[str]:
    rendered = [str(item) for item in command]
    process = subprocess.Popen(
        rendered,
        cwd=cwd,
        env=dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    observed: set[str] = {Path(rendered[0]).stem.lower()}
    deadline = time.monotonic() + timeout
    while process.poll() is None:
        if time.monotonic() >= deadline:
            process.kill()
            raise RuntimeError("published Hermes command timed out")
        try:
            import psutil

            for child in psutil.Process(process.pid).children(recursive=True):
                try:
                    observed.add(Path(child.exe()).stem.lower())
                except (psutil.Error, OSError):
                    pass
        except (ImportError, OSError):
            pass
        time.sleep(0.01)
    stdout, stderr = process.communicate()
    forbidden = observed & FORBIDDEN
    if forbidden:
        raise RuntimeError(
            "forbidden executable invoked: " + ", ".join(sorted(forbidden))
        )
    if process.returncode:
        raise RuntimeError((stderr or stdout)[-3000:])
    return subprocess.CompletedProcess(rendered, process.returncode, stdout, stderr)


def _json_result(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    for line in reversed(completed.stdout.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise RuntimeError("command did not return JSON")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download(version: str, wheelhouse: Path, env: Mapping[str, str]) -> Path:
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--only-binary=:all:",
            "--dest",
            wheelhouse,
            f"wright-engineering[runtime]=={version}",
        ],
        env=env,
        cwd=wheelhouse.parent,
    )
    matches = list(wheelhouse.glob(f"wright_engineering-{version}-*.whl"))
    if len(matches) != 1:
        raise RuntimeError(f"expected one published Wright {version} wheel")
    return matches[0]


def _plugin_action(
    action: str,
    version: str,
    *,
    wheel: Path,
    env: Mapping[str, str],
    cwd: Path,
) -> dict[str, object]:
    command: list[str | Path] = [
        "hermes",
        "plugins",
        action,
        f"wright-engineering=={version}",
        "--expected-sha256",
        _sha256(wheel),
        "--json",
    ]
    if action == "install-package":
        command.append("--enable")
    return _json_result(_run(command, env=env, cwd=cwd))


def _native(
    python: Path,
    command: str,
    *,
    env: Mapping[str, str],
    cwd: Path,
    argument: str | None = None,
) -> dict[str, object]:
    args: list[str | Path] = [python, "-m", "wright_engineering.cli", "native", command]
    if argument:
        args.append(argument)
    result = _json_result(_run(args, env=env, cwd=cwd))
    if result.get("ok") is not True:
        raise RuntimeError(f"native {command} failed: {result.get('code')}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--previous-version", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    capability = require_released_package_capability()
    with tempfile.TemporaryDirectory(prefix="wright-published-hermes-") as value:
        root = Path(value)
        wheelhouse = root / "wheelhouse"
        wheelhouse.mkdir()
        hermes_home = root / "hermes"
        cwd = root / "isolated"
        cwd.mkdir()
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("WRIGHT_REPO_DIR", None)
        env["HERMES_HOME"] = str(hermes_home)
        env["HERMES_PLUGIN_INSTALL_CAPABILITY"] = capability.capability or ""
        env["HERMES_VERSION_OVERRIDE"] = capability.version
        previous = _download(args.previous_version, wheelhouse, env)
        candidate = _download(args.version, wheelhouse, env)
        installed = _plugin_action(
            "install-package",
            args.previous_version,
            wheel=previous,
            env=env,
            cwd=cwd,
        )
        python = Path(str(installed.get("python_executable", "")))
        if not python.is_file():
            raise RuntimeError("Hermes did not report its managed plugin interpreter")
        env.update(
            {
                "WRIGHT_RUNTIME_ARTIFACT": str(previous),
                "WRIGHT_RUNTIME_VERSION": args.previous_version,
                "WRIGHT_RUNTIME_CHANNEL": "stable",
                "WRIGHT_RUNTIME_SHA256": _sha256(previous),
            }
        )
        _native(python, "start", env=env, cwd=cwd)
        _native(python, "status", env=env, cwd=cwd)
        _native(python, "doctor", env=env, cwd=cwd)
        data = hermes_home / "wright" / "data"
        data.mkdir(parents=True, exist_ok=True)
        sentinel = data / "published-lifecycle.txt"
        sentinel.write_text("preserve\n", encoding="utf-8")

        updated = _plugin_action(
            "update-package", args.version, wheel=candidate, env=env, cwd=cwd
        )
        python = Path(str(updated.get("python_executable", "")))
        env.update(
            {
                "WRIGHT_RUNTIME_ARTIFACT": str(candidate),
                "WRIGHT_RUNTIME_VERSION": args.version,
                "WRIGHT_RUNTIME_SHA256": _sha256(candidate),
            }
        )
        _native(python, "update", argument=args.version, env=env, cwd=cwd)
        _native(python, "rollback", env=env, cwd=cwd)
        _native(python, "update", argument=args.version, env=env, cwd=cwd)
        _native(python, "stop", env=env, cwd=cwd)
        _native(python, "uninstall", env=env, cwd=cwd)
        if not sentinel.is_file():
            raise RuntimeError("published uninstall deleted retained data")
        _plugin_action(
            "rollback-package",
            args.previous_version,
            wheel=previous,
            env=env,
            cwd=cwd,
        )
        current = _plugin_action(
            "update-package", args.version, wheel=candidate, env=env, cwd=cwd
        )
        python = Path(str(current.get("python_executable", "")))
        _native(python, "start", env=env, cwd=cwd)
        _native(python, "stop", env=env, cwd=cwd)
        preview = _json_result(
            _run(
                [python, "-m", "wright_engineering.cli", "native", "purge"],
                env=env,
                cwd=cwd,
            )
        )
        confirmation = str(
            dict(preview.get("details", {})).get("confirmation_code", "")
        )
        _native(python, "purge", argument=confirmation, env=env, cwd=cwd)
        _run(
            ["hermes", "plugins", "remove-package", "wright-engineering", "--json"],
            env=env,
            cwd=cwd,
        )
        if data.exists():
            raise RuntimeError("published purge left Wright data behind")
        evidence = {
            "schema_version": 1,
            "status": "passed",
            "platform": f"{platform.system().lower()}-{platform.release()}",
            "architecture": platform.machine().lower(),
            "source_isolation": True,
            "forbidden_executables": [],
            "hermes_version": capability.version,
            "hermes_capability": capability.capability,
            "candidate": {
                "filename": candidate.name,
                "version": args.version,
                "sha256": _sha256(candidate),
            },
            "previous_stable": {
                "filename": previous.name,
                "version": args.previous_version,
                "sha256": _sha256(previous),
            },
            "lifecycle": list(LIFECYCLE),
            "data_preserved_on_uninstall": True,
            "purge_exact": True,
        }
    args.evidence.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
