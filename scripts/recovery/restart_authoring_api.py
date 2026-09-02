"""Restart one verified local authoring API, preserving its environment privately.

This operator helper records only source identity, file-count and health state;
it never serializes process environment variables or workflow contents.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

import psutil


BACKEND_SOURCE_FILES = (
    "apps/api/src/api/main.py",
    "apps/api/src/api/routers/workspace.py",
    "apps/api/src/api/schemas/workspace.py",
    "packages/workspace_service/src/workspace_service/workflow_sources.py",
)
OPERATOR_SOURCE_FILE = "scripts/recovery/restart_authoring_api.py"
MODULE_SOURCE_FILES = {
    "api.main": "apps/api/src/api/main.py",
    "workspace_service.workflow_sources": "packages/workspace_service/src/workspace_service/workflow_sources.py",
}

# Resolve the two leaf modules without importing either application package.
# Python's normal site initialization is retained to match the API environment.
MODULE_ORIGIN_PROBE = """
import importlib.machinery
import importlib.util
import json
from pathlib import Path

origins = {}
for name in ("api.main", "workspace_service.workflow_sources"):
    package = name.rsplit(".", 1)[0]
    parent = importlib.util.find_spec(package)
    if parent is None or parent.submodule_search_locations is None:
        raise RuntimeError("Expected application package is unavailable")
    leaf = importlib.machinery.PathFinder.find_spec(name, parent.submodule_search_locations)
    if leaf is None or leaf.origin is None:
        raise RuntimeError("Expected application source is unavailable")
    origins[name] = str(Path(leaf.origin).resolve())
