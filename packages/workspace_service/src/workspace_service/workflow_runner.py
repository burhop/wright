"""Optional, supervised Rivet fixture runner.

This slice deliberately executes no Rivet tool, plugin, MCP, network, or native
authority.  It establishes the bounded lifecycle boundary that later node work
will use.
"""

from __future__ import annotations

import os
import shutil
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from core.workflow_runs import (
    RunnerAvailability,
    WorkflowRun,
    WorkflowRunEvent,
    WorkflowRunnerError,
    WorkflowRunnerUnavailable,
    WorkflowRunState,
)

from .surfaces.process_supervisor import ProcessSupervisor, ProcessSupervisorError
from .workflows import WorkspaceWorkflowStore


@dataclass(frozen=True, slots=True)
class RunnerSettings:
    enabled: bool = False
    maximum_concurrent_runs: int = 2
    captured_log_bytes: int = 256 * 1024
    cancellation_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.maximum_concurrent_runs < 1 or self.captured_log_bytes < 1:
            raise ValueError("Runner limits must be positive")
        if self.cancellation_seconds <= 0:
            raise ValueError("Runner cancellation deadline must be positive")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "RunnerSettings":
        source = env or os.environ
        return cls(
            enabled=source.get("WRIGHT_RIVET_RUNNER_ENABLED", "0").strip().lower()
            in {"1", "true", "yes"},
            maximum_concurrent_runs=int(
                source.get("WRIGHT_RIVET_RUNNER_MAX_CONCURRENT", "2")
            ),
            captured_log_bytes=int(
                source.get("WRIGHT_RIVET_RUNNER_LOG_BYTES", str(256 * 1024))
            ),
            cancellation_seconds=float(
                source.get("WRIGHT_RIVET_RUNNER_CANCEL_SECONDS", "2")
            ),
        )


@dataclass(frozen=True, slots=True)
class RunnerStatus:
    availability: RunnerAvailability
    generation: int
    detail: str | None = None


