import asyncio
import json
import inspect
import math
import os
import subprocess
import structlog
import shlex
import time
import uuid
from typing import List, Dict, Any, Optional, Union
from opentelemetry import trace
from core.redaction import SECRET_KEY_RE, redact_command, redact_mapping, redact_text
from .base import BaseRunner, ProgressCallback

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


def _slow_call_threshold_ms() -> float:
    try:
        return max(0.0, float(os.getenv("WRIGHT_MCP_SLOW_CALL_MS", "2000")))
    except ValueError:
        return 2000.0


class StdioRunner(BaseRunner):
    """MCP Runner implementing stdio-based JSON-RPC communication with local subprocesses."""

    def __init__(
        self,
        command: Union[List[str], str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        operation_timeout: float = 60.0,
    ):
        if operation_timeout <= 0:
            raise ValueError("operation_timeout must be positive")
        if isinstance(command, str):
            self.command = shlex.split(command)
        else:
            self.command = [str(c) for c in command]
        self.env = env
        self.cwd = cwd
        self.operation_timeout = operation_timeout
        self.process: Optional[asyncio.subprocess.Process] = None
        self._read_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[Union[int, str], asyncio.Future] = {}
        self._progress_callbacks: dict[
            str | int, tuple[ProgressCallback, float | None]
        ] = {}
        self._request_progress_tokens: dict[int | str, int | str] = {}
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
            self._progress_callbacks.clear()
            self._request_progress_tokens.clear()

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
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> Dict[str, Any]:
        with tracer.start_as_current_span("mcp.call_tool") as span:
            span.set_attribute("mcp.tool_name", tool_name)
            span.set_attribute("mcp.command", redact_command(self.command))
            try:
                payload: dict[str, Any] = {
                    "name": tool_name,
                    "arguments": arguments,
                }
                progress_token: str | None = None
                if progress_callback is not None:
                    progress_token = f"wright-{uuid.uuid4().hex}"
                    payload["_meta"] = {"progressToken": progress_token}
                    self._progress_callbacks[progress_token] = (
                        progress_callback,
                        None,
                    )
                try:
                    response = await asyncio.wait_for(
                        self._send_request("tools/call", payload),
                        timeout=self.operation_timeout,
                    )
                    return response
                finally:
                    if progress_token is not None:
                        self._progress_callbacks.pop(progress_token, None)
            except asyncio.TimeoutError as e:
                span.record_exception(e)
                raise TimeoutError(
                    f"Call to tool '{tool_name}' timed out after "
                    f"{self.operation_timeout:g} seconds."
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
        progress_token = ((params or {}).get("_meta") or {}).get("progressToken")
        if progress_token in self._progress_callbacks:
            self._request_progress_tokens[req_id] = progress_token

        payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            payload["params"] = params

        serialized = json.dumps(payload) + "\n"
        request_bytes = len(serialized.encode("utf-8"))
        tool_name = str((params or {}).get("name") or "") or None
        started = time.perf_counter()
        logger.info(
            "mcp_request_started",
            request_id=req_id,
            method=method,
            tool_name=tool_name,
            request_bytes=request_bytes,
            child_pid=self.process.pid if self.process else None,
        )
        try:
            self.process.stdin.write(serialized.encode("utf-8"))
            await self.process.stdin.drain()
        except Exception as e:
            self._pending_requests.pop(req_id, None)
            token = self._request_progress_tokens.pop(req_id, None)
            if token is not None:
                self._progress_callbacks.pop(token, None)
            raise RuntimeError(f"Failed to write request to stdin: {e}") from e
        try:
            result = await fut
        except BaseException as exc:
            self._pending_requests.pop(req_id, None)
            token = self._request_progress_tokens.pop(req_id, None)
            if token is not None:
                self._progress_callbacks.pop(token, None)
            logger.warning(
                "mcp_request_failed",
                request_id=req_id,
                method=method,
                tool_name=tool_name,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
                error_type=type(exc).__name__,
                child_pid=self.process.pid if self.process else None,
            )
            raise

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response_bytes = len(
            json.dumps(result, sort_keys=True, default=str).encode("utf-8")
        )
        event = (
            "mcp_request_slow"
            if duration_ms >= _slow_call_threshold_ms()
            else "mcp_request_completed"
        )
        log = logger.warning if event == "mcp_request_slow" else logger.info
        log(
            event,
            request_id=req_id,
            method=method,
            tool_name=tool_name,
            duration_ms=duration_ms,
            request_bytes=request_bytes,
            response_bytes=response_bytes,
            child_pid=self.process.pid if self.process else None,
        )
        return result

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
                    progress_token = self._request_progress_tokens.pop(msg_id, None)
                    if progress_token is not None:
                        self._progress_callbacks.pop(progress_token, None)
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
                    method = message.get("method")
                    if method == "notifications/progress":
                        await self._handle_progress_notification(message.get("params"))
                    # Handle notifications or requests initiated by the server if any (e.g. logMessage)
                    elif method == "notifications/message":
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

    async def _handle_progress_notification(self, params: Any) -> None:
        if not isinstance(params, dict):
            logger.warning("mcp_progress_ignored", reason="invalid_params")
            return
        token = params.get("progressToken")
        try:
            registered = self._progress_callbacks.get(token)
        except TypeError:
            registered = None
        if registered is None:
            logger.warning("mcp_progress_ignored", reason="unknown_token")
            return
        callback, previous = registered
        progress = _finite_number(params.get("progress"))
        total = _finite_number(params.get("total"), optional=True)
        if progress is None:
            logger.warning("mcp_progress_ignored", reason="invalid_progress")
            return
        if total is not None and total <= 0:
            logger.warning("mcp_progress_ignored", reason="invalid_total")
            return
        if previous is not None and progress < previous:
            logger.warning("mcp_progress_ignored", reason="decreasing_progress")
            return
        self._progress_callbacks[token] = (callback, progress)
        message = params.get("message")
        bounded_message = None if message is None else str(message)[:512]
        update: dict[str, Any] = {"progress": progress}
        if total is not None:
            update["total"] = total
        if bounded_message is not None:
            update["message"] = bounded_message
        try:
            result = callback(update)
            if inspect.isawaitable(result):
                await result
        except Exception:
            logger.warning("mcp_progress_callback_failed")

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


def _finite_number(value: Any, *, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None
