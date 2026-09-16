"""Install only the qualified selected Modelica campaign sidecar; no workflow dispatch."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import urllib.parse
import urllib.request

IMAGE = "sha256:e5dc37e5cde7722fa9547962b438548122def738019b85f380f9cb84d4b2bc47"
CONTAINER = "wright-081-modelica-runtime"


def attempt_mounts(workspace, attempts):
    """Declare only named dataset/attempt roots; never mount the whole workspace."""
    attempts = list(attempts or ["attempt-001"])
    if len(set(attempts)) != len(attempts) or any(not re.fullmatch(r"attempt-[A-Za-z0-9-]{1,40}", value) for value in attempts):
        raise ValueError("Unique explicit attempt IDs are required for export mounts")
    workspace = workspace.resolve()
    mounts = []
    for attempt in attempts:
        for index in range(1, 4):
            dataset = f"water-heater-sizing-{index:02d}"
            path = (workspace / "campaign" / dataset / attempt / "artifacts").resolve()
            if not path.is_relative_to(workspace):
                raise ValueError("Unsafe output mount")
            mounts.append({"host": str(path), "container": f"/exports/{dataset}/{attempt}", "read_only": False})
    return mounts


def request(api, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    with urllib.request.urlopen(urllib.request.Request(api + path, data=data, method=method, headers={"Content-Type": "application/json"}), timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--refresh-unregistered", action="store_true")
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--attempt", action="append", help="Repeat to declare exact export attempts for a new container; default attempt-001.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    args = parser.parse_args()
    workspace = args.workspace_root.resolve(strict=True)
    exports = attempt_mounts(workspace, args.attempt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = json.loads(args.output.read_text(encoding="utf-8")) if args.output.exists() else {"image": IMAGE, "container": CONTAINER, "operations": []}
    if args.attempt and report.get("container_started"):
        recorded = {(m["host"], m["container"]) for m in report.get("mounts", [])}
        if not {(m["host"], m["container"]) for m in exports}.issubset(recorded):
            raise ValueError("Existing recorded container lacks requested attempt mounts; extend its idle mounts explicitly before claiming readiness")

    def persist():
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.refresh_unregistered:
        if "server_id" in report or not report.get("container_started"):
            raise ValueError("Refresh is only for this recorded, unregistered idle runtime")
        processes = subprocess.check_output(["docker", "top", CONTAINER], text=True).strip().splitlines()
        if [line.split(None, 7)[-1] for line in processes[1:]] != ["sleep infinity"] or any((args.output.parent / "production-runs").iterdir()):
            raise ValueError("Runtime is not idle with an empty native store")
        archive = args.output.parent / ("installation-before-" + IMAGE.split(":")[1][:12] + ".json")
        archive.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        subprocess.run(["docker", "stop", CONTAINER], check=True, capture_output=True, timeout=30)
        subprocess.run(["docker", "rm", CONTAINER], check=True, capture_output=True, timeout=30)
        report = {"image": IMAGE, "container": CONTAINER, "operations": []}
        persist()

    if not report.get("container_started"):
        existing = subprocess.run(["docker", "inspect", CONTAINER], capture_output=True, text=True, timeout=30)
        if existing.returncode == 0:
            raise ValueError("Unrecorded named runtime exists; inspect instead of replacing")
        native = (args.output.parent / "production-runs").resolve()
        native.mkdir(exist_ok=True)
        if any(native.iterdir()):
            raise ValueError("New production native store must be empty")
        command = ["docker", "run", "--detach", "--name", CONTAINER, "--network", "none", "--cpus", "2", "--memory", "3g", "--entrypoint", "sleep", "--mount", f"type=bind,source={native},target=/runs"]
        mounts = [{"host": str(native), "container": "/runs", "read_only": False}]
        for mount in exports:
            path = Path(mount["host"])
            path.mkdir(parents=True, exist_ok=True)
            if any(path.iterdir()):
                raise ValueError("New attempt output directory must be empty")
            target = mount["container"]
            command += ["--mount", f"type=bind,source={path},target={target}"]
            mounts.append(mount)
        command += [IMAGE, "infinity"]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)
        production_command = ["docker", "exec", "-i", CONTAINER, "deno", "run", "--cached-only", "--allow-read=/app,/runs,/exports", "--allow-write=/runs,/exports", "--allow-run=omc,perl", "--allow-env=MODELICA_RUN_DIR,OPENMODELICALIBRARY", "/app/server.ts", "--stdio"]
        report.update(container_started=True, container_id=result.stdout.strip(), mounts=mounts, production_command=production_command)
        persist()
    if args.prepare_only:
        print(json.dumps({"status": "prepared", "container": CONTAINER}))
        return
    qualification = args.output.parent / "production-stdio-gateway.json"
    qualified = json.loads(qualification.read_text(encoding="utf-8")) if qualification.exists() else {}
    if qualified.get("status") != "passed" or qualified.get("image") != IMAGE:
        raise ValueError("Exact production StdioRunner/GatewayService qualification required before registration")
    if "server_id" not in report:
        result = request(args.api, "POST", "/api/mcp/servers", {"name": "Modelica — selected bounded water-heater campaign kit", "type": "stdio", "command": report["production_command"], "category": "simulation", "description": "Isolated Casys0.6.5 MIT derivative, separate wright-water-heater-v1@0.1.0 identity; pinned OMC1.27/MSL4.1. Native thermal components, explicit electrical efficiency, sealed independent timestep/tolerance scenarios and confined same-attempt native CSV/provenance export. Original kit retained unchanged.", "source_url": "https://github.com/Casys-ai/mcp-modelica/tree/62e26009a566d15b625493b0c3510bdd14b01c3b", "default_enabled": False, "risk_level": "medium", "deployment_mode": "local-only"})
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
    catalog = request(args.api, "GET", "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session))
    report["tools"] = [tool for tool in catalog["tools"] if tool["server_id"] == identity]
    report["status"] = "installed_discovered" if len(report["tools"]) == 15 else "tool_discovery_incomplete"
    persist()
    print(json.dumps({"status": report["status"], "server_id": identity, "tools": len(report["tools"])}))


if __name__ == "__main__":
    main()
