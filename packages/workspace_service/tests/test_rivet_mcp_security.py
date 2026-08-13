from __future__ import annotations

import os

import pytest

from workspace_service.rivet_mcp import (
    RivetMcpBinding,
    RivetMcpError,
    RivetWorkflowMcpService,
)


def _service(tmp_path):
    return RivetWorkflowMcpService(
        RivetMcpBinding(
            str(tmp_path), str(tmp_path / "state.db"), "workspace", "session"
        )
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("slug", ["../escape", "UPPER", "two words", "", "a" * 64])
async def test_create_rejects_unsafe_slugs(tmp_path, slug) -> None:
    with pytest.raises(RivetMcpError) as caught:
        await _service(tmp_path).create_workflow(
            {"slug": slug, "templateId": "basic-flow"}
        )
    assert caught.value.code == "RIVET_WORKFLOW_INVALID"


@pytest.mark.asyncio
async def test_create_rejects_duplicate_and_oversized_or_ambiguous_sources(
    tmp_path,
) -> None:
    service = _service(tmp_path)
    await service.create_workflow({"slug": "same", "templateId": "basic-flow"})
    with pytest.raises(RivetMcpError) as duplicate:
        await service.create_workflow({"slug": "same", "templateId": "basic-flow"})
    assert duplicate.value.code == "RIVET_WORKFLOW_EXISTS"
    with pytest.raises(RivetMcpError):
        await service.create_workflow(
            {"slug": "ambiguous", "templateId": "basic-flow", "project": "version: 4"}
        )
    with pytest.raises(RivetMcpError):
        await service.create_workflow(
            {"slug": "large", "project": "x" * (4 * 1024 * 1024 + 1)}
        )


@pytest.mark.asyncio
async def test_validation_fails_closed_on_stale_revision_and_digest(tmp_path) -> None:
    service = _service(tmp_path)
    created = await service.create_workflow(
        {"slug": "fresh", "templateId": "basic-flow"}
    )
    with pytest.raises(RivetMcpError) as stale:
        await service.validate_workflow(
            {
                "slug": "fresh",
                "expectedRevision": 2,
                "expectedDigest": created["workflow"]["digest"],
            }
        )
    assert stale.value.code == "RIVET_WORKFLOW_REVISION_CONFLICT"
    with pytest.raises(RivetMcpError) as changed:
        await service.validate_workflow(
            {"slug": "fresh", "expectedRevision": 1, "expectedDigest": "0" * 64}
        )
    assert changed.value.code == "RIVET_WORKFLOW_REVISION_CONFLICT"


@pytest.mark.asyncio
async def test_workspace_symlink_is_rejected(tmp_path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    workflows = tmp_path / "workflows"
    try:
        os.symlink(outside, workflows, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("host does not permit symlink creation")
    with pytest.raises(RivetMcpError):
        await _service(tmp_path).create_workflow(
            {"slug": "linked", "templateId": "basic-flow"}
        )


def test_binding_requires_absolute_canonical_identity_and_cannot_use_tool_arguments(
    tmp_path,
) -> None:
    binding = RivetMcpBinding.from_environment(
        {
            "WRIGHT_RIVET_MCP_WORKSPACE": str(tmp_path.resolve()),
            "WRIGHT_RIVET_MCP_DATABASE": str((tmp_path / "state.db").resolve()),
            "WRIGHT_RIVET_MCP_WORKSPACE_ID": "workspace-1",
            "WRIGHT_RIVET_MCP_SESSION_ID": "session-1",
        }
    )
    assert binding.workspace_id == "workspace-1"
    with pytest.raises(ValueError):
        RivetMcpBinding.from_environment({})
