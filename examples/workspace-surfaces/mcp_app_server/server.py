"""Reference MCP server that publishes one packaged MCP App over stdio."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server
from pydantic import AnyUrl

APP_URI = "ui://wright.reference/design"
APP_HTML = Path(__file__).with_name("ui") / "dist" / "index.html"
MCP_APP_MIME = "text/html;profile=mcp-app"

server = Server(
    "wright-reference-mcp-app",
    version="1.0.0",
    instructions="A minimal design viewer with meaningful non-UI results.",
)
_design = {"shape": "bracket", "width": 80, "height": 50, "revision": 1}


@server.list_resources()
async def list_resources() -> list[types.Resource]:
    # MCP Apps resources are allowed to be read by exact URI without being listed.
    return []


@server.read_resource()
async def read_resource(uri: AnyUrl) -> list[ReadResourceContents]:
    if str(uri) != APP_URI:
        raise ValueError("Unknown resource")
    if not APP_HTML.is_file():
        raise RuntimeError("Build the packaged UI with `npm run build` in ui/")
    return [
        ReadResourceContents(
            content=APP_HTML.read_text(encoding="utf-8"),
            mime_type=MCP_APP_MIME,
            meta={
                "ui": {
                    "csp": {"connectDomains": [], "resourceDomains": []},
                    "permissions": {},
                }
            },
        )
    ]


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    empty_object = {"type": "object", "properties": {}, "additionalProperties": False}
    return [
        types.Tool(
            name="show_design",
            description="Show the current design. Returns a text summary without UI support.",
            inputSchema=empty_object,
            _meta={"ui": {"resourceUri": APP_URI, "visibility": ["model", "app"]}},
        ),
        types.Tool(
            name="resize_design",
            description="Resize the current design from its packaged app.",
            inputSchema={
                "type": "object",
                "properties": {
                    "width": {"type": "integer", "minimum": 10, "maximum": 500},
                    "height": {"type": "integer", "minimum": 10, "maximum": 500},
                },
                "required": ["width", "height"],
                "additionalProperties": False,
            },
            _meta={"ui": {"visibility": ["app"]}},
        ),
        types.Tool(
            name="model_only_status",
            description="A model-only operation used to demonstrate host denial from the app.",
            inputSchema=empty_object,
            _meta={"ui": {"visibility": ["model"]}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> Any:
    if name == "show_design":
        return (
            [
                types.TextContent(
                    type="text",
                    text=(
                        f"Design: {_design['shape']}, {_design['width']} by "
                        f"{_design['height']} millimetres (revision {_design['revision']})."
                    ),
                )
            ],
            dict(_design),
        )
    if name == "resize_design":
        values = arguments or {}
        _design.update(width=values["width"], height=values["height"])
        _design["revision"] += 1
        return (
            [types.TextContent(type="text", text="Design dimensions updated.")],
            dict(_design),
        )
    if name == "model_only_status":
        return {"status": "ready", "revision": _design["revision"]}
    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(
                notification_options=NotificationOptions(),
                experimental_capabilities={"io.modelcontextprotocol/ui": {}},
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
