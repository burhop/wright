"""Bounded protocol/source qualification; no model calls or workflow execution."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def qualify(state, phase):
    output = state / "native-editor-probe.json"
    if phase == "resource":
        await inspect_resource(state)
        return
    if phase == "reconcile":
        await reconcile(state, output)
        return
    if output.exists():
        raise ValueError("Preserve this probe; do not replay source creation")
    evidence = {
        "boundary": "official MCP client to isolated Wright source owner; not desktop UI acceptance",
        "calls": [],
    }
    output.write_text(json.dumps(evidence, indent=2))
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
            "--native-editor",
        ],
    )
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            async def call(name, arguments):
                result = await session.call_tool(name, arguments)
                evidence["calls"].append(
                    {"tool": name, "is_error": bool(result.isError)}
                )
                output.write_text(json.dumps(evidence, indent=2))
                if result.isError:
                    raise ValueError("Wright rejected probe operation: " + name)
                return result.structuredContent or json.loads(result.content[0].text)

            tools = await session.list_tools()
            by_name = {tool.name: tool for tool in tools.tools}
            assert by_name["wright_workflow_save"].meta["ui"]["visibility"] == ["app"]
            uri = by_name["wright_workflow_open"].meta["ui"]["resourceUri"]
            resource = await session.read_resource(uri)
            html = resource.contents[0].text
            assert hashlib.sha256(html.encode()).hexdigest() in uri
            assert html == Path(__file__).with_name("native-editor.html").read_text()
            evidence["resource"] = {
                "uri": uri,
                "sha256": hashlib.sha256(html.encode()).hexdigest(),
                "bytes": len(html.encode()),
            }
            workspace = await call(
                "wright_workspace_create", {"name": "Native editor qualification"}
            )
            evidence["workspace"] = workspace
            scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
            source = (
                Path(__file__).parents[2]
                / "specs/083-process-working-interfaces/fixtures/declared-human-input.workflow.wflow"
            ).read_text()
            scope["path"] = "workflows/native-editor.workflow.wflow"
            doc = await call("wright_workflow_create", {**scope, "source": source})
            opened = await call("wright_workflow_open", scope)
            assert opened["document"] == doc
            arguments = {
                **scope,
                "source": source.replace(
                    'name: "Test"', 'name: "Native editor proof"', 1
                ),
                "expected_storage_revision": doc["storage_revision"],
                "expected_storage_digest": doc["storage_digest"],
                "semantic_change_validated": True,
            }
            saved = await call("wright_workflow_save", arguments)
            assert saved["ok"] is True
            assert saved["document"]["source"] == arguments["source"]
            stale = await call("wright_workflow_save", arguments)
            assert (
                stale["error"]["code"] == "WORKFLOW_SOURCE_CONFLICT"
                and stale["error"]["outcome_known"] is True
            )
            denied = await call(
                "wright_workflow_save", {**arguments, "workspace_id": "wrong-workspace"}
            )
            assert denied["error"]["code"] == "PERMISSION_DENIED"
            assert await call("wright_workflow_read", scope) == saved["document"]
            evidence.update(
                scope=scope,
                accepted=saved["document"],
                passed=[
                    "versioned self-contained resource",
                    "UI-only save metadata",
                    "exact saved source open",
                    "source CAS save",
                    "stale rejection",
                    "wrong-scope denial",
                    "accepted readback",
                ],
            )
    output.write_text(json.dumps(evidence, indent=2))
    # A new MCP connection restores accepted source; it must not recreate or save.
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            restored = await session.call_tool("wright_workflow_read", scope)
            assert (
                not restored.isError
                and (restored.structuredContent or json.loads(restored.content[0].text))
                == evidence["accepted"]
            )
    evidence["passed"].append(
        "fresh connection accepted-source restoration without write"
    )
    output.write_text(json.dumps(evidence, indent=2))
    print(json.dumps({"passed": evidence["passed"], "state": str(state)}))


async def reconcile(state, output):
    evidence = json.loads(output.read_text())
    scope = {key: evidence["workspace"][key] for key in ("workspace_id", "session_id")}
    scope["path"] = "workflows/native-editor.workflow.wflow"
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
            "--native-editor",
        ],
    )
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            restored = await session.call_tool("wright_workflow_read", scope)
            assert not restored.isError
            doc = restored.structuredContent or json.loads(restored.content[0].text)
            expected = (
                (
                    Path(__file__).parents[2]
                    / "specs/083-process-working-interfaces/fixtures/declared-human-input.workflow.wflow"
                )
                .read_text()
                .replace('name: "Test"', 'name: "Native editor proof"', 1)
            )
            assert doc["source"] == expected and doc["storage_revision"] == 2
            assert (
                doc["storage_digest"] == hashlib.sha256(expected.encode()).hexdigest()
            )
    evidence.update(
        scope=scope,
        accepted=doc,
        reconciliation="read only after probe result-decoding assertion failed; no mutation replay",
    )
    evidence["passed"] = [
        "versioned resource",
        "source CAS save",
        "stale rejection",
        "wrong-scope denial",
        "fresh connection exact accepted source",
    ]
    output.with_name("native-editor-reconciled.json").write_text(
        json.dumps(evidence, indent=2)
    )
    print(json.dumps({"passed": evidence["passed"], "state": str(state)}))


async def inspect_resource(state, *, native_working_view=False):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
            "--native-editor",
            *(["--native-working-view"] if native_working_view else []),
        ],
    )
    record = {
        "boundary": "official MCP client; resource/source reads only, not Windows acceptance"
    }
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = {tool.name: tool for tool in (await session.list_tools()).tools}
            uri = tools["wright_workflow_open"].meta["ui"]["resourceUri"]
            html = (await session.read_resource(uri)).contents[0].text
            sha = hashlib.sha256(html.encode()).hexdigest()
            assert (
                sha in uri
                and html == Path(__file__).with_name("native-editor.html").read_text()
            )
            assert tools["wright_workflow_save"].meta["ui"]["visibility"] == ["app"]
            record.update(
                resource_uri=uri,
                resource_sha256=sha,
                resource_bytes=len(html.encode()),
                tools=len(tools),
                ui_save_visibility=["app"],
                native_working_view=native_working_view,
            )
    (state / "native-editor-current-resource.json").write_text(
        json.dumps(record, indent=2)
    )
    print(json.dumps(record))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument(
        "--phase", choices=["qualify", "reconcile", "resource"], default="qualify"
    )
    parser.add_argument("--native-working-view", action="store_true")
    args = parser.parse_args()
    if args.native_working_view:
        if args.phase != "resource":
            parser.error("Working-view opt-in is available only for resource inspection")
        asyncio.run(inspect_resource(args.state_dir, native_working_view=True))
    else:
        asyncio.run(qualify(args.state_dir, args.phase))
