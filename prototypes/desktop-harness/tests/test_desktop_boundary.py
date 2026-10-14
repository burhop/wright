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


def test_image_transport_is_opt_in_and_changes_frozen_connection(boundary):
    from desktop_backend import DesktopBackend

    default, service, _ = boundary
    enabled = DesktopBackend(
        service, default.state, 5201, confined_inspection=True, image_inputs=True
    )
    assert default.binding.image_input_profile == "unavailable"
    assert enabled.binding.image_input_profile == "inline-png-jpeg-v1"
    assert enabled.binding.connection_id != default.binding.connection_id
    assert enabled.binding.digest != default.binding.digest


@pytest.fixture
def enrolled_boundary(boundary):
    from desktop_backend import DesktopBackend

    default, service, source = boundary
    enabled = DesktopBackend(service, default.state, 5201, enrolled_mcp_tasks=True)
    service.workflow_sources.read.return_value.source = (
        source.replace("wright-workspace-files", "qualified-provider")
        .replace("inspect_file", "inspect_geometry")
        .replace('"max_tool_calls":1', '"max_tool_calls":2')
    )
    service.workflow_integration_policies.get.return_value["allowed_tools"] = [
        {
            "server_id": "qualified-provider",
            "name": "qualified-provider__inspect_geometry",
            "schema_digest": "d" * 64,
        }
    ]
    return enabled, default, service


def test_enrolled_tasks_are_separate_frozen_opt_in(enrolled_boundary):
    enabled, default, service = enrolled_boundary
    assert enabled.binding.digest != default.binding.digest
    with pytest.raises(HTTPException) as failure:
        check(default)
    assert failure.value.status_code == 503
    service.workflow_integration_policies.get.assert_not_called()
    check(enabled)
    service.workflow_integration_policies.get.assert_called_once_with("b" * 64)


@pytest.mark.parametrize(
    "field,value",
    [
        ("workspace_id", "other"),
        ("source_path", "workflows/other.wflow"),
        ("source_digest", "e" * 64),
        ("approval_mode", "auto"),
        ("allowed_tools", []),
        (
            "allowed_tools",
            [
                {
                    "server_id": "qualified-provider",
                    "name": "qualified-provider__write_geometry",
                }
            ],
        ),
    ],
)
def test_enrolled_tasks_reject_changed_manual_scope(enrolled_boundary, field, value):
    enabled, _, service = enrolled_boundary
    service.workflow_integration_policies.get.return_value[field] = value
    with pytest.raises(HTTPException) as failure:
        check(enabled)
    assert failure.value.status_code == 403


def test_enrolled_tasks_require_grant_and_preserve_image_gate(enrolled_boundary):
    enabled, _, service = enrolled_boundary
    with pytest.raises(HTTPException) as failure:
        check(enabled, grant=False)
    assert failure.value.status_code == 403
    service.workflow_integration_policies.get.assert_not_called()
    document = service.workflow_sources.read.return_value
    document.source = document.source.replace(
        '"kind":"engineering_document"', '"kind":"reference_images"', 2
    )
    with pytest.raises(HTTPException, match="image input"):
        check(enabled)
    service.workflow_integration_policies.get.assert_not_called()


def test_enrolled_tasks_reject_extra_tool(enrolled_boundary):
    enabled, _, service = enrolled_boundary
    service.workflow_integration_policies.get.return_value["allowed_tools"].append(
        {
            "server_id": "qualified-provider",
            "name": "qualified-provider__write_geometry",
        }
    )
    with pytest.raises(HTTPException) as failure:
        check(enabled)
    assert failure.value.status_code == 403


@pytest.mark.parametrize("invalidity", ["revoked", "expired", "unknown"])
def test_enrolled_tasks_use_actual_policy_owner(
    enrolled_boundary, monkeypatch, invalidity
):
    import time
    from workspace_service.workflow_integration_policy import (
        WorkflowIntegrationPolicyService,
    )

    enabled, _, service = enrolled_boundary
    policy = WorkflowIntegrationPolicyService(service.db_path, enabled=True)
    expiry = int(time.time()) + 60
    digest = policy.enroll(
        campaign_id="desktop-boundary-fixture",
        dataset_id="synthetic",
        dataset_digest="c" * 64,
        workspace_id="workspace",
        source_path="workflows/read.workflow.wflow",
        source_digest="a" * 64,
        input_files={"inputs/requirements.md": "c" * 64},
        output_root="outputs/private",
        allowed_tools=service.workflow_integration_policies.get.return_value[
            "allowed_tools"
        ],
        expires_at=expiry,
    )
    service.workflow_integration_policies = policy
    if invalidity == "revoked":
        policy.revoke(digest)
    elif invalidity == "expired":
        monkeypatch.setattr(
            "workspace_service.workflow_integration_policy.time.time", lambda: expiry
        )
    else:
        digest = "0" * 64
    with pytest.raises(HTTPException) as failure:
        asyncio.run(
            enabled.qualify_digital_source(
                {
                    "session_id": "session",
                    "path": "workflows/read.workflow.wflow",
                    "integration_policy_digest": digest,
                },
                operation="/api/workspace/process-interfaces/runs",
            )
        )
    assert failure.value.status_code == 403


def test_image_input_qualification_requires_explicit_profile(boundary):
    from desktop_backend import DesktopBackend

    default, service, source = boundary
    service.workflow_sources.read.return_value.source = source.replace(
        '"kind":"engineering_document"', '"kind":"reference_images"', 2
    )
    with pytest.raises(HTTPException, match="image input"):
        check(default)
    enabled = DesktopBackend(
        service, default.state, 5201, confined_inspection=True, image_inputs=True
    )
    check(enabled)
    assert enabled.binding.digest != default.binding.digest


def test_image_input_profile_does_not_enable_generation(boundary):
    from desktop_backend import DesktopBackend
    from packages.workspace_service.tests.test_workflow_image_outputs import image_task
    from packages.workspace_service.tests.test_workflow_ai_task import source

    default, service, _ = boundary
    service.workflow_sources.read.return_value.source = source(
        image_task(authoring_template="ai-prompt", mcp_server="")
    )
    enabled = DesktopBackend(service, default.state, 5201, image_inputs=True)
    with pytest.raises(HTTPException, match="generation capabilities"):
        check(enabled)
