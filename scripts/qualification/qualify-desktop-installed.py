"""Fresh installed-artifact proof. No engineering runs or external providers."""

import argparse
import asyncio
import base64
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from wright_engineering.runtime.auth import ensure_control_plane_token
from wright_engineering.runtime.layout import NativeLayout

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--evidence-dir", type=Path, required=True)
parser.add_argument(
    "--retained-fixture",
    type=Path,
    help="Explicit JSON manifest for a read-only copied workspace",
)
parser.add_argument(
    "--browser-script", type=Path, help="Read-only installed UI rehearsal after restart"
)
args = parser.parse_args()
EVIDENCE = args.evidence_dir.resolve()
EVIDENCE.mkdir(parents=True, exist_ok=False)
HOME = Path(tempfile.mkdtemp(prefix="wright-installed-desktop-"))
layout = NativeLayout.from_wright_home(HOME)
token = ensure_control_plane_token(layout)
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
url = f"http://127.0.0.1:{port}"
env = {
    k: v
    for k, v in os.environ.items()
    if not k.startswith(("WRIGHT_", "HERMES_", "CODEX_"))
    and k not in {"PYTHONPATH", "DATABASE_PATH", "FRONTEND_DIST_DIR"}
}
env.update(
    WRIGHT_HOME=str(HOME),
    WRIGHT_DESKTOP_ENABLED="1",
    WRIGHT_AUTH_MODE="enforced",
    WRIGHT_API_TOKEN=token,
    WRIGHT_API_MCP_AUTOSTART="0",
    WRIGHT_MCP_OAUTH_FLOW="device_code",
    WRIGHT_SECRETS_PATH=str(layout.data / "credentials.json"),
    WRIGHT_SECRETS_DIR=str(layout.data / "secrets.d"),
)
SOURCE = 'workflow installed_check\n  name: "Installed artifact check"\n  purpose: "Save and reopen without execution"\n  discipline: "mechanical.design"\n  reviewed_ai_suggestions: true\nend\n'
receipt = {
    "schema": "wright.installed-desktop-qualification/1",
    "python": sys.executable,
    "home": str(HOME),
    "topology": "Linux ARM64 installed artifact; no desktop visual claim",
    "engineering_runs": 0,
}
retained = (
    json.loads(args.retained_fixture.read_text()) if args.retained_fixture else None
)


def file_manifest(root):
    """Only explicitly selected engineering state; never copy profile or credentials."""
    result = {}
    for directory in ("workflows", "results", "runs", ".wright/workflow-sources"):
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_symlink():
                raise ValueError("Migration rehearsal refuses symlinks")
            if path.is_file() and path.name != ".lock":
                result[str(path.relative_to(root))] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    return result


def copy_retained():
    from data_vault.workspace_repository import WorkspaceRepository
    from data_vault.process_input_repository import ProcessInputRepository
    from data_vault.state_store import connect_state_db
    from core.process_interactions import InputSnapshot, StartReceipt

    original = Path(retained["directory"]).resolve(strict=True)
    target = layout.workspaces / "retained-copy"
    target.mkdir(parents=True, exist_ok=False)
    manifest = file_manifest(original)
    for relative in manifest:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((original / relative).read_bytes())
    assert file_manifest(target) == manifest
    repository = WorkspaceRepository(str(layout.data / "wright.db"), secrets=None)
    repository.create(
        retained["workspace_id"],
        retained["session_id"],
        str(target),
        workspace_name="Retained inspection — copied state",
        agent_id="openai-desktop-harness",
    )
    receipt["retained"] = {
        "original": str(original),
        "copy": str(target),
        "files": manifest,
        "scope": retained,
    }
    # File history alone cannot authorize attaching a durable process. Copy only
    # this completed run's original immutable receipt/input, not account tables,
    # review grants, responses or live task state. No start operation is invoked.
    with connect_state_db(retained["database"], read_only=True) as db:
        row = db.execute(
            "SELECT payload_json FROM process_start_receipts WHERE workspace_id=? AND source_path=? AND run_id=?",
            (retained["workspace_id"], retained["path"], retained["run_id"]),
        ).fetchone()
        start = StartReceipt.model_validate_json(row["payload_json"])
        row = db.execute(
            "SELECT payload_json FROM process_input_snapshots WHERE workspace_id=? AND snapshot_id=?",
            (retained["workspace_id"], start.input_snapshot_id),
        ).fetchone()
        inputs = InputSnapshot.model_validate_json(row["payload_json"])
    assert start.process.source_digest == retained["source_digest"]
    owner = ProcessInputRepository(str(layout.data / "wright.db"))
    copied, created = owner.reserve_start(inputs, start)
    assert created and copied == start
    receipt["retained"]["copied_receipt_sha256"] = hashlib.sha256(
        start.model_dump_json().encode()
    ).hexdigest()
    receipt["retained"]["copied_input_sha256"] = hashlib.sha256(
        inputs.model_dump_json().encode()
    ).hexdigest()


