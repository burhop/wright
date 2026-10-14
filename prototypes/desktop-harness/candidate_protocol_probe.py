"""Read-only package-command/resource qualification; no desktop acceptance claim."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(package, output):
    if output.exists():
        raise ValueError("Preserve existing receipt")
    manifest = json.loads((package / ".codex-plugin/plugin.json").read_text())
    wiring = json.loads((package / ".mcp.json").read_text())["mcpServers"]
    assert list(wiring) == ["wright-desktop-gb10"]
    config = wiring["wright-desktop-gb10"]
    params = StdioServerParameters(command=config["command"], args=config["args"])
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as client:
            initialized = await client.initialize()
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert len(tools) == 31
            for name in (
                "wright_workflow_history",
                "wright_reasoning_image",
                "wright_home",
            ):
                assert tools[name].annotations.readOnlyHint
            assert tools["wright_workflow_save"].meta["ui"]["visibility"] == ["app"]
            assert tools["wright_workspace_create"].meta["ui"]["visibility"] == [
                "model",
                "app",
            ]
            uri = tools["wright_home"].meta["ui"]["resourceUri"]
            assert tools["wright_process_view"].meta["ui"]["resourceUri"] == uri
            resource = await client.read_resource(uri)
            data = resource.contents[0].text.encode()
            digest = hashlib.sha256(data).hexdigest()
            assert digest in uri
            assert (
                data
                == (Path(config["args"][0]).parent / "native-editor.html").read_bytes()
            )
            home = await client.call_tool("wright_home", {})
            assert not home.isError and home.structuredContent["view"] == "home"
            state = Path(config["args"][config["args"].index("--state-dir") + 1])
            binding = json.loads((state / "desktop-binding.json").read_text())
            assert binding["image_input_profile"] == "unavailable"
            evidence = {
                "package": str(package),
                "version": manifest["version"],
                "protocol": initialized.protocolVersion,
                "tool_count": len(tools),
                "resource": {"uri": uri, "sha256": digest, "bytes": len(data)},
                "files": {
                    str(path.relative_to(package)): hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest()
                    for path in sorted(package.rglob("*"))
                    if path.is_file()
                },
                "profile": binding["image_input_profile"],
                "boundary": "actual package command, MCP protocol and resource; no writes or native desktop acceptance",
            }
            output.write_text(json.dumps(evidence, indent=2) + "\n")
            print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    asyncio.run(main(args.package.resolve(), args.output.resolve()))
