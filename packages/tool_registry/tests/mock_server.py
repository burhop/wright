import sys
import json


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Handle requests
        if req_id is not None:
            if method == "initialize":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {"name": "mock-server", "version": "1.0"},
                    },
                }
            elif method == "tools/list":
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "test_tool",
                                "title": "Test Tool",
                                "description": "A test tool",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {"val": {"type": "string"}},
                                    "required": ["val"],
                                },
                                "outputSchema": {"type": "object"},
                                "annotations": {
                                    "title": "Test Tool",
                                    "readOnlyHint": True,
                                },
                            }
                        ]
                    },
                }
            elif method == "tools/call":
                args = params.get("arguments", {})
                progress_token = (params.get("_meta") or {}).get("progressToken")
                if progress_token is not None:
                    for token, progress, message in (
                        (progress_token, 1, "Preparing"),
                        (progress_token, 0.5, "Stale"),
                        ("unknown-token", 2, "Wrong request"),
                        (progress_token, 2, "Completed"),
                    ):
                        sys.stdout.write(
                            json.dumps(
                                {
                                    "jsonrpc": "2.0",
                                    "method": "notifications/progress",
                                    "params": {
                                        "progressToken": token,
                                        "progress": progress,
                                        "total": 2,
                                        "message": message,
                                    },
                                }
                            )
                            + "\n"
                        )
                        sys.stdout.flush()
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Called test_tool with: {json.dumps(args)}",
                            }
                        ]
                    },
                }
            else:
                res = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": "Method not found"},
                }
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        else:
            # Handle notifications (e.g. notifications/initialized)
            pass


if __name__ == "__main__":
    main()
