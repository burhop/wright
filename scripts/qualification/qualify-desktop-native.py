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
parser.add_argument(
    "--manager-python", type=Path, help="Dependency-light installed CLI interpreter"
)
parser.add_argument(
    "--predecessor-wheel",
    type=Path,
    help="Same-version prior candidate for an actual update check",
)
args = parser.parse_args()
evidence = args.evidence_dir.resolve()
evidence.mkdir(parents=True, exist_ok=False)
home = Path(tempfile.mkdtemp(prefix="wright-managed-desktop-"))
wheel = args.wheel.resolve(strict=True)
manager_python = str(
    args.manager_python.absolute() if args.manager_python else sys.executable
)
initial_wheel = (
    args.predecessor_wheel.resolve(strict=True) if args.predecessor_wheel else wheel
)
if args.predecessor_wheel and initial_wheel.name != wheel.name:
    raise ValueError("This bounded rehearsal requires same-version candidate wheels")
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
    WRIGHT_RUNTIME_ARTIFACT=str(initial_wheel),
    WRIGHT_RUNTIME_VERSION=version("wright-engineering"),
    WRIGHT_RUNTIME_CHANNEL="local_candidate",
    WRIGHT_RUNTIME_SHA256=hashlib.sha256(initial_wheel.read_bytes()).hexdigest(),
    WRIGHT_RUNTIME_WHEELHOUSE=str(args.wheelhouse.resolve(strict=True)),
    WRIGHT_DESKTOP_ENABLED="1",
    WRIGHT_AUTH_MODE="enforced",
    WRIGHT_API_MCP_AUTOSTART="0",
)
receipt = {
    "schema": "wright.managed-desktop-qualification/1",
    "home": str(home),
    "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
    "initial_wheel_sha256": env["WRIGHT_RUNTIME_SHA256"],
    "manager_python": manager_python,
    "topology": "Linux ARM64; actual managed lifecycle; no desktop visual claim",
    "engineering_runs": 0,
}


def lifecycle(command, label):
    result = subprocess.run(
        [manager_python, "-I", "-m", "wright_engineering.cli", "native", command],
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
        command=manager_python,
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

                async def call(name, arguments):
                    result = await session.call_tool(name, arguments)
                    assert not result.isError, f"{name} failed"
                    return result.structuredContent or json.loads(
                        result.content[0].text
                    )

                if "workspace" not in receipt:
                    receipt["workspace"] = await call(
                        "wright_workspace_create", {"name": "Managed lifecycle check"}
                    )
                    scope = {
                        k: receipt["workspace"][k]
                        for k in ("workspace_id", "session_id")
                    }
                    receipt["saved_source"] = await call(
                        "wright_workflow_create",
                        {
                            **scope,
                            "path": "workflows/lifecycle-check.workflow.wflow",
                            "source": 'workflow lifecycle_check\n  name: "Managed lifecycle check"\n  purpose: "Preserve saved source across restart and update"\n  discipline: "mechanical.design"\n  reviewed_ai_suggestions: true\nend\n',
                        },
                    )
                scope = {
                    k: receipt["workspace"][k] for k in ("workspace_id", "session_id")
                }
                reopened = await call(
                    "wright_workflow_read",
                    {**scope, "path": "workflows/lifecycle-check.workflow.wflow"},
                )
                assert (
                    reopened["storage_digest"]
                    == receipt["saved_source"]["storage_digest"]
                )
                assert reopened["source"] == receipt["saved_source"]["source"]
                receipt[label] = {
                    "tools": sorted(tool.name for tool in tools.tools),
                    "status": status.model_dump(mode="json"),
                    "saved_source_sha256": reopened["storage_digest"],
                }


try:
    lifecycle("start", "first-start")
    lifecycle("status", "healthy-status")
    lifecycle("doctor", "doctor")
    asyncio.run(bridge("first-bridge"))
    lifecycle("stop", "first-stop")
    lifecycle("start", "restart")
    asyncio.run(bridge("restarted-bridge"))
    if args.predecessor_wheel:
        env.update(
            WRIGHT_RUNTIME_ARTIFACT=str(wheel),
            WRIGHT_RUNTIME_SHA256=receipt["wheel_sha256"],
        )
        lifecycle("update", "candidate-update")
        asyncio.run(bridge("updated-bridge"))
        lifecycle("doctor", "updated-doctor")
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
