"""Disposable MCP server: reads only the test-created local measurement fixture.

No packages, network, credentials, paid APIs, host CAD, or process execution.
Run only through the explicit opt-in native protocol test.
"""

import json
import sys
from pathlib import Path

INPUT_SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "number", "minimum": 0.25}},
    "required": ["value"],
    "additionalProperties": False,
}
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "number"}},
    "required": ["value"],
    "additionalProperties": False,
}


def main():
    transcript = Path(sys.argv[1])
    initialized = False
    for line in sys.stdin:
        request = json.loads(line)
        method = request.get("method")
        with transcript.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps({"direction": "request", "message": request}) + "\n"
            )
        if method == "initialize":
            result = {
                "protocolVersion": request["params"]["protocolVersion"],
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "native-disposable-measurement", "version": "1"},
            }
        elif method == "notifications/initialized":
            initialized = True
            continue
        elif initialized and method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "measure",
                        "description": "Measure a safe local fixture",
                        "inputSchema": INPUT_SCHEMA,
                        "outputSchema": OUTPUT_SCHEMA,
                    }
                ]
            }
        elif (
            initialized
            and method == "tools/call"
            and request["params"]["name"] == "measure"
        ):
            seed = json.loads(Path("fixture-data.json").read_text(encoding="utf-8"))
            value = request["params"]["arguments"]["value"] * seed["multiplier"]
            result = {
                "content": [{"type": "text", "text": "Local fixture measured"}],
                "structuredContent": {"value": value},
            }
        else:
            raise RuntimeError(
                "Unexpected protocol method or call before initialization"
            )
        response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
        with transcript.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps({"direction": "response", "message": response}) + "\n"
            )
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
