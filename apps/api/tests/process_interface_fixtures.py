"""Attach the real process owner to small, explicitly scoped API test services."""

from types import SimpleNamespace
from workspace_service.process_interfaces.service import ProcessInterfaceService


def bind_process_interfaces(service, root, workspace_id, *, registered_root=None):
    service.db_path = str(root / "state.db")
    service.repository = SimpleNamespace(
        get_by_id=lambda key: (
            {
                "local_path": str(registered_root or root),
            }
            if key == workspace_id
            else None
        )
    )
    service.process_interfaces = ProcessInterfaceService(service)
    return service
