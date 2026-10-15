"""Transfer an existing declared input through actual MCP owners; never run CAD."""

import asyncio
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.workflow_bundle import WorkflowBundle
from core.process_validation import canonical_digest


async def main(state):
    (state / "asset-transfer.started").touch(exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    evidence = {"scope": "declared reference portability only", "status": "started"}
    receipt = state / "asset-transfer-proof.json"

    def save():
        receipt.write_text(json.dumps(evidence, indent=2) + "\n")

    def workspace_path(scope):
        with sqlite3.connect(state / "wright.sqlite") as db:
            return Path(
                db.execute(
                    "SELECT local_path FROM engineering_workspaces WHERE workspace_id=?",
                    (scope["workspace_id"],),
                ).fetchone()[0]
            )

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

            async def call(name, arguments):
                response = await client.call_tool(name, arguments)
                if response.isError:
                    evidence.update(status="failed", failed_tool=name)
                    save()
                    raise RuntimeError(
                        "MCP rejected operation; retain state, no replay"
                    )
                value = response.structuredContent or json.loads(
                    response.content[0].text
                )
                if value.get("ok") is False:
                    evidence.update(status="failed", failed_tool=name, rejection=value)
                    save()
                    raise RuntimeError("Owner rejected operation; no retry")
                return value

            scopes = []
            for name in ("Private reference export", "Private reference import"):
                workspace = await call("wright_workspace_create", {"name": name})
                scopes.append(
                    {key: workspace[key] for key in ("workspace_id", "session_id")}
                )
            origin, target = scopes
            evidence.update(origin=origin, target=target)
            save()
            templates = (
                root
                / "packages/workspace_service/src/workspace_service/engineering_workflow_templates"
            )
            asset = (
                templates
                / "inputs/printed-replacement-part/replacement-knob-source.svg"
            ).read_bytes()
            relative = "inputs/replacement-knob-source.svg"
            fixture = workspace_path(origin) / relative
            fixture.parent.mkdir(parents=True, exist_ok=True)
            # Existing input fixture only, not a generated engineering result.
            with fixture.open("xb") as stream:
                stream.write(asset)
            source = (
                templates / "templates/printed-replacement-part.workflow.wflow"
            ).read_text()
            document = await call(
                "wright_workflow_create",
                {
                    **origin,
                    "path": "workflows/reference-export.workflow.wflow",
                    "source": source.replace(
                        "__instance__", "reference_transfer"
                    ).replace("__input_root__", "inputs"),
                },
            )
            exported = await call(
                "wright_workflow_export",
                {
                    "request": {
                        **origin,
                        "path": document["path"],
                        "expected_storage_digest": document["storage_digest"],
                        "mode": "bundle",
                        "selected_reference_paths": [relative],
                        "selected_ui_ids": [],
                    }
                },
            )
            bundle = WorkflowBundle.model_validate(exported["bundle"])
            assert bundle.source == document["source"]
            assert canonical_digest(bundle) == exported["bundle_digest"]
            assert len(bundle.assets) == 1
            assert (
                bundle.assets[0].path == relative
                and bundle.assets[0].decoded() == asset
            )
            request = {
                **target,
                "bundle": exported["bundle"],
                "destination_path": "workflows/reference-import.workflow.wflow",
            }
            inspection = await call(
                "wright_workflow_import_inspect", {"request": request}
            )
            assert inspection["can_import"] and inspection["can_run"] is False
            result = await call(
                "wright_workflow_import",
                {
                    "request": {
                        **request,
                        "expected_bundle_digest": inspection["bundle_digest"],
                    }
                },
            )
            imported = result["document"]["source"]
            assert imported["source"] == document["source"]
            assert imported["storage_digest"] == document["storage_digest"]
            assert (workspace_path(target) / relative).read_bytes() == asset
            assert fixture.read_bytes() == asset
            repeated = await call(
                "wright_workflow_import_inspect", {"request": request}
            )
            assert repeated["can_import"] is False
            assert all(
                not list((workspace_path(scope) / "runs").rglob("*.json"))
                for scope in scopes
            )
            evidence.update(
                status="passed",
                reference_path=relative,
                reference_sha256=hashlib.sha256(asset).hexdigest(),
                source_digest=document["storage_digest"],
                bundle_digest=exported["bundle_digest"],
                exact_source_and_asset_bytes_preserved=True,
                existing_asset_and_destination_rejected=True,
                process_runs_started=0,
                saved_interface_transfer_verified=False,
                engineering_execution_verified=False,
                native_windows_verified=False,
            )
            save()
            print(json.dumps({"status": "passed", "scope": evidence["scope"]}))


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]).resolve(strict=True)))
