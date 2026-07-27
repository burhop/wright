from __future__ import annotations

from .ports import WorkspaceNotifier
from .service import WorkspaceService


def build_workspace_service(
    db_path: str, *, notifier: WorkspaceNotifier | None = None
) -> WorkspaceService:
    """Construct the production local workspace application graph explicitly."""
    return WorkspaceService(db_path, notifier=notifier)
