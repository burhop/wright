import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from fastapi import HTTPException
import pytest


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_backend import DesktopBackend
    from gateway_probe import SOURCE

    root = tmp_path / "workspaces" / "private"
    root.mkdir(parents=True)
    row = {
        "workspace_id": "workspace",
        "session_id": "session",
        "local_path": str(root),
    }
    service = SimpleNamespace(
        db_path=str(tmp_path / "wright.sqlite"),
        repository=SimpleNamespace(
            get_by_session=Mock(return_value=row),
            list_sessions=Mock(
                return_value=[
                    {"session_id": "session", "agent_id": "openai-desktop-harness"}
                ]
            ),
        ),
        workflow_sources=SimpleNamespace(
            read=AsyncMock(
                return_value=SimpleNamespace(
                    source=SOURCE,
                    path="workflows/read.workflow.wflow",
                    storage_digest="a" * 64,
                )
            )
        ),
        workflow_integration_policies=SimpleNamespace(
            get=Mock(
                return_value={
                    "workspace_id": "workspace",
                    "source_path": "workflows/read.workflow.wflow",
                    "source_digest": "a" * 64,
                    "approval_mode": "manual",
                    "allowed_tools": [
                        {
                            "server_id": "wright-workspace-files",
                            "name": "wright-workspace-files__inspect_file",
                        }
                    ],
                }
            )
        ),
    )
    backend = DesktopBackend(service, tmp_path, 5201, confined_inspection=True)
    return backend, service, SOURCE


def check(backend, *, grant=True):
    body = {"session_id": "session", "path": "workflows/read.workflow.wflow"}
    if grant:
        body["integration_policy_digest"] = "b" * 64
    asyncio.run(
        backend.qualify_digital_source(
            body, operation="/api/workspace/process-interfaces/runs"
        )
    )


def test_readonly_source_without_private_grant_is_denied(boundary):
    backend, service, _ = boundary
    with pytest.raises(HTTPException) as failure:
        check(backend, grant=False)
    assert failure.value.status_code == 403
    service.workflow_integration_policies.get.assert_not_called()


@pytest.mark.parametrize(
    "operation",
    [
        "/api/workspace/process-interfaces/inputs",
        "/api/workspace/process-interfaces/readiness",
        "/api/workspace/process-interfaces/runs",
    ],
)
def test_original_image_input_is_unavailable_before_prepare_or_dispatch(
    boundary, operation
):
    backend, service, source = boundary
    image_source = source.replace(
        '"kind":"engineering_document"', '"kind":"reference_images"', 2
    ).replace('"inputs/requirements.md"', '"inputs/original-sketch.png"')
    service.workflow_sources.read.return_value.source = image_source
    with pytest.raises(HTTPException, match="image input") as failure:
        asyncio.run(
            backend.qualify_digital_source(
                {"session_id": "session", "path": "workflows/read.workflow.wflow"},
                operation=operation,
            )
        )
    assert failure.value.status_code == 503
    service.workflow_integration_policies.get.assert_not_called()


def test_native_image_generation_is_explicitly_unavailable(boundary):
    from packages.workspace_service.tests.test_workflow_image_outputs import image_task
    from packages.workspace_service.tests.test_workflow_ai_task import source

    backend, service, _ = boundary
    service.workflow_sources.read.return_value.source = source(
        image_task(authoring_template="ai-prompt", mcp_server="")
    )
    with pytest.raises(HTTPException, match="generation capabilities") as failure:
        check(backend)
    assert failure.value.status_code == 503
    service.workflow_integration_policies.get.assert_not_called()


@pytest.mark.parametrize(
    "old,new",
    [
        ('"inspect_file"', '"write_text_document"'),
        ('"wright-workspace-files"', '"other-provider"'),
        ('"max_tool_calls":1', '"max_tool_calls":2'),
    ],
)
def test_other_tool_scope_is_denied_before_private_policy_lookup(boundary, old, new):
    backend, service, source = boundary
    service.workflow_sources.read.return_value.source = source.replace(old, new)
    with pytest.raises(HTTPException) as failure:
        check(backend)
    assert failure.value.status_code == 503
    service.workflow_integration_policies.get.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("workspace_id", "other-workspace"),
        ("source_digest", "c" * 64),
        ("approval_mode", "integration_test_auto"),
        (
            "allowed_tools",
            [
                {
                    "server_id": "wright-workspace-files",
                    "name": "wright-workspace-files__copy_file",
                }
            ],
        ),
    ],
)
def test_grant_cannot_expand_the_qualified_boundary(boundary, field, value):
    backend, service, _ = boundary
    service.workflow_integration_policies.get.return_value[field] = value
    with pytest.raises(HTTPException) as failure:
        check(backend)
    assert failure.value.status_code == 403


def test_capability_flag_is_frozen_in_connection_identity(boundary):
    from desktop_backend import DesktopBackend

    enabled, service, _ = boundary
    disabled = DesktopBackend(service, enabled.state, 5201, confined_inspection=False)
    assert enabled.binding.digest != disabled.binding.digest
    with pytest.raises(HTTPException) as failure:
        check(disabled)
    assert failure.value.status_code == 503
