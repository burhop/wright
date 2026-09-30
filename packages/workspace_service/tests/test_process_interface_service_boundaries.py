"""Application scopes and errors do not rely on browser identity or HTTP types."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.process_interactions import ProcessRef
from workspace_service.process_interfaces.errors import (
    ProcessInterfaceError,
    safe_diagnostic,
)
from workspace_service.process_interfaces.limits import ProcessInterfaceLimits
from workspace_service.process_interfaces.service import (
    ProcessInterfaceService,
    ProcessScope,
)

DIGEST = "a" * 64


def process(**changes):
    return ProcessRef(
        **{
            "workspace_id": "workspace",
            "source_path": "workflows/analysis.wflow",
            "source_digest": DIGEST,
            **changes,
        }
    )


def service(tmp_path):
    sources = SimpleNamespace(
        read=AsyncMock(
            return_value=SimpleNamespace(
                storage_digest=DIGEST,
                source="accepted source",
                path="workflows/analysis.wflow",
            )
        )
    )
    workspaces = SimpleNamespace(
        get_by_id=lambda identifier: (
            {"local_path": str(tmp_path)} if identifier == "workspace" else None
        )
    )
    owner = SimpleNamespace(
        db_path=tmp_path / "state.db",
        repository=workspaces,
        workflow_sources=sources,
        ensure_workspace_path_safe=lambda path: None,
    )
    return ProcessInterfaceService(owner), sources


def scope(**changes):
    return ProcessScope(
        **{
            "principal_id": "user",
            "workspace_id": "workspace",
            "capabilities": frozenset({"process.read"}),
            **changes,
        }
    )


@pytest.mark.asyncio
async def test_source_read_uses_existing_owner_and_accepted_digest(tmp_path):
    app, sources = service(tmp_path)
    resolved = await app.resolve_process(scope(), process())
    assert resolved.document.source == "accepted source"
    assert resolved.process == process()
    assert resolved.workspace_dir == str(tmp_path)
    sources.read.assert_awaited_once_with(str(tmp_path), "workflows/analysis.wflow")


@pytest.mark.asyncio
async def test_scope_mismatch_rejects_before_reading_any_source(tmp_path):
    app, sources = service(tmp_path)
    with pytest.raises(ProcessInterfaceError) as exc:
        await app.resolve_process(scope(workspace_id="other"), process())
    assert exc.value.reason.code == "SCOPE_DENIED"
    assert exc.value.reason.correction
    sources.read.assert_not_awaited()
    with pytest.raises(ProcessInterfaceError):
        await app.resolve_process(scope(capabilities=frozenset()), process())
    sources.read.assert_not_awaited()


@pytest.mark.asyncio
async def test_changed_source_requires_repreparation_not_silent_rebinding(tmp_path):
    app, sources = service(tmp_path)
    sources.read.return_value.storage_digest = "b" * 64
    with pytest.raises(ProcessInterfaceError) as exc:
        await app.resolve_process(scope(), process())
    assert exc.value.reason.code == "SOURCE_CHANGED"
    assert exc.value.reason.navigation.kind == "process"


@pytest.mark.asyncio
async def test_unknown_source_contract_is_explicitly_unsupported(tmp_path):
    app, sources = service(tmp_path)
    with pytest.raises(ProcessInterfaceError) as exc:
        await app.resolve_process(scope(), process(source_contract="unqualified-graph"))
    assert exc.value.reason.code == "READINESS_UNSUPPORTED"
    sources.read.assert_not_awaited()


def test_scope_has_closed_capabilities_and_no_empty_principal():
    for changes in (
        {"principal_id": ""},
        {"workspace_id": ""},
        {"capabilities": frozenset({"invokeTool"})},
    ):
        with pytest.raises(ValueError):
            scope(**changes)


def test_diagnostics_are_redacted_and_bounded():
    diagnostic = safe_diagnostic(
        {
            "authorization": "Bearer secret",
            "argv": ["token=abc"],
            "message": "password=xyz " + "x" * 8000,
        }
    )
    assert (
        "secret" not in str(diagnostic)
        and "abc" not in str(diagnostic)
        and "xyz" not in str(diagnostic)
    )
    assert len(diagnostic["message"]) <= 4096


def test_limits_are_owned_by_wright_and_reject_invalid_bounds():
    limits = ProcessInterfaceLimits()
    assert limits.compiler_timeout_seconds == 120
    assert limits.maximum_repairs == 2
    for changes in (
        {"maximum_repairs": 3},
        {"maximum_upload_bytes": 0},
        {"compiler_timeout_seconds": float("inf")},
    ):
        with pytest.raises(ValueError):
            replace(limits, **changes)


def test_service_repositories_are_lazy_and_share_existing_database(tmp_path):
    app, _ = service(tmp_path)
    assert not (tmp_path / "state.db").exists()
    assert app.inputs.db_path == app.interfaces.db_path == tmp_path / "state.db"
