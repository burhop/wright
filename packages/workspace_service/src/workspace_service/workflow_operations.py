"""Review-gated workflow operations over Wright-owned workspace boundaries."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import dataclass

from core.workflow_runs import WorkflowRun, WorkflowRunEvent
from data_vault import WorkflowReview, WorkflowReviewRepository

from .workflow_runner import WorkspaceWorkflowRunner
from .workflows import WorkspaceWorkflowStore


class WorkflowOperationsError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class WorkflowOperationsSettings:
    enabled: bool = False
    history_limit: int = 100

    @classmethod
    def from_env(
        cls, env: Mapping[str, str] | None = None
    ) -> "WorkflowOperationsSettings":
        source = env or os.environ
        return cls(
            enabled=source.get("WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED", "0")
            .strip()
            .lower()
            in {"1", "true", "yes"},
            history_limit=max(
                1, int(source.get("WRIGHT_RIVET_WORKFLOW_HISTORY_LIMIT", "100"))
            ),
        )


@dataclass(frozen=True, slots=True)
class WorkflowOperationRecord:
    workflow_id: str
    slug: str
    revision: int
    digest: str
    review: WorkflowReview | None


class WorkspaceWorkflowOperations:
    """Makes approval a durable prerequisite without storing authored content."""

    def __init__(
        self,
        reviews: WorkflowReviewRepository,
        runner: WorkspaceWorkflowRunner,
        *,
        settings: WorkflowOperationsSettings | None = None,
    ) -> None:
        self._reviews = reviews
        self._runner = runner
        self._settings = settings or WorkflowOperationsSettings.from_env()

    def _enabled(self) -> None:
        if not self._settings.enabled:
            raise WorkflowOperationsError(
                "RIVET_OPERATIONS_DISABLED", "Rivet workflow operations are disabled"
            )

    async def review(
        self,
        *,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        state: str,
        reviewer: str,
    ) -> WorkflowOperationRecord:
        self._enabled()
        if not reviewer.strip():
            raise WorkflowOperationsError(
                "RIVET_REVIEWER_REQUIRED", "A reviewer is required"
            )
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        review = WorkflowReview(
            workspace_id,
            document.workflow_id,
            document.revision,
            state,
            reviewer.strip(),
            int(time.time()),
        )
        self._reviews.set(review)
        return WorkflowOperationRecord(
            document.workflow_id,
            document.slug,
            document.revision,
            document.digest,
            review,
        )

    async def detail(
        self, *, workspace_id: str, workspace_dir: str, slug: str
    ) -> WorkflowOperationRecord:
        self._enabled()
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        return WorkflowOperationRecord(
            document.workflow_id,
            document.slug,
            document.revision,
            document.digest,
            self._reviews.get(workspace_id, document.workflow_id),
        )

    async def list(
        self, *, workspace_id: str, workspace_dir: str
    ) -> tuple[WorkflowOperationRecord, ...]:
        self._enabled()
        store = WorkspaceWorkflowStore(workspace_dir)
        records: list[WorkflowOperationRecord] = []
        for slug in store.list_slugs():
            document = store.read(slug)
            records.append(
                WorkflowOperationRecord(
                    document.workflow_id,
                    document.slug,
                    document.revision,
                    document.digest,
                    self._reviews.get(workspace_id, document.workflow_id),
                )
            )
        return tuple(records)

    async def start(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        slug: str,
        expected_generation: int | None = None,
    ) -> WorkflowRun:
        self._enabled()
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        if not self._reviews.approved(
            workspace_id, document.workflow_id, document.revision
        ):
            raise WorkflowOperationsError(
                "RIVET_WORKFLOW_REVIEW_REQUIRED",
                "The current workflow revision has not been approved",
            )
        return await self._runner.start(
            workspace_id=workspace_id,
            session_id=session_id,
            workspace_dir=workspace_dir,
            slug=slug,
            expected_generation=expected_generation,
        )

    def history(
        self,
        *,
        workspace_id: str,
        session_id: str,
        run_id: str,
        after_sequence: int = 0,
    ) -> tuple[WorkflowRunEvent, ...]:
        self._enabled()
        run = self._runner.get(run_id)
        if run.workspace_id != workspace_id or run.session_id != session_id:
            raise WorkflowOperationsError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            )
        return self._runner.events(run_id, after_sequence=after_sequence)[
            -self._settings.history_limit :
        ]

    def run(self, *, workspace_id: str, session_id: str, run_id: str) -> WorkflowRun:
        self._enabled()
        run = self._runner.get(run_id)
        if run.workspace_id != workspace_id or run.session_id != session_id:
            raise WorkflowOperationsError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            )
        return run

    async def cancel(
        self, *, workspace_id: str, session_id: str, run_id: str, generation: int
    ) -> WorkflowRun:
        self._enabled()
        run = self._runner.get(run_id)
        if run.workspace_id != workspace_id or run.session_id != session_id:
            raise WorkflowOperationsError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            )
        return await self._runner.cancel(run_id, generation=generation)
