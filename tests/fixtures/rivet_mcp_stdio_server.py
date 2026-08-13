"""Minimal deterministic MCP stdio server for Rivet full-system tests."""

from __future__ import annotations

import json
import sys


def _response(request: dict) -> dict | None:
    request_id = request.get("id")
    if request_id is None:
        return None
    method = request.get("method")
    if method == "initialize":
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "wright-rivet-stdio-fixture", "version": "1.0"},
        }
    elif method == "tools/list":
        result = {
            "tools": [
                {
                    "name": "test_tool",
                    "title": "Engineering fixture tool",
                    "description": "Deterministic real stdio subprocess",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"val": {"type": "string"}},
                        "required": ["val"],
                        "additionalProperties": False,
                    },
                }
            ]
        }
    elif method == "tools/call":
        arguments = dict((request.get("params") or {}).get("arguments") or {})
        result = {
            "content": [
                {
                    "type": "text",
                    "text": f"inspected:{arguments.get('val', 'unknown')}",
                }
            ],
            "structuredContent": {"inspected": arguments.get("val")},
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": "Method not found"},
        }
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> None:
    for raw in sys.stdin:
        try:
            response = _response(json.loads(raw))
        except (TypeError, ValueError):
            continue
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
