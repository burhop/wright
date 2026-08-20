from __future__ import annotations

from collections.abc import Callable
import time

from data_vault import WorkflowIndexRecord, WorkflowRepository

from ..executor import BoundedExecutor
from ..rivet_project import normalize_graph_output_ids
from ..workflows import WorkflowDocument, WorkspaceWorkflowStore


class WorkspaceWorkflowUseCases:
    """Coordinates authoritative files with their rebuildable metadata index."""

    def __init__(
        self,
        executor: BoundedExecutor,
        index: WorkflowRepository,
        store_factory: Callable[[str], WorkspaceWorkflowStore] = WorkspaceWorkflowStore,
    ) -> None:
        self._executor = executor
        self._index = index
        self._store_factory = store_factory

    def _index_document(self, workspace_id: str, document: WorkflowDocument) -> None:
        self._index.upsert(
            WorkflowIndexRecord(
                workspace_id,
                document.workflow_id,
                document.slug,
                document.revision,
                document.digest,
                "active",
                int(time.time()),
            )
        )

    async def create(
        self,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        project: str,
        datasets: dict[str, str] | None = None,
    ) -> WorkflowDocument:
        def work() -> WorkflowDocument:
            document = self._store_factory(workspace_dir).create(
                slug, project, datasets
            )
            self._index_document(workspace_id, document)
            return document

        return await self._executor.run(
            "workspace.workflows.create", work, timeout_seconds=30.0
        )

    async def save(
        self,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        expected_revision: int,
        project: str,
        datasets: dict[str, str] | None = None,
    ) -> WorkflowDocument:
        def work() -> WorkflowDocument:
            document = self._store_factory(workspace_dir).save(
                slug,
                expected_revision,
                normalize_graph_output_ids(project),
                datasets,
            )
            self._index_document(workspace_id, document)
            return document

        return await self._executor.run(
            "workspace.workflows.save", work, timeout_seconds=30.0
        )

    async def read(self, workspace_dir: str, slug: str) -> WorkflowDocument:
        return await self._executor.run(
            "workspace.workflows.read",
            lambda: self._store_factory(workspace_dir).read(slug),
            timeout_seconds=30.0,
        )

    async def rename(
        self,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        expected_revision: int,
        new_slug: str,
    ) -> WorkflowDocument:
        def work() -> WorkflowDocument:
            document = self._store_factory(workspace_dir).rename(
                slug, expected_revision, new_slug
            )
            self._index_document(workspace_id, document)
            return document

        return await self._executor.run(
            "workspace.workflows.rename", work, timeout_seconds=30.0
        )

    async def delete(
        self, workspace_id: str, workspace_dir: str, slug: str, expected_revision: int
    ) -> str:
        def work() -> str:
            store = self._store_factory(workspace_dir)
            current = store.read(slug)
            recovery_id = store.delete(slug, expected_revision)
            self._index.mark_deleted(workspace_id, current.workflow_id)
            return recovery_id

        return await self._executor.run(
            "workspace.workflows.delete", work, timeout_seconds=30.0
        )

    async def recover(
        self, workspace_id: str, workspace_dir: str, recovery_id: str, slug: str
    ) -> WorkflowDocument:
        def work() -> WorkflowDocument:
            document = self._store_factory(workspace_dir).recover(recovery_id, slug)
            self._index_document(workspace_id, document)
            return document

        return await self._executor.run(
            "workspace.workflows.recover", work, timeout_seconds=30.0
        )

    async def rebuild_index(self, workspace_id: str, workspace_dir: str) -> int:
        def work() -> int:
            root = self._store_factory(workspace_dir)
            count = 0
            for slug in root.list_slugs():
                document = root.read(slug)
                self._index_document(workspace_id, document)
                count += 1
            return count

        return await self._executor.run(
            "workspace.workflows.rebuild", work, timeout_seconds=30.0
        )
