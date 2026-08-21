"""Neutral workflow-run values; execution adapters remain optional."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
from enum import StrEnum


class RunnerAvailability(StrEnum):
    DISABLED = "disabled"
    AVAILABLE = "available"
    MISSING = "missing"
    INCOMPATIBLE = "incompatible"
    DEGRADED = "degraded"


class WorkflowRunState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class WorkflowRunnerError(RuntimeError):
    """A runner failure safe to return through a typed boundary."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class WorkflowRunnerUnavailable(WorkflowRunnerError):
    def __init__(self, availability: RunnerAvailability, message: str) -> None:
        super().__init__("RIVET_RUNNER_UNAVAILABLE", message)
        self.availability = availability


@dataclass(frozen=True, slots=True)
class WorkflowRun:
    run_id: str
    workspace_id: str
    session_id: str
    workflow_id: str
    revision: int
    generation: int
    state: WorkflowRunState
    runtime_id: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not all((self.run_id, self.workspace_id, self.session_id, self.workflow_id)):
            raise ValueError("Workflow run identity is required")
        if self.revision < 1 or self.generation < 1:
            raise ValueError("Workflow run revision and generation must be positive")


@dataclass(frozen=True, slots=True)
class WorkflowRunEvent:
    run_id: str
    sequence: int
    kind: str
    payload: Mapping[str, str | int | float | bool | None]
    occurred_at: int | None = None

    def __post_init__(self) -> None:
        if not self.run_id or not self.kind or self.sequence < 1:
            raise ValueError("Workflow run event is invalid")
