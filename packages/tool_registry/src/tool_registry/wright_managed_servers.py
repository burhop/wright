from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any


RIVET_WORKFLOWS_SERVER_ID = "rivet-workflows"
RIVET_WORKFLOW_MUTATION_APPROVAL = "rivet-workflow-mutation"

# No legacy engine is installed as a built-in provider.
WRIGHT_MANAGED_TOOLS: tuple[dict[str, Any], ...] = ()
WRIGHT_MANAGED_SERVERS: tuple[dict[str, Any], ...] = ()

_SAFE_BINDING_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")


def trusted_managed_launch_environment(
    server_id: str,
    *,
    workspace_path: str | None,
    database_path: str,
    binding: Mapping[str, object] | None,
) -> dict[str, str]:
    """Return process-only authority for a Wright-owned server.

    This data is intentionally not persisted in the MCP catalog, where a model
    or user-managed entry could otherwise attempt to override it.
    """

    if server_id != RIVET_WORKFLOWS_SERVER_ID:
        return {}
    if not workspace_path:
        raise ValueError("Rivet MCP requires a bound workspace")
    source = binding or {}
    workspace_id = str(source.get("workspace_id") or "")
    session_id = str(source.get("session_id") or "")
    if not _SAFE_BINDING_ID.fullmatch(workspace_id) or not _SAFE_BINDING_ID.fullmatch(
        session_id
    ):
        raise ValueError("Rivet MCP requires safe workspace and session identities")
    return {
        "WRIGHT_RIVET_MCP_WORKSPACE": os.path.realpath(os.path.abspath(workspace_path)),
        "WRIGHT_RIVET_MCP_DATABASE": os.path.realpath(os.path.abspath(database_path)),
        "WRIGHT_RIVET_MCP_WORKSPACE_ID": workspace_id,
        "WRIGHT_RIVET_MCP_SESSION_ID": session_id,
    }
