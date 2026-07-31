#!/usr/bin/env python3
"""Verify published Wright artifacts through released Hermes' real Git plugin."""

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

from release.hermes_capability import require_released_git_plugin_interface


FORBIDDEN = {"git", "docker", "node", "nodejs", "npm", "npx", "pnpm"}
BASE_LIFECYCLE = (
    "install",
    "start",
    "status",
    "doctor",
    "stop",
    "uninstall",
    "purge",
)


def _run(
    command: Sequence[str | Path],
    *,
    env: Mapping[str, str],
    cwd: Path,
    timeout: float = 600,
    allow_executables: frozenset[str] = frozenset(),
) -> subprocess.CompletedProcess[str]:
    rendered = [str(item) for item in command]
    # Temporary files avoid a Windows deadlock when a lifecycle command starts
    # a background runtime that inherits the parent's redirected handles. A
    # pipe-backed communicate() waits for every inheriting descendant to close
    # the pipe even after the lifecycle command itself has exited.
    with (
        tempfile.TemporaryFile(
            mode="w+", encoding="utf-8", errors="replace"
        ) as stdout_file,
        tempfile.TemporaryFile(
            mode="w+", encoding="utf-8", errors="replace"
        ) as stderr_file,
    ):
        process = subprocess.Popen(
            rendered,
            cwd=cwd,
            env=dict(env),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=stdout_file,
            stderr=stderr_file,
        )
        observed: set[str] = {Path(rendered[0]).stem.lower()}
        deadline = time.monotonic() + timeout
        while process.poll() is None:
            if time.monotonic() >= deadline:
                process.kill()
                process.wait()
                raise RuntimeError("published Hermes command timed out")
            try:
                import psutil
            except ImportError:
                pass
            else:
                try:
                    children = psutil.Process(process.pid).children(recursive=True)
                    for child in children:
                        try:
                            observed.add(Path(child.exe()).stem.lower())
                        except (psutil.Error, OSError):
                            pass
                except (psutil.Error, OSError):
                    pass
            time.sleep(0.01)
        process.wait()
        stdout_file.flush()
        stderr_file.flush()
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read()
        stderr = stderr_file.read()
    forbidden = (observed & FORBIDDEN) - set(allow_executables)
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


def _adapter_lifecycle(
    plugin_dir: Path,
    command: str,
    *,
    env: Mapping[str, str],
    cwd: Path,
    argument: str | None = None,
    require_ok: bool = True,
) -> dict[str, object]:
    script = (
        "import importlib.util,json,pathlib,sys;"
        "p=pathlib.Path(sys.argv[1]);"
        "s=importlib.util.spec_from_file_location('wright_adapter_bootstrap',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.invoke_lifecycle(sys.argv[2],sys.argv[3] or None),sort_keys=True))"
    )
    args: list[str | Path] = [
        sys.executable,
        "-c",
        script,
        plugin_dir / "bootstrap.py",
        command,
        argument or "",
    ]
    result = _json_result(_run(args, env=env, cwd=cwd))
    if require_ok and result.get("ok") is not True:
        raise RuntimeError(f"native {command} failed: {result.get('code')}")
    return result


def _failed_doctor_checks(result: Mapping[str, object]) -> list[str]:
    details = result.get("details")
    if not isinstance(details, dict):
        return []
    checks = details.get("checks")
    if not isinstance(checks, dict):
        return []
    return sorted(
        str(name)
        for name, value in checks.items()
        if not isinstance(value, dict) or value.get("ok") is not True
    )


