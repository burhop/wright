import sys
import asyncio
import json
import os
import httpx

# Resolve default API base URL
API_BASE_URL = os.getenv("WRIGHT_API_BASE_URL", "http://127.0.0.1:8000")


async def get_stdio_streams():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    w_transport, w_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer


async def listen_for_events(writer):
    """Listens to the FastAPI backend's SSE events for tool changes and forwards them to Hermes."""
    url = f"{API_BASE_URL}/api/gateway/events"
    while True:
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as r:
                    async for line in r.aiter_lines():
                        if line.startswith("data:"):
                            data = line[len("data:") :].strip()
                            if data == "list_changed":
                                notification = {
                                    "jsonrpc": "2.0",
                                    "method": "notifications/tools/list_changed",
                                }
                                payload = json.dumps(notification) + "\n"
                                writer.write(payload.encode("utf-8"))
                                await writer.drain()
        except Exception:
            # Fail silently and retry connection in the background
            await asyncio.sleep(3.0)


async def main():
    reader, writer = await get_stdio_streams()

    # Start the SSE background listener
    event_task = asyncio.create_task(listen_for_events(writer))

    async with httpx.AsyncClient(timeout=120.0) as client:
        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                try:
                    request = json.loads(line_str)
                except json.JSONDecodeError:
                    continue

                method = request.get("method")
                req_id = request.get("id")

                if method == "initialize":
                    # Respond locally with capabilities
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {"listChanged": True}},
                            "serverInfo": {
                                "name": "wright-gateway",
                                "version": "0.1.0",
                            },
                        },
                    }
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()

                elif method == "notifications/initialized":
                    # No response needed for notifications
                    continue

                elif method == "ping":
                    # Respond locally
                    response = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()

                elif method == "tools/list":
                    # Proxy request to API backend
                    try:
                        r = await client.get(f"{API_BASE_URL}/api/gateway/tools")
                        if r.status_code == 200:
                            result = r.json()
                        else:
                            result = {
                                "tools": [],
                                "error": f"Backend returned HTTP {r.status_code}",
                            }
                    except Exception as e:
                        result = {"tools": [], "error": str(e)}

                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()

                elif method == "tools/call":
                    # Proxy request to API backend
                    params = request.get("params", {})
                    try:
                        r = await client.post(
                            f"{API_BASE_URL}/api/gateway/call", json=params
                        )
                        if r.status_code == 200:
                            result = r.json()
                        else:
                            result = {
                                "isError": True,
                                "content": [
                                    {
                                        "type": "text",
                                        "text": f"Backend error: HTTP {r.status_code}",
                                    }
                                ],
                            }
                    except Exception as e:
                        result = {
                            "isError": True,
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Error communicating with backend: {e}",
                                }
                            ],
                        }

                    response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()

                elif req_id is not None:
                    # Method not found
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}",
                        },
                    }
                    writer.write((json.dumps(response) + "\n").encode("utf-8"))
                    await writer.drain()

            except Exception:
                # Catch any unexpected errors in loop to keep stdin reader alive
                pass

    event_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
