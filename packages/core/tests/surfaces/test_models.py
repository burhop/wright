from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.surfaces.errors import SurfaceError, SurfaceErrorCode
from core.surfaces.models import (
    DisplaySurfaceSource,
    ExternalUrlSurfaceSource,
    FileSurfaceSource,
    GenerationProvenance,
    InvalidSurfaceTransition,
    LiveAppOwnership,
    LiveAppSurfaceSource,
    McpAppSurfaceSource,
    ProvenanceMode,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceInstanceId,
    SurfaceLifecycle,
    SurfaceRevision,
    SurfaceSourceKind,
    next_generation,
    generation_provenance_from_dict,
    generation_provenance_to_dict,
    require_surface_transition,
)


pytestmark = pytest.mark.workspace_surfaces


def _now() -> datetime:
    return datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _file_source() -> FileSurfaceSource:
    return FileSurfaceSource(
        path="models/bracket.step",
        file_revision="sha256:abc123",
        media_type="model/step",
        provider_id="three-d-viewer",
    )


def test_opaque_surface_identity_is_trimmed_bounded_and_not_a_url() -> None:
    assert str(SurfaceId(" surface-01 ")) == "surface-01"
    assert str(SurfaceInstanceId("instance:01")) == "instance:01"
    with pytest.raises(ValueError, match="must not be empty"):
        SurfaceId(" ")
    with pytest.raises(ValueError, match="opaque"):
        SurfaceId("https://example.test/surface")
    with pytest.raises(ValueError, match="128"):
        SurfaceId("s" * 129)


def test_surface_revision_is_positive_and_monotonic() -> None:
    assert int(SurfaceRevision(1)) == 1
    assert int(SurfaceRevision(7).next()) == 8
    with pytest.raises(ValueError, match="positive"):
        SurfaceRevision(0)


@pytest.mark.parametrize(
    ("source", "kind"),
    [
        (_file_source(), SurfaceSourceKind.FILE),
        (
            DisplaySurfaceSource(
                execution_id="execution-1",
                display_id="loads-chart",
                artifact_revision=3,
                durability="durable",
                media_types=("application/vnd.plotly.v1+json", "text/plain"),
            ),
            SurfaceSourceKind.DISPLAY,
        ),
        (
            LiveAppSurfaceSource(
                manifest_id="brep",
                manifest_version="1.2.0",
                manifest_hash="a" * 64,
                ownership=LiveAppOwnership.WRIGHT_OWNED,
                administrator_approved=True,
                sharing_mode="shared",
            ),
            SurfaceSourceKind.LIVE_APP,
        ),
        (
            McpAppSurfaceSource(
                gateway_session_id="gateway-1",
                server_connection_id="server-1",
                resource_uri="ui://brep/main",
                content_hash="b" * 64,
                protocol_version="2026-01-26",
            ),
            SurfaceSourceKind.MCP_APP,
        ),
        (
            ExternalUrlSurfaceSource(
                normalized_url="https://docs.example.test/guide",
                approval_id="approval-1",
                view_only=True,
            ),
            SurfaceSourceKind.EXTERNAL_URL,
        ),
    ],
)
def test_all_source_discriminators_are_explicit(source, kind) -> None:
    assert source.kind is kind
    assert source.source_version


@pytest.mark.parametrize(
    "path",
    ["../secret.txt", "/absolute.txt", "C:/escape.txt", "models/../../secret"],
)
def test_file_source_rejects_paths_outside_the_workspace(path: str) -> None:
    with pytest.raises(ValueError, match="workspace-relative"):
        FileSurfaceSource(
            path=path,
            file_revision="revision-1",
            media_type="text/plain",
            provider_id="text-viewer",
        )


def test_mcp_source_requires_ui_uri_and_server_scoped_identity() -> None:
    with pytest.raises(ValueError, match="ui://"):
        McpAppSurfaceSource(
            gateway_session_id="gateway-1",
            server_connection_id="server-1",
            resource_uri="https://example.test/app",
            content_hash="c" * 64,
            protocol_version="2026-01-26",
        )
    with pytest.raises(ValueError, match="server_connection_id"):
        McpAppSurfaceSource(
            gateway_session_id="gateway-1",
            server_connection_id=" ",
            resource_uri="ui://brep/main",
            content_hash="c" * 64,
            protocol_version="2026-01-26",
        )


def test_external_url_is_always_view_only_and_credential_free() -> None:
    with pytest.raises(ValueError, match="view-only"):
        ExternalUrlSurfaceSource(
            normalized_url="https://docs.example.test",
            approval_id="approval-1",
            view_only=False,
        )
    with pytest.raises(ValueError, match="credentials"):
        ExternalUrlSurfaceSource(
            normalized_url="https://user:secret@docs.example.test",
            approval_id="approval-1",
            view_only=True,
        )


