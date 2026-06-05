import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
import httpx
from httpx_sse import aconnect_sse
from .base import BaseRunner

logger = logging.getLogger(__name__)


class SseRunner(BaseRunner):
    """MCP Runner implementing SSE (Server-Sent Events) communication with remote MCP servers."""

    def __init__(self, sse_url: str):
        self.sse_url = sse_url
        self.client: Optional[httpx.AsyncClient] = None
        self._message_endpoint: Optional[str] = None
        self._read_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()
        self._endpoint_ready = asyncio.Event()

    async def start(self) -> None:
        async with self._lock:
            if self.client is not None:
                raise RuntimeError("Runner is already running.")

            self.client = httpx.AsyncClient(timeout=60.0)
            self._read_task = asyncio.create_task(self._connect_and_read())

            # Wait for endpoint event to be ready (handshake) within 15 seconds
            try:
                await asyncio.wait_for(self._endpoint_ready.wait(), timeout=15.0)
            except Exception as e:
                logger.error(
                    "Failed to connect or establish SSE endpoint with %s: %s",
                    self.sse_url,
                    e,
                )
                await self.stop()
                raise RuntimeError(f"SSE handshake failed: {e}") from e

            # Perform MCP Handshake
            try:
                await asyncio.wait_for(self._handshake(), timeout=10.0)
            except Exception as e:
                logger.error(
                    "Handshake failed with SSE MCP server %s: %s", self.sse_url, e
                )
                await self.stop()
                raise RuntimeError(f"MCP handshake failed: {e}") from e

    async def stop(self) -> None:
        async with self._lock:
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
        init_res = await self._send_request("initialize", init_params)
        logger.debug("Received SSE initialize response: %s", init_res)

        # 2. Send initialized notification (no ID)
        await self._send_notification("notifications/initialized")

    async def _send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.is_running():
            raise RuntimeError("SSE runner is not running or not initialized.")

        req_id = self._next_id
        self._next_id += 1

        fut = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = fut

        payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params

        try:
            # Post request to the message endpoint
            response = await self.client.post(self._message_endpoint, json=payload)
            response.raise_for_status()

            # If the response contains the result directly, resolve immediately
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "id" in data and data["id"] == req_id:
                        self._pending_requests.pop(req_id, None)
                        if "error" in data:
                            raise RuntimeError(f"RPC Error: {data['error']}")
                        return data.get("result", {})
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            self._pending_requests.pop(req_id, None)
            raise RuntimeError(
                f"Failed to post request to message endpoint: {e}"
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

        try:
            response = await self.client.post(self._message_endpoint, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to send SSE notification %s: %s", method, e)

    async def _connect_and_read(self) -> None:
        while self.client:
            try:
                async with aconnect_sse(
                    self.client, "GET", self.sse_url
                ) as event_source:
                    async for sse in event_source.aiter_sse():
                        event_type = sse.event
                        data_str = sse.data.strip()

                        if event_type == "endpoint":
                            # The data is the endpoint URL for posting messages
                            if data_str:
                                self._message_endpoint = urljoin(self.sse_url, data_str)
                                logger.info(
                                    "SSE message endpoint established: %s",
                                    self._message_endpoint,
                                )
                                self._endpoint_ready.set()
                        elif event_type == "message":
                            if not data_str:
                                continue
                            try:
                                message = json.loads(data_str)
                            except json.JSONDecodeError:
                                logger.warning(
                                    "Received invalid JSON message from SSE: %s",
                                    data_str,
                                )
                                continue

                            if "id" in message:
                                msg_id = message["id"]
                                fut = self._pending_requests.pop(msg_id, None)
                                if fut and not fut.done():
                                    if "error" in message:
                                        fut.set_exception(
                                            RuntimeError(
                                                f"RPC Error: {message['error']}"
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
                    "SSE stream error with %s: %s. Retrying in 5 seconds...",
                    self.sse_url,
                    e,
                )
                await asyncio.sleep(5)
