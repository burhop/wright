from __future__ import annotations

import json
from typing import Any

from data_vault import WorkspaceRepository


class WorkspaceContextUseCases:
    def __init__(self, repository: WorkspaceRepository) -> None:
        self.repository = repository

    def config(self, local_path: str) -> dict[str, Any] | None:
        workspace = self.repository.get_by_path(local_path)
        if workspace:
            workspace = {
                **workspace,
                "has_token": self.repository.has_git_token(workspace["workspace_id"]),
            }
        return workspace

    def save(self, workspace_id: str, context_data: Any) -> None:
        self.repository.save_context(workspace_id, json.dumps(context_data))

    def load(self, workspace_id: str) -> dict[str, Any] | None:
        row = self.repository.load_context(workspace_id)
        if not row:
            return None
        try:
            context_data = json.loads(row["context_data"])
        except (TypeError, json.JSONDecodeError):
            context_data = row["context_data"]
        return {
            "workspace_id": workspace_id,
            "context_data": context_data,
            "updated_at": row.get("updated_at"),
        }
