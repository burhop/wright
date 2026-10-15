"""Exercise existing file/text declarations only; never prepare or start a run."""

import asyncio
import base64
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    root = Path(__file__).resolve().parents[3]
    state = Path(sys.argv[1]).resolve(strict=True)
    marker = state / "existing-declarations-v3.started"
    marker.touch(exist_ok=False)
    receipt = state / "existing-declarations-v3.json"
    evidence = {
        "scope": "existing input declarations only; not full workflow qualification",
        "cases": [],
    }

    def save():
        receipt.write_text(json.dumps(evidence, indent=2) + "\n")

    save()
    templates = (
        root
        / "packages/workspace_service/src/workspace_service/engineering_workflow_templates"
    )
    image = templates / "inputs/printed-replacement-part/replacement-knob-source.svg"
    cases = [
        (
            "manufacturing",
            templates / "templates/printed-replacement-part.workflow.wflow",
            "image_and_scale_upload_declaration",
            image.name,
            image.read_bytes(),
            True,
        ),
        (
            "stevecad",
            root
            / "examples/stevecad-demonstrations/prompt-to-reviewed-cad/prompt-to-reviewed-cad-native.workflow.wflow",
            "design_prompt",
            "unrequested.txt",
            b"Do not replace the accepted text prompt.\n",
            False,
        ),
    ]
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            str(root / "prototypes/desktop-harness/mcp_bridge.py"),
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
                response = await client.call_tool(name, args)
                if response.isError:
                    evidence["failure"] = {
                        "tool": name,
                        "content": [
                            part.text
                            for part in response.content
                            if hasattr(part, "text")
                        ],
                    }
                    save()
                    raise RuntimeError(
                        "Tool rejected; inspect retained failure, do not replay"
                    )
                return response.structuredContent or json.loads(
                    response.content[0].text
                )

            for label, original, input_id, filename, content, accepted in cases:
                text = original.read_text().replace(
                    "__instance__", "upload_declaration"
                )
                item = {
                    "case": label,
                    "original": str(original.relative_to(root)),
                    "original_sha256": hashlib.sha256(
                        original.read_bytes()
                    ).hexdigest(),
                    "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "input_id": input_id,
                    "expected_acceptance": accepted,
                    "status": "pending",
                }
                evidence["cases"].append(item)
                save()
                workspace = await call(
                    "wright_workspace_create",
                    {"name": f"Private {label} input declaration proof v3"},
                )
                scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
                doc = await call(
                    "wright_workflow_create",
                    {
                        **scope,
                        "path": f"workflows/{label}-input-proof.workflow.wflow",
                        "source": text,
                    },
                )
                with sqlite3.connect(state / "wright.sqlite") as db:
                    directory = Path(
                        db.execute(
                            "SELECT local_path FROM engineering_workspaces WHERE workspace_id=?",
                            (scope["workspace_id"],),
                        ).fetchone()[0]
                    )
                before = set(directory.rglob("*"))
                item.update(scope=scope, document=doc)
                save()
                reply = await call(
                    "wright_process_ui_update",
                    {
                        "request": {
                            **scope,
                            "path": doc["path"],
                            "expected_storage_digest": doc["storage_digest"],
                            "operation": "upload",
                            "input_id": input_id,
                            "filename": filename,
                            "bytes_base64": base64.b64encode(content).decode(),
                        }
                    },
                )
                item["reply"] = reply
                save()
                assert reply.get("ok") is accepted
                if accepted:
                    ref = reply["document"]
                    assert (directory / ref["artifact_ref"]).read_bytes() == content
                    assert ref["sha256"] == hashlib.sha256(content).hexdigest()
                else:
                    assert set(directory.rglob("*")) == before
                assert (directory / doc["path"]).read_text() == text
                assert not list((directory / "runs").rglob("*.json"))
                item.update(
                    status="passed", source_unchanged=True, process_runs_started=0
                )
                save()
    evidence["status"] = "passed"
    save()
    print(json.dumps({"status": "passed", "cases": len(cases), "runs": 0}))


if __name__ == "__main__":
    asyncio.run(main())
