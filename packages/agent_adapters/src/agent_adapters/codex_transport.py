"""Bounded async bridge to the optional, isolated official Codex SDK worker."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import sys
from typing import AsyncIterator

from core.redaction import redact_mapping

from .codex_policy import RPC_METHODS
from .codex_policy import confined_rpc_params
from .codex_policy import permitted_gateway_request

MAX_BYTES = 2_097_152


class CodexTransportError(RuntimeError):
    def __init__(self, code: str, *, outcome_uncertain: bool = False):
        self.code = code
        self.outcome_uncertain = outcome_uncertain
        super().__init__(code)


@dataclass(frozen=True)
class CodexRuntimeSettings:
    state_root: Path
    python: Path = Path(sys.executable)
    timeout_seconds: float = 30
    gateway_enabled: bool = False

    def __post_init__(self):
        if not self.state_root.is_absolute() or not self.python.is_absolute():
            raise ValueError("Codex state and interpreter paths must be absolute")
        if not 1 <= self.timeout_seconds <= 150:
            raise ValueError("Codex RPC timeout must be within 1–150 seconds")
        if type(self.gateway_enabled) is not bool:
            raise ValueError("Codex gateway switch must be a boolean")


def isolated_environment(state_root: Path) -> dict[str, str]:
    """Do not inherit provider credentials, profiles, hooks or connector env."""
    environment = {"PATH": os.defpath, "CODEX_HOME": str(state_root / "home")}
    if os.name == "nt":
        # Native process creation requires the operating-system installation,
        # not the user's profile or credential-bearing environment.
        for name in ("SystemRoot", "SYSTEMROOT", "WINDIR"):
            if name in os.environ:
                environment[name] = os.environ[name]
    return environment


class CodexSdkTransport:
    def __init__(
        self, settings: CodexRuntimeSettings, *, observer=None, tool_handler=None
    ):
        self.settings = settings
        self.observer = observer
        self.tool_handler = tool_handler
        self._tool_tasks = set()
        self._child = None
        self._reader = None
        self._pending: dict[int, asyncio.Future] = {}
        self._started: set[int] = set()
        self._handed_off: set[int] = set()
        self._events: dict[str, asyncio.Queue] = {}
        self._counter = 0
        self._write_lock = asyncio.Lock()
        self._slots = asyncio.Semaphore(8)
        self._failure = None
        self._closing = False

    async def start(self):
        if self._child is not None:
            raise CodexTransportError("CODEX_TRANSPORT_ALREADY_STARTED")
        if self._closing or self._failure:
            raise CodexTransportError("CODEX_TRANSPORT_CLOSED")
        # Reject links before creating anything: a private home must never resolve
        # into the user's existing Codex configuration, even through a parent.
        root = self.settings.state_root
        home, cwd = self.settings.state_root / "home", self.settings.state_root / "cwd"
        for path in (home, cwd, root, *root.parents):
            if path.is_symlink():
                raise CodexTransportError("CODEX_STATE_ROOT_INVALID")
        for path in (home / "auth.json", home / "config.toml"):
            if path.is_symlink():
                raise CodexTransportError("CODEX_STATE_ROOT_INVALID")
        auth = home / "auth.json"
        if auth.exists() and os.name != "nt":
            auth_stat = auth.stat()
            if auth_stat.st_uid != os.getuid() or auth_stat.st_mode & 0o077:
                raise CodexTransportError("CODEX_STATE_ROOT_NOT_PRIVATE")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for path in (root, home, cwd):
            path.mkdir(exist_ok=True, mode=0o700)
            if os.name != "nt":
                stat = path.stat()
                if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
                    raise CodexTransportError("CODEX_STATE_ROOT_NOT_PRIVATE")
        environment = isolated_environment(self.settings.state_root)
        if self.settings.gateway_enabled:
            environment["WRIGHT_CODEX_GATEWAY_ENABLED"] = "1"
        self._child = await asyncio.create_subprocess_exec(
            str(self.settings.python),
            "-I",
            str(Path(__file__).with_name("codex_worker.py")),
            cwd=cwd,
            env=environment,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            limit=MAX_BYTES + 1,
            start_new_session=os.name != "nt",
        )
        self._reader = asyncio.create_task(self._read())
        try:
            return await self.request("initialize", {})
        except BaseException:
            await self.close()
            raise

    async def _observe(self, phase, method, value):
        if self.observer is not None:
            await self.observer(
                redact_mapping(
                    {
                        "schema_version": "wright.codex-client-evidence/1",
                        "capture_scope": "app_server_sdk_call",
                        "phase": phase,
                        "method": method,
                        "fields": value,
                    }
                )
            )

    async def request(self, method: str, params: dict) -> dict:
        if method not in RPC_METHODS:
            raise CodexTransportError("CODEX_METHOD_UNAVAILABLE")
        if not isinstance(params, dict):
            raise ValueError("Codex RPC params must be an object")
        # Validate before observing/handing off; the worker independently repeats
        # validation and adds the fixed confinement fields.
        confined_rpc_params(method, params)
        async with self._slots:
            if self._child is None or self._failure or self._closing:
                raise CodexTransportError(self._failure or "CODEX_TRANSPORT_CLOSED")
            self._counter += 1
            request_id = self._counter
            payload = {"id": request_id, "method": method, "params": params}
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n"
            if len(raw) > MAX_BYTES:
                raise CodexTransportError("CODEX_REQUEST_TOO_LARGE")
            await self._observe("prepared", method, params)
            future = asyncio.get_running_loop().create_future()
            self._pending[request_id] = future
            try:
                async with self._write_lock:
                    self._handed_off.add(request_id)
                    self._child.stdin.write(raw)
                    await self._child.stdin.drain()
                async with asyncio.timeout(self.settings.timeout_seconds):
                    reply = await asyncio.shield(future)
                if "error" in reply:
                    raise CodexTransportError(
                        reply["error"]["code"],
                        outcome_uncertain=request_id in self._started,
                    )
                await self._observe("acknowledged", method, reply["result"])
                return reply["result"]
            except TimeoutError as exc:
                # Never retry a turn start whose receipt has been lost.
                raise CodexTransportError(
                    "CODEX_RPC_TIMEOUT", outcome_uncertain=True
                ) from exc
            except (BrokenPipeError, ConnectionResetError) as exc:
                raise CodexTransportError(
                    "CODEX_TRANSPORT_LOST", outcome_uncertain=True
                ) from exc
            finally:
                self._pending.pop(request_id, None)
                self._started.discard(request_id)
                self._handed_off.discard(request_id)
                if not future.done():
                    future.cancel()
                elif not future.cancelled():
                    # An observer/cancellation failure can race a pipe failure.
                    # Consume the recorded exception; it remains uncertain and
                    # is never retried or turned into a successful acknowledgement.
                    future.exception()

    def _fail(self, code):
        self._failure = code
        for request_id, future in self._pending.items():
            if not future.done():
                future.set_exception(
                    CodexTransportError(
                        code, outcome_uncertain=request_id in self._handed_off
                    )
                )
        for queue in self._events.values():
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(CodexTransportError(code, outcome_uncertain=True))

    async def _read(self):
        try:
            while raw := await self._child.stdout.readline():
                if len(raw) > MAX_BYTES or not raw.endswith(b"\n"):
                    raise CodexTransportError("CODEX_EVENT_TOO_LARGE")
                event = json.loads(raw)
                if event.get("kind") == "call_started":
                    if event["id"] in self._pending:
                        self._started.add(event["id"])
                        await self._observe("sdk_call_started", event["method"], {})
                elif event.get("kind") == "transport_error":
                    raise CodexTransportError(event["code"])
                elif event.get("kind") == "notification":
                    params = event["params"]
                    turn_id = params.get("turnId") or params.get("turn", {}).get("id")
                    if not isinstance(turn_id, str) or not 0 < len(turn_id) <= 160:
                        raise CodexTransportError("CODEX_EVENT_ID_INVALID")
                    if turn_id not in self._events and len(self._events) >= 8:
                        raise CodexTransportError("CODEX_EVENT_BUFFER_FULL")
                    queue = self._events.setdefault(turn_id, asyncio.Queue(maxsize=128))
                    if queue.full():
                        raise CodexTransportError("CODEX_EVENT_BUFFER_FULL")
                    queue.put_nowait(event)
                elif event.get("kind") == "permission_denied":
                    await self._observe("permission_denied", event["method"], {})
                elif event.get("kind") == "runtime_notice":
                    method = event["method"]
                    await self._observe("runtime_notice", method, event["params"])
                    if method in {"model/rerouted", "account/updated"} and self._events:
                        raise CodexTransportError("CODEX_RUNTIME_IDENTITY_CHANGED")
                elif event.get("kind") == "gateway_request":
                    if len(self._tool_tasks) >= 4:
                        raise CodexTransportError("CODEX_GATEWAY_REQUEST_LIMIT")
                    task = asyncio.create_task(self._gateway_request(event))
                    self._tool_tasks.add(task)
                    task.add_done_callback(self._tool_tasks.discard)
                elif event.get("id") in self._pending:
                    future = self._pending[event["id"]]
                    if not future.done():
                        future.set_result(event)
                else:
                    # A late reply to a timed-out call is not a new receipt or
                    # evidence of success. The owning attempt requires recovery.
                    await self._observe("unclaimed_reply", "unknown", {})
            self._fail("CODEX_TRANSPORT_LOST")
        except asyncio.CancelledError:
            raise
        except CodexTransportError as exc:
            self._fail(exc.code)
        except Exception:
            self._fail("CODEX_PROTOCOL_INVALID")

    async def _gateway_request(self, event):
        result = {
            "success": False,
            "contentItems": [
                {
                    "type": "inputText",
                    "text": "Wright gateway operation unavailable or denied.",
                }
            ],
        }
        try:
            params = event["params"]
            if (
                self.settings.gateway_enabled
                and self.tool_handler
                and permitted_gateway_request(params)
            ):
                await self._observe("gateway_request", "item/tool/call", params)
                async with asyncio.timeout(15):
                    result = await self.tool_handler(params)
                await self._observe("gateway_result", "item/tool/call", result)
            raw = (
                json.dumps(
                    {"kind": "gateway_reply", "id": event["id"], "result": result}
                ).encode()
                + b"\n"
            )
            if len(raw) > MAX_BYTES:
                raise ValueError("Gateway result exceeds the transport bound")
            async with self._write_lock:
                self._child.stdin.write(raw)
                await self._child.stdin.drain()
        except asyncio.CancelledError:
            raise
        except Exception:
            self._fail("CODEX_GATEWAY_FAILED")

    async def events(self, turn_id: str) -> AsyncIterator[dict]:
        if self._failure:
            raise CodexTransportError(self._failure, outcome_uncertain=True)
        if turn_id not in self._events and len(self._events) >= 8:
            raise CodexTransportError("CODEX_EVENT_BUFFER_FULL")
        queue = self._events.setdefault(turn_id, asyncio.Queue(maxsize=128))
        try:
            while True:
                try:
                    async with asyncio.timeout(150):
                        event = await queue.get()
                except TimeoutError as exc:
                    raise CodexTransportError(
                        "CODEX_EVENT_TIMEOUT", outcome_uncertain=True
                    ) from exc
                if isinstance(event, Exception):
                    raise event
                yield event
                if event["method"] == "turn/completed":
                    break
        finally:
            self._events.pop(turn_id, None)

    async def close(self):
        self._closing = True
        self._fail("CODEX_TRANSPORT_CLOSED")
        for task in tuple(self._tool_tasks):
            task.cancel()
        await asyncio.gather(*self._tool_tasks, return_exceptions=True)
        child = self._child
        if child is not None:
            if os.name != "nt":
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            elif child.returncode is None:
                child.terminate()
            try:
                async with asyncio.timeout(3):
                    await child.wait()
            except TimeoutError:
                if os.name != "nt":
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    child.kill()
                await child.wait()
        if self._reader is not None:
            self._reader.cancel()
            await asyncio.gather(self._reader, return_exceptions=True)
        self._child = None
