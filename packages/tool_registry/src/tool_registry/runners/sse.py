import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import httpx
from httpx_sse import aconnect_sse, EventSource
from core.redaction import redact_mapping, redact_text
from .base import BaseRunner

logger = logging.getLogger(__name__)


class SseRunner(BaseRunner):
    """MCP Runner implementing SSE (Server-Sent Events) and Streamable HTTP transport with remote MCP servers."""

    def __init__(self, sse_url: str):
        self.sse_url = sse_url
        self.client: Optional[httpx.AsyncClient] = None
        self._message_endpoint: Optional[str] = None
        self._read_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()
        self._endpoint_ready = asyncio.Event()

        # Streamable HTTP state
        self._is_streamable_http = False
        self._session_id: Optional[str] = None
        self._protocol_version: Optional[str] = None
        self._probe_response: Optional[Dict[str, Any]] = None

    def _prepare_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        if self._protocol_version:
            headers["mcp-protocol-version"] = self._protocol_version
        return headers

    async def start(self) -> None:
        async with self._lock:
            if self.client is not None:
                raise RuntimeError("Runner is already running.")

            # Set up base client
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Cache-Control": "no-cache",
            }
            self.client = httpx.AsyncClient(
                timeout=60.0,
                headers=headers,
                follow_redirects=True,
            )

            # Probe for Streamable HTTP by sending a POST initialize payload
            logger.info("Probing MCP endpoint for Streamable HTTP support")
            probe_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "wright", "version": "0.1.0"},
                },
            }
            try:
                response = await self.client.post(
                    self.sse_url,
                    json=probe_payload,
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "").lower()
                    resp_data = None
                    if "application/json" in content_type:
                        try:
                            resp_data = response.json()
                        except Exception:
                            pass
                    elif "text/event-stream" in content_type:
                        try:
                            event_source = EventSource(response)
                            async for sse in event_source.aiter_sse():
                                if sse.event == "message" and sse.data:
                                    resp_data = json.loads(sse.data)
                                    break
                        except Exception:
                            pass

                    if resp_data and (
                        "result" in resp_data
                        and "protocolVersion" in resp_data["result"]
                    ):
                        self._is_streamable_http = True
                        self._session_id = response.headers.get("mcp-session-id")
                        if "result" in resp_data:
                            self._protocol_version = str(
                                resp_data["result"].get("protocolVersion")
                            )
                        self._probe_response = resp_data
                        self._message_endpoint = self.sse_url
                        logger.info("Detected Streamable HTTP support")
            except Exception as e:
                logger.debug(
                    "Streamable HTTP probe failed; falling back to legacy SSE: %s",
                    redact_text(e),
                )

            # Start reading task
            self._read_task = asyncio.create_task(self._connect_and_read())

            if self._is_streamable_http:
                self._endpoint_ready.set()
            else:
                # Wait for endpoint event to be ready (handshake) within 15 seconds
                try:
                    await asyncio.wait_for(self._endpoint_ready.wait(), timeout=15.0)
                except asyncio.TimeoutError as te:
                    logger.error(
                        "Timeout waiting for SSE endpoint event",
                    )
                    await self._stop_locked()
                    raise RuntimeError(
                        "SSE handshake failed: timeout waiting for endpoint event"
                    ) from te
                except Exception as e:
                    logger.error("Failed to establish SSE endpoint: %s", redact_text(e))
                    await self._stop_locked()
                    raise RuntimeError(f"SSE handshake failed: {e}") from e

            # Perform MCP Handshake
            try:
                await asyncio.wait_for(self._handshake(), timeout=10.0)
            except Exception as e:
                logger.error("SSE MCP handshake failed: %s", redact_text(e))
                await self._stop_locked()
                raise RuntimeError(f"MCP handshake failed: {e}") from e

    async def _stop_locked(self) -> None:
        if self._read_task:
            self._read_task.cancel()
            self._read_task = None

        # Resolve pending requests with an exception
        for fut in self._pending_requests.values():
            if not fut.done():
                fut.set_exception(RuntimeError("Runner stopped."))
        self._pending_requests.clear()

        if self.client:
            await self.client.aclose()
            self.client = None

        self._message_endpoint = None
        self._endpoint_ready.clear()
        self._is_streamable_http = False
        self._session_id = None
        self._protocol_version = None
        self._probe_response = None

    async def stop(self) -> None:
        async with self._lock:
            await self._stop_locked()

    def is_running(self) -> bool:
        return self.client is not None and self._message_endpoint is not None

    async def list_tools(self) -> List[Dict[str, Any]]:
        try:
            response = await asyncio.wait_for(
                self._send_request("tools/list"), timeout=60.0
            )
            return response.get("tools", [])
        except asyncio.TimeoutError:
            raise TimeoutError("List tools request timed out after 60 seconds.")

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            payload = {"name": tool_name, "arguments": arguments}
            response = await asyncio.wait_for(
                self._send_request("tools/call", payload), timeout=60.0
            )
            return response
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Call to tool '{tool_name}' timed out after 60 seconds."
            )

    async def _handshake(self) -> None:
        # 1. Send initialize
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "wright", "version": "0.1.0"},
        }
        await self._send_request("initialize", init_params)
        logger.debug("SSE initialize response received")

        # 2. Send initialized notification (no ID)
        await self._send_notification("notifications/initialized")

    async def _send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.is_running():
            raise RuntimeError("SSE runner is not running or not initialized.")

        # Intercept initialize if we already performed it in Streamable HTTP probe
        if method == "initialize" and self._is_streamable_http and self._probe_response:
            if "error" in self._probe_response:
                raise RuntimeError(
                    "RPC Error: "
                    + redact_text(
                        redact_mapping({"error": self._probe_response["error"]})
                    )
                )
            return self._probe_response.get("result", {})

        req_id = self._next_id
        self._next_id += 1

        fut = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = fut

        payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params

        headers = self._prepare_headers() if self._is_streamable_http else None

        try:
            # Post request to the message endpoint
            response = await self.client.post(
                self._message_endpoint, json=payload, headers=headers
            )
            response.raise_for_status()

            # If the response contains the result directly, resolve immediately
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    try:
                        data = response.json()
                        if "id" in data and data["id"] == req_id:
                            self._pending_requests.pop(req_id, None)
                            if "error" in data:
                                raise RuntimeError(
                                    "RPC Error: "
                                    + redact_text(
                                        redact_mapping({"error": data["error"]})
                                    )
                                )
                            return data.get("result", {})
                    except Exception:
                        pass
                elif "text/event-stream" in content_type:
                    # Read and parse response body as SSE event
                    try:
                        event_source = EventSource(response)
                        async for sse in event_source.aiter_sse():
                            if sse.event == "message" and sse.data:
                                data = json.loads(sse.data)
                                if "id" in data and data["id"] == req_id:
                                    self._pending_requests.pop(req_id, None)
                                    if "error" in data:
                                        raise RuntimeError(
                                            "RPC Error: "
                                            + redact_text(
                                                redact_mapping({"error": data["error"]})
                                            )
                                        )
                                    return data.get("result", {})
                    except Exception as sse_err:
                        logger.error(
                            "Failed to parse SSE response in POST request: %s",
                            redact_text(sse_err),
                        )
        except Exception as e:
            self._pending_requests.pop(req_id, None)
            raise RuntimeError(
                f"Failed to post request to message endpoint: {redact_text(e)}"
            ) from e

        # Otherwise wait for the response to arrive in the SSE stream
        return await fut

    async def _send_notification(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self.is_running():
            raise RuntimeError("SSE runner is not running or not initialized.")

        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params

        headers = self._prepare_headers() if self._is_streamable_http else None

        try:
            response = await self.client.post(
                self._message_endpoint, json=payload, headers=headers
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(
                "Failed to send SSE notification %s: %s", method, redact_text(e)
            )

    async def _connect_and_read(self) -> None:
        if self._is_streamable_http and not self._session_id:
            logger.info(
                "Streamable HTTP server without session ID. Skipping background GET stream."
            )
            return

        while self.client:
            try:
                headers = (
                    self._prepare_headers()
                    if self._is_streamable_http
                    else {
                        "Accept": "text/event-stream",
                    }
                )
                async with aconnect_sse(
                    self.client, "GET", self.sse_url, headers=headers
                ) as event_source:
                    async for sse in event_source.aiter_sse():
                        event_type = sse.event
                        data_str = sse.data.strip()

                        if event_type == "endpoint":
                            # The data is the endpoint URL for posting messages
                            if data_str:
                                self._message_endpoint = urljoin(self.sse_url, data_str)
                                logger.info("SSE message endpoint established")
                                self._endpoint_ready.set()
                        elif event_type == "message":
                            if not data_str:
                                continue
                            try:
                                message = json.loads(data_str)
                            except json.JSONDecodeError:
                                logger.warning(
                                    "Received invalid JSON message from SSE (%s bytes)",
                                    len(data_str),
                                )
                                continue

                            if "id" in message:
                                msg_id = message["id"]
                                fut = self._pending_requests.pop(msg_id, None)
                                if fut and not fut.done():
                                    if "error" in message:
                                        fut.set_exception(
                                            RuntimeError(
                                                "RPC Error: "
                                                + redact_text(
                                                    redact_mapping(
                                                        {"error": message["error"]}
                                                    )
                                                )
                                            )
                                        )
                                    else:
                                        fut.set_exception(
                                            RuntimeError(
                                                "RPC Error: Result missing in response"
                                            )
                                        ) if "result" not in message else fut.set_result(
                                            message["result"]
                                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "SSE stream error: %s. Retrying in 5 seconds...",
                    redact_text(e),
                )
                await asyncio.sleep(5)