def test_surface_descriptor_validates_schema_scope_title_and_time() -> None:
    descriptor = SurfaceDescriptor(
        schema_version=1,
        surface_id=SurfaceId("surface-1"),
        workspace_id="workspace-1",
        source=_file_source(),
        title="Bracket",
        lifecycle=SurfaceLifecycle.DECLARED,
        revision=SurfaceRevision(1),
        created_at=_now(),
        updated_at=_now(),
    )
    assert descriptor.surface_id == SurfaceId("surface-1")
    assert descriptor.source.kind is SurfaceSourceKind.FILE
    with pytest.raises(ValueError, match="schema_version"):
        SurfaceDescriptor(
            schema_version=2,
            surface_id=SurfaceId("surface-2"),
            workspace_id="workspace-1",
            source=_file_source(),
            title="Bracket",
            lifecycle=SurfaceLifecycle.DECLARED,
            revision=SurfaceRevision(1),
            created_at=_now(),
            updated_at=_now(),
        )
    with pytest.raises(ValueError, match="updated_at"):
        SurfaceDescriptor(
            schema_version=1,
            surface_id=SurfaceId("surface-2"),
            workspace_id="workspace-1",
            source=_file_source(),
            title="Bracket",
            lifecycle=SurfaceLifecycle.DECLARED,
            revision=SurfaceRevision(1),
            created_at=_now(),
            updated_at=datetime(2026, 7, 29, tzinfo=UTC),
        )


def test_lifecycle_transition_matrix_is_exhaustive() -> None:
    allowed = {
        SurfaceLifecycle.DECLARED: {
            SurfaceLifecycle.STARTING,
            SurfaceLifecycle.STOPPED,
        },
        SurfaceLifecycle.STARTING: {
            SurfaceLifecycle.READY,
            SurfaceLifecycle.FAILED,
            SurfaceLifecycle.STOPPING,
        },
        SurfaceLifecycle.READY: {
            SurfaceLifecycle.UNHEALTHY,
            SurfaceLifecycle.STOPPING,
            SurfaceLifecycle.FAILED,
        },
        SurfaceLifecycle.UNHEALTHY: {
            SurfaceLifecycle.READY,
            SurfaceLifecycle.STOPPING,
            SurfaceLifecycle.FAILED,
        },
        SurfaceLifecycle.STOPPING: {
            SurfaceLifecycle.STOPPED,
            SurfaceLifecycle.FAILED,
        },
        SurfaceLifecycle.STOPPED: {SurfaceLifecycle.STARTING},
        SurfaceLifecycle.FAILED: {SurfaceLifecycle.STARTING},
    }
    assert set(allowed) == set(SurfaceLifecycle)
    for current in SurfaceLifecycle:
        for target in SurfaceLifecycle:
            if target in allowed[current]:
                assert require_surface_transition(current, target) is target
            else:
                with pytest.raises(InvalidSurfaceTransition):
                    require_surface_transition(current, target)


def test_new_generation_is_created_only_when_restarting_terminal_state() -> None:
    assert next_generation(SurfaceLifecycle.STOPPED, 4) == 5
    assert next_generation(SurfaceLifecycle.FAILED, 4) == 5
    with pytest.raises(InvalidSurfaceTransition):
        next_generation(SurfaceLifecycle.READY, 4)


def test_generation_provenance_distinguishes_prompt_from_direct_execution() -> None:
    generated = GenerationProvenance(
        mode=ProvenanceMode.AGENT_GENERATED,
        prompt="Plot the measured load by time.",
        no_prompt=False,
        effective_constraints={"units": "N", "offline": True},
        script_vault_digest="sha256:" + "d" * 64,
        script_content_hash="e" * 64,
        script_revision=2,
        task_id="task-1",
        execution_id="execution-1",
        trace_id="trace-1",
        created_at=_now(),
    )
    assert generated.prompt.startswith("Plot")
    assert generation_provenance_from_dict(
        generation_provenance_to_dict(generated)
    ) == generated
    direct = GenerationProvenance(
        mode=ProvenanceMode.DIRECT_EXECUTION,
        prompt=None,
        no_prompt=True,
        effective_constraints={"offline": True},
        script_vault_digest="sha256:" + "f" * 64,
        script_content_hash="a" * 64,
        script_revision=1,
        task_id="task-2",
        execution_id="execution-2",
        trace_id="trace-2",
        created_at=_now(),
    )
    assert direct.no_prompt is True
    with pytest.raises(ValueError, match="no-prompt"):
        GenerationProvenance(
            mode=ProvenanceMode.DIRECT_EXECUTION,
            prompt="invented prompt",
            no_prompt=False,
            effective_constraints={},
            script_vault_digest="sha256:" + "f" * 64,
            script_content_hash="a" * 64,
            script_revision=1,
            task_id="task-3",
            execution_id="execution-3",
            trace_id="trace-3",
            created_at=_now(),
        )


def test_surface_errors_have_stable_codes_safe_context_and_retryability() -> None:
    error = SurfaceError(
        code=SurfaceErrorCode.STALE_REVISION,
        message="The surface changed; refresh and retry.",
        retryable=True,
        correlation_id="correlation-1",
        context={"expected_revision": 1, "token": "secret"},
    )
    assert error.code == "SURFACE_STATE_STALE_REVISION"
    assert error.retryable is True
    assert error.as_dict() == {
        "code": "SURFACE_STATE_STALE_REVISION",
        "message": "The surface changed; refresh and retry.",
        "retryable": True,
        "correlation_id": "correlation-1",
        "context": {"expected_revision": 1, "token": "[REDACTED]"},
    }
    assert "secret" not in repr(error)
