"""Contained host for the inventoried Rivet 2 Node workflow runner."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import secrets
import shutil
import threading
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import structlog
from agent_adapters.hermes_config import HermesApiSettings, resolve_hermes_api_settings
from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError,
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
)
from core.workflow_runs import RunnerAvailability
from core.workflows import WorkflowDocument

from .surfaces.process_supervisor import ProcessSupervisor, ProcessSupervisorError
from .workflow_runner import RivetMcpRuntimeGrant, RunnerAssetCatalog, RunnerSettings


ProgressCallback = Callable[[dict[str, Any]], Awaitable[None] | None]
logger = structlog.get_logger(__name__)


class RivetRuntimeError(RuntimeError):
    """Stable error raised by the trusted Python runner boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class RivetRuntimeResult:
    run_id: str
    state: str
    outputs: dict[str, Any] | None
    error: dict[str, str] | None
    events: tuple[dict[str, Any], ...]
    runtime_id: str
    duration_ms: int


class _AiBridgeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        *,
        bridge: HermesOpenAICompatibilityBridge,
        token: str,
        maximum_request_bytes: int,
    ) -> None:
        self.bridge = bridge
        self.token = token
        self.maximum_request_bytes = maximum_request_bytes
        super().__init__(address, _AiBridgeHandler)


class _AiBridgeHandler(BaseHTTPRequestHandler):
    server_version = "WrightRivetRunnerAI/1"

    @property
    def _server(self) -> _AiBridgeServer:
        return self.server  # type: ignore[return-value]

    def _json(self, status: int, value: Mapping[str, Any]) -> None:
        body = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        prefix = "Bearer "
        return supplied.startswith(prefix) and secrets.compare_digest(
            supplied[len(prefix) :], self._server.token
        )

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        if self.path != "/v1/chat/completions":
            self._json(HTTPStatus.NOT_FOUND, {"error": {"code": "invalid_request"}})
            return
        if self.client_address[0] not in {"127.0.0.1", "::1"} or not self._authorized():
            self._json(HTTPStatus.UNAUTHORIZED, {"error": {"code": "invalid_token"}})
            return
        if (
            self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            != "application/json"
        ):
            self._json(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                {"error": {"code": "invalid_request"}},
            )
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            length = -1
        if length < 1 or length > self._server.maximum_request_bytes:
            self._json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {"error": {"code": "invalid_request"}},
            )
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeError, json.JSONDecodeError):
            self._json(HTTPStatus.BAD_REQUEST, {"error": {"code": "invalid_request"}})
            return
        if not isinstance(payload, dict):
            self._json(HTTPStatus.BAD_REQUEST, {"error": {"code": "invalid_request"}})
            return
        request_id = secrets.token_hex(16)
        if payload.get("stream") is True:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()

            async def relay() -> None:
                async for chunk in self._server.bridge.stream(
                    payload, request_id=request_id
                ):
                    self.wfile.write(chunk.encode("utf-8"))
                    self.wfile.flush()

            try:
                asyncio.run(relay())
            except (BrokenPipeError, ConnectionResetError):
                return
            except HermesBridgeError as error:
                self.wfile.write(
                    f"data: {json.dumps(error.envelope(), separators=(',', ':'))}\n\ndata: [DONE]\n\n".encode(
                        "utf-8"
                    )
                )
            finally:
                self.close_connection = True
            return
        try:
            result = asyncio.run(
                self._server.bridge.complete(payload, request_id=request_id)
            )
        except HermesBridgeError as error:
            self._json(error.status_code, error.envelope())
            return
        self._json(HTTPStatus.OK, result)

    def log_message(self, format: str, *args: object) -> None:
        return


