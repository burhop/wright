import asyncio
import json
import os
import subprocess
import structlog
import shlex
from typing import List, Dict, Any, Optional, Union
from opentelemetry import trace
from core.redaction import SECRET_KEY_RE, redact_command, redact_mapping, redact_text
from .base import BaseRunner

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


def _subprocess_kwargs() -> Dict[str, Any]:
    """Hide stdio tool subprocess consoles on Windows."""
    if os.name != "nt":
        return {}

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if not creationflags:
        return {}

    return {"creationflags": creationflags}


class StdioRunner(BaseRunner):
    """MCP Runner implementing stdio-based JSON-RPC communication with local subprocesses."""

    def __init__(
        self,
        command: Union[List[str], str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ):
        if isinstance(command, str):
            self.command = shlex.split(command)
        else:
            self.command = [str(c) for c in command]
        self.env = env
        self.cwd = cwd
        self.process: Optional[asyncio.subprocess.Process] = None
        self._read_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[Union[int, str], asyncio.Future] = {}
        self._next_id = 1
        self._lock = asyncio.Lock()

    def _secret_values(self) -> list[str]:
        return [
            value
            for key, value in (self.env or {}).items()
            if value and SECRET_KEY_RE.search(key)
        ]

    async def start(self) -> None:
        async with self._lock:
            if self.process is not None:
                raise RuntimeError("Runner is already running.")

            import os

            run_env = os.environ.copy()
            if self.env:
                run_env.update(self.env)

            logger.info(
                "mcp_server_spawning",
                command=redact_command(self.command),
                cwd=self.cwd,
            )
            try:
                self.process = await asyncio.create_subprocess_exec(
                    *self.command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=run_env,
                    cwd=self.cwd,
                    **_subprocess_kwargs(),
                )
                # Increase StreamReader limit to 10MB to support large tool schemas/responses
                if self.process.stdout:
                    self.process.stdout._limit = 10 * 1024 * 1024
                if self.process.stderr:
                    self.process.stderr._limit = 10 * 1024 * 1024
            except Exception as e:
                logger.error(
                    "mcp_server_spawn_failed",
                    command=redact_command(self.command),
                    error=redact_text(e, self._secret_values()),
                )
                raise RuntimeError(f"Failed to spawn subprocess: {e}") from e

            self._read_task = asyncio.create_task(self._read_stdout())
            self._stderr_task = asyncio.create_task(self._read_stderr())

        # Enforce handshake within 60 seconds (done outside lock to prevent deadlock)
        try:
            await asyncio.wait_for(self._handshake(), timeout=60.0)
        except Exception as e:
            logger.error(
                "mcp_server_handshake_failed",
                command=redact_command(self.command),
                error=redact_text(e, self._secret_values()),
            )
            await self.stop()
            raise RuntimeError(f"MCP handshake failed: {e}") from e

    async def stop(self) -> None:
        async with self._lock:
            # Cancel reader tasks
            if self._read_task:
                self._read_task.cancel()
                self._read_task = None
            if self._stderr_task:
                self._stderr_task.cancel()
                self._stderr_task = None

            # Resolve pending requests with an exception
            for fut in self._pending_requests.values():
                if not fut.done():
                    fut.set_exception(RuntimeError("Runner stopped."))
            self._pending_requests.clear()

            if self.process:
                logger.info("mcp_server_stopping", command=redact_command(self.command))
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                except Exception:
                    pass

                try:
                    # Give it a brief moment to exit cleanly
                    await asyncio.wait_for(self.process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning(
                        "mcp_server_force_killing", command=redact_command(self.command)
                    )
                    try:
                        self.process.kill()
                    except Exception:
                        pass
                self.process = None

    def is_running(self) -> bool:
        return self.process is not None and self.process.returncode is None

    async def list_tools(self) -> List[Dict[str, Any]]:
        with tracer.start_as_current_span("mcp.list_tools") as span:
            span.set_attribute("mcp.command", redact_command(self.command))
            try:
                response = await asyncio.wait_for(
                    self._send_request("tools/list"), timeout=60.0
                )
                tools = response.get("tools", [])
                span.set_attribute("mcp.tools_count", len(tools))
                return tools
            except asyncio.TimeoutError as e:
                span.record_exception(e)
                raise TimeoutError("List tools request timed out after 60 seconds.")
            except Exception as e:
                span.record_exception(e)
                raise

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        with tracer.start_as_current_span("mcp.call_tool") as span:
            span.set_attribute("mcp.tool_name", tool_name)
            span.set_attribute("mcp.command", redact_command(self.command))
            try:
                payload = {"name": tool_name, "arguments": arguments}
                response = await asyncio.wait_for(
                    self._send_request("tools/call", payload), timeout=60.0
                )
                return response
            except asyncio.TimeoutError as e:
                span.record_exception(e)
                raise TimeoutError(
                    f"Call to tool '{tool_name}' timed out after 60 seconds."
                )
            except Exception as e:
                span.record_exception(e)
                raise

    async def _handshake(self) -> None:
        # 1. Send initialize
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "wright", "version": "0.1.0"},
        }
        await self._send_request("initialize", init_params)
        logger.debug("mcp_initialize_response_received")

        # 2. Send initialized notification (no ID)
        await self._send_notification("notifications/initialized")

    async def _send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.is_running():
            raise RuntimeError("Subprocess is not running.")

        req_id = self._next_id
        self._next_id += 1

        fut = asyncio.get_running_loop().create_future()
        self._pending_requests[req_id] = fut

        payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params

        serialized = json.dumps(payload) + "\n"
        try:
            self.process.stdin.write(serialized.encode("utf-8"))
            await self.process.stdin.drain()
        except Exception as e:
            self._pending_requests.pop(req_id, None)
            raise RuntimeError(f"Failed to write request to stdin: {e}") from e

        return await fut

    async def _send_notification(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> None:
        if not self.is_running():
            raise RuntimeError("Subprocess is not running.")

        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params

        serialized = json.dumps(payload) + "\n"
        try:
            self.process.stdin.write(serialized.encode("utf-8"))
            await self.process.stdin.drain()
        except Exception as e:
            logger.error(
                "mcp_notification_send_failed",
                method=method,
                error=redact_text(e, self._secret_values()),
            )

    async def _read_stdout(self) -> None:
        while self.process and self.process.stdout:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break

                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue

                try:
                    message = json.loads(line_str)
                except json.JSONDecodeError:
                    logger.warning(
                        "mcp_non_json_stdout", byte_count=len(line), redacted=True
                    )
                    continue

                logger.debug(
                    "mcp_protocol_message_received",
                    method=message.get("method"),
                    has_id="id" in message,
                    has_error="error" in message,
                )

                if "id" in message:
                    msg_id = message["id"]
                    fut = self._pending_requests.pop(msg_id, None)
                    if fut and not fut.done():
                        if "error" in message:
                            fut.set_exception(
                                RuntimeError(
                                    "RPC Error: "
                                    + redact_text(
                                        redact_mapping({"error": message["error"]}),
                                        self._secret_values(),
                                    )
                                )
                            )
                        else:
                            fut.set_exception(
                                RuntimeError("RPC Error: Result missing in response")
                            ) if "result" not in message else fut.set_result(
                                message["result"]
                            )
                else:
                    # Handle notifications or requests initiated by the server if any (e.g. logMessage)
                    if message.get("method") == "notifications/message":
                        logger.info(
                            "mcp_server_notification", method=message.get("method")
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "mcp_stdout_read_failed",
                    error=redact_text(e, self._secret_values()),
                )
                break

    async def _read_stderr(self) -> None:
        while self.process and self.process.stderr:
            try:
                line = await self.process.stderr.readline()
                if not line:
                    break
                line_str = line.decode("utf-8").strip()
                if line_str:
                    logger.warning(
                        "mcp_server_stderr",
                        output=redact_text(line_str, self._secret_values()),
                    )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "mcp_stderr_read_failed",
                    error=redact_text(e, self._secret_values()),
                )
                break
