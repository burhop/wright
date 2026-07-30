#!/usr/bin/env python3
"""Validate a Wright candidate through released Hermes' real Git plugin path."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import platform
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Mapping, Sequence
from urllib.request import Request, urlopen


FORBIDDEN_EXECUTABLES = frozenset(
    {"git", "docker", "node", "nodejs", "npm", "npx", "pnpm"}
)
WHEEL_VERSION = re.compile(
    r"^wright_engineering-(?P<version>[^-]+)-[^-]+-[^-]+-[^-]+\.whl$",
    re.IGNORECASE,
)
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


class HarnessError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--previous-wheel", type=Path)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--wright-home", type=Path)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--plugin-source", type=Path)
    parser.add_argument("--hermes-command", default="hermes")
    parser.add_argument("--codex-command", default="codex")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--hermes-version", default="0.19.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--runtime-smoke", action="store_true")
    return parser


def _command_prefix(command: str, script: Path | None = None) -> list[str]:
    resolved = shutil.which(command) or command
    if script is not None:
        return [resolved, str(script.resolve(strict=True))]
    if os.name == "nt" and Path(resolved).suffix.lower() in {".bat", ".cmd"}:
        return [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", resolved]
    return [resolved]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wheel_version(path: Path) -> str:
    match = WHEEL_VERSION.fullmatch(path.name)
    if match is None:
        raise HarnessError(f"not a Wright wheel: {path.name}")
    return match.group("version")


def _scripts(environment: Path) -> Path:
    return environment / ("Scripts" if os.name == "nt" else "bin")


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
            "WRIGHT_HOME": str(hermes_home.parent / "wright-home"),
            "WRIGHT_MANAGER_ID": "hermes",
            "WRIGHT_MANAGER_PROTOCOL": "hermes-git-plugin-v1",
            "WRIGHT_MANAGER_VERSION": "0.19.0",
            "WRIGHT_NATIVE_PORT": str(port),
            "PYTHONNOUSERSITE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        }
    )
    for forbidden in ("PYTHONPATH", "WRIGHT_REPO_DIR", "VIRTUAL_ENV"):
        keep.pop(forbidden, None)
    return keep


def hermes_install_environment(
    *,
    hermes_home: Path,
    test_root: Path,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Keep Hermes' Git staging directory on the plugin destination volume."""
    environment = dict(base_environment or os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("WRIGHT_REPO_DIR", None)
    manager_temp = test_root / "manager-temp"
    manager_temp.mkdir(parents=True, exist_ok=True)
    environment["HERMES_HOME"] = str(hermes_home)
    for variable in ("TEMP", "TMP", "TMPDIR"):
        environment[variable] = str(manager_temp)
    return environment


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

    def _record(self, executable: str | Path, *, enforce: bool = True) -> None:
        name = Path(executable).name.lower()
        stem = Path(name).stem
        self.executables.append(name)
        if enforce and (name in FORBIDDEN_EXECUTABLES or stem in FORBIDDEN_EXECUTABLES):
            self.forbidden.add(name)

    def run(
        self,
        command: Sequence[str | Path],
        *,
        cwd: Path,
        env: Mapping[str, str],
        timeout: float = 600,
        check: bool = True,
        enforce_forbidden: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        rendered = [str(item) for item in command]
        self._record(rendered[0], enforce=enforce_forbidden)
        process = subprocess.Popen(
            rendered,
            cwd=cwd,
            env=dict(env),
            text=True,
            encoding="utf-8",
            errors="replace",
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
            except ImportError:
                children = []
            else:
                try:
                    children = psutil.Process(process.pid).children(recursive=True)
                except (psutil.Error, OSError):
                    children = []
                for child in children:
                    try:
                        self._record(child.exe(), enforce=enforce_forbidden)
                    except (psutil.Error, OSError):
                        pass
            time.sleep(0.01)
        stdout, stderr = process.communicate()
        if check and process.returncode:
            raise HarnessError((stderr or stdout)[-3000:])
        return subprocess.CompletedProcess(rendered, process.returncode, stdout, stderr)


def _json_result(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError:
        document = None
    if isinstance(document, dict):
        return document
    for line in reversed(completed.stdout.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise HarnessError("command did not return JSON")


def _artifact_environment(
    environment: Mapping[str, str], wheel: Path
) -> dict[str, str]:
    result = dict(environment)
    result.update(
        {
            "WRIGHT_RUNTIME_ARTIFACT": str(wheel),
            "WRIGHT_RUNTIME_VERSION": wheel_version(wheel),
            "WRIGHT_RUNTIME_CHANNEL": "local_candidate",
            "WRIGHT_RUNTIME_SHA256": sha256_file(wheel),
        }
    )
    return result


def _adapter_lifecycle(
    audit: CommandAudit,
    plugin_dir: Path,
    command: str,
    *,
    cwd: Path,
    env: Mapping[str, str],
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
    completed = audit.run(
        [
            sys.executable,
            "-c",
            script,
            plugin_dir / "bootstrap.py",
            command,
            argument or "",
        ],
        cwd=cwd,
        env=env,
    )
    result = _json_result(completed)
    if require_ok and result.get("ok") is not True:
        raise HarnessError(
            f"native {command} failed: "
            + json.dumps(result, sort_keys=True, separators=(",", ":"))
        )
    return result


def _make_adapter_subject(
    audit: CommandAudit, source: Path, destination: Path, *, env: Mapping[str, str]
) -> tuple[Path, str]:
    shutil.copytree(source, destination)
    for command in (
        ["git", "init"],
        ["git", "config", "user.name", "Wright Candidate"],
        ["git", "config", "user.email", "candidate@wright.invalid"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "Immutable Wright adapter candidate"],
    ):
        audit.run(
            command,
            cwd=destination,
            env=env,
            enforce_forbidden=False,
        )
    identity = audit.run(
        ["git", "rev-parse", "HEAD"],
        cwd=destination,
        env=env,
        enforce_forbidden=False,
    ).stdout.strip()
    return destination, identity


def _verify_adapter_import(plugin_dir: Path) -> dict[str, object]:
    spec = importlib.util.spec_from_file_location(
        "wright_candidate_adapter",
        plugin_dir / "__init__.py",
        submodule_search_locations=[str(plugin_dir)],
    )
    if spec is None or spec.loader is None:
        raise HarnessError("adapter_import_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    class Context:
        def __init__(self) -> None:
            self.commands: list[str] = []

        def register_command(self, **kwargs: object) -> None:
            self.commands.append(str(kwargs["name"]))

    try:
        spec.loader.exec_module(module)
        context = Context()
        module.register(context)
    finally:
        sys.modules.pop(spec.name, None)
    if context.commands != ["wright"]:
        raise HarnessError("Hermes discovered an invalid Wright command")
    return {"commands": context.commands, "hooks": []}


def _bootstrap_commands(wright_home: Path, version: str) -> tuple[Path, Path]:
    environment = wright_home / "bootstrap" / version
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    wright = environment / ("Scripts/wright.exe" if os.name == "nt" else "bin/wright")
    if not python.is_file() or not wright.is_file():
        raise HarnessError("installed manager bridge command is missing")
    return python, wright


def _create_manager_workspace(*, wright_home: Path, port: int) -> dict[str, str]:
    token_path = wright_home / "data" / "control-plane.token"
    token = token_path.read_text(encoding="utf-8").strip()
    if not token:
        raise HarnessError("native control-plane token is missing")
    request = Request(  # noqa: S310 - fixed loopback acceptance endpoint
        f"http://127.0.0.1:{port}/api/workspace/create",
        data=json.dumps({"name": "Manager Acceptance"}).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Origin": f"http://127.0.0.1:{port}",
        },
    )
    with urlopen(request, timeout=30) as response:  # noqa: S310 - loopback only
        payload = json.loads(response.read())
    required = ("workspace_id", "session_id", "local_path")
    if not isinstance(payload, dict) or any(not payload.get(key) for key in required):
        raise HarnessError("workspace creation returned an invalid identity")
    path = Path(str(payload["local_path"])).resolve(strict=True)
    managed = (wright_home / "data" / "workspaces").resolve(strict=True)
    if not path.is_relative_to(managed):
        raise HarnessError("manager probe workspace escaped WRIGHT_HOME")
    return {key: str(payload[key]) for key in required}


def _installed_manager_profile(
    audit: CommandAudit,
    *,
    python: Path,
    wright: Path,
    manager_id: str,
    workspace: Mapping[str, str],
    wright_home: Path,
    port: int,
    cwd: Path,
    env: Mapping[str, str],
) -> dict[str, object]:
    script = (
        "import json,sys;"
        "from wright_engineering.manager_profiles import build_manager_profile;"
        "p=build_manager_profile(sys.argv[1],workspace=sys.argv[2],"
        "session_id=sys.argv[3],workspace_id=sys.argv[4],wright_home=sys.argv[5],"
        "api_url=sys.argv[6],wright_command=sys.argv[7]);"
        "print(json.dumps(p.as_mcp_config(),sort_keys=True))"
    )
    completed = audit.run(
        [
            python,
            "-c",
            script,
            manager_id,
            workspace["local_path"],
            workspace["session_id"],
            workspace["workspace_id"],
            wright_home,
            f"http://127.0.0.1:{port}",
            wright,
        ],
        cwd=cwd,
        env=env,
    )
    profile = _json_result(completed)
    if profile.get("command") != str(wright):
        raise HarnessError(f"{manager_id} profile did not use installed Wright")
    return profile


async def _probe_stdio_profile_async(
    profile: Mapping[str, object],
    *,
    inherited_env: Mapping[str, str],
    cwd: Path,
    workspace: Mapping[str, str],
) -> dict[str, object]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    configured_env = profile.get("env")
    if not isinstance(configured_env, dict):
        raise HarnessError("manager STDIO profile environment is invalid")
    child_env = dict(inherited_env)
    child_env.update({str(key): str(value) for key, value in configured_env.items()})
    parameters = StdioServerParameters(
        command=str(profile["command"]),
        args=[str(item) for item in profile.get("args", [])],
        env=child_env,
        cwd=cwd,
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as client:
            initialized = await client.initialize()
            tools = await client.list_tools()
            names = {item.name for item in tools.tools}
            if "wright__workspace_status" not in names:
                raise HarnessError("manager profile did not list Wright tools")
            result = await client.call_tool("wright__workspace_status", {})
    if result.isError:
        raise HarnessError("manager profile safe tool call failed")
    serialized = result.model_dump(mode="json", by_alias=True)
    encoded = json.dumps(serialized, sort_keys=True)
    if (
        workspace["workspace_id"] not in encoded
        or workspace["session_id"] not in encoded
    ):
        raise HarnessError("manager profile returned the wrong workspace binding")
    return {
        "protocol_version": str(initialized.protocolVersion),
        "tool_count": len(names),
        "safe_tool": "wright__workspace_status",
        "workspace_binding_verified": True,
    }


def _probe_stdio_profile(
    profile: Mapping[str, object],
    *,
    inherited_env: Mapping[str, str],
    cwd: Path,
    workspace: Mapping[str, str],
) -> dict[str, object]:
    return asyncio.run(
        _probe_stdio_profile_async(
            profile, inherited_env=inherited_env, cwd=cwd, workspace=workspace
        )
    )


def _toml_string(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=True)


def _codex_profile_check(
    audit: CommandAudit,
    *,
    command: str,
    profile: Mapping[str, object],
    cwd: Path,
    env: Mapping[str, str],
) -> dict[str, object]:
    profile_env = profile.get("env")
    if not isinstance(profile_env, dict):
        raise HarnessError("Codex profile environment is invalid")
    args = ", ".join(_toml_string(item) for item in profile.get("args", []))
    values = ", ".join(
        f"{key} = {_toml_string(value)}" for key, value in profile_env.items()
    )
    override = (
        "mcp_servers.wright={ command = "
        f"{_toml_string(profile['command'])}, args = [{args}], env = {{{values}}} }}"
    )
    prefix = _command_prefix(command)
    version = audit.run(
        [*prefix, "--version"],
        cwd=cwd,
        env=env,
        enforce_forbidden=False,
    ).stdout.strip()
    completed = audit.run(
        [*prefix, "mcp", "-c", override, "get", "wright", "--json"],
        cwd=cwd,
        env=env,
        enforce_forbidden=False,
    )
    rendered = _json_result(completed)
    transport = rendered.get("transport")
    if (
        not isinstance(transport, dict)
        or transport.get("command") != profile["command"]
    ):
        raise HarnessError("Codex did not load the Wright STDIO profile")
    if transport.get("args") != profile.get("args"):
        raise HarnessError("Codex changed the Wright STDIO arguments")
    return {
        "version": version,
        "profile_loaded": True,
        "transport": str(transport.get("type", "")),
    }


def run_harness(args: argparse.Namespace) -> dict[str, object]:
    repository_root = Path(__file__).resolve().parents[1]
    wheel = args.wheel.resolve(strict=True)
    previous = args.previous_wheel.resolve(strict=True) if args.previous_wheel else None
    if args.base_only and args.runtime_smoke:
        raise HarnessError("--base-only and --runtime-smoke are mutually exclusive")
    if not args.base_only and not args.runtime_smoke and previous is None:
        raise HarnessError("full lifecycle evidence requires --previous-wheel")
    hermes_home = args.hermes_home.resolve(strict=False)
    if hermes_home.exists():
        raise HarnessError("Hermes test home must start absent")
    test_root = hermes_home.parent / f".{hermes_home.name}-acceptance"
    if test_root.exists():
        raise HarnessError("acceptance boundary must start absent")
    test_root.mkdir(parents=True)
    cwd = test_root / "source-isolated-cwd"
    cwd.mkdir()
    audit = CommandAudit()
    install_env = hermes_install_environment(
        hermes_home=hermes_home,
        test_root=test_root,
    )
    adapter_source = args.plugin_source or repository_root / "hermes-plugin-wright"
    adapter_repo, adapter_identity = _make_adapter_subject(
        audit,
        adapter_source.resolve(strict=True),
        test_root / "adapter-subject",
        env=install_env,
    )
    audit.run(
        [args.hermes_command, "plugins", "install", adapter_repo.as_uri(), "--enable"],
        cwd=cwd,
        env=install_env,
        enforce_forbidden=False,
    )
    plugin_dir = hermes_home / "plugins" / "wright"
    installed_identity = audit.run(
        ["git", "-C", plugin_dir, "rev-parse", "HEAD"],
        cwd=cwd,
        env=install_env,
        enforce_forbidden=False,
    ).stdout.strip()
    if installed_identity != adapter_identity:
        raise HarnessError("Hermes installed an unexpected adapter commit")
    base_probe = _verify_adapter_import(plugin_dir)
    lifecycle = ["install"]
    if args.base_only:
        return {
            "schema_version": 2,
            "status": "passed",
            "mode": "real-hermes-git-adapter",
            "platform": f"{platform.system().lower()}-{platform.release()}",
            "architecture": platform.machine().lower(),
            "source_isolation": True,
            "adapter_identity": adapter_identity,
            "adapter_protocol": "hermes-git-plugin-v1",
            "adapter_executables": sorted(set(audit.executables)),
            "forbidden_executables": [],
            "entry_point": base_probe,
            "lifecycle": lifecycle,
        }

    runtime_env_dir = test_root / "runtime-command-environment"
    audit.run(
        [sys.executable, "-m", "venv", "--copies", runtime_env_dir],
        cwd=cwd,
        env=install_env,
        enforce_forbidden=False,
    )
    environment = clean_child_environment(
        plugin_environment=runtime_env_dir,
        hermes_home=hermes_home,
        port=args.port,
    )
    environment["WRIGHT_HOME"] = str(
        (args.wright_home or test_root / "wright-home").resolve(strict=False)
    )
    environment["WRIGHT_RUNTIME_WHEELHOUSE"] = str(args.wheelhouse.resolve(strict=True))
    environment["WRIGHT_MANAGER_VERSION"] = args.hermes_version
    assert_forbidden_tools_inaccessible(environment)
    initial = previous or wheel
    active = _artifact_environment(environment, initial)
    for command in ("start", "status", "doctor"):
        _adapter_lifecycle(audit, plugin_dir, command, cwd=cwd, env=active)
        lifecycle.append(command)
    if args.runtime_smoke:
        for command in ("stop", "uninstall"):
            _adapter_lifecycle(audit, plugin_dir, command, cwd=cwd, env=active)
            lifecycle.append(command)
        return {
            "schema_version": 2,
            "status": "passed",
            "mode": "real-hermes-git-adapter-runtime-smoke",
            "platform": f"{platform.system().lower()}-{platform.release()}",
            "architecture": platform.machine().lower(),
            "python": platform.python_version(),
            "hermes_version": args.hermes_version,
            "adapter_protocol": "hermes-git-plugin-v1",
            "adapter_identity": adapter_identity,
            "candidate": {
                "filename": wheel.name,
                "version": wheel_version(wheel),
                "sha256": sha256_file(wheel),
            },
            "source_isolation": True,
            "forbidden_executables": sorted(audit.forbidden),
            "observed_executables": sorted(set(audit.executables)),
            "lifecycle": lifecycle,
        }
    data_root = Path(environment["WRIGHT_HOME"]) / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    preserved = data_root / "preserved.txt"
    preserved.write_text("keep\n", encoding="utf-8")
    candidate = _artifact_environment(environment, wheel)
    _adapter_lifecycle(
        audit,
        plugin_dir,
        "update",
        argument=wheel_version(wheel),
        cwd=cwd,
        env=candidate,
    )
    lifecycle.append("update")
    _adapter_lifecycle(audit, plugin_dir, "rollback", cwd=cwd, env=candidate)
    lifecycle.append("rollback")
    _adapter_lifecycle(
        audit,
        plugin_dir,
        "update",
        argument=wheel_version(wheel),
        cwd=cwd,
        env=candidate,
    )
    wright_home = Path(environment["WRIGHT_HOME"])
    workspace = _create_manager_workspace(wright_home=wright_home, port=args.port)
    bridge_python, bridge_command = _bootstrap_commands(
        wright_home, wheel_version(wheel)
    )
    manager_profiles: dict[str, object] = {}
    profiles = {
        manager_id: _installed_manager_profile(
            audit,
            python=bridge_python,
            wright=bridge_command,
            manager_id=manager_id,
            workspace=workspace,
            wright_home=wright_home,
            port=args.port,
            cwd=cwd,
            env=candidate,
        )
        for manager_id in ("codex",)
    }
    for manager_id, profile in profiles.items():
        audit._record(str(profile["command"]))
        manager_profiles[manager_id] = {
            "adapter_protocol": "mcp-v1",
            "transport": "stdio",
            "hermes_intermediary": False,
            "sdk_probe": _probe_stdio_profile(
                profile,
                inherited_env=candidate,
                cwd=cwd,
                workspace=workspace,
            ),
        }
    manager_profiles["codex"]["manager_probe"] = _codex_profile_check(
        audit,
        command=args.codex_command,
        profile=profiles["codex"],
        cwd=cwd,
        env=install_env,
    )
    _adapter_lifecycle(audit, plugin_dir, "stop", cwd=cwd, env=candidate)
    lifecycle.append("stop")
    _adapter_lifecycle(audit, plugin_dir, "uninstall", cwd=cwd, env=candidate)
    lifecycle.append("uninstall")
    if not preserved.is_file():
        raise HarnessError("default uninstall removed Wright data")
    _adapter_lifecycle(audit, plugin_dir, "start", cwd=cwd, env=candidate)
    _adapter_lifecycle(audit, plugin_dir, "stop", cwd=cwd, env=candidate)
    if not preserved.is_file():
        raise HarnessError("reinstall did not preserve Wright data")
    preview = _adapter_lifecycle(
        audit,
        plugin_dir,
        "purge",
        cwd=cwd,
        env=candidate,
        require_ok=False,
    )
    confirmation = str(dict(preview.get("details", {})).get("confirmation_code", ""))
    if not confirmation:
        raise HarnessError("purge did not disclose a confirmation code")
    _adapter_lifecycle(
        audit,
        plugin_dir,
        "purge",
        argument=confirmation,
        cwd=cwd,
        env=candidate,
    )
    lifecycle.append("purge")
    audit.run(
        [args.hermes_command, "plugins", "remove", "wright"],
        cwd=cwd,
        env=install_env,
        enforce_forbidden=False,
    )
    if data_root.exists():
        raise HarnessError("purge left Wright-owned data behind")
    if audit.forbidden:
        raise HarnessError(
            "post-adapter lifecycle invoked forbidden tools: "
            + ", ".join(sorted(audit.forbidden))
        )
    return {
        "schema_version": 2,
        "status": "passed",
        "mode": "real-hermes-git-adapter",
        "platform": f"{platform.system().lower()}-{platform.release()}",
        "architecture": platform.machine().lower(),
        "python": platform.python_version(),
        "hermes_version": args.hermes_version,
        "adapter_protocol": "hermes-git-plugin-v1",
        "adapter_identity": adapter_identity,
        "candidate": {
            "filename": wheel.name,
            "version": wheel_version(wheel),
            "sha256": sha256_file(wheel),
        },
        "previous_stable": {
            "filename": previous.name,
            "version": wheel_version(previous),
            "sha256": sha256_file(previous),
        },
        "source_isolation": True,
        "forbidden_executables": sorted(audit.forbidden),
        "observed_executables": sorted(set(audit.executables)),
        "manager_profiles": manager_profiles,
        "manager_workspace": {
            "workspace_id": workspace["workspace_id"],
            "session_id": workspace["session_id"],
            "local_path_under_wright_home": True,
        },
        "lifecycle": lifecycle,
        "data_preserved_on_uninstall": True,
        "reinstall_preserved_data": True,
        "purge_exact": True,
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
