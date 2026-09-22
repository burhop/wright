"""Explicit selected KiCad setup through Docker and normal Wright APIs."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request

IMAGE = "sha256:eaaf00be76c3750bf5d0525f3637d8cf630232f13a249709a4adbdb2e12beda7"
RUNTIMES = {
    "sensor-interface-pcb": {
        "container": "wright-081-kicad-runtime",
        "name": "KiCad blwfish — selected engineering dataset runtime",
        "description": (
            "Isolated no-network KiCad9.0.2, pinned blwfish0.13.0 with stderr "
            "history repair, native ERC/DRC JSON report tool and FreeRouter2.2.4. "
            "Only three selected PCB attempt input/output directories mounted. "
            "Local prerequisite qualification, not manufacturing release."
        ),
    },
    "sensor-fan-harness": {
        "container": "wright-082-harness-kicad-runtime",
        "name": "KiCad blwfish — selected harness interconnect runtime",
        "description": (
            "Isolated no-network KiCad9.0.2, pinned blwfish0.13.0 for the "
            "independent harness interconnect handoff. Only three exact harness "
            "attempt input directories are mounted read-only and their artifact "
            "directories read/write. No PCB fabrication or physical action."
        ),
    },
}


def selected_runtime(family, container=None):
    runtime = dict(RUNTIMES[family])
    if container is not None:
        if not re.fullmatch(r"wright-[a-zA-Z0-9-]{1,80}", container):
            raise ValueError("Use an explicit confined Wright runtime name")
        if container != runtime["container"]:
            runtime["name"] += " (" + container + ")"
        runtime["container"] = container
    return runtime


def validate_runtime(info, report):
    if info.get("Id") != report.get("container_id") or info.get("Image") != report.get("image"):
        raise ValueError("Observed KiCad runtime identity/image differs from the setup receipt")
    if not info.get("State", {}).get("Running"):
        raise ValueError("Selected KiCad runtime is stopped")
    actual = {(str(Path(m["Source"]).resolve()).casefold(), m["Destination"], not m["RW"])
              for m in info.get("Mounts", []) if m["Type"] == "bind"}
    expected = {(str(Path(m["host"]).resolve()).casefold(), m["container"], m["read_only"])
                for m in report["mounts"]}
    if actual != expected:
        raise ValueError("Observed KiCad mounts differ from the exact attempt receipt")


def campaign_mount_specs(workspace: Path, family: str, attempt: str) -> list[dict]:
    """Return the six exact per-attempt mounts for one approved campaign family."""
    mounts = []
    for index in range(1, 4):
        for name, readonly in (("inputs", True), ("artifacts", False)):
            relative = f"campaign/{family}-{index:02d}/{attempt}/{name}"
            path = (workspace / relative).resolve()
            if not path.is_relative_to(workspace):
                raise ValueError("Unsafe campaign mount")
            mounts.append(
                {
                    "host": path,
                    "container": "/work/" + relative,
                    "read_only": readonly,
                }
            )
    return mounts


def request(api, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    with urllib.request.urlopen(urllib.request.Request(api + path, data=data, method=method, headers={"Content-Type": "application/json"}), timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--family", choices=sorted(RUNTIMES), default="sensor-interface-pcb")
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--container", help="Separate owned runtime for a successor; never replaces an existing container")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.attempt or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in args.attempt):
        raise ValueError("Invalid attempt component")
    workspace = args.workspace_root.resolve(strict=True)
    runtime = selected_runtime(args.family, args.container)
    container = runtime["container"]
    report = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {
        "operations": [],
        "image": IMAGE,
        "container": container,
        "family": args.family,
        "attempt": args.attempt,
    }
    if report.get("container") != container or report.get("family") != args.family or report.get("attempt") != args.attempt or report.get("image") != IMAGE:
        raise ValueError("Existing setup receipt belongs to a different runtime family or attempt")
    def persist():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    if not report.get("container_started"):
        inspected = subprocess.run(["docker", "inspect", container], capture_output=True, text=True, timeout=30)
        if inspected.returncode == 0:
            raise ValueError("Named runtime already exists without this setup receipt; inspect it, do not blindly replace")
        command = ["docker", "run", "--detach", "--name", container, "--network", "none", "--cpus", "2", "--memory", "3g", "--entrypoint", "sleep"]
        mounts = []
        for spec in campaign_mount_specs(workspace, args.family, args.attempt):
            path = spec["host"]
            path.mkdir(parents=True, exist_ok=True)
            mount = f"type=bind,source={path},target={spec['container']}" + (",readonly" if spec["read_only"] else "")
            command += ["--mount", mount]
            mounts.append({**spec, "host": str(path)})
        command += [IMAGE, "infinity"]
        launched = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)
        report.update(container_started=True, container_id=launched.stdout.strip(), mounts=mounts)
        persist()
    observed = json.loads(subprocess.check_output(["docker", "inspect", container], text=True, timeout=30))[0]
    validate_runtime(observed, report)
    if "server_id" not in report:
        result = request(args.api, "POST", "/api/mcp/servers", {"name": runtime["name"], "type": "stdio", "command": ["docker", "exec", "-i", "-e", "PYTHONPATH=", container, "/opt/kicad-mcp/.venv/bin/python", "/opt/wright-kicad/server.py"], "category": "electronics", "description": runtime["description"], "source_url": "https://github.com/blwfish/kicad-mcp/tree/bcc6f11de92e5f47cb7dde1d24565f7779b2fbed", "default_enabled": False, "risk_level": "medium", "deployment_mode": "local-only"})
        report["server_id"] = result["server_id"]
        report["operations"].append({"stage": "register", "result": result})
        persist()
    identity = report["server_id"]
    for stage, method, path, body in [
        ("install", "POST", "/api/mcp/servers/" + identity + "/install?session_id=" + urllib.parse.quote(args.session), None),
        ("enable_demo", "POST", "/api/workspace/tools/toggle", {"session_id": args.session, "server_id": identity, "is_enabled": True}),
        ("activate", "PATCH", "/api/mcp/servers/" + identity, {"is_active": True}),
    ]:
        if any(item["stage"] == stage for item in report["operations"]):
            continue
        result = request(args.api, method, path, body)
        report["operations"].append({"stage": stage, "result": result})
        persist()
    tools = request(args.api, "GET", "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session))
    report["tools"] = [tool for tool in tools["tools"] if tool["server_id"] == identity]
    report["status"] = "installed_discovered" if len(report["tools"]) == 18 else "tool_discovery_incomplete"
    persist()
    print(json.dumps({"status": report["status"], "server_id": identity, "tools": len(report["tools"])}))


if __name__ == "__main__":
    main()
