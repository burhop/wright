"""Explicit selected KiCad setup through Docker and normal Wright APIs."""
import argparse
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

IMAGE = "sha256:eaaf00be76c3750bf5d0525f3637d8cf630232f13a249709a4adbdb2e12beda7"
CONTAINER = "wright-081-kicad-runtime"


def request(api, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    with urllib.request.urlopen(urllib.request.Request(api + path, data=data, method=method, headers={"Content-Type": "application/json"}), timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.attempt or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in args.attempt):
        raise ValueError("Invalid attempt component")
    workspace = args.workspace_root.resolve(strict=True)
    report = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {"operations": [], "image": IMAGE, "container": CONTAINER}
    def persist():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    if not report.get("container_started"):
        inspected = subprocess.run(["docker", "inspect", CONTAINER], capture_output=True, text=True, timeout=30)
        if inspected.returncode == 0:
            raise ValueError("Named runtime already exists without this setup receipt; inspect it, do not blindly replace")
        command = ["docker", "run", "--detach", "--name", CONTAINER, "--network", "none", "--cpus", "2", "--memory", "3g", "--entrypoint", "sleep"]
        mounts = []
        for index in range(1, 4):
            for name, readonly in [("inputs", True), ("artifacts", False)]:
                relative = f"campaign/sensor-interface-pcb-{index:02d}/{args.attempt}/{name}"
                path = (workspace / relative).resolve()
                if not path.is_relative_to(workspace):
                    raise ValueError("Unsafe campaign mount")
                path.mkdir(parents=True, exist_ok=True)
                if not readonly and any(path.iterdir()):
                    raise ValueError("New campaign output mount must be empty")
                mount = f"type=bind,source={path},target=/work/{relative}" + (",readonly" if readonly else "")
                command += ["--mount", mount]
                mounts.append({"host": str(path), "container": "/work/" + relative, "read_only": readonly})
        command += [IMAGE, "infinity"]
        launched = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)
        report.update(container_started=True, container_id=launched.stdout.strip(), mounts=mounts)
        persist()
    if "server_id" not in report:
        result = request(args.api, "POST", "/api/mcp/servers", {"name": "KiCad blwfish — selected engineering dataset runtime", "type": "stdio", "command": ["docker", "exec", "-i", "-e", "PYTHONPATH=", CONTAINER, "/opt/kicad-mcp/.venv/bin/python", "/opt/wright-kicad/server.py"], "category": "electronics", "description": "Isolated no-network KiCad9.0.2, pinned blwfish0.13.0 with stderr history repair, native ERC/DRC JSON report tool and FreeRouter2.2.4. Only three selected PCB attempt input/output directories mounted. Local prerequisite qualification, not manufacturing release.", "source_url": "https://github.com/blwfish/kicad-mcp/tree/bcc6f11de92e5f47cb7dde1d24565f7779b2fbed", "default_enabled": False, "risk_level": "medium", "deployment_mode": "local-only"})
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
