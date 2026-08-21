"""Deterministic child MCP behavior for Rivet gateway tests.

These fixtures intentionally avoid the network, subprocesses, proprietary software,
and credentials. Integration tests adapt them through the existing gateway lifecycle.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping


ProgressCallback = Callable[[Mapping[str, Any]], Awaitable[None] | None]


@dataclass(slots=True)
class FakeRivetMcpServer:
    server_id: str
    namespace: str
    revision: str = "fixture-v1"
    receipts: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    cancellation_received: asyncio.Event = field(default_factory=asyncio.Event)
    release_slow_call: asyncio.Event = field(default_factory=asyncio.Event)
    ignore_cancellation: bool = False

    @property
    def tools(self) -> tuple[dict[str, Any], ...]:
        return (
            {
                "name": "inspect",
                "title": f"{self.namespace} inspect",
                "inputSchema": {
                    "type": "object",
                    "properties": {"value": {"type": "number"}},
                    "required": ["value"],
                    "additionalProperties": False,
                },
                "outputSchema": {
                    "type": "object",
                    "properties": {
                        "server": {"type": "string"},
                        "value": {"type": "number"},
                    },
                    "required": ["server", "value"],
                    "additionalProperties": False,
                },
            },
            {
                "name": "slow",
                "title": f"{self.namespace} slow operation",
                "inputSchema": {"type": "object", "additionalProperties": False},
                "outputSchema": {
                    "type": "object",
                    "properties": {"completed": {"type": "boolean"}},
                    "required": ["completed"],
                    "additionalProperties": False,
                },
            },
        )

    async def call_tool(
        self,
        name: str,
        arguments: Mapping[str, Any],
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        self.receipts.append((name, dict(arguments)))
        if name == "inspect":
            if progress_callback is not None:
                result = progress_callback(
                    {"status": "running", "progress": 0.5, "title": "Inspecting"}
                )
                if result is not None:
                    await result
            structured = {"server": self.server_id, "value": arguments["value"]}
            return {
                "content": [{"type": "text", "text": f"{self.server_id}: inspected"}],
                "structuredContent": structured,
            }
        if name != "slow":
            return {
                "content": [{"type": "text", "text": "unknown fixture tool"}],
                "isError": True,
            }
        if progress_callback is not None:
            result = progress_callback(
                {"status": "running", "progress": 0.1, "title": "Started slow call"}
            )
            if result is not None:
                await result
        try:
            await self.release_slow_call.wait()
        except asyncio.CancelledError:
            self.cancellation_received.set()
            if not self.ignore_cancellation:
                raise
            await self.release_slow_call.wait()
        return {
            "content": [{"type": "text", "text": "slow call completed"}],
            "structuredContent": {"completed": True},
        }


def fake_rivet_mcp_pair() -> tuple[FakeRivetMcpServer, FakeRivetMcpServer]:
    return (
        FakeRivetMcpServer("fixture-alpha", "alpha"),
        FakeRivetMcpServer("fixture-beta", "beta"),
    )
