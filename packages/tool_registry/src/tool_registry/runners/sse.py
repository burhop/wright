import asyncio
import json
import logging
import hashlib
import webbrowser
from typing import List, Dict, Any, Optional
from urllib.parse import parse_qs, urljoin, urlsplit

import httpx
from httpx_sse import aconnect_sse, EventSource
from mcp.client.auth import OAuthClientProvider
from mcp.shared.auth import (
    OAuthClientInformationFull,
    OAuthClientMetadata,
    OAuthToken,
)
from core.redaction import redact_mapping, redact_text
from .base import BaseRunner, ProgressCallback
from .protocol import ChildProtocolState, NotificationHandler
from ..secrets import read_secrets, write_secrets

logger = logging.getLogger(__name__)


class _WrightOAuthTokenStorage:
    """Persist MCP OAuth state in Wright's server-scoped secret bundle."""

    def __init__(self, server_id: str) -> None:
        self.server_id = server_id

    def _read_model(self, key: str, model_type):
        raw = read_secrets(self.server_id).get(key)
        if not raw:
            return None
        try:
            return model_type.model_validate_json(raw)
        except Exception:
            logger.warning("Ignoring invalid stored OAuth state for %s", self.server_id)
            return None

    def _write_model(self, key: str, value) -> None:
        credentials = read_secrets(self.server_id)
        credentials[key] = value.model_dump_json()
        write_secrets(self.server_id, credentials)

    def clear_oauth_state(self) -> None:
        credentials = read_secrets(self.server_id)
        changed = False
        for key in ("MCP_OAUTH_TOKEN", "MCP_OAUTH_CLIENT"):
            if key in credentials:
                del credentials[key]
                changed = True
        if changed:
            write_secrets(self.server_id, credentials)

    async def get_tokens(self) -> OAuthToken | None:
        return self._read_model("MCP_OAUTH_TOKEN", OAuthToken)

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._write_model("MCP_OAUTH_TOKEN", tokens)

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self._read_model("MCP_OAUTH_CLIENT", OAuthClientInformationFull)

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._write_model("MCP_OAUTH_CLIENT", client_info)


class _OAuthCallbackServer:
    """Small loopback receiver for an interactive OAuth authorization code."""

    def __init__(self, *, timeout: float = 300.0) -> None:
        self.timeout = timeout
        self.server: asyncio.AbstractServer | None = None
        self.future: asyncio.Future[tuple[str, str | None]] | None = None

    async def start(self, *, port: int | None = None) -> str:
        self.future = asyncio.get_running_loop().create_future()
        self.server = await asyncio.start_server(
            self._handle_connection,
            host="127.0.0.1",
            port=port or 0,
        )
        socket = self.server.sockets[0]
        port = socket.getsockname()[1]
        return f"http://127.0.0.1:{port}/oauth/callback"

    async def open_authorization_url(self, url: str) -> None:
        try:
            opened = webbrowser.open(url, new=2)
            if not opened:
                logger.warning("Could not open the MCP OAuth authorization page")
        except Exception as error:
            logger.warning("Could not open the MCP OAuth authorization page: %s", redact_text(error))

    async def wait_for_callback(self) -> tuple[str, str | None]:
        if self.future is None:
            raise RuntimeError("OAuth callback server is not started")
        try:
            result = await asyncio.wait_for(self.future, timeout=self.timeout)
        except BaseException:
            await self.close()
            raise
        self.future = asyncio.get_running_loop().create_future()
        return result

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        result: tuple[str, str | None] | None = None
        error: Exception | None = None
        try:
            request = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), timeout=10.0)
            request_line = request.splitlines()[0].decode("ascii", errors="replace")
            parts = request_line.split(" ", 2)
            if len(parts) < 2:
                raise ValueError("Invalid OAuth callback request")
            target = urlsplit(parts[1])
            if target.path != "/oauth/callback":
                raise ValueError("Invalid OAuth callback path")
            query = parse_qs(target.query, keep_blank_values=True)
            state = query.get("state", [None])[0]
            oauth_error = query.get("error", [None])[0]
            if oauth_error:
                raise RuntimeError(f"OAuth authorization failed: {oauth_error}")
            code = query.get("code", [None])[0]
            if not code:
                raise RuntimeError("OAuth callback did not include an authorization code")
            result = (code, state)
        except Exception as caught:
            error = caught

        if self.future is not None and not self.future.done():
            if error is not None:
                self.future.set_exception(error)
            elif result is not None:
                self.future.set_result(result)

        body = (
            "Wright received the authorization response. You can return to Wright."
            if error is None
            else "Wright could not complete MCP authorization. Return to Wright for details."
        )
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            f"Content-Length: {len(body.encode('utf-8'))}\r\n"
            "Connection: close\r\n\r\n"
            f"{body}"
        )
        writer.write(response.encode("utf-8"))
        try:
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def close(self) -> None:
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        if self.future is not None and not self.future.done():
            self.future.cancel()


