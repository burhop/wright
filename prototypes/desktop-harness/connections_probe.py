"""Read-only official MCP-client catalog qualification in an existing isolated scope."""

import asyncio
import json
from pathlib import Path
import sys
import time

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(state: Path):
    seed = json.loads((state / "home-probe.json").read_text())
    scope = {key: seed["scope"][key] for key in ("workspace_id", "session_id")}
    output = state / f"connections-probe-{time.time_ns()}.json"
    report = {
        "boundary": "official MCP client and real Wright catalog; no provider calls or engineering execution",
        "scope": scope,
        "calls": [],
    }
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py").resolve()),
            "--state-dir",
            str(state),
            "--native-editor",
            "--native-working-view",
        ],
    )
    try:
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as client:
                await client.initialize()
                result = await client.call_tool(
                    "wright_connections_list", {**scope, "search": "SteveCAD"}
                )
                report["calls"].append(
                    {
                        "tool": "wright_connections_list",
                        "is_error": bool(result.isError),
                    }
                )
                if result.isError or not result.structuredContent:
                    raise RuntimeError("Catalog read not confirmed")
                data = result.structuredContent
                assert data["workspace_id"] == scope["workspace_id"]
                assert data["connections"], (
                    "Expected the existing SteveCAD catalog entry"
                )
                report["catalog"] = data
                denied = await client.call_tool(
                    "wright_connections_list", {**scope, "session_id": "wrong-session"}
                )
                assert denied.isError, "Wrong-session read must be denied"
                report["calls"].append(
                    {"tool": "wright_connections_list", "wrong_session_denied": True}
                )
                report["passed"] = True
    finally:
        output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"evidence": str(output), "passed": report.get("passed", False)}))


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]).resolve(strict=True)))
