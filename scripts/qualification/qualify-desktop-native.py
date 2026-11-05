"""Exercise the installed CLI's managed lifecycle and desktop bridge in a new home."""

import argparse
import asyncio
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tempfile
import zipfile

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
with zipfile.ZipFile(wheel) as archive:
    viewer_paths = [
        name
        for name in archive.namelist()
        if name.endswith("api/desktop/native-editor.html")
    ]
    if len(viewer_paths) != 1:
        raise ValueError("Candidate must contain exactly one maintained desktop viewer")
    expected_ui_sha256 = hashlib.sha256(archive.read(viewer_paths[0])).hexdigest()
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
    "topology": "Installed managed desktop MCP; no desktop visual claim",
    "platform": platform.system(),
    "architecture": platform.machine(),
    "python": platform.python_version(),
    "expected_ui_sha256": expected_ui_sha256,
    "engineering_runs": 0,
    "engineering_tool_calls": 0,
    "fixture_process_runs": 0,
}


def lifecycle(command, label, *, required=True):
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
    receipt.setdefault("lifecycle_exit_codes", {})[label] = result.returncode
    # Keep the CLI's already-redacted result even when the command fails. CI
    # uploads the receipt, not the private stdout/stderr files.
    receipt[label] = json.loads(result.stdout)
    if required and result.returncode != 0:
        try:
            lifecycle("doctor", f"{label}-doctor", required=False)
        except Exception as exc:
            receipt[f"{label}-doctor"] = {
                "code": "diagnostic_unavailable",
                "error_type": type(exc).__name__,
            }
        raise AssertionError(f"{command} failed; see {label} evidence")


REASONING_SOURCE = """workflow desktop_handoff
  name: "Desktop reasoning handoff"
  purpose: "Qualify one desktop-supplied digital inspection brief through Wright's source runtime."
  discipline: "mechanical.inspection"
  reviewed_ai_suggestions: true
end
task brief
  name: "Prepare a digital inspection brief"
  purpose: "Separate supplied dimensions from missing inspection criteria without claiming measurement."
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: [{"key":"brief_prompt","kind":"engineering_document","name":"Prompt","item":null,"required":false,"quantity":"optional","description":"Optional upstream requirements"}]
  outputs: [{"key":"brief_response","kind":"engineering_document","name":"Inspection brief","item":null,"required":true,"quantity":"one","description":"Digital inspection brief, not measured evidence"}]
  prompt: "Prepare a short digital inspection brief for a rectangular plate: length 120 mm, width 80 mm, thickness 6 mm, four mounting holes of diameter 8 mm. Identify the dimensions to check, distinguish supplied requirements from unspecified hole locations, and explain why no manufacturing release can be claimed. This task performs no physical action and no CAD measurement."
  settings: {"authoring_template":"ai-prompt","output_format":"markdown","output_filename":"inspection-brief.md"}
  tool: null
  reusable_step: null
end
"""


async def reasoning_lifecycle(call, scope, label):
    """Start through the real installed API; cancel without supplying a model reply."""
    if "reasoning_start" not in receipt:
        document = await call(
            "wright_workflow_create",
            {
                **scope,
                "path": "workflows/reasoning-lifecycle.workflow.wflow",
                "source": REASONING_SOURCE,
            },
        )
        source = {
            **scope,
            "path": document["path"],
            "source_digest": document["storage_digest"],
        }
        prepared = await call("wright_process_prepare", {**source, "bindings": []})
        start_arguments = {
            **source,
            "input_snapshot_id": prepared["snapshot_id"],
            "input_digest": prepared["digest"],
            "request_id": "native-reasoning-start",
        }
        started = await call("wright_process_start", start_arguments)
        receipt["reasoning_start"] = started
        receipt["fixture_process_runs"] = 1
        reference = {**source, "run_id": started["run_id"]}
        receipt["reasoning_reference"] = reference
        receipt["reasoning_start_arguments"] = start_arguments
        async with asyncio.timeout(30):
            while True:
                pending = await call("wright_reasoning_pending", scope)
                tasks = [
                    task
                    for task in pending["tasks"]
                    if task["request"]["run_id"] == started["run_id"]
                ]
                if tasks:
                    break
                await asyncio.sleep(0.25)
        assert len(tasks) == 1
        task = tasks[0]
        assert task["request"]["binding"]["adapter"] == "openai-desktop-harness"
        assert task["request"]["payload"]["tools"] == []
        assert task["request"]["payload"]["tool_choice"] == "none"
        receipt["reasoning_request"] = task
        # Repeated Start reconciles the same receipt, not a second run.
        assert await call("wright_process_start", start_arguments) == started
        receipt["reasoning_cancel"] = await call(
            "wright_process_cancel",
            {
                **reference,
                "request_id": "native-reasoning-cancel",
            },
        )
        async with asyncio.timeout(30):
            while True:
                snapshot = await call("wright_process_read", reference)
                if snapshot["state"] == "cancelled":
                    break
                await asyncio.sleep(0.25)
    reference = receipt["reasoning_reference"]
    snapshot = await call("wright_process_read", reference)
    assert snapshot["state"] == "cancelled", snapshot["state"]
    assert (
        await call("wright_process_start", receipt["reasoning_start_arguments"])
        == receipt["reasoning_start"]
    )
    pending = await call("wright_reasoning_pending", scope)
    assert not any(
        t["request"]["run_id"] == reference["run_id"] for t in pending["tasks"]
    )
    receipt.setdefault("reasoning_states", {})[label] = snapshot["state"]


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
                resources = await session.list_resources()
                viewer_uri = next(
                    resource.uri
                    for resource in resources.resources
                    if str(resource.uri).startswith("ui://wright/workflow/")
                )
                viewer = await session.read_resource(viewer_uri)
                ui_sha256 = hashlib.sha256(
                    viewer.contents[0].text.encode("utf-8")
                ).hexdigest()
                expected_wheel = (
                    initial_wheel
                    if label == "first-bridge" or label == "restarted-bridge"
                    else wheel
                )
                with zipfile.ZipFile(expected_wheel) as archive:
                    expected_ui = hashlib.sha256(
                        archive.read(viewer_paths[0])
                    ).hexdigest()
                assert ui_sha256 == expected_ui, (
                    "Served viewer differs from installed candidate"
                )

                async def call(name, arguments):
                    result = await session.call_tool(name, arguments)
                    assert not result.isError, f"{name} failed: {result.content}"
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
                await reasoning_lifecycle(call, scope, label)
                receipt[label] = {
                    "tools": sorted(tool.name for tool in tools.tools),
                    "status": status.model_dump(mode="json"),
                    "saved_source_sha256": reopened["storage_digest"],
                    "served_ui_sha256": ui_sha256,
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
