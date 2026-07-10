from __future__ import annotations

from data_vault import WorkspaceRepository


class WorkspaceLifecycleUseCases:
    def __init__(self, repository: WorkspaceRepository) -> None:
        self.repository = repository

    def get_by_id(self, workspace_id: str):
        return self.repository.get_by_id(workspace_id)

    def get_by_session(self, session_id: str):
        return self.repository.get_by_session(session_id)

    def get_by_path(self, local_path: str):
        return self.repository.get_by_path(local_path)

    def list_recent(self, limit: int = 5):
        return self.repository.list_recent(limit)

    def list_all(self):
        return self.repository.list_all()
