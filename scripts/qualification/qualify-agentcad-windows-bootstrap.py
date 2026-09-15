"""Qualify a pinned selected AgentCAD bootstrap using isolated actual native CAD."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.runners.stdio import StdioRunner

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ["uv", "run", "--no-project", "--isolated", "--python", "3.12.11",
          "--with", "agentcad[mcp]==0.6.0", "--with", "numpy==2.5.2", "--with", "build123d==0.10.0"]


async def run(args):
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError("Choose a fresh private qualification directory")
    output.mkdir(parents=True)
    source = (ROOT / "scripts/engineering/agentcad_windows_bootstrap.py").read_bytes()
    sha = hashlib.sha256(source).hexdigest()
    snapshot = ROOT / ".local-run/feature-081-live/sources" / ("agentcad-bootstrap-" + sha[:16]) / "bootstrap.py"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if snapshot.exists() and snapshot.read_bytes() != source:
        raise ValueError("Immutable bootstrap snapshot differs")
    if not snapshot.exists():
        snapshot.write_bytes(source)
    project = output / "private-project"
    project.mkdir()
    init = subprocess.run([*PREFIX, "agentcad", "init", "--name", "bootstrap-probe", "--build-dir", "build"],
                          cwd=project, capture_output=True, text=True, timeout=180)
    (output / "initialization.json").write_text(json.dumps({"returncode": init.returncode, "stdout": init.stdout, "stderr": init.stderr}, indent=2))
    if init.returncode:
        raise ValueError("Private native initialization failed")
    script = project / "tiny.py"
    script.write_text("from build123d import Box\nshow_object(Box(2, 3, 4))\n", encoding="utf-8")
    command = [*PREFIX, "python", "-B", str(snapshot)]
    runner = StdioRunner(command, cwd=str(output), operation_timeout=90)
    spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "scripts/qualify_stdio_mcp.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    proof = {"status": "running", "scope": "selected Windows host prerequisite; separate actual tiny CAD, no campaign execution",
             "bootstrap_sha256": sha, "snapshot": str(snapshot), "command": command, "registry_changed": False,
             "continuous_open_stdin": True, "base_image_changed": False}
    try:
        await runner.start()
        tools = await runner.list_tools()
        (output / "tools.json").write_text(json.dumps(tools, indent=2))
        context = await runner.call_tool("context", {"cwd": str(project), "build_dir": "build"})
        if context.get("isError"):
            raise ValueError("Direct isolated context probe failed")
        (output / "direct-context.json").write_text(json.dumps(context, indent=2))
        # Leave MCP stdin open and allow its background reader to block normally.
        await asyncio.sleep(2)
        now = int(time.time())
        server = McpServer(server_id="agentcad-bootstrap-probe", name="AgentCAD selected bootstrap probe", type="stdio",
                           command=command, is_active=True, is_installed=True, status="active", created_at=now,
                           updated_at=now, risk_level="high", default_enabled=False)
        gateway = GatewayService(workspaces=helpers._Workspaces(project, server.server_id), catalog=helpers._Catalog(server, tools),
            lifecycle=helpers._Lifecycle(runner), audit=helpers._Audit(), notifier=GatewayNotificationHub(), operation_timeout=90, maximum_timeout=90)
        gateway.open_session(session_id="qualification", principal_id="wright-validator", workspace_id="qualification", transport="stdio")
        gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name="bootstrap-probe", client_version="1", client_capabilities={})
        started = time.monotonic()
        result = await gateway.call_tool("qualification", "tiny-native-cad", server.server_id + "__run", {
            "script": str(script), "output": "tiny", "cwd": str(project), "build_dir": "build",
            "preview": False, "view": False, "diff": False})
        proof["native_call_seconds"] = time.monotonic() - started
        if result.is_error:
            raise ValueError("Actual isolated native CAD returned an MCP error")
        (output / "gateway-result.json").write_text(json.dumps({"content": list(result.content), "structured_content": result.structured_content}, indent=2))
        native = project / "build/v1_tiny"
        meta = json.loads((native / "meta.json").read_text())
        if meta.get("status") != "success" or not (native / "output.step").stat().st_size:
            raise ValueError("Actual native STEP/history did not complete")
        proof.update(status="passed", tool_count=len(tools), native_status=meta["status"],
                     files=[{"path": str(p), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                            for p in [script, native / "script.py", native / "output.step", native / "meta.json"]])
    except Exception as error:
        proof.update(status="failed", error_type=type(error).__name__, error=str(error)[:2000])
        raise
    finally:
        await runner.stop()
        (output / "qualification.json").write_text(json.dumps(proof, indent=2) + "\n")
    return proof


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    print(json.dumps(asyncio.run(run(parser.parse_args())), indent=2))