class WorkspaceWorkflowRunner:
    """Own fixture run state and delegate process ownership to ProcessSupervisor."""

    def __init__(
        self,
        *,
        supervisor: ProcessSupervisor,
        settings: RunnerSettings | None = None,
        node_path: str | None = None,
        fixture_path: Path | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._supervisor = supervisor
        self._settings = settings or RunnerSettings.from_env()
        self._node_path = node_path
        self._fixture_path = fixture_path or (
            Path(__file__).resolve().parents[4]
            / "integrations"
            / "rivet"
            / "runner"
            / "fixture-runner.mjs"
        )
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        self._generation = 1
        self._runs: dict[str, WorkflowRun] = {}
        self._events: dict[str, list[WorkflowRunEvent]] = {}
        self._next_sequence: dict[str, int] = {}

    def status(self) -> RunnerStatus:
        if not self._settings.enabled:
            return RunnerStatus(RunnerAvailability.DISABLED, self._generation)
        if not self._fixture_path.is_file():
            return RunnerStatus(
                RunnerAvailability.INCOMPATIBLE,
                self._generation,
                "Runner fixture is missing",
            )
        if not self._node():
            return RunnerStatus(
                RunnerAvailability.MISSING, self._generation, "Node.js is unavailable"
            )
        return RunnerStatus(RunnerAvailability.AVAILABLE, self._generation)

    def _node(self) -> str | None:
        return self._node_path or shutil.which("node")

    def _append_event(
        self, run_id: str, kind: str, **payload: str | int | float | bool | None
    ) -> None:
        events = self._events.setdefault(run_id, [])
        # Keep a small in-memory projection; the ProcessSupervisor owns bounded raw logs.
        if len(events) >= 256:
            events.pop(0)
        sequence = self._next_sequence.get(run_id, 0) + 1
        self._next_sequence[run_id] = sequence
        events.append(WorkflowRunEvent(run_id, sequence, kind, payload))

    async def start(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        slug: str,
        expected_generation: int | None = None,
    ) -> WorkflowRun:
        status = self.status()
        if status.availability is not RunnerAvailability.AVAILABLE:
            raise WorkflowRunnerUnavailable(
                status.availability, status.detail or "Rivet runner is unavailable"
            )
        if expected_generation is not None and expected_generation != self._generation:
            raise WorkflowRunnerError(
                "RIVET_RUNNER_STALE_GENERATION", "Runner generation is stale"
            )
        active = [
            item
            for item in self._runs.values()
            if item.state
            in {
                WorkflowRunState.QUEUED,
                WorkflowRunState.RUNNING,
                WorkflowRunState.CANCELLING,
            }
        ]
        if len(active) >= self._settings.maximum_concurrent_runs:
            raise WorkflowRunnerError(
                "RIVET_RUNNER_CONCURRENCY_LIMIT", "Runner concurrency limit reached"
            )
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        run_id = self._id_factory()
        if not run_id:
            raise WorkflowRunnerError(
                "RIVET_RUNNER_ID_INVALID", "Run ID factory returned empty"
            )
        run = WorkflowRun(
            run_id,
            workspace_id,
            session_id,
            document.workflow_id,
            document.revision,
            self._generation,
            WorkflowRunState.QUEUED,
        )
        self._runs[run_id] = run
        self._append_event(
            run_id, "queued", revision=document.revision, digest=document.digest
        )
        try:
            snapshot = await self._supervisor.start(
                workspace_id=workspace_id,
                instance_id=f"rivet-run-{run_id}",
                generation=run.generation,
                argv=(self._node() or "node", str(self._fixture_path)),
                cwd=str(Path(workspace_dir).resolve()),
                environment={
                    "WRIGHT_RIVET_RUN_ID": run_id,
                    "WRIGHT_RIVET_WORKFLOW_DIGEST": document.digest,
                },
                secret_environment_names=frozenset(),
                redaction_query_names=frozenset(),
                limits={
                    "captured_log_bytes": self._settings.captured_log_bytes,
                    "graceful_shutdown_seconds": self._settings.cancellation_seconds,
                    "max_processes": 4,
                    "max_memory_mib": 512,
                    "cpu_cores": 1.0,
                },
                idempotency_key=run_id,
            )
        except ProcessSupervisorError as error:
            self._runs[run_id] = replace(
                run, state=WorkflowRunState.FAILED, reason=error.code
            )
            self._append_event(run_id, "failed", code=error.code)
            return self._runs[run_id]
        self._runs[run_id] = replace(
            run, state=WorkflowRunState.RUNNING, runtime_id=snapshot.runtime_id
        )
        self._append_event(run_id, "started", generation=run.generation)
        return self._runs[run_id]

    def get(self, run_id: str) -> WorkflowRun:
        try:
            run = self._runs[run_id]
        except KeyError as error:
            raise WorkflowRunnerError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            ) from error
        if run.runtime_id and run.state is WorkflowRunState.RUNNING:
            runtime = self._supervisor.snapshot(run.runtime_id)
            if runtime.status == "exited":
                state = (
                    WorkflowRunState.SUCCEEDED
                    if runtime.exit_code == 0
                    else WorkflowRunState.FAILED
                )
                run = replace(
                    run,
                    state=state,
                    reason=None
                    if state is WorkflowRunState.SUCCEEDED
                    else "process_exit",
                )
                self._runs[run_id] = run
                self._append_event(
                    run_id,
                    "completed" if state is WorkflowRunState.SUCCEEDED else "failed",
                    exit_code=runtime.exit_code,
                )
        return run

    async def cancel(self, run_id: str, *, generation: int) -> WorkflowRun:
        run = self.get(run_id)
        if run.generation != generation:
            raise WorkflowRunnerError(
                "RIVET_RUNNER_STALE_GENERATION", "Run generation is stale"
            )
        if run.state in {
            WorkflowRunState.CANCELLED,
            WorkflowRunState.SUCCEEDED,
            WorkflowRunState.FAILED,
        }:
            return run
        if not run.runtime_id:
            updated = replace(
                run, state=WorkflowRunState.CANCELLED, reason="cancelled_before_start"
            )
            self._runs[run_id] = updated
            self._append_event(run_id, "cancelled")
            return updated
        self._runs[run_id] = replace(run, state=WorkflowRunState.CANCELLING)
        self._append_event(run_id, "cancelling")
        snapshot = await self._supervisor.stop(
            runtime_id=run.runtime_id,
            generation=generation,
            deadline=datetime.now(UTC)
            + timedelta(seconds=self._settings.cancellation_seconds),
        )
        state = (
            WorkflowRunState.CANCELLED
            if snapshot.stop_result and snapshot.stop_result.complete
            else WorkflowRunState.FAILED
        )
        self._runs[run_id] = replace(
            run,
            state=state,
            reason=None
            if state is WorkflowRunState.CANCELLED
            else "cleanup_incomplete",
        )
        self._append_event(
            run_id, "cancelled" if state is WorkflowRunState.CANCELLED else "failed"
        )
        return self._runs[run_id]

    def events(
        self, run_id: str, *, after_sequence: int = 0
    ) -> tuple[WorkflowRunEvent, ...]:
        self.get(run_id)
        return tuple(
            event
            for event in self._events.get(run_id, ())
            if event.sequence > after_sequence
        )

    async def reconcile(self) -> tuple[WorkflowRun, ...]:
        self._generation += 1
        reconciled: list[WorkflowRun] = []
        for run in tuple(self._runs.values()):
            if run.state in {
                WorkflowRunState.QUEUED,
                WorkflowRunState.RUNNING,
                WorkflowRunState.CANCELLING,
            }:
                updated = replace(
                    run, state=WorkflowRunState.FAILED, reason="runner_restarted"
                )
                self._runs[run.run_id] = updated
                self._append_event(run.run_id, "failed", code="runner_restarted")
                reconciled.append(updated)
        return tuple(reconciled)

    async def shutdown(self) -> tuple[WorkflowRun, ...]:
        """Stop all owned children before the workspace service is disposed."""
        for run in tuple(self._runs.values()):
            if run.runtime_id and run.state in {
                WorkflowRunState.QUEUED,
                WorkflowRunState.RUNNING,
                WorkflowRunState.CANCELLING,
            }:
                try:
                    await self.cancel(run.run_id, generation=run.generation)
                except WorkflowRunnerError:
                    continue
        return await self.reconcile()
