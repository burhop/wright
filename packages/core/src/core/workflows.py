"""Neutral workflow identifiers, revisions, and persistence errors."""

from __future__ import annotations

from dataclasses import dataclass


class WorkflowPersistenceError(ValueError):
    """A safe workflow persistence validation failure."""


class WorkflowRevisionConflict(WorkflowPersistenceError):
    def __init__(self, revision: int, digest: str) -> None:
        super().__init__("Workflow revision conflict")
        self.revision = revision
        self.digest = digest


@dataclass(frozen=True, slots=True)
class WorkflowDocument:
    workflow_id: str
    slug: str
    revision: int
    digest: str
    project: str
    datasets: dict[str, str]
