"""Register reviewed selected Pi reference/CFD tools through normal local API; explicit opt-in."""
import argparse
import json
from pathlib import Path
import urllib.parse
import urllib.request


def request(api, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    with urllib.request.urlopen(urllib.request.Request(api+path, data=data, method=method, headers={"Content-Type": "application/json"}), timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.output.read_text()) if args.output.exists() else {"server_map": {}, "operations": []}
    def persist():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+"\n")
    base = ["docker", "exec", "-i", "-e", "PYTHONPATH="]
    definitions = {
        "wright-campaign-pi-visual-references": ("Pi primary visual references v2", base+["-e", "WRIGHT_PI_REFERENCE_WORKSPACE=/demo", "wright-081-pi-visual-runtime", "/tmp/pi-visual-env/bin/python", "/operations/pi_reference_visual_mcp.py"], None),
    }
    for alias, (name, command, source) in definitions.items():
        if alias not in report["server_map"]:
            created = request(args.api, "POST", "/api/mcp/servers", {"name": name, "type": "stdio", "command": command, "category": "engineering", "description": "Selected local disposable dataset runtime. Fixed primary Pi PDFs and supplier product/dimensional references, bounded actual rendered source-image observations; no Blender, arbitrary URLs/code, device or supplier transaction access. Local scope only; not a public catalog qualification.", "source_url": source, "default_enabled": False, "risk_level": "medium", "deployment_mode": "local-only"})
            report["server_map"][alias] = created["server_id"]
            report["operations"].append({"stage": "register", "alias": alias, "result": created})
            persist()
        identity = report["server_map"][alias]
        for stage, method, path, body in [
            ("install", "POST", "/api/mcp/servers/"+identity+"/install?session_id="+urllib.parse.quote(args.session), None),
            ("enable_demo", "POST", "/api/workspace/tools/toggle", {"session_id": args.session, "server_id": identity, "is_enabled": True}),
            ("activate", "PATCH", "/api/mcp/servers/"+identity, {"is_active": True}),
        ]:
            if any(item["stage"] == stage and item.get("alias") == alias for item in report["operations"]):
                continue
            result = request(args.api, method, path, body)
            report["operations"].append({"stage": stage, "alias": alias, "result": result})
            persist()
    discovered = request(args.api, "GET", "/api/workspace/workflow-sources/tools?session_id="+urllib.parse.quote(args.session))
    report["tools"] = [tool for tool in discovered["tools"] if tool["server_id"] in report["server_map"].values()]
    report["status"] = "installed_discovered" if len(report["tools"]) == 3 else "tool_discovery_incomplete"
    persist()
    print(json.dumps({"status": report["status"], "server_map": report["server_map"], "tools": len(report["tools"])}))


if __name__ == "__main__":
    main()
