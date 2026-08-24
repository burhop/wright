from __future__ import annotations

import os
import sqlite3

import pytest

from data_vault import WorkspaceArtifactRepository, upgrade_database
from tool_registry.gateway_models import GatewayError, GatewaySessionContext
from workspace_service.workspace_document_artifacts import (
    MAX_DOCUMENT_BYTES,
    WorkspaceDocumentArtifactService,
)
from workspace_service.workspace_document_gateway import (
    WorkspaceDocumentGatewayProvider,
)


def _fixture(tmp_path):
    database = tmp_path / "state.db"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('w1', 's1', ?, 1, 1)""",
            (str(workspace),),
        )
        connection.commit()
    service = WorkspaceDocumentArtifactService(
        WorkspaceArtifactRepository(str(database))
    )
    session = GatewaySessionContext(
        "gateway-s1", "p1", "w1", str(workspace), "legacy", binding_session_id="s1"
    )
    return database, workspace, service, session


@pytest.mark.asyncio
async def test_provider_requires_explicit_gate_and_returns_verified_resource_link(
    tmp_path,
) -> None:
    _database, workspace, artifacts, session = _fixture(tmp_path)
    provider = WorkspaceDocumentGatewayProvider(artifacts)
    tool = provider.tools(session)[0]
    arguments = {
        "relativePath": "reports/review.md",
        "content": "# Review\n",
        "mediaType": "text/markdown",
        "overwrite": False,
    }

    with pytest.raises(GatewayError, match="approval"):
        await provider.call(
            session,
            tool,
            arguments,
            request_id="request-denied",
            approval_context={},
            progress_callback=None,
        )
    result = await provider.call(
        session,
        tool,
        arguments,
        request_id="request-1",
        approval_context={
            "workspace_approvals": ["workspace_write_approval"],
            "correlation_id": "trace-1",
        },
        progress_callback=None,
    )

    assert (workspace / "reports" / "review.md").read_text(
        encoding="utf-8"
    ) == "# Review\n"
    structured = result["structuredContent"]
    assert structured["relativePath"] == "reports/review.md"
    assert structured["bytes"] == 9
    assert len(structured["sha256"]) == 64
    assert (
        result["content"][0]["uri"]
        == f"wright://artifact/w1/{structured['artifactId']}"
    )
    assert (
        artifacts.read_resource(session, result["content"][0]["uri"]).content
        == b"# Review\n"
    )


@pytest.mark.asyncio
async def test_provider_never_overwrites_an_existing_document(tmp_path) -> None:
    _database, workspace, artifacts, session = _fixture(tmp_path)
    provider = WorkspaceDocumentGatewayProvider(artifacts)
    tool = provider.tools(session)[0]
    target = workspace / "report.txt"
    target.write_text("original", encoding="utf-8")

    with pytest.raises(GatewayError, match="already exists"):
        await provider.call(
            session,
            tool,
            {
                "relativePath": "report.txt",
                "content": "replacement",
                "mediaType": "text/plain",
                "overwrite": False,
            },
            request_id="request-1",
            approval_context={"workspace_approvals": ["workspace_write_approval"]},
            progress_callback=None,
        )
    assert target.read_text(encoding="utf-8") == "original"
    assert not [item for item in workspace.iterdir() if ".wright-" in item.name]


@pytest.mark.asyncio
async def test_artifact_read_fails_closed_when_published_bytes_change(tmp_path) -> None:
    _database, workspace, artifacts, session = _fixture(tmp_path)
    provider = WorkspaceDocumentGatewayProvider(artifacts)
    result = await provider.call(
        session,
        provider.tools(session)[0],
        {
            "relativePath": "report.txt",
            "content": "reviewed",
            "mediaType": "text/plain",
            "overwrite": False,
        },
        request_id="request-1",
        approval_context={"workspace_approvals": ["workspace_write_approval"]},
        progress_callback=None,
    )
    uri = result["content"][0]["uri"]
    (workspace / "report.txt").write_text("changed", encoding="utf-8")

    with pytest.raises(GatewayError, match="integrity"):
        artifacts.read_resource(session, uri)


def test_publication_compensates_exact_file_when_registration_fails(tmp_path) -> None:
    _database, workspace, _artifacts, session = _fixture(tmp_path)

    class RejectingRepository:
        def insert(self, _record) -> None:
            raise sqlite3.OperationalError("registration unavailable")

    artifacts = WorkspaceDocumentArtifactService(RejectingRepository())
    with pytest.raises(sqlite3.OperationalError, match="registration unavailable"):
        artifacts.publish(
            session=session,
            relative_path="reports/review.md",
            content="reviewed",
            media_type="text/markdown",
            overwrite=False,
            request_id="request-1",
            correlation_id="trace-1",
        )

    assert not (workspace / "reports" / "review.md").exists()
    assert not list((workspace / "reports").glob("*.wright-*.tmp"))


@pytest.mark.parametrize(
    "relative_path, media_type",
    [
        ("../outside.txt", "text/plain"),
        ("/absolute.txt", "text/plain"),
        ("C:/drive.txt", "text/plain"),
        ("//server/share.txt", "text/plain"),
        ("https://example.test/report.txt", "text/plain"),
        ("report.txt:stream", "text/plain"),
        (".hidden/report.txt", "text/plain"),
        (".git/config.txt", "text/plain"),
        (".wright/report.txt", "text/plain"),
        ("CON.txt", "text/plain"),
        ("part.par", "text/plain"),
        ("mesh.stl", "text/plain"),
        ("report.pdf", "application/pdf"),
    ],
)
def test_document_publication_rejects_unsafe_or_native_targets(
    tmp_path, relative_path, media_type
) -> None:
    _database, workspace, artifacts, session = _fixture(tmp_path)
    with pytest.raises(ValueError):
        artifacts.publish(
            session=session,
            relative_path=relative_path,
            content="safe text",
            media_type=media_type,
            overwrite=False,
            request_id="request-1",
            correlation_id="trace-1",
        )
    assert list(workspace.rglob("*")) == []


def test_document_publication_rejects_oversize_and_symlink_paths(tmp_path) -> None:
    _database, workspace, artifacts, session = _fixture(tmp_path)
    with pytest.raises(ValueError, match="byte limit"):
        artifacts.publish(
            session=session,
            relative_path="large.txt",
            content="x" * (MAX_DOCUMENT_BYTES + 1),
            media_type="text/plain",
            overwrite=False,
            request_id="request-1",
            correlation_id="trace-1",
        )
    if hasattr(os, "symlink"):
        outside = tmp_path / "outside"
        outside.mkdir()
        try:
            os.symlink(outside, workspace / "linked", target_is_directory=True)
        except OSError:
            return
        with pytest.raises(ValueError, match="symbolic links|reparse"):
            artifacts.publish(
                session=session,
                relative_path="linked/report.txt",
                content="safe",
                media_type="text/plain",
                overwrite=False,
                request_id="request-2",
                correlation_id="trace-2",
            )
