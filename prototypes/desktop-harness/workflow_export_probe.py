"""Actual owner/MCP definition transfer; no execution, review or host download."""

import asyncio
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core.process_validation import canonical_digest
from core.workflow_bundle import WorkflowBundle


async def main(state):
    root = Path(__file__).resolve().parents[2]
    (state / "workflow-export.started").touch(exist_ok=False)
    receipt = state / "workflow-export-proof.json"
    evidence = {"scope": "definition transfer only", "cases": []}

    def save():
        receipt.write_text(json.dumps(evidence, indent=2) + "\n")

    save()
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
            "--native-editor",
        ],
    )
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as client:
            await client.initialize()

            async def call(name, args):
                result = await client.call_tool(name, args)
                if result.isError:
                    evidence["failed_tool"] = name
                    save()
                    raise RuntimeError(
                        "MCP rejected operation; retain state, no replay"
                    )
                return result.structuredContent or json.loads(result.content[0].text)

            workspace = await call(
                "wright_workspace_create", {"name": "Private workflow export proof"}
            )
            scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
            with sqlite3.connect(state / "wright.sqlite") as db:
                workspace_root = Path(
                    db.execute(
                        "SELECT local_path FROM engineering_workspaces WHERE workspace_id=?",
                        (scope["workspace_id"],),
                    ).fetchone()[0]
                )
            fixture = workspace_root / "inputs/private-transfer-proof.txt"
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(
                "Private transfer-list fixture; not an engineering output.\n"
            )
            cases = {
                "manufacturing": "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/printed-replacement-part.workflow.wflow",
                "stevecad": "examples/stevecad-demonstrations/prompt-to-reviewed-cad/prompt-to-reviewed-cad-native.workflow.wflow",
            }
            for label, relative in cases.items():
                original = (root / relative).read_bytes()
                document = await call(
                    "wright_workflow_create",
                    {
                        **scope,
                        "path": f"workflows/export-{label}.workflow.wflow",
                        "source": original.decode().replace(
                            "__instance__", "export_probe"
                        ),
                    },
                )
                request = {
                    **scope,
                    "path": document["path"],
                    "expected_storage_digest": document["storage_digest"],
                }
                references = await call(
                    "wright_workflow_transfer_assets",
                    {"request": {**request, "kind": "references"}},
                )
                assert any(
                    item["path"] == "inputs/private-transfer-proof.txt"
                    for item in references["files"]
                )
                interfaces = await call(
                    "wright_workflow_transfer_assets",
                    {"request": {**request, "kind": "interfaces"}},
                )
                assert interfaces == {"interfaces": []}
                exported = await call("wright_workflow_export", {"request": request})
                if not exported.get("ok"):
                    evidence["rejection"] = exported
                    save()
                    raise RuntimeError("Owner rejected export; no substitute or replay")
                bundle = WorkflowBundle.model_validate(exported["bundle"])
                assert bundle.source == document["source"]
                assert bundle.source_digest == document["storage_digest"]
                assert canonical_digest(bundle) == exported["bundle_digest"]
                denied = await call(
                    "wright_workflow_export",
                    {"request": {**request, "expected_storage_digest": "0" * 64}},
                )
                assert not denied["ok"]
                observed = await call(
                    "wright_workflow_read", {**scope, "path": document["path"]}
                )
                assert observed["source"] == document["source"]
                transfer = {
                    **scope,
                    "bundle": exported["bundle"],
                    "destination_path": f"workflows/import-{label}.workflow.wflow",
                }
                report = await call(
                    "wright_workflow_import_inspect", {"request": transfer}
                )
                if not report["can_import"]:
                    evidence["inspection_rejection"] = report
                    save()
                    raise RuntimeError(
                        "Original definition requires correction; no simplification"
                    )
                assert report["can_run"] is False
                imported = await call(
                    "wright_workflow_import",
                    {
                        "request": {
                            **transfer,
                            "expected_bundle_digest": report["bundle_digest"],
                        }
                    },
                )
                if not imported.get("ok"):
                    evidence["import_failure"] = imported
                    save()
                    raise RuntimeError(
                        "Import not confirmed; inspect state, never retry"
                    )
                imported_document = imported["document"]["source"]
                assert imported_document["source"] == document["source"]
                assert imported_document["storage_digest"] == document["storage_digest"]
                duplicate = await call(
                    "wright_workflow_import_inspect", {"request": transfer}
                )
                assert duplicate["can_import"] is False
                evidence["cases"].append(
                    {
                        "original": relative,
                        "original_sha256": hashlib.sha256(original).hexdigest(),
                        "accepted_source_digest": document["storage_digest"],
                        "bundle_digest": exported["bundle_digest"],
                        "dependencies": [
                            d.model_dump(mode="json") for d in bundle.dependencies
                        ],
                        "accepted_source_unchanged": True,
                        "stale_source_denied": True,
                        "reference_fixture_discovered": True,
                        "saved_interface_list": "empty confirmed by owner; saved UI transfer unqualified",
                        "imported_source_digest": imported_document["storage_digest"],
                        "existing_destination_inspection_denied": True,
                        "import_can_run": report["can_run"],
                    }
                )
                save()
            with sqlite3.connect(state / "wright.sqlite") as db:
                workspace_root = Path(
                    db.execute(
                        "SELECT local_path FROM engineering_workspaces WHERE workspace_id=?",
                        (scope["workspace_id"],),
                    ).fetchone()[0]
                )
            assert not list((workspace_root / "runs").rglob("*.json"))
            evidence.update(
                status="passed",
                process_runs_started=0,
                host_download_verified=False,
                engineering_execution_verified=False,
            )
            save()
            print(json.dumps({"status": "passed", "cases": len(cases), "runs": 0}))


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]).resolve(strict=True)))
