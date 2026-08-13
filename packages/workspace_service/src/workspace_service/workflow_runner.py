"""Supervised fixture and inventoried real Rivet workflow execution."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import shutil
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from data_vault import (
    WorkflowRunEventRecord,
    WorkflowRunRecord,
    WorkflowRunRepository,
)

from core.workflow_runs import (
    RunnerAvailability,
    WorkflowRun,
    WorkflowRunEvent,
    WorkflowRunnerError,
    WorkflowRunnerUnavailable,
    WorkflowRunState,
)

from .surfaces.process_supervisor import ProcessSupervisor, ProcessSupervisorError
from .rivet_validation import validate_rivet_project
from .workflows import WorkspaceWorkflowStore

if TYPE_CHECKING:
    from .rivet_runtime_host import ProgressCallback, RivetRuntimeHost


@dataclass(frozen=True, slots=True)
class RunnerSettings:
    enabled: bool = False
    real_execution_enabled: bool = False
    maximum_concurrent_runs: int = 2
    captured_log_bytes: int = 256 * 1024
    captured_output_bytes: int = 1024 * 1024
    maximum_event_bytes: int = 64 * 1024
    run_timeout_seconds: float = 300.0
    cancellation_seconds: float = 2.0

    def __post_init__(self) -> None:
        if (
            self.maximum_concurrent_runs < 1
            or self.captured_log_bytes < 1
            or self.captured_output_bytes < 1
            or self.maximum_event_bytes < 256
        ):
            raise ValueError("Runner limits must be positive")
        if self.maximum_event_bytes > self.captured_output_bytes:
            raise ValueError("Runner event limit may not exceed output limit")
        if not 1 <= self.run_timeout_seconds <= 3600:
            raise ValueError("Runner timeout must be between 1 and 3600 seconds")
        if self.cancellation_seconds <= 0:
            raise ValueError("Runner cancellation deadline must be positive")

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "RunnerSettings":
        source = env or os.environ
        return cls(
            enabled=source.get("WRIGHT_RIVET_RUNNER_ENABLED", "0").strip().lower()
            in {"1", "true", "yes"},
            real_execution_enabled=source.get(
                "WRIGHT_RIVET_REAL_EXECUTION_ENABLED", "0"
            )
            .strip()
            .lower()
            in {"1", "true", "yes"},
            maximum_concurrent_runs=int(
                source.get("WRIGHT_RIVET_RUNNER_MAX_CONCURRENT", "2")
            ),
            captured_log_bytes=int(
                source.get("WRIGHT_RIVET_RUNNER_LOG_BYTES", str(256 * 1024))
            ),
            captured_output_bytes=int(
                source.get("WRIGHT_RIVET_RUNNER_OUTPUT_BYTES", str(1024 * 1024))
            ),
            maximum_event_bytes=int(
                source.get("WRIGHT_RIVET_RUNNER_EVENT_BYTES", str(64 * 1024))
            ),
            run_timeout_seconds=float(
                source.get("WRIGHT_RIVET_RUNNER_TIMEOUT_SECONDS", "300")
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


@dataclass(frozen=True, slots=True)
class RunnerArtifactManifest:
    protocol_version: int
    rivet_version: str
    package_version: str
    entrypoint: Path
    sha256: str
    bytes: int


class RunnerAssetCatalog:
    """Verify the checked-in Rivet Node worker before it can execute."""

    _SOURCE_REVISION = "4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053"
    _RIVET_VERSION = "2.8.9"
    _PACKAGE_VERSION = "2.1.9"
    _SOURCE_REPOSITORY = "https://github.com/valerypopoff/rivet2.0.git"
    _SOURCE_PACKAGE = "@valerypopoff/rivet2-node"

    def __init__(self, manifest_path: Path | None = None) -> None:
        checkout_manifest = (
            Path(__file__).resolve().parents[4]
            / "integrations"
            / "rivet"
            / "runner"
            / "manifest.json"
        )
        packaged_manifest = (
            Path(__file__).resolve().parent / "_rivet" / "runner" / "manifest.json"
        )
        self._manifest_path = manifest_path or (
            checkout_manifest if checkout_manifest.is_file() else packaged_manifest
        )

    @staticmethod
    def _confined(root: Path, relative: object) -> Path | None:
        if not isinstance(relative, str) or not relative:
            return None
        path = (root / relative).resolve()
        if path == root or root not in path.parents:
            return None
        return path

    def status(
        self,
    ) -> tuple[RunnerAvailability, RunnerArtifactManifest | None, str | None]:
        if not self._manifest_path.is_file():
            return (
                RunnerAvailability.MISSING,
                None,
                "Runner artifact manifest is missing",
            )
        try:
            raw = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            if (
                raw.get("schema_version") != 1
                or raw.get("runner") != "wright-rivet2-node"
            ):
                raise ValueError("Unsupported runner manifest")
            if (
                raw.get("protocol_version") != 1
                or raw.get("rivet_version") != self._RIVET_VERSION
            ):
                raise ValueError("Unexpected runner version")
            source = raw["source"]
            if source != {
                "repository": self._SOURCE_REPOSITORY,
                "revision": self._SOURCE_REVISION,
                "package": self._SOURCE_PACKAGE,
                "package_version": self._PACKAGE_VERSION,
            }:
                raise ValueError("Unexpected runner source")
            root = self._manifest_path.parent.resolve()
            entrypoint = self._confined(root, raw.get("entrypoint"))
            build_input_entry = raw.get("build_input")
            if not isinstance(build_input_entry, dict):
                raise ValueError("Missing runner build input")
            build_input = self._confined(root, build_input_entry.get("path"))
            if entrypoint is None or build_input is None:
                raise ValueError("Unconfined runner path")
            manifest = RunnerArtifactManifest(
                protocol_version=1,
                rivet_version=self._RIVET_VERSION,
                package_version=self._PACKAGE_VERSION,
                entrypoint=entrypoint,
                sha256=str(raw["sha256"]),
                bytes=int(raw["bytes"]),
            )
            expected_input = str(build_input_entry["sha256"])
        except (OSError, KeyError, TypeError, ValueError):
            return (
                RunnerAvailability.INCOMPATIBLE,
                None,
                "Runner artifact manifest is invalid",
            )
        if not entrypoint.is_file() or not build_input.is_file():
            return RunnerAvailability.MISSING, manifest, "Runner artifact is incomplete"
        content = entrypoint.read_bytes()
        if len(content) != manifest.bytes or not secrets.compare_digest(
            hashlib.sha256(content).hexdigest(), manifest.sha256
        ):
            return (
                RunnerAvailability.INCOMPATIBLE,
                manifest,
                "Runner artifact integrity does not match",
            )
        if not secrets.compare_digest(
            hashlib.sha256(build_input.read_bytes()).hexdigest(), expected_input
        ):
            return (
                RunnerAvailability.INCOMPATIBLE,
                manifest,
                "Runner build input integrity does not match",
            )
        return RunnerAvailability.AVAILABLE, manifest, None


class WorkspaceWorkflowRunner:
    """Own fixture run state and delegate process ownership to ProcessSupervisor."""

    def __init__(
        self,
        *,
        supervisor: ProcessSupervisor,
        settings: RunnerSettings | None = None,
        node_path: str | None = None,
        fixture_path: Path | None = None,
        artifact_catalog: RunnerAssetCatalog | None = None,
        runtime_host: RivetRuntimeHost | None = None,
        run_repository: WorkflowRunRepository | None = None,
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
        self._artifact_catalog = artifact_catalog or RunnerAssetCatalog()
        self._runtime_host = runtime_host
        self._run_repository = run_repository
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        self._generation = 1
        self._runs: dict[str, WorkflowRun] = {}
        self._events: dict[str, list[WorkflowRunEvent]] = {}
        self._next_sequence: dict[str, int] = {}
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def status(self) -> RunnerStatus:
        if not self._settings.enabled:
            return RunnerStatus(RunnerAvailability.DISABLED, self._generation)
        if self._settings.real_execution_enabled:
            availability, _manifest, detail = self._artifact_catalog.status()
            if availability is not RunnerAvailability.AVAILABLE:
                return RunnerStatus(availability, self._generation, detail)
            if self._runtime_host is None:
                return RunnerStatus(
                    RunnerAvailability.INCOMPATIBLE,
                    self._generation,
                    "Real Rivet runtime host is unavailable",
                )
        elif not self._fixture_path.is_file():
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
        if self._run_repository is not None:
            self._run_repository.append_event(
                WorkflowRunEventRecord(
                    run_id=run_id,
                    sequence=sequence,
                    occurred_at=int(time.time()),
                    kind=kind,
                    payload=dict(payload),
                )
            )

    async def start(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        slug: str,
        expected_generation: int | None = None,
        expected_revision: int | None = None,
        expected_digest: str | None = None,
        graph: str | None = None,
        inputs: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
        timeout_seconds: float | None = None,
        progress_callback: ProgressCallback | None = None,
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
        if expected_revision is not None and document.revision != expected_revision:
            raise WorkflowRunnerError(
                "RIVET_WORKFLOW_REVISION_CONFLICT", "Workflow revision changed"
            )
        if expected_digest is not None and document.digest != expected_digest:
            raise WorkflowRunnerError(
                "RIVET_WORKFLOW_REVISION_CONFLICT", "Workflow contents changed"
            )
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
        if self._settings.real_execution_enabled:
            validation = validate_rivet_project(
                document.project,
                workflow_id=document.workflow_id,
                revision=document.revision,
                digest=document.digest,
                selected_graph=graph,
                expected_revision=expected_revision,
                expected_digest=expected_digest,
            )
            if not validation.valid or validation.main_graph is None:
                self._runs.pop(run_id, None)
                raise WorkflowRunnerError(
                    "RIVET_WORKFLOW_INVALID", "Workflow is not executable"
                )
            selected_graph = graph or validation.main_graph.name
            if self._run_repository is not None:
                self._run_repository.create(
                    WorkflowRunRecord(
                        run_id=run_id,
                        workspace_id=workspace_id,
                        session_id=session_id,
                        workflow_id=document.workflow_id,
                        revision=document.revision,
                        digest=document.digest,
                        graph=selected_graph,
                        state="queued",
                        generation=self._generation,
                        started_at=None,
                        completed_at=None,
                        reason_code=None,
                        output_summary=None,
                        output_truncated=False,
                    )
                )
        self._append_event(
            run_id, "queued", revision=document.revision, digest=document.digest
        )
        if self._settings.real_execution_enabled:
            running = replace(run, state=WorkflowRunState.RUNNING)
            self._runs[run_id] = running
            if self._run_repository is not None:
                self._run_repository.transition(run_id, "running")
            self._append_event(run_id, "started", generation=run.generation)
            task = asyncio.create_task(
                self._execute_real(
                    run=running,
                    workspace_dir=workspace_dir,
                    document=document,
                    graph=selected_graph,
                    inputs=inputs or {},
                    context=context or {},
                    requirements=validation.requirements,
                    timeout_seconds=timeout_seconds,
                    progress_callback=progress_callback,
                ),
                name=f"rivet-workflow-{run_id}",
            )
            self._tasks[run_id] = task
            return running
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

    async def _execute_real(
        self,
        *,
        run: WorkflowRun,
        workspace_dir: str,
        document,
        graph: str,
        inputs: Mapping[str, Any],
        context: Mapping[str, Any],
        requirements: tuple[str, ...],
        timeout_seconds: float | None,
        progress_callback: ProgressCallback | None,
    ) -> None:
        from .rivet_runtime_host import RivetRuntimeError

        async def progress(event: dict[str, Any]) -> None:
            payload = {
                key: value
                for key, value in event.items()
                if key not in {"type", "runId", "sequence"}
                and isinstance(value, (str, int, float, bool, type(None)))
            }
            self._append_event(run.run_id, "progress", **payload)
            if progress_callback is not None:
                result = progress_callback(event)
                if isinstance(result, Awaitable):
                    await result

        try:
            assert self._runtime_host is not None
            result = await self._runtime_host.run(
                run_id=run.run_id,
                workspace_id=run.workspace_id,
                session_id=run.session_id,
                workspace_dir=workspace_dir,
                document=document,
                graph=graph,
                inputs=inputs,
                context=context,
                requirements=requirements,
                timeout_seconds=timeout_seconds,
                progress_callback=progress,
                generation=run.generation,
            )
            state = WorkflowRunState(result.state)
            reason = result.error["code"] if result.error else None
            updated = replace(
                self._runs[run.run_id],
                state=state,
                runtime_id=result.runtime_id,
                reason=reason,
            )
            self._runs[run.run_id] = updated
            output = {
                "outputs": result.outputs or {},
                "durationMs": result.duration_ms,
            }
            if self._run_repository is not None:
                self._run_repository.transition(
                    run.run_id,
                    state.value,
                    completed_at=int(time.time()),
                    reason_code=reason,
                    output_summary=output,
                )
            self._append_event(
                run.run_id,
                "completed" if state is WorkflowRunState.SUCCEEDED else state.value,
                duration_ms=result.duration_ms,
                code=reason,
            )
        except asyncio.CancelledError:
            current = self._runs.get(run.run_id, run)
            if current.state not in {
                WorkflowRunState.CANCELLED,
                WorkflowRunState.SUCCEEDED,
                WorkflowRunState.FAILED,
            }:
                self._runs[run.run_id] = replace(
                    current, state=WorkflowRunState.CANCELLED, reason="cancelled"
                )
                if self._run_repository is not None:
                    record = self._run_repository.get(run.run_id)
                    if record and record.state == "running":
                        self._run_repository.transition(run.run_id, "cancelling")
                    record = self._run_repository.get(run.run_id)
                    if record and record.state == "cancelling":
                        self._run_repository.transition(
                            run.run_id,
                            "cancelled",
                            completed_at=int(time.time()),
                            reason_code="cancelled",
                        )
                self._append_event(run.run_id, "cancelled", code="cancelled")
            raise
        except RivetRuntimeError as error:
            self._runs[run.run_id] = replace(
                self._runs.get(run.run_id, run),
                state=WorkflowRunState.FAILED,
                reason=error.code,
            )
            if self._run_repository is not None:
                self._run_repository.transition(
                    run.run_id,
                    "failed",
                    completed_at=int(time.time()),
                    reason_code=error.code,
                )
            self._append_event(run.run_id, "failed", code=error.code)
        finally:
            self._tasks.pop(run.run_id, None)

    def get(self, run_id: str) -> WorkflowRun:
        try:
            run = self._runs[run_id]
        except KeyError as error:
            raise WorkflowRunnerError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            ) from error
        if (
            not self._settings.real_execution_enabled
            and run.runtime_id
            and run.state is WorkflowRunState.RUNNING
        ):
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

    def result(self, run_id: str) -> WorkflowRunRecord | None:
        self.get(run_id)
        return self._run_repository.get(run_id) if self._run_repository else None

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
        if self._settings.real_execution_enabled:
            self._runs[run_id] = replace(run, state=WorkflowRunState.CANCELLING)
            if self._run_repository is not None:
                record = self._run_repository.get(run_id)
                if record and record.state == "running":
                    self._run_repository.transition(run_id, "cancelling")
            self._append_event(run_id, "cancelling")
            task = self._tasks.get(run_id)
            if task is not None:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            current = self._runs[run_id]
            if current.state is WorkflowRunState.CANCELLING:
                current = replace(
                    current, state=WorkflowRunState.CANCELLED, reason="cancelled"
                )
                self._runs[run_id] = current
                if self._run_repository is not None:
                    record = self._run_repository.get(run_id)
                    if record and record.state == "cancelling":
                        self._run_repository.transition(
                            run_id,
                            "cancelled",
                            completed_at=int(time.time()),
                            reason_code="cancelled",
                        )
                self._append_event(run_id, "cancelled", code="cancelled")
            return current
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
        tasks = tuple(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
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
