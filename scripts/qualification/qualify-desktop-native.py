"""Exercise the installed CLI's managed lifecycle and desktop bridge in a new home."""

import argparse
import asyncio
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--wheel", type=Path, required=True)
parser.add_argument("--wheelhouse", type=Path, required=True)
parser.add_argument("--evidence-dir", type=Path, required=True)
args = parser.parse_args()
evidence = args.evidence_dir.resolve()
evidence.mkdir(parents=True, exist_ok=False)
home = Path(tempfile.mkdtemp(prefix="wright-managed-desktop-"))
wheel = args.wheel.resolve(strict=True)
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
env = {
    k: v
    for k, v in os.environ.items()
    if not k.startswith(("WRIGHT_", "HERMES_", "CODEX_"))
    and k not in {"PYTHONPATH", "DATABASE_PATH", "FRONTEND_DIST_DIR"}
}
env.update(
    WRIGHT_HOME=str(home),
    WRIGHT_NATIVE_PORT=str(port),
    WRIGHT_RUNTIME_ARTIFACT=str(wheel),
    WRIGHT_RUNTIME_VERSION=version("wright-engineering"),
    WRIGHT_RUNTIME_CHANNEL="local_candidate",
    WRIGHT_RUNTIME_SHA256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
    WRIGHT_RUNTIME_WHEELHOUSE=str(args.wheelhouse.resolve(strict=True)),
    WRIGHT_DESKTOP_ENABLED="1",
    WRIGHT_AUTH_MODE="enforced",
    WRIGHT_API_MCP_AUTOSTART="0",
)
receipt = {
    "schema": "wright.managed-desktop-qualification/1",
    "home": str(home),
    "wheel_sha256": env["WRIGHT_RUNTIME_SHA256"],
    "topology": "Linux ARM64; actual managed lifecycle; no desktop visual claim",
    "engineering_runs": 0,
}


def lifecycle(command, label):
    result = subprocess.run(
        [sys.executable, "-I", "-m", "wright_engineering.cli", "native", command],
        env=env,
        cwd=home,
        capture_output=True,
        text=True,
        timeout=240,
    )
    (evidence / f"{label}.stdout").write_text(result.stdout)
    (evidence / f"{label}.stderr").write_text(result.stderr)
    assert result.returncode == 0, f"{command} failed; see {label} evidence"
    receipt[label] = json.loads(result.stdout)


async def bridge(label):
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-I",
            "-m",
            "wright_engineering.cli",
            "mcp",
            "desktop",
            "--api-url",
            f"http://127.0.0.1:{port}",
        ],
        env=env,
        cwd=str(home),
    )
    with (evidence / f"{label}.stderr").open("w") as errors:
        async with stdio_client(params, errlog=errors) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert "wright_home" in {tool.name for tool in tools.tools}
                status = await session.call_tool("wright_connection_status", {})
                assert not status.isError
                value = status.structuredContent or json.loads(
                    next(item.text for item in status.content if item.type == "text")
                )
                assert value["connected"] is True
                assert value["binding"]["adapter"] == "openai-desktop-harness"
                receipt[label] = {
                    "tools": sorted(tool.name for tool in tools.tools),
                    "status": status.model_dump(mode="json"),
                }


try:
    lifecycle("start", "first-start")
    lifecycle("status", "healthy-status")
    lifecycle("doctor", "doctor")
    asyncio.run(bridge("first-bridge"))
    lifecycle("stop", "first-stop")
    lifecycle("start", "restart")
    asyncio.run(bridge("restarted-bridge"))
    receipt["result"] = "PASS"
except BaseException:
    receipt["result"] = "FAIL"
    raise
finally:
    try:
        lifecycle("stop", "final-stop")
    except BaseException:
        receipt["result"] = "FAIL"
        raise
    finally:
        (evidence / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
