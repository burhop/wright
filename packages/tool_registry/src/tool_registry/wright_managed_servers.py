from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any


RIVET_WORKFLOWS_SERVER_ID = "rivet-workflows"
RIVET_WORKFLOW_MUTATION_APPROVAL = "rivet-workflow-mutation"

_SLUG = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{0,62}$"}
_DIGEST = {"type": "string", "pattern": "^[a-f0-9]{64}$"}


def _tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    *,
    required: tuple[str, ...] = (),
    read_only: bool,
    destructive: bool,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": list(required),
            "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": read_only,
            "destructiveHint": destructive,
            "idempotentHint": not destructive,
            "openWorldHint": False,
        },
    }


WRIGHT_MANAGED_TOOLS: tuple[dict[str, Any], ...] = (
    _tool(
        "list_templates",
        "List reviewed Rivet workflow templates.",
        {},
        read_only=True,
        destructive=False,
    ),
    _tool(
        "list_workflows",
        "List workflow identities in the bound workspace without project content.",
        {"limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}},
        read_only=True,
        destructive=False,
    ),
    _tool(
        "inspect_workflow",
        "Inspect one workflow identity, graphs, ports, and requirements.",
        {"slug": _SLUG},
        required=("slug",),
        read_only=True,
        destructive=False,
    ),
    _tool(
        "create_workflow",
        "Create one new workflow from a reviewed template or bounded Rivet project.",
        {
            "slug": _SLUG,
            "templateId": {"type": "string", "maxLength": 63},
            "project": {"type": "string", "maxLength": 4 * 1024 * 1024},
        },
        required=("slug",),
        read_only=False,
        destructive=True,
    ),
    _tool(
        "validate_workflow",
        "Validate a workflow and optionally verify its exact revision and digest.",
        {
            "slug": _SLUG,
            "expectedRevision": {"type": "integer", "minimum": 1},
            "expectedDigest": _DIGEST,
            "graph": {"type": "string", "maxLength": 256},
        },
        required=("slug",),
        read_only=True,
        destructive=False,
    ),
    _tool(
        "run_workflow",
        "Run an exact saved workflow revision through Wright's Rivet runtime.",
        {
            "slug": _SLUG,
            "expectedRevision": {"type": "integer", "minimum": 1},
            "expectedDigest": _DIGEST,
            "graph": {"type": "string", "maxLength": 256},
            "inputs": {"type": "object"},
            "context": {"type": "object"},
            "timeoutSeconds": {"type": "number", "minimum": 1, "maximum": 300},
        },
        required=("slug", "expectedRevision", "expectedDigest"),
        read_only=False,
        destructive=True,
    ),
)

WRIGHT_MANAGED_SERVERS: tuple[dict[str, Any], ...] = (
    {
        "server_id": RIVET_WORKFLOWS_SERVER_ID,
        "name": "Rivet Workflows",
        "type": "stdio",
        "command": ["wright-rivet-mcp"],
        "category": "workflow",
        "description": (
            "Wright-managed workspace tools for listing, creating, validating, "
            "and running Rivet workflows."
        ),
        "instructions": (
            "Use workflow slugs and exact revision/digest identities returned by "
            "the server. Never invent workspace paths."
        ),
        "verification_state": "verified_mcp",
        "installability_tier": "tested",
        "risk_level": "medium",
        "deployment_mode": "wright-managed",
        "platform_support": {
            "windows_11_x64": {"status": "yes", "tested": True},
            "linux_x64": {"status": "yes", "tested": True},
            "linux_arm64": {"status": "yes", "tested": True},
        },
        "host_software_required": ["nodejs"],
        "credentials_required": [],
        "default_enabled": True,
        "approval_gates": [],
        "validation_result": {
            "status": "passed",
            "message": "Shipped and tested as part of the Wright runtime.",
            "environment": "wright-runtime",
            "missing_dependencies": [],
        },
    },
)

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