@dataclass(slots=True)
class _RunningAiBridge:
    server: _AiBridgeServer
    thread: threading.Thread
    token: str

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}/v1"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class RivetRuntimeHost:
    """Verify, launch, observe, and clean up one real Rivet workflow run."""

    def __init__(
        self,
        *,
        supervisor: ProcessSupervisor,
        settings: RunnerSettings | None = None,
        artifact_catalog: RunnerAssetCatalog | None = None,
        node_path: str | None = None,
        hermes_settings_resolver: Callable[
            [], HermesApiSettings
        ] = resolve_hermes_api_settings,
    ) -> None:
        self._supervisor = supervisor
        self._settings = settings or RunnerSettings.from_env()
        self._artifacts = artifact_catalog or RunnerAssetCatalog()
        self._node_path = node_path
        self._hermes_settings_resolver = hermes_settings_resolver
        self._semaphore = asyncio.Semaphore(self._settings.maximum_concurrent_runs)

    def _node(self) -> str:
        candidate = self._node_path or shutil.which("node")
        if not candidate:
            raise RivetRuntimeError(
                "RIVET_RUNNER_UNAVAILABLE", "Node.js is unavailable."
            )
        path = Path(candidate).resolve()
        if not path.is_file():
            raise RivetRuntimeError(
                "RIVET_RUNNER_UNAVAILABLE", "Node.js is unavailable."
            )
        return str(path)

    @staticmethod
    def _project_path(workspace_dir: str, document: WorkflowDocument) -> Path:
        lexical_root = Path(workspace_dir)
        if not lexical_root.is_absolute() or lexical_root.is_symlink():
            raise RivetRuntimeError(
                "RIVET_WORKSPACE_INVALID", "The workflow workspace is not canonical."
            )
        root = lexical_root.resolve(strict=True)
        if not root.is_dir():
            raise RivetRuntimeError(
                "RIVET_WORKSPACE_INVALID", "The workflow workspace is invalid."
            )
        candidate = root / "workflows" / document.slug / "workflow.rivet-project"
        cursor = candidate
        while cursor != root:
            if cursor.is_symlink():
                raise RivetRuntimeError(
                    "RIVET_WORKSPACE_INVALID", "Workflow paths may not contain links."
                )
            cursor = cursor.parent
        project = candidate.resolve(strict=True)
        if root not in project.parents or not project.is_file():
            raise RivetRuntimeError(
                "RIVET_WORKSPACE_INVALID",
                "The workflow project is outside its workspace.",
            )
        return project

    def _start_ai_bridge(self) -> _RunningAiBridge:
        hermes = self._hermes_settings_resolver()
        bridge = HermesOpenAICompatibilityBridge(
            HermesOpenAIBridgeSettings(
                base_url=hermes.base_url,
                api_key=hermes.api_key,
                timeout_seconds=self._settings.run_timeout_seconds,
                maximum_output_bytes=self._settings.captured_output_bytes,
            )
        )
        if not bridge.available:
            raise RivetRuntimeError(
                "RIVET_AI_UNAVAILABLE", "Hermes subscription-backed AI is unavailable."
            )
        token = secrets.token_urlsafe(32)
        server = _AiBridgeServer(
            ("127.0.0.1", 0),
            bridge=bridge,
            token=token,
            maximum_request_bytes=1024 * 1024,
        )
        thread = threading.Thread(
            target=server.serve_forever,
            name="wright-rivet-run-ai",
            daemon=True,
        )
        thread.start()
        return _RunningAiBridge(server, thread, token)

    @staticmethod
    def _environment() -> dict[str, str]:
        allowed = ("SystemRoot", "ComSpec", "PATHEXT", "TEMP", "TMP", "LANG")
        return {name: os.environ[name] for name in allowed if os.environ.get(name)}

    async def _wait_for_exit(self, runtime_id: str) -> int | None:
        while True:
            snapshot = self._supervisor.snapshot(runtime_id)
            if snapshot.status in {"exited", "stopped", "failed-stop"}:
                return snapshot.exit_code
            await asyncio.sleep(0.02)

    async def _stop(self, runtime_id: str, generation: int) -> None:
        snapshot = self._supervisor.snapshot(runtime_id)
        if snapshot.status in {"exited", "stopped", "failed-stop"}:
            return
        await self._supervisor.stop(
            runtime_id=runtime_id,
            generation=generation,
            deadline=datetime.now(UTC)
            + timedelta(seconds=self._settings.cancellation_seconds),
        )

    async def run(
        self,
        *,
        run_id: str,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        document: WorkflowDocument,
        graph: str | None,
        inputs: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        requirements: tuple[str, ...] = (),
        mcp_grant: RivetMcpRuntimeGrant | None = None,
        timeout_seconds: float | None = None,
        progress_callback: ProgressCallback | None = None,
        generation: int = 1,
    ) -> RivetRuntimeResult:
        del session_id  # identity is persisted by the caller; never sent to Node.
        availability, manifest, detail = self._artifacts.status()
        if availability is not RunnerAvailability.AVAILABLE or manifest is None:
            raise RivetRuntimeError(
                "RIVET_RUNNER_UNAVAILABLE", detail or "The Rivet runner is unavailable."
            )
        project_path = self._project_path(workspace_dir, document)
        if timeout_seconds is None:
            timeout_seconds = self._settings.run_timeout_seconds
        timeout_seconds = min(
            float(timeout_seconds), self._settings.run_timeout_seconds
        )
        if timeout_seconds < 1:
            raise RivetRuntimeError(
                "RIVET_RUNNER_REQUEST_INVALID", "Run timeout is invalid."
            )

        ai_bridge: _RunningAiBridge | None = None
        runtime_id: str | None = None
        started = time.monotonic()
        events: list[dict[str, Any]] = []
        buffer = bytearray()
        loop = asyncio.get_running_loop()
        terminal: asyncio.Future[dict[str, Any]] = loop.create_future()

        async def consume(payload: bytes) -> None:
            nonlocal buffer
            if len(buffer) + len(payload) > self._settings.captured_output_bytes:
                error = RivetRuntimeError(
                    "RIVET_RUNNER_OUTPUT_TOO_LARGE",
                    "Runner output exceeded the configured limit.",
                )
                if not terminal.done():
                    terminal.set_exception(error)
                raise error
            buffer.extend(payload)
            while b"\n" in buffer:
                raw, _, remainder = buffer.partition(b"\n")
                buffer = bytearray(remainder)
                if not raw.strip():
                    continue
                if len(raw) > self._settings.maximum_event_bytes:
                    error = RivetRuntimeError(
                        "RIVET_RUNNER_EVENT_TOO_LARGE",
                        "Runner event exceeded the configured limit.",
                    )
                    if not terminal.done():
                        terminal.set_exception(error)
                    raise error
                try:
                    event = json.loads(raw)
                except (UnicodeError, json.JSONDecodeError) as caught:
                    error = RivetRuntimeError(
                        "RIVET_RUNNER_PROTOCOL_INVALID", "Runner emitted invalid JSONL."
                    )
                    if not terminal.done():
                        terminal.set_exception(error)
                    raise error from caught
                if not isinstance(event, dict) or event.get("runId") != run_id:
                    error = RivetRuntimeError(
                        "RIVET_RUNNER_PROTOCOL_INVALID",
                        "Runner emitted an invalid run identity.",
                    )
                    if not terminal.done():
                        terminal.set_exception(error)
                    raise error
                kind = event.get("type")
                if kind == "progress" and not terminal.done():
                    projected = {**event, "sequence": len(events) + 1}
                    events.append(projected)
                    if progress_callback is not None:
                        result = progress_callback(projected)
                        if inspect.isawaitable(result):
                            await result
                elif kind == "result" and not terminal.done():
                    if event.get("state") not in {"succeeded", "failed", "cancelled"}:
                        terminal.set_exception(
                            RivetRuntimeError(
                                "RIVET_RUNNER_PROTOCOL_INVALID",
                                "Runner terminal state is invalid.",
                            )
                        )
                    else:
                        terminal.set_result(event)
                else:
                    error = RivetRuntimeError(
                        "RIVET_RUNNER_PROTOCOL_INVALID",
                        "Runner emitted an unexpected event.",
                    )
                    if not terminal.done():
                        terminal.set_exception(error)
                    raise error

        async with self._semaphore:
            try:
                request: dict[str, Any] = {
                    "protocolVersion": manifest.protocol_version,
                    "runId": run_id,
                    "projectPath": str(project_path),
                    "expectedDigest": document.digest,
                    "inputs": dict(inputs or {}),
                    "context": dict(context or {}),
                    "capabilities": [],
                }
                if graph:
                    request["graph"] = graph
                if "ai" in requirements:
                    ai_bridge = self._start_ai_bridge()
                    request["ai"] = {
                        "baseUrl": ai_bridge.base_url,
                        "token": ai_bridge.token,
                        "model": "wright-hermes",
                    }
                if "mcp" in requirements:
                    if mcp_grant is None:
                        raise RivetRuntimeError(
                            "RIVET_MCP_GRANT_REQUIRED",
                            "A current reviewed MCP run grant is required.",
                        )
                    request["capabilities"].append("mcp")
                    request["mcp"] = {
                        "authorityId": mcp_grant.authority_id,
                        "bridgeBaseUrl": mcp_grant.bridge_base_url,
                        "token": mcp_grant.token,
                        "expiresAt": mcp_grant.expires_at.isoformat().replace(
                            "+00:00", "Z"
                        ),
                        "bindingSetDigest": mcp_grant.binding_set_digest,
                        "discoveryHandle": mcp_grant.discovery_handle,
                        "bindings": list(mcp_grant.bindings),
                    }
                encoded = json.dumps(
                    request, separators=(",", ":"), default=str
                ).encode("utf-8")
                snapshot = await self._supervisor.start(
                    workspace_id=workspace_id,
                    instance_id=f"rivet-run-{run_id}",
                    generation=generation,
                    argv=(self._node(), str(manifest.entrypoint)),
                    cwd=str(Path(workspace_dir).resolve()),
                    environment=self._environment(),
                    secret_environment_names=frozenset(),
                    secret_values=tuple(
                        value
                        for value in (
                            ai_bridge.token if ai_bridge else None,
                            mcp_grant.token if mcp_grant else None,
                        )
                        if value
                    ),
                    redaction_query_names=frozenset({"token", "api_key", "key"}),
                    limits={
                        "captured_log_bytes": self._settings.captured_log_bytes,
                        "captured_log_bytes_per_second": self._settings.captured_log_bytes,
                        "captured_log_burst_bytes": self._settings.captured_log_bytes,
                        "graceful_shutdown_seconds": self._settings.cancellation_seconds,
                        "processes_per_owned_tree": 4,
                        "memory_mib_per_owned_app": 1024,
                        "cpu_cores": 1.0,
                    },
                    idempotency_key=run_id,
                    stdin_payload=encoded,
                    stdout_callback=consume,
                )
                runtime_id = snapshot.runtime_id
                result_event = await asyncio.wait_for(
                    asyncio.shield(terminal), timeout=timeout_seconds
                )
                elapsed = time.monotonic() - started
                exit_code = await asyncio.wait_for(
                    self._wait_for_exit(runtime_id),
                    timeout=max(0.1, timeout_seconds - elapsed),
                )
                state = str(result_event["state"])
                if state == "succeeded" and exit_code != 0:
                    raise RivetRuntimeError(
                        "RIVET_RUNNER_PROCESS_EXIT",
                        "Runner exited unsuccessfully after its result.",
                    )
                outputs = result_event.get("outputs")
                if outputs is not None and not isinstance(outputs, dict):
                    raise RivetRuntimeError(
                        "RIVET_RUNNER_PROTOCOL_INVALID",
                        "Runner outputs have an invalid shape.",
                    )
                raw_error = result_event.get("error")
                error = (
                    {
                        "code": str(raw_error.get("code") or "RIVET_RUNNER_FAILED"),
                        "message": str(
                            raw_error.get("message") or "Rivet execution failed."
                        ),
                    }
                    if isinstance(raw_error, dict)
                    else None
                )
                result = RivetRuntimeResult(
                    run_id=run_id,
                    state=state,
                    outputs=outputs,
                    error=error,
                    events=tuple(events),
                    runtime_id=runtime_id,
                    duration_ms=int((time.monotonic() - started) * 1000),
                )
                logger.info(
                    "rivet_runtime_completed",
                    run_id=run_id,
                    workflow_id=document.workflow_id,
                    revision=document.revision,
                    graph=graph,
                    state=state,
                    event_count=len(events),
                    duration_ms=result.duration_ms,
                )
                return result
            except asyncio.TimeoutError as error:
                raise RivetRuntimeError(
                    "RIVET_RUNNER_TIMEOUT", "Rivet workflow execution timed out."
                ) from error
            except ProcessSupervisorError as error:
                raise RivetRuntimeError(
                    error.code, "Rivet runner process launch failed."
                ) from error
            finally:
                if runtime_id is not None:
                    await self._stop(runtime_id, generation)
                if ai_bridge is not None:
                    ai_bridge.close()


__all__ = [
    "ProgressCallback",
    "RivetRuntimeError",
    "RivetRuntimeHost",
    "RivetRuntimeResult",
]
