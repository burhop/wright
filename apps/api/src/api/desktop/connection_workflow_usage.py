"""Bounded read-only projection of explicit saved workflow/provider references.

Source integrity and confinement remain with the workspace source owner. This
is not execution readiness, an update approval, or a scan of other workspaces.
"""

import asyncio

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    _parse,
)
from workspace_service.workflow_sources import WorkflowSourceStorageError


async def connection_workflow_usage(sources, workspace_dir: str, server_id: str):
    matches, unchecked = [], []
    complete = True
    examined = 0
    total_bytes = 0
    try:
        async with asyncio.timeout(15):
            files = await sources.list_input_files(workspace_dir)
            paths = sorted(
                item["path"]
                for item in files
                if item["path"].startswith("workflows/")
                and item["path"].endswith(".workflow.wflow")
            )
            complete = len(paths) <= 64
            for path in paths[:64]:
                try:
                    document = await sources.read(workspace_dir, path)
                    total_bytes += document.size_bytes
                    if total_bytes > 4 * 1024 * 1024:
                        complete = False
                        break
                    sections = _parse(document.source)
                    if any(
                        s["kind"]
                        not in {
                            "workflow",
                            "task",
                            "input",
                            "connection",
                            "group",
                            "item",
                        }
                        for s in sections
                    ):
                        raise ValueError("Unknown source section")
                    workflow = [s for s in sections if s["kind"] == "workflow"]
                    if len(workflow) != 1:
                        raise ValueError("Unknown workflow declaration")
                    title = workflow[0]["fields"].get("name")
                    if not isinstance(title, str) or not title:
                        title = path
                    steps = []
                    unresolved = False
                    for section in sections:
                        if section["kind"] != "task":
                            continue
                        fields = section["fields"]
                        settings = fields.get("settings")
                        if not isinstance(settings, dict):
                            unresolved = True
                            continue
                        selected = settings.get("mcp_server")
                        if selected == server_id:
                            name = fields.get("name")
                            steps.append(
                                {
                                    "id": section["id"],
                                    "title": name
                                    if isinstance(name, str)
                                    else section["id"],
                                }
                            )
                        if (
                            fields.get("tool") is not None
                            or fields.get("reusable_step") is not None
                            or (
                                fields.get("performed_by") == "configured_tool"
                                and not selected
                            )
                            or (selected is not None and not isinstance(selected, str))
                            or (
                                settings.get("authoring_template")
                                in ("mcp-task", "mcp-tool")
                                and not selected
                            )
                            or (settings.get("mcp_tool") and not selected)
                        ):
                            unresolved = True
                    if steps:
                        matches.append(
                            {
                                "path": document.path,
                                "title": title,
                                "source_digest": document.storage_digest,
                                "steps": steps,
                            }
                        )
                    if unresolved:
                        unchecked.append(path)
                    examined += 1
                except (
                    OSError,
                    ValueError,
                    WorkflowSourceStorageError,
                    WorkflowSourceExecutionError,
                ):
                    unchecked.append(path)
    except (TimeoutError, OSError, ValueError, WorkflowSourceStorageError):
        complete = False
    return {
        "scope": "selected-workspace-saved-explicit-bindings",
        "matches": matches,
        "unchecked_paths": unchecked,
        "scan_complete": complete and not unchecked,
        "examined": examined,
    }