async def inspect_retained(call):
    scope = {key: retained[key] for key in ("workspace_id", "session_id", "path")}
    source = await call("wright_workflow_read", scope)
    history = await call("wright_workflow_history", scope)
    drafts = await call("wright_editor_drafts_read", {"request": scope})
    saved = await call(
        "wright_recorded_run_read",
        {
            "request": {
                **scope,
                "run_id": retained["run_id"],
                "source_digest": retained["source_digest"],
            }
        },
    )
    preview = await call(
        "wright_workspace_file_download",
        {
            **{key: scope[key] for key in ("workspace_id", "session_id")},
            "path": retained["image_path"],
        },
    )
    content = base64.b64decode(preview["content_base64"], validate=True)
    assert hashlib.sha256(content).hexdigest() == retained["image_sha256"]
    assert retained["run_id"] in json.dumps(history)
    receipt["retained"].update(
        source=source,
        history=history,
        drafts=drafts,
        saved_run=saved,
        image_sha256=retained["image_sha256"],
    )
    for root in ("original", "copy"):
        assert (
            file_manifest(Path(receipt["retained"][root]))
            == receipt["retained"]["files"]
        )


async def exercise(resume=False):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-I", "-m", "wright_engineering.cli", "mcp", "desktop", "--api-url", url],
        env={k: v for k, v in env.items() if k != "WRIGHT_API_TOKEN"},
        cwd=str(HOME),
    )
    with (EVIDENCE / ("resumed-mcp.log" if resume else "installed-mcp.log")).open(
        "w"
    ) as error:
        async with stdio_client(params, errlog=error) as (read, write):
            async with ClientSession(
                read, write, read_timeout_seconds=timedelta(seconds=30)
            ) as session:
                await session.initialize()
                tools = await session.list_tools()
                receipt["tools"] = [t.name for t in tools.tools]

                async def call(name, args={}):
                    result = await session.call_tool(name, args)
                    if result.isError:
                        raise AssertionError(str(result.content))
                    value = result.structuredContent
                    if value is None:
                        value = json.loads(result.content[0].text)
                    return value

                status = await call("wright_connection_status")
                assert status["connected"] is True, status
                ws = (
                    receipt["workspace_result"]
                    if resume
                    else await call(
                        "wright_workspace_create",
                        {"name": "Installed desktop qualification"},
                    )
                )
                receipt["workspace_result"] = ws
                scope = {k: ws[k] for k in ("workspace_id", "session_id")}
                path = "workflows/installed-check.workflow.wflow"
                doc = (
                    receipt["saved_source"]
                    if resume
                    else await call(
                        "wright_workflow_create",
                        {**scope, "path": path, "source": SOURCE},
                    )
                )
                receipt["saved_source"] = doc
                reopened = await call("wright_workflow_read", {**scope, "path": path})
                assert reopened["storage_digest"] == doc["storage_digest"]
                assert reopened["source"] == doc["source"]
                assert "Installed artifact check" in reopened["source"]
                assert (
                    hashlib.sha256(reopened["source"].encode()).hexdigest()
                    == reopened["storage_digest"]
                )
                receipt["source_sha256"] = doc["storage_digest"]
                opened = await call("wright_workflow_open", {**scope, "path": path})
                receipt["open_keys"] = sorted(opened)
                resources = await session.list_resources()
                native = [
                    r
                    for r in resources.resources
                    if str(r.uri).startswith("ui://wright/workflow/")
                ]
                receipt["resources"] = [str(r.uri) for r in resources.resources]
                assert native, receipt["resources"]
                html = await session.read_resource(native[0].uri)
                assert "<!doctype html>" in html.contents[0].text.lower()
                receipt["editor_bytes"] = len(html.contents[0].text.encode())
                if retained:
                    await inspect_retained(call)
                receipt["restart_preserves_source"] = resume


for resume in (False, True):
    receipt["status"] = "IN_PROGRESS"
    receipt["phase"] = "restart" if resume else "initial"
    log = (
        EVIDENCE / ("resumed-runtime.log" if resume else "installed-runtime.log")
    ).open("w")
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-m",
            "wright_engineering.cli",
            "runtime",
            "serve",
            "--port",
            str(port),
            "--data-root",
            str(layout.data),
        ],
        cwd=HOME,
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        with httpx.Client(base_url=url, trust_env=False) as http:
            for attempt in range(120):
                if process.poll() is not None:
                    raise RuntimeError(
                        "Installed runtime exited before health; inspect installed-runtime.log"
                    )
                try:
                    response = http.get("/api/health", timeout=1)
                    if response.is_success:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.25)
            else:
                raise RuntimeError("Installed startup health timed out")
            config = http.get(
                "/api/desktop/configuration",
                headers={"Authorization": "Bearer " + token},
            )
            assert config.status_code == 200, config.text
            receipt["configuration"] = config.json()
            assert http.get("/api/desktop/configuration").status_code == 401
        if retained and not resume:
            copy_retained()
        asyncio.run(exercise(resume))
        if resume and args.browser_script:
            if not retained:
                raise ValueError("Browser rehearsal requires explicit copied state")
            receipt_path = EVIDENCE / "installed-receipt.json"
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
            subprocess.run(
                [
                    "node",
                    str(args.browser_script.resolve()),
                    str(receipt_path),
                    str(EVIDENCE / "browser"),
                ],
                env={**env, "WRIGHT_DESKTOP_API_URL": url},
                check=True,
                timeout=180,
            )
            # UI inspection must not change original or copied historical data.
            for root in ("original", "copy"):
                assert (
                    file_manifest(Path(receipt["retained"][root]))
                    == receipt["retained"]["files"]
                )
        receipt["status"] = "PASS" if resume else "INITIAL_PASS"
    except BaseException as error:
        receipt["status"] = "FAIL"
        receipt["error_type"] = type(error).__name__
        raise
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        log.close()
        (EVIDENCE / "installed-receipt.json").write_text(
            json.dumps(receipt, indent=2) + "\n"
        )
print(json.dumps({"status": receipt.get("status", "FAIL"), "home": str(HOME)}))
