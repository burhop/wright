"""Private actual-MCP upload proof; no workflow execution or engineering approval."""

import argparse
import asyncio
import base64
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from packages.workspace_service.tests.test_process_input_readiness import source


async def main(state):
    receipt = state / "input-upload-proof.json"
    marker = state / "input-upload-proof.started"
    marker.touch(exist_ok=False)
    evidence = {
        "scope": "private synthetic upload qualification, no process starts",
        "calls": [],
    }

    def save():
        receipt.write_text(json.dumps(evidence, indent=2))

    save()
    bridge = Path(__file__).resolve().parents[1] / "mcp_bridge.py"
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            str(bridge),
            "--state-dir",
            str(state),
            "--native-editor",
            "--native-working-view",
        ],
    )
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as client:
            await client.initialize()

            async def call(name, args):
                result = await client.call_tool(name, args)
                evidence["calls"].append(
                    {"tool": name, "is_error": bool(result.isError)}
                )
                save()
                if result.isError:
                    raise RuntimeError(
                        "MCP rejected "
                        + name
                        + "; inspect retained exact state, do not replay"
                    )
                return result.structuredContent or json.loads(result.content[0].text)

            workspace = await call(
                "wright_workspace_create",
                {"name": "Private declared-input upload proof"},
            )
            scope = {k: workspace[k] for k in ("workspace_id", "session_id")}
            text = source(file="original.txt")
            doc = await call(
                "wright_workflow_create",
                {
                    **scope,
                    "path": "workflows/upload-proof.workflow.wflow",
                    "source": text,
                },
            )
            evidence.update(workspace=workspace, source=doc)
            save()
            with sqlite3.connect(state / "wright.sqlite") as db:
                root = Path(
                    db.execute(
                        "SELECT local_path FROM engineering_workspaces WHERE workspace_id=?",
                        (scope["workspace_id"],),
                    ).fetchone()[0]
                )
            original = (root / doc["path"]).read_bytes()
            request = {
                **scope,
                "path": doc["path"],
                "expected_storage_digest": doc["storage_digest"],
                "operation": "upload",
                "input_id": "brief",
                "filename": "requirements.txt",
            }
            for label, content in [
                (
                    "small",
                    b"Synthetic requirement document. No engineering acceptance.\n",
                ),
                ("maximum", b"x" * 33_554_432),
            ]:
                evidence["pending_upload"] = {
                    "label": label,
                    "bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
                save()
                reply = await call(
                    "wright_process_ui_update",
                    {
                        "request": {
                            **request,
                            "bytes_base64": base64.b64encode(content).decode(),
                        }
                    },
                )
                if not reply.get("ok"):
                    evidence["failure"] = reply
                    save()
                    raise RuntimeError("Upload owner rejected " + label + "; no replay")
                ref = reply["document"]
                actual = (root / ref["artifact_ref"]).read_bytes()
                assert (
                    actual == content
                    and ref["sha256"] == hashlib.sha256(content).hexdigest()
                )
                evidence.setdefault("uploads", []).append(
                    {**evidence.pop("pending_upload"), "reference": ref}
                )
                save()
            before = set(root.rglob("*"))
            for label, changes in [
                ("stale-source", {"expected_storage_digest": "0" * 64}),
                ("undeclared-input", {"input_id": "missing"}),
                ("unsafe-filename", {"filename": "../escape.txt"}),
            ]:
                reply = await call(
                    "wright_process_ui_update",
                    {"request": {**request, **changes, "bytes_base64": "YQ=="}},
                )
                assert reply.get("ok") is False, label
                assert set(root.rglob("*")) == before, label
                evidence.setdefault("denials", []).append(
                    {
                        "case": label,
                        "reason": reply.get("reason"),
                        "http_status": reply.get("http_status"),
                    }
                )
                save()
            assert (root / doc["path"]).read_bytes() == original
            assert not (root / "runs").exists() or not list(
                (root / "runs").rglob("*.json")
            )
            evidence.update(
                status="passed",
                source_unchanged=True,
                process_runs_started=0,
                desktop_host_limit_verified=False,
            )
            save()
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "uploads": [x["bytes"] for x in evidence["uploads"]],
                        "denials": len(evidence["denials"]),
                    }
                )
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    asyncio.run(main(parser.parse_args().state_dir.resolve(strict=True)))