class SseRunner(BaseRunner):
    """MCP Runner implementing SSE (Server-Sent Events) and Streamable HTTP transport with remote MCP servers."""

    def __init__(
        self,
        sse_url: str,
        *,
        ui_enabled: bool = False,
        server_id: str | None = None,
        oauth_enabled: bool = True,
    ):
        self.sse_url = sse_url
        self.server_id = server_id or "remote-" + hashlib.sha256(sse_url.encode()).hexdigest()[:32]
        self.oauth_enabled = oauth_enabled
        self.client: Optional[httpx.AsyncClient] = None
        self._oauth_callback: _OAuthCallbackServer | None = None
        self._oauth_provider: OAuthClientProvider | None = None
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
        self.protocol = ChildProtocolState(ui_enabled=ui_enabled)

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

    def _preferred_oauth_callback_port(
        self, client_info: OAuthClientInformationFull | None
    ) -> int:
        if client_info and client_info.redirect_uris:
            redirect = urlsplit(str(client_info.redirect_uris[0]))
            if (
                redirect.scheme == "http"
                and redirect.hostname == "127.0.0.1"
                and redirect.path == "/oauth/callback"
                and redirect.port
            ):
                return redirect.port
        return 8700 + int(hashlib.sha256(self.server_id.encode()).hexdigest()[:4], 16) % 1000

    async def start(self) -> None:
        async with self._lock:
            if self.client is not None:
                raise RuntimeError("Runner is already running.")

            # Set up base client
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Cache-Control": "no-cache",
            }
            auth = None
            if self.oauth_enabled:
                self._oauth_callback = _OAuthCallbackServer()
                oauth_storage = _WrightOAuthTokenStorage(self.server_id)
                stored_client = await oauth_storage.get_client_info()
                try:
                    redirect_uri = await self._oauth_callback.start(
                        port=self._preferred_oauth_callback_port(stored_client)
                    )
                except OSError:
                    if stored_client is not None:
                        oauth_storage.clear_oauth_state()
                    await self._oauth_callback.close()
                    self._oauth_callback = _OAuthCallbackServer()
                    redirect_uri = await self._oauth_callback.start()
                metadata = OAuthClientMetadata(
                    redirect_uris=[redirect_uri],
                    client_name="Wright",
                    software_id="wright",
                    software_version="0.1.0",
                )
                self._oauth_provider = OAuthClientProvider(
                    self.sse_url,
                    metadata,
                    oauth_storage,
                    redirect_handler=self._oauth_callback.open_authorization_url,
                    callback_handler=self._oauth_callback.wait_for_callback,
                    timeout=self._oauth_callback.timeout,
                )
                auth = self._oauth_provider

            self.client = httpx.AsyncClient(
                timeout=60.0,
                headers=headers,
                follow_redirects=True,
                auth=auth,
            )

            # Probe for Streamable HTTP by sending a POST initialize payload
            logger.info("Probing MCP endpoint for Streamable HTTP support")
            probe_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": self.protocol.initialize_parameters(),
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

        if self._oauth_callback:
            await self._oauth_callback.close()
            self._oauth_callback = None
        self._oauth_provider = None

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
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        progress_callback: ProgressCallback | None = None,
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

    async def list_resources(self, cursor: str | None = None) -> Dict[str, Any]:
        params = {"cursor": cursor} if cursor else None
        return await asyncio.wait_for(
            self._send_request("resources/list", params), timeout=60.0
        )

    async def list_resource_templates(
        self, cursor: str | None = None
    ) -> Dict[str, Any]:
        params = {"cursor": cursor} if cursor else None
        return await asyncio.wait_for(
            self._send_request("resources/templates/list", params), timeout=60.0
        )

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        return await asyncio.wait_for(
            self._send_request("resources/read", {"uri": uri}), timeout=60.0
        )

    async def subscribe_resource(self, uri: str) -> None:
        await asyncio.wait_for(
            self._send_request("resources/subscribe", {"uri": uri}), timeout=60.0
        )

    async def unsubscribe_resource(self, uri: str) -> None:
        await asyncio.wait_for(
            self._send_request("resources/unsubscribe", {"uri": uri}), timeout=60.0
        )

    def add_notification_handler(self, handler: NotificationHandler) -> None:
        self.protocol.add_notification_handler(handler)

    async def _handshake(self) -> None:
        result = await self._send_request(
            "initialize", self.protocol.initialize_parameters()
        )
        self.protocol.accept_initialize(result)
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
        except asyncio.CancelledError:
            self._pending_requests.pop(req_id, None)
            try:
                await asyncio.shield(
                    self._send_notification(
                        "notifications/cancelled",
                        {"requestId": req_id, "reason": "caller cancelled"},
                    )
                )
            except Exception:
                logger.warning(
                    "Failed to send SSE cancellation notification for %s", req_id
                )
            raise
        except Exception as e:
            self._pending_requests.pop(req_id, None)
            raise RuntimeError(
                f"Failed to post request to message endpoint: {redact_text(e)}"
            ) from e

        # Otherwise wait for the response to arrive in the SSE stream.
        try:
            return await fut
        except asyncio.CancelledError:
            self._pending_requests.pop(req_id, None)
            try:
                await asyncio.shield(
                    self._send_notification(
                        "notifications/cancelled",
                        {"requestId": req_id, "reason": "caller cancelled"},
                    )
                )
            except Exception:
                logger.warning(
                    "Failed to send SSE cancellation notification for %s", req_id
                )
            raise

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
                            else:
                                method = message.get("method")
                                if isinstance(method, str):
                                    params = message.get("params")
                                    await self.protocol.handle_notification(
                                        method,
                                        params if isinstance(params, dict) else None,
                                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "SSE stream error: %s. Retrying in 5 seconds...",
                    redact_text(e),
                )
                await asyncio.sleep(5)
