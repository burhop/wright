from __future__ import annotations

from typing import Any

from core.secrets import CredentialStatus


class RecordingRepository:
    def __init__(self) -> None:
        self.workspaces: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, str] = {}
        self.contexts: dict[str, dict[str, Any]] = {}
        self.tools: dict[str, list[str]] = {}

    def add(self, workspace_id: str, session_id: str, path: str) -> None:
        self.workspaces[workspace_id] = {
            "workspace_id": workspace_id,
            "session_id": session_id,
            "workspace_name": workspace_id,
            "local_path": path,
            "updated_at": 1,
        }
        self.sessions[session_id] = workspace_id

    def get_by_id(self, workspace_id: str):
        return self.workspaces.get(workspace_id)

    def get_by_session(self, session_id: str):
        workspace_id = self.sessions.get(session_id)
        return self.workspaces.get(workspace_id) if workspace_id else None

    def get_by_path(self, local_path: str):
        return next(
            (
                row
                for row in self.workspaces.values()
                if row["local_path"] == local_path
            ),
            None,
        )

    def list_recent(self, limit: int = 5):
        return list(self.workspaces.values())[:limit]

    def list_all(self):
        return list(self.workspaces.values())

    def enabled_tools(self, workspace_id: str):
        return self.tools.get(workspace_id)

    def set_enabled_tools(self, workspace_id: str, tools: list[str]) -> None:
        self.tools[workspace_id] = list(tools)

    def save_context(self, workspace_id: str, context_data: str) -> None:
        self.contexts[workspace_id] = {
            "workspace_id": workspace_id,
            "context_data": context_data,
            "updated_at": 1,
        }

    def load_context(self, workspace_id: str):
        return self.contexts.get(workspace_id)

    def has_git_token(self, workspace_id: str) -> bool:
        return False


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[tuple[str, str | None, str | None]] = []

    def publish(self, event: str, *, workspace_id=None, session_id=None) -> None:
        self.events.append((event, workspace_id, session_id))


class MemorySecrets:
    def get(self, reference):
        return None

    def set(self, reference, value):
        return None

    def delete(self, reference):
        return None

    def status(self, reference):
        return CredentialStatus(False, "memory")
