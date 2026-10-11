"""Internal fixed-runtime declaration for an already verified immutable bundle."""

from pathlib import Path
import re
import sys

from core.process_interfaces import InterfaceManifest
from core.surfaces.live_app_manifest import parse_live_app_manifest
from data_vault.process_ui_artifacts import ImmutableFileSet

from ..workspace_path import WorkspacePath


def process_ui_manifest(
    workspace_dir: str,
    interface: InterfaceManifest,
    inventory_digest: str,
    *,
    python_executable=None,
):
    """The model chooses no executable, launch arguments, root or environment."""
    if not re.fullmatch(r"ui-[0-9a-f]{32}", interface.ui_id) or not re.fullmatch(
        r"revision-[0-9a-f]{32}", interface.revision_id
    ):
        raise ValueError(
            "Managed interface artifacts require allocated opaque identities"
        )
    vault = WorkspacePath(workspace_dir).resolve(
        f".wright/process-uis/{interface.ui_id}/revisions/{interface.revision_id}",
        must_exist=True,
    )
    ImmutableFileSet(vault).read(inventory_digest)
    python = Path(python_executable or sys.executable).absolute()
    if not python.is_file():
        raise ValueError("The installed static runtime Python is unavailable")
    value = {
        "schemaVersion": 1,
        "id": "process." + interface.ui_id + "." + interface.revision_id,
        "version": "1.0.0",
        "title": interface.title[:256],
        "description": "Wright-owned static presentation of one accepted process.",
        "ownershipPolicy": "wright-owned",
        "launch": {
            "mode": "command",
            "framework": "generic",
            "workingDirectory": ".",
            "argv": [
                str(python),
                "-m",
                "workspace_service.surfaces.process_ui_static",
                "--vault-directory",
                str(vault),
                "--inventory-digest",
                inventory_digest,
                "--host",
                "${WRIGHT_BIND_HOST}",
                "--port",
                "${WRIGHT_PORT}",
            ],
            "environment": {},
        },
        "readiness": {
            "path": "/__wright/health",
            "expectedStatus": 200,
            # This is the complete startup window, not a per-request timeout.
            # The installed Python imports and immutable inventory verification
            # must finish before readiness; retain the platform's bounded budget.
            "timeoutMs": 30000,
            "intervalMs": 250,
        },
        "health": {
            "path": "/__wright/health",
            "expectedStatus": 200,
            "timeoutMs": 1000,
            "intervalMs": 5000,
        },
        "presentation": {
            "panel": True,
            "browser": False,
            "sharing": "isolated",
            "basePathMode": "root",
            "allowedFrameAncestors": [],
            "permissionsPolicy": [],
        },
        "transports": {"http": True, "websocket": False, "sse": False},
        "navigation": {
            "externalLinks": "deny",
            "downloads": "deny",
            "allowSameTargetRedirects": False,
        },
        "lifetime": {"policy": "presentation"},
        "capabilities": list(interface.capabilities),
    }
    parsed = parse_live_app_manifest(value)
    return value, parsed
