"""One native coordinator per data root and a bounded sequential operation runner."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from decimal import DecimalException
from pathlib import Path
from typing import Any, Protocol

from core.native_runtime_json import runtime_json_loads
from core.logging import get_logger
from core.native_process import (
    Finding,
    NativeProcessError,
    validate_definition,
    readiness,
)
from core.native_quantities import Quantity
from core.tracing import traced
from data_vault.lifecycle_lock import lifecycle_lock
from data_vault.models import DatabaseBusyError
from data_vault.native_process_artifacts import NativeArtifactStore
from data_vault.native_process_repository import NativeRepositoryError
from data_vault.native_process_runs import NativeRunRepository, TERMINAL_STATES

from .native_process_service import NativeServiceError
from .workspace_path import WorkspacePath

logger = get_logger(__name__)


class NativeMcp(Protocol):
    async def call(
        self,
        session_id: str,
        binding: dict[str, Any],
        arguments: dict[str, Any],
        timeout_seconds: float,
        trace_id: str,
    ) -> str: ...


class OperationFailure(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        recovery: str = "Correct the indicated step and create a linked run.",
    ):
        super().__init__(message)
        self.code = code
        self.recovery = recovery


def _text(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 4000:
        raise OperationFailure(
            "TEXT_LIMIT", "Native text values must contain at most 4,000 characters."
        )
    return value


def _join(config, inputs):
    return {
        "text": _text(inputs["first"] + config.get("separator", "") + inputs["second"])
    }


def _require(config, inputs):
    text = _text(inputs["text"])
    missing = [term for term in config["terms"] if term not in text]
    if missing:
        raise OperationFailure(
            "ASSERTION_FAILED", "Text is missing required terms: " + ", ".join(missing)
        )
    return {"text": text}


def _range(config, inputs):
    value = Quantity(**inputs["value"])
    if (
        value.compare(Quantity(**config["minimum"])) < 0
        or value.compare(Quantity(**config["maximum"])) > 0
    ):
        raise OperationFailure(
            "ASSERTION_FAILED",
            f"Measured quantity {value.value} {value.unit} is outside the configured inclusive range.",
        )
    return {"value": value.as_dict()}


def _format(config, inputs):
    value = Quantity(**inputs["value"])
    label = config.get("label", "")
    return {
        "text": _text((label + ": " if label else "") + value.value + " " + value.unit)
    }


# Versioned data operations are selected by operation identity, never by a
# workflow/example title, engineering domain, vendor name, or canvas node type.
_PURE = {
    "text.input@1": lambda config, inputs: {"value": _text(config["value"])},
    "quantity.input@1": lambda config, inputs: {
        "value": Quantity(**config["value"]).as_dict()
    },
    "text.join@1": _join,
    "text.require@1": _require,
    "quantity.multiply@1": lambda config, inputs: {
        "value": Quantity(**inputs["left"])
        .multiply(Quantity(**inputs["right"]), config["unit"])
        .as_dict()
    },
    "quantity.convert@1": lambda config, inputs: {
        "value": Quantity(**inputs["value"]).convert(config["unit"]).as_dict()
    },
    "quantity.range@1": _range,
    "quantity.format@1": _format,
}


class NativeRuntime:
    def __init__(
        self,
        repository: NativeRunRepository,
        scope_resolver: Callable[[str], tuple[str, WorkspacePath]],
        *,
        mcp: NativeMcp | None = None,
    ):
        self.repository = repository
        self.scope_resolver = scope_resolver
        self.mcp = mcp
        self._owner = None
        self._owner_guard = threading.Lock()
        self._tasks: dict[tuple[str, str], asyncio.Task] = {}
        self._closed = False

    def ensure_owner(self):
        with self._owner_guard:
            if self._closed:
                raise NativeServiceError(
                    "NATIVE_RUNTIME_BUSY",
                    "Native runtime is stopping.",
                    "Reconnect after the local service restarts.",
                )
            if self._owner is not None:
                return
            lock = lifecycle_lock(
                Path(self.repository.db_path).resolve().parent
                / ".native-runtime-owner",
                timeout=0,
            )
            try:
                lock.__enter__()
            except DatabaseBusyError as error:
                raise NativeServiceError(
                    "NATIVE_RUNTIME_BUSY",
                    "Another native runtime owns this data root.",
                    "Use the existing local service.",
                ) from error
            try:
                interrupted = self.repository.interrupt_abandoned()
            except BaseException:
                lock.__exit__(None, None, None)
                raise
            self._owner = lock
            if interrupted:
                logger.info("native_runs_interrupted", count=interrupted)

    def enqueue(self, workspace_id: str, session_id: str, run_id: str):
        self.ensure_owner()
        key = (workspace_id, run_id)
        if (
            key in self._tasks
            or self.repository.summary(workspace_id, run_id)["state"] != "queued"
        ):
            return
        task = asyncio.create_task(
            self._drive(workspace_id, session_id, run_id), name=f"native-run-{run_id}"
        )
        self._tasks[key] = task
        task.add_done_callback(lambda completed: self._tasks.pop(key, None))

    def _scope(self, workspace_id: str, session_id: str) -> WorkspacePath:
        current, paths = self.scope_resolver(session_id)
        if current != workspace_id:
            raise NativeServiceError(
                "NATIVE_DENIED",
                "Workspace binding changed during this run.",
                "Select the original workspace and create a linked run.",
            )
        return paths

    @traced("native.run.execute")
    async def _drive(self, workspace_id: str, session_id: str, run_id: str):
        snapshot = self.repository.inspect(workspace_id, run_id)
        trace_id = snapshot["trace_id"]
        active_step: list[str | None] = [None]
        try:
            if not self.repository.start(workspace_id, run_id):
                return
            document = validate_definition(snapshot["snapshot"]["definition"])
            bound = (
                frozenset(snapshot["bindings"]) if self.mcp is not None else frozenset()
            )
            findings = readiness(document, bound_step_ids=bound)
            if findings:
                raise NativeServiceError(
                    "NATIVE_NOT_READY",
                    "Saved process is not ready for execution.",
                    "Resolve the readiness findings.",
                    findings=findings,
                )
            deadline = asyncio.get_running_loop().time() + snapshot["timeout_seconds"]
            await asyncio.wait_for(
                self._execute(
                    workspace_id, session_id, run_id, snapshot, active_step, deadline
                ),
                timeout=snapshot["timeout_seconds"],
            )
            self.repository.finish(workspace_id, run_id, "succeeded")
        except asyncio.TimeoutError:
            self.repository.finish(
                workspace_id,
                run_id,
                "timed_out",
                reason=Finding(
                    "DEADLINE_EXCEEDED",
                    "The run exceeded its total deadline.",
                    "Inspect the last step and retry with a suitable bounded deadline.",
                    active_step[0],
                ).as_dict(),
            )
        except asyncio.CancelledError:
            self.repository.finish(
                workspace_id,
                run_id,
                "cancelled",
                reason=Finding(
                    "CANCELLED",
                    "The run was cancelled.",
                    "Inspect retained evidence or create a linked run.",
                    active_step[0],
                ).as_dict(),
            )
        except (
            OperationFailure,
            NativeServiceError,
            NativeRepositoryError,
            NativeProcessError,
            DecimalException,
            ValueError,
            OSError,
        ) as error:
            findings = getattr(error, "findings", ())
            finding = (
                findings[0]
                if findings
                else Finding(
                    getattr(error, "code", "OPERATION_FAILED"),
                    str(error)
                    if isinstance(
                        error,
                        (OperationFailure, NativeServiceError, NativeRepositoryError),
                    )
                    else "The operation could not produce a valid bounded result.",
                    getattr(
                        error,
                        "recovery",
                        "Inspect the indicated step, correct its inputs and create a linked run.",
                    ),
                    active_step[0],
                )
            )
            self.repository.finish(
                workspace_id,
                run_id,
                "failed",
                reason=finding.as_dict(),
                failed_step_id=active_step[0],
            )
        except Exception as error:
            logger.error(
                "native_run_internal_failure",
                run_id=run_id,
                error_type=type(error).__name__,
                trace_id=trace_id,
            )
            self.repository.finish(
                workspace_id,
                run_id,
                "failed",
                reason=Finding(
                    "INTERNAL_ERROR",
                    "Run stopped after an internal operation error.",
                    "Inspect local support diagnostics using the trace identity.",
                    active_step[0],
                ).as_dict(),
                failed_step_id=active_step[0],
            )
        finally:
            logger.info(
                "native_run_finished",
                run_id=run_id,
                state=self.repository.summary(workspace_id, run_id)["state"],
                trace_id=trace_id,
            )

    async def _execute(
        self, workspace_id, session_id, run_id, snapshot, active_step, deadline
    ):
        definition = snapshot["snapshot"]["definition"]
        steps = {step["id"]: step for step in definition["steps"]}
        sources = {
            edge["target_port_id"]: edge["source_port_id"]
            for edge in definition["connections"]
        }
        values: dict[str, Any] = {}
        for recorded_step in snapshot["steps"]:
            identity = recorded_step["step_id"]
            active_step[0] = identity
            step = steps[identity]
            ports = [
                port for port in definition["ports"] if port["step_id"] == identity
            ]
            inputs = {
                port["id"]: values[sources[port["id"]]]
                for port in ports
                if port["direction"] == "input"
            }
            keyed_inputs = {
                port["key"]: inputs[port["id"]]
                for port in ports
                if port["direction"] == "input"
            }
            store = NativeArtifactStore(self._scope(workspace_id, session_id))
            if not self.repository.start_step(workspace_id, run_id, identity, inputs):
                return
            promoted: list[dict[str, Any]] = []
            abandoned = threading.Event()
            try:
                if step["operation"] == "mcp.call@1":
                    assert self.mcp is not None
                    arguments = runtime_json_loads(
                        _text(keyed_inputs["arguments"]).encode("utf-8"),
                        max_bytes=16 * 1024,
                    )
                    if not isinstance(arguments, dict):
                        raise OperationFailure(
                            "MCP_ARGUMENTS_INVALID",
                            "MCP arguments must be a strict JSON object.",
                        )
                    remaining = max(
                        0.001, min(15, deadline - asyncio.get_running_loop().time())
                    )
                    try:
                        result = await asyncio.wait_for(
                            self.mcp.call(
                                session_id,
                                snapshot["bindings"][identity],
                                arguments,
                                remaining,
                                snapshot["trace_id"],
                            ),
                            timeout=remaining,
                        )
                    except asyncio.TimeoutError as error:
                        raise OperationFailure(
                            "TOOL_DEADLINE_EXCEEDED",
                            "The tool call exceeded its bounded deadline.",
                        ) from error
                    output_values = {"result": _text(result)}
                else:
                    output_values = await asyncio.to_thread(
                        self._local_operation,
                        workspace_id,
                        run_id,
                        snapshot,
                        step,
                        ports,
                        keyed_inputs,
                        store,
                        promoted,
                        abandoned,
                    )
                outputs = {
                    port["id"]: output_values[port["key"]]
                    for port in ports
                    if port["direction"] == "output"
                }
                if not self.repository.complete_step(
                    workspace_id, run_id, identity, outputs, artifacts=tuple(promoted)
                ):
                    return
                values.update(outputs)
                promoted.clear()
            finally:
                # Publish abandonment before inspecting the list. A worker may
                # promote after this finally but before the terminal DB commit.
                # Append-before-check in the worker covers either ordering.
                abandoned.set()
                for record in promoted:
                    self._discard(workspace_id, run_id, store, record)
        active_step[0] = None

    def _local_operation(
        self,
        workspace_id,
        run_id,
        snapshot,
        step,
        ports,
        inputs,
        store,
        promoted,
        abandoned,
    ):
        operation, config = step["operation"], step["config"]
        if operation in _PURE:
            return _PURE[operation](config, inputs)
        if operation == "artifact.read-text@1":
            record = self.repository.artifact(
                workspace_id, run_id, inputs["artifact"]["artifact_id"]
            )
            content = store.read(record)
            try:
                return {"text": _text(content.decode("utf-8", errors="strict"))}
            except UnicodeError as error:
                raise OperationFailure(
                    "ARTIFACT_ENCODING", "Artifact is not valid UTF-8 text."
                ) from error
        if operation in {"artifact.input@1", "artifact.write-text@1"}:
            content = (
                store.input_bytes(config["path"])
                if operation == "artifact.input@1"
                else _text(inputs["text"]).encode("utf-8")
            )
            filename = (
                config["path"].replace("\\", "/").split("/")[-1]
                if operation == "artifact.input@1"
                else config["filename"]
            )
            output = next(port for port in ports if port["direction"] == "output")
            provenance = {
                "mode": "workspace_input_snapshot"
                if operation == "artifact.input@1"
                else "local_computation",
                "operation": operation,
                "step_id": step["id"],
                "run_id": run_id,
                "trace_id": snapshot["trace_id"],
                "semantic_digest": snapshot["semantic_digest"],
                "inputs": inputs,
                "config": config,
                "actor": snapshot["actor"],
            }
            record = store.promote(
                run_id,
                content,
                filename=filename,
                port_id=output["id"],
                provenance=provenance,
            )
            promoted.append(record)
            state = self.repository.summary(workspace_id, run_id)["state"]
            if abandoned.is_set() or state in TERMINAL_STATES:
                self._discard(workspace_id, run_id, store, record)
            return {
                output["key"]: {
                    key: record[key]
                    for key in ("artifact_id", "content_digest", "size", "filename")
                }
            }
        raise OperationFailure(
            "OPERATION_UNBOUND", "The operation version is not installed."
        )

    def _discard(self, workspace_id, run_id, store, record):
        if not store.discard_unindexed(run_id, record):
            self.repository.record_cleanup_residue(
                workspace_id, run_id, record["artifact_id"]
            )

    async def cancel(self, workspace_id: str, run_id: str) -> dict[str, Any]:
        self.ensure_owner()
        result = self.repository.finish(
            workspace_id,
            run_id,
            "cancelled",
            reason=Finding(
                "CANCELLED",
                "The run was cancelled by the operator.",
                "Inspect retained evidence or create a linked run.",
            ).as_dict(),
        )
        task = self._tasks.get((workspace_id, run_id))
        if task is not None:
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=5)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
        return result

    async def close(self):
        self._closed = True
        for (workspace_id, run_id), task in tuple(self._tasks.items()):
            self.repository.finish(
                workspace_id,
                run_id,
                "interrupted",
                reason=Finding(
                    "OWNER_STOPPING",
                    "The local runtime is stopping.",
                    "Reconnect and inspect the retained run.",
                ).as_dict(),
            )
            task.cancel()
        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(
                        *tuple(self._tasks.values()), return_exceptions=True
                    ),
                    timeout=5,
                )
            except asyncio.TimeoutError:
                pass
        if self._owner is not None:
            self._owner.__exit__(None, None, None)
            self._owner = None