def _wait_for_doctor(
    plugin_dir: Path,
    *,
    env: Mapping[str, str],
    cwd: Path,
    timeout: float = 30,
    interval: float = 0.5,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    while True:
        result = _adapter_lifecycle(
            plugin_dir,
            "doctor",
            env=env,
            cwd=cwd,
            require_ok=False,
        )
        if result.get("ok") is True:
            return result
        if time.monotonic() >= deadline:
            failed = ",".join(_failed_doctor_checks(result)) or "unknown"
            raise RuntimeError(
                "native doctor did not become healthy: "
                f"code={result.get('code')} failed_checks={failed}"
            )
        time.sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--previous-version")
    parser.add_argument("--hermes-version", default="0.19.0")
    parser.add_argument("--plugin-source", required=True)
    parser.add_argument("--plugin-identity", required=True)
    parser.add_argument("--wright-commit", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    interface = require_released_git_plugin_interface()
    if interface.version != args.hermes_version:
        raise RuntimeError(
            f"Hermes version mismatch: expected {args.hermes_version}, "
            f"observed {interface.version}"
        )
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
        env["WRIGHT_HOME"] = str(root / "wright")
        env["WRIGHT_MANAGER_ID"] = "hermes"
        env["WRIGHT_MANAGER_PROTOCOL"] = interface.adapter_protocol
        env["WRIGHT_MANAGER_VERSION"] = interface.version
        previous = (
            _download(args.previous_version, wheelhouse, env)
            if args.previous_version
            else None
        )
        candidate = _download(args.version, wheelhouse, env)
        initial = previous or candidate
        env.update(
            {
                "WRIGHT_RUNTIME_ARTIFACT": str(initial),
                "WRIGHT_RUNTIME_VERSION": args.previous_version or args.version,
                "WRIGHT_RUNTIME_CHANNEL": "stable",
                "WRIGHT_RUNTIME_SHA256": _sha256(initial),
            }
        )
        _run(
            ["hermes", "plugins", "install", args.plugin_source, "--enable"],
            env=env,
            cwd=cwd,
            allow_executables=frozenset({"git"}),
        )
        plugin_dir = hermes_home / "plugins" / "wright"
        if not (plugin_dir / "bootstrap.py").is_file():
            raise RuntimeError("Hermes did not install the Wright Git adapter")
        expected_adapter = args.plugin_identity.removeprefix("git:")
        installed_adapter = _run(
            ["git", "-C", plugin_dir, "rev-parse", "HEAD"],
            env=env,
            cwd=cwd,
            allow_executables=frozenset({"git"}),
        ).stdout.strip()
        if installed_adapter != expected_adapter:
            raise RuntimeError(
                "installed Hermes adapter identity mismatch: "
                f"expected {expected_adapter}, observed {installed_adapter}"
            )
        provenance_path = plugin_dir / "provenance.json"
        if not provenance_path.is_file():
            raise RuntimeError("installed Hermes adapter has no provenance.json")
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance.get("commit_sha") != args.wright_commit:
            raise RuntimeError(
                "Hermes adapter provenance does not match the Wright release commit"
            )
        _adapter_lifecycle(plugin_dir, "start", env=env, cwd=cwd)
        _adapter_lifecycle(plugin_dir, "status", env=env, cwd=cwd)
        _wait_for_doctor(plugin_dir, env=env, cwd=cwd)
        lifecycle = ["install", "start", "status", "doctor"]
        data = Path(env["WRIGHT_HOME"]) / "data"
        data.mkdir(parents=True, exist_ok=True)
        sentinel = data / "published-lifecycle.txt"
        sentinel.write_text("preserve\n", encoding="utf-8")

        env.update(
            {
                "WRIGHT_RUNTIME_ARTIFACT": str(candidate),
                "WRIGHT_RUNTIME_VERSION": args.version,
                "WRIGHT_RUNTIME_SHA256": _sha256(candidate),
            }
        )
        _run(
            ["hermes", "plugins", "update", "wright"],
            env=env,
            cwd=cwd,
            allow_executables=frozenset({"git"}),
        )
        updated_adapter = _run(
            ["git", "-C", plugin_dir, "rev-parse", "HEAD"],
            env=env,
            cwd=cwd,
            allow_executables=frozenset({"git"}),
        ).stdout.strip()
        if updated_adapter != expected_adapter:
            raise RuntimeError(
                "Hermes adapter changed identity during release verification"
            )
        if previous is not None:
            _adapter_lifecycle(
                plugin_dir, "update", argument=args.version, env=env, cwd=cwd
            )
            lifecycle.append("update")
            _adapter_lifecycle(plugin_dir, "rollback", env=env, cwd=cwd)
            lifecycle.append("rollback")
            _adapter_lifecycle(
                plugin_dir, "update", argument=args.version, env=env, cwd=cwd
            )
        _adapter_lifecycle(plugin_dir, "stop", env=env, cwd=cwd)
        lifecycle.append("stop")
        _adapter_lifecycle(plugin_dir, "uninstall", env=env, cwd=cwd)
        lifecycle.append("uninstall")
        if not sentinel.is_file():
            raise RuntimeError("published uninstall deleted retained data")
        _adapter_lifecycle(plugin_dir, "start", env=env, cwd=cwd)
        _adapter_lifecycle(plugin_dir, "stop", env=env, cwd=cwd)
        preview = _adapter_lifecycle(
            plugin_dir, "purge", env=env, cwd=cwd, require_ok=False
        )
        confirmation = str(
            dict(preview.get("details", {})).get("confirmation_code", "")
        )
        _adapter_lifecycle(plugin_dir, "purge", argument=confirmation, env=env, cwd=cwd)
        lifecycle.append("purge")
        _run(
            ["hermes", "plugins", "remove", "wright"],
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
            "hermes_version": interface.version,
            "adapter_protocol": interface.adapter_protocol,
            "adapter_identity": args.plugin_identity,
            "adapter_provenance_commit": args.wright_commit,
            "candidate": {
                "filename": candidate.name,
                "version": args.version,
                "sha256": _sha256(candidate),
            },
            "previous_stable": (
                {
                    "filename": previous.name,
                    "version": args.previous_version,
                    "sha256": _sha256(previous),
                }
                if previous is not None
                else None
            ),
            "release_mode": (
                "upgrade" if previous is not None else "initial_native_release"
            ),
            "lifecycle": lifecycle,
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