print(json.dumps(origins))
"""


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise RuntimeError("Unable to verify clean committed code identity")
    return result.stdout.strip()


def snapshot_code_identity(repo: Path) -> dict[str, object]:
    if git_output(repo, "status", "--porcelain", "--untracked-files=no") or git_output(
        repo,
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        "apps/api/src",
        "packages/workspace_service/src",
    ):
        raise RuntimeError("Restart provenance requires clean committed source")
    git_output(
        repo,
        "ls-files",
        "--error-unmatch",
        "--",
        *BACKEND_SOURCE_FILES,
        OPERATOR_SOURCE_FILE,
    )

    def file_identity(relative: str) -> dict[str, str]:
        path = (repo / relative).resolve(strict=True)
        if not path.is_relative_to(repo):
            raise RuntimeError("Code identity escaped the expected checkout")
        return {
            "path": relative,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    return {
        "git_commit": git_output(repo, "rev-parse", "HEAD"),
        "git_tree": git_output(repo, "rev-parse", "HEAD^{tree}"),
        "tracked_worktree_clean": True,
        "backend_files": [file_identity(relative) for relative in BACKEND_SOURCE_FILES],
        "operator_helper": file_identity(OPERATOR_SOURCE_FILE),
    }


def validate_module_origins(repo: Path, origins: object) -> dict[str, dict[str, str]]:
    if not isinstance(origins, dict) or set(origins) != set(MODULE_SOURCE_FILES):
        raise RuntimeError("Module origins do not match the expected checkout")
    verified = {}
    for name, relative in MODULE_SOURCE_FILES.items():
        origin = origins[name]
        expected = repo / relative
        if not isinstance(origin, str) or Path(origin) != expected:
            raise RuntimeError("Module origin is outside the expected checkout")
        path = expected.resolve(strict=True)
        if not path.is_relative_to(repo):
            raise RuntimeError("Module origin is outside the expected checkout")
        verified[name] = {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return verified


def probe_module_origins(
    repo: Path, environment: dict[str, str]
) -> dict[str, dict[str, str]]:
    result = subprocess.run(
        [str(repo / ".venv/Scripts/python.exe"), "-B", "-c", MODULE_ORIGIN_PROBE],
        cwd=repo / "apps/api",
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise RuntimeError("Read-only module-origin probe failed")
    try:
        origins = json.loads(result.stdout)
    except ValueError as error:
        raise RuntimeError(
            "Read-only module-origin probe returned invalid output"
        ) from error
    return validate_module_origins(repo, origins)


def capture_code_provenance(
    repo: Path, environment: dict[str, str]
) -> dict[str, object]:
    before = snapshot_code_identity(repo)
    origins = probe_module_origins(repo, environment)
    if snapshot_code_identity(repo) != before:
        raise RuntimeError("Backend code changed during the module-origin probe")
    hashes = {value["path"]: value["sha256"] for value in before["backend_files"]}
    if any(
        origins[name]["sha256"] != hashes[relative]
        for name, relative in MODULE_SOURCE_FILES.items()
    ):
        raise RuntimeError("Backend code changed during the module-origin probe")
    return {
        **before,
        "module_origins": origins,
        "origin_method": "same-venv-env-cwd PathFinder probe; application packages not imported",
    }


def validate_api_process_command(
    repo: Path, port: int, command: list[str], cwd: Path | str
) -> None:
    """Allow only the exact local command this one-off helper can recreate.

    Windows uvicorn launchers run either directly or under their same-worktree
    Python launcher. Reject extra/reordered flags rather than silently dropping
    reload/worker/bind behavior when restarting an unrelated process.
    """
    executable = repo / ".venv/Scripts/uvicorn.exe"
    python = repo / ".venv/Scripts/python.exe"
    suffix = ["api.main:app", "--host", "127.0.0.1", "--port", str(port)]
    direct = (
        len(command) == len(suffix) + 1
        and Path(command[0]) == executable
        and command[1:] == suffix
    )
    wrapped = (
        len(command) == len(suffix) + 2
        and Path(command[0]) == python
        and Path(command[1]) == executable
        and command[2:] == suffix
    )
    if (
        not 1 <= port <= 65535
        or Path(cwd).resolve() != repo / "apps/api"
        or not (direct or wrapped)
    ):
        raise RuntimeError("The requested process is not the exact owned API")


def find_launched_api_listener(
    launcher_pid: int, repo: Path, port: int
) -> psutil.Process:
    launcher = psutil.Process(launcher_pid)
    candidates = [launcher, *launcher.children(recursive=True)]
    for candidate in candidates:
        try:
            if not any(
                connection.laddr.port == port and connection.status == "LISTEN"
                for connection in candidate.net_connections(kind="inet")
            ):
                continue
            validate_api_process_command(
                repo, port, candidate.cmdline(), candidate.cwd()
            )
            return candidate
        except psutil.NoSuchProcess:
            continue
    raise RuntimeError("The launched API process tree does not own its listening port")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    evidence = args.evidence.resolve()
    if not evidence.is_relative_to(repo / ".local-run"):
        raise RuntimeError(
            "Restart evidence must stay inside the checkout's .local-run directory"
        )
    process = psutil.Process(args.pid)
    executable = repo / ".venv/Scripts/uvicorn.exe"
    command = process.cmdline()
    validate_api_process_command(repo, args.port, command, process.cwd())
    if not any(
        connection.laddr.port == args.port and connection.status == "LISTEN"
        for connection in process.net_connections(kind="inet")
    ):
        raise RuntimeError("The requested process does not own the API listening port")
    base = f"http://127.0.0.1:{args.port}"

    def get(route: str):
        with urllib.request.urlopen(base + route, timeout=10) as response:
            if "application/json" not in response.headers.get("Content-Type", ""):
                raise RuntimeError("The API route did not return JSON")
            return json.load(response)

    source_route = "/api/workspace/workflow-sources?" + urllib.parse.urlencode(
        {"session_id": args.session, "path": args.source}
    )
    before = get(source_route)
    if before["workspace_id"] != args.workspace or before["path"] != args.source:
        raise RuntimeError("The before-state was not the exact workspace document")
    files_route = (
        "/api/workspace/workflow-sources/input-files?"
        + urllib.parse.urlencode({"session_id": args.session})
    )
    before_files = get(files_route)
    if before_files["workspace_id"] != args.workspace:
        raise RuntimeError("File choices were not scoped to the requested workspace")
    before_documents = {args.source: before}
    for choice in before_files["files"]:
        if choice["path"].startswith("workflows/") and choice["path"].endswith(
            ".workflow.wflow"
        ):
            route = "/api/workspace/workflow-sources?" + urllib.parse.urlencode(
                {"session_id": args.session, "path": choice["path"]}
            )
            before_documents[choice["path"]] = get(route)
    environment = process.environ()  # carried in memory only, never printed
    code_before = capture_code_provenance(repo, environment)
    evidence.mkdir(parents=True, exist_ok=False)
    process.terminate()
    process.wait(timeout=15)
    with (
        (evidence / "stdout.log").open("wb") as stdout,
        (evidence / "stderr.log").open("wb") as stderr,
    ):
        child = subprocess.Popen(
            [
                str(executable),
                "api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
            ],
            cwd=repo / "apps/api",
            env=environment,
            stdout=stdout,
            stderr=stderr,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    for attempt in range(30):
        try:
            after = get(source_route)
            break
        except (OSError, ValueError):
            if child.poll() is not None or attempt == 29:
                raise RuntimeError(
                    "Restarted API is unavailable; inspect the scoped restart log"
                )
            time.sleep(1)
    keys = (
        "workspace_id",
        "path",
        "storage_revision",
        "storage_digest",
        "definition_revision",
        "source",
    )
    if any(before[key] != after[key] for key in keys):
        raise RuntimeError("Existing source changed across restart")
    verified_documents = []
    for path, original in before_documents.items():
        current = get(
            "/api/workspace/workflow-sources?"
            + urllib.parse.urlencode({"session_id": args.session, "path": path})
        )
        if any(original[key] != current[key] for key in keys):
            raise RuntimeError("A workspace workflow changed across restart")
        verified_documents.append(
            {
                "path": path,
                "storage_revision": current["storage_revision"],
                "storage_digest": current["storage_digest"],
                "definition_revision": current["definition_revision"],
                "layout_revision": current["layout_revision"],
                "layout_status": current["layout_status"],
            }
        )
    files = get(files_route)
    if files["workspace_id"] != args.workspace:
        raise RuntimeError("File choices were not scoped to the requested workspace")
    listener = find_launched_api_listener(child.pid, repo, args.port)
    code_after = capture_code_provenance(repo, listener.environ())
    if code_after != code_before:
        raise RuntimeError("Committed code or module origins changed across restart")
    result = {
        "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "previous_pid": args.pid,
        "launcher_pid": child.pid,
        "listener_pid": listener.pid,
        "listener_parent_pid": listener.ppid(),
        "listener_started_at_epoch": listener.create_time(),
        "listener_cwd": listener.cwd(),
        "listener_command": listener.cmdline(),
        "port": args.port,
        "code_provenance": code_after,
        "code_identity_unchanged_across_restart": True,
        "source_unchanged": True,
        "source_sha256": hashlib.sha256(after["source"].encode()).hexdigest(),
        "storage_revision": after["storage_revision"],
        "storage_digest": after["storage_digest"],
        "definition_revision": after["definition_revision"],
        "layout_revision": after["layout_revision"],
        "layout_status": after["layout_status"],
        "workspace_id": files["workspace_id"],
        "verified_documents": verified_documents,
        "input_file_count": len(files["files"]),
        "agent_health_state": get("/api/agent/health").get("state"),
    }
    (evidence / "verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
