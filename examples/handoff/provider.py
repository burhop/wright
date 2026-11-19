"""Two small, independently launched stdio providers for the file-handoff example."""

import asyncio
import csv
import hashlib
import math
import sys
from io import StringIO
from pathlib import Path

from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool


def description(name):
    return Tool(
        name=name,
        inputSchema={
            "type": "object",
            "properties": {"path": {"type": "string", "const": "points.csv"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        outputSchema={
            "type": "object",
            "properties": {
                "sha256": {"type": "string"},
                "length_mm": {"type": "number"},
            },
            "required": ["sha256"],
            "additionalProperties": False,
        },
    )


async def serve(name):
    if name not in {"write_points", "measure_length"}:
        raise ValueError("Choose write_points or measure_length.")
    server = Server("example-" + name, version="1.0.0")

    @server.list_tools()
    async def tools():
        return [description(name)]

    @server.call_tool()
    async def call(tool, arguments):
        if tool != name or arguments != {"path": "points.csv"}:
            raise ValueError("Unexpected tool or input.")
        path = Path("points.csv")
        if name == "write_points":
            path.write_bytes(b"x_mm,y_mm\n0,0\n3,4\n")
        content = path.read_bytes()
        result = {"sha256": hashlib.sha256(content).hexdigest()}
        if name == "measure_length":
            points = [
                (float(row["x_mm"]), float(row["y_mm"]))
                for row in csv.DictReader(StringIO(content.decode("ascii")))
            ]
            result["length_mm"] = sum(
                math.dist(a, b) for a, b in zip(points, points[1:])
            )
        return result

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(serve(sys.argv[1]))
