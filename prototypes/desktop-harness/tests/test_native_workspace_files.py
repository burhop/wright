"""Read-only native presentation with real file/source owners and isolated state."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI

from data_vault import WorkspaceRepository, upgrade_database
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases
from workspace_service.use_cases.lifecycle import WorkspaceLifecycleUseCases
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases


PROTOTYPE = Path(__file__).resolve().parents[1]
REPO = PROTOTYPE.parents[1]
SOURCE = 'workflow file_test\n  name: "File test"\n  purpose: "Inspect without execution"\n  discipline: "mechanical.design"\n  reviewed_ai_suggestions: true\nend\n'
# Only signature classification is qualified here, not image decoder fidelity.
PNG = b"\x89PNG\r\n\x1a\nfixture"


@pytest_asyncio.fixture
async def native_files(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(PROTOTYPE))
    from desktop_backend import DesktopBackend

    database = str(tmp_path / "state.db")
    upgrade_database(database)
    secrets = Mock()
    secrets.get.side_effect = AssertionError("No credential reads")
    secrets.set.side_effect = AssertionError("No credential writes")
    repository = WorkspaceRepository(database, secrets=secrets)
    executor = BoundedExecutor()
    service = SimpleNamespace(
        db_path=database,
        repository=repository,
        lifecycle=WorkspaceLifecycleUseCases(repository),
        workflow_sources=WorkspaceWorkflowSourceUseCases(executor),
        files=WorkspaceFileUseCases(
            database, executor, LocalWorkspaceFiles, repository=repository
        ),
    )
    backend = DesktopBackend(
        service, tmp_path, 5210, native_editor=True, native_workspace_files=True
    )
    backend.clients["isolated-test"] = backend._now() + 3600
    app = FastAPI()
    app.include_router(backend.router())

    def create(name="alpha", *, agent="openai-desktop-harness", outside=False):
        root = tmp_path / ("outside" if outside else "workspaces") / name
        root.mkdir(parents=True)
        repository.create(
            name, "desktop-" + name, str(root), workspace_name=name, agent_id=agent
        )
        repository.associate_session(name, "desktop-" + name, agent_id=agent)
        return root

    root = create()
    scope = {"workspace_id": "alpha", "session_id": "desktop-alpha"}
    accepted = await service.workflow_sources.create(
        str(root), "workflows/file.workflow.wflow", SOURCE
    )
    (root / "preview.png").write_bytes(PNG)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app), base_url="http://test"
    ) as client:
        yield SimpleNamespace(
            app=app,
            client=client,
            root=root,
            state=tmp_path,
            scope=scope,
            accepted=accepted,
            backend=backend,
            create=create,
            repository=repository,
            service=service,
            secrets=secrets,
        )
    await executor.close()
    assert not secrets.mock_calls


async def describe(fixture, path, **extra):
    return await fixture.client.post(
        "/api/desktop/native-files/describe",
        json={
            **fixture.scope,
            "path": path,
            **extra,
        },
    )


async def resolve(fixture, path, **extra):
    return await fixture.client.post(
        "/api/desktop/native-files/context",
        json={
            "absolute_path": str(path),
            **extra,
        },
    )


def snapshot(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.asyncio
async def test_exact_source_and_image_round_trip_without_source_or_scope_writes(
    native_files,
):
    f = native_files
    files_before = snapshot(f.root)
    repository_before = f.repository.list_all()
    sessions_before = f.repository.list_sessions("alpha")
    for path, viewer in [(f.accepted.path, "workflow"), ("preview.png", "image")]:
        result = await describe(f, path)
        assert result.status_code == 200, result.text
        document = result.json()
        assert document["supported"] is True and document["viewer"] == viewer
        assert document["path"] == path
        assert document["sha256"] == files_before[path]
        assert document["absolute_path"] == str(f.root / path)
        reopened = await resolve(f, f.root / path)
        assert reopened.status_code == 200 and reopened.json() == document
    assert document["bytes"] == len(PNG)
    assert snapshot(f.root) == files_before
    assert f.repository.list_all() == repository_before
    assert f.repository.list_sessions("alpha") == sessions_before
    assert not (f.root / "runs").exists()


@pytest.mark.asyncio
async def test_substantially_different_existing_sources_use_same_owner(native_files):
    f = native_files
    fixtures = [
        REPO
        / "specs/080-canonical-workflow-recovery/fixtures/mounting-bracket.workflow.wflow",
        REPO
        / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/robot-tracking-diagnosis.workflow.wflow",
    ]
    for source in fixtures:
        accepted = await f.service.workflow_sources.create(
            str(f.root), "workflows/" + source.name, source.read_text()
        )
        before = snapshot(f.root)
        response = await describe(
            f, accepted.path, expected_sha256=accepted.storage_digest
        )
        assert response.status_code == 200, response.text
        assert response.json()["definition_revision"] == accepted.definition_revision
        assert snapshot(f.root) == before


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "patch",
    [
        {"workspace_id": "foreign"},
        {"session_id": "foreign"},
        {"session_id": "desktop-beta"},
    ],
)
async def test_scope_is_exact_and_never_rebound(native_files, patch):
    f = native_files
    f.create("beta")
    before = f.repository.list_all()
    response = await describe(f, f.accepted.path, **patch)
    assert response.status_code == 403
    assert f.repository.list_all() == before


@pytest.mark.asyncio
async def test_wrong_agent_and_outside_managed_root_rejected(native_files):
    f = native_files
    for name, kwargs in [
        ("hermes", {"agent": "hermes"}),
        ("outside", {"outside": True}),
    ]:
        root = f.create(name, **kwargs)
        (root / "preview.png").write_bytes(PNG)
        response = await describe(
            f, "preview.png", workspace_id=name, session_id="desktop-" + name
        )
        assert response.status_code == 403
        assert (await resolve(f, root / "preview.png")).status_code in {403, 409}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "../state.db",
        "/etc/passwd",
        "C:\\Windows\\file",
        "\\\\server\\share\\file",
        "preview.png:stream",
        ".hidden/secret",
        "freecad_mcp_work/private.png",
        "workflows//file.workflow.wflow",
        "workflows/./file.workflow.wflow",
        "bad\nname",
        "missing.png",
        "workflows",
    ],
)
async def test_hidden_invalid_missing_and_nonregular_files_fail_without_paths(
    native_files, path
):
    response = await describe(native_files, path)
    assert response.status_code == 422, response.text
    assert (
        str(native_files.root) not in response.text and "state.db" not in response.text
    )


@pytest.mark.asyncio
async def test_links_and_host_paths_cannot_escape_scope(native_files):
    f = native_files
    private = f.state / "private.png"
    private.write_bytes(PNG)
    try:
        (f.root / "alias.png").symlink_to(private)
    except OSError as error:
        pytest.skip(f"Host cannot create symlink fixture: {error.__class__.__name__}")
    for path in ["alias.png", "../private.png"]:
        assert (await describe(f, path)).status_code == 422
    for path in [private, "relative.png", f.root / ".." / ".." / "private.png"]:
        assert (await resolve(f, path)).status_code in {403, 422}


@pytest.mark.asyncio
async def test_size_limit_and_opaque_unaccepted_workflow_fail_closed(native_files):
    f = native_files
    with (f.root / "large.png").open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    assert (await describe(f, "large.png")).status_code == 422
    (f.root / "workflows/unaccepted.workflow.wflow").write_text(SOURCE)
    before = snapshot(f.root)
    response = await describe(f, "workflows/unaccepted.workflow.wflow")
    assert response.status_code == 409
    after = snapshot(f.root)
    lock = ".wright/workflow-sources/unaccepted/.lock"
    assert set(after) - set(before) == {lock}
    assert {path: digest for path, digest in after.items() if path != lock} == before
    assert (f.root / lock).read_bytes() == b"\x00"


@pytest.mark.asyncio
async def test_opaque_uploaded_workflow_keeps_read_only_file_fallback(native_files):
    f = native_files
    content = SOURCE.encode()
    path = await f.service.files.stage_upload(
        str(f.root), "incoming.wflow", content, hashlib.sha256(content).hexdigest()
    )
    before = snapshot(f.root)
    result = await describe(f, path)
    assert result.status_code == 200 and result.json()["supported"] is False
    assert "absolute_path" not in result.json()
    assert snapshot(f.root) == before


@pytest.mark.asyncio
async def test_extension_does_not_claim_unqualified_viewer(native_files):
    f = native_files
    for path, content in [("part.step", b"ISO-10303-21;"), ("fake.png", b"text")]:
        (f.root / path).write_bytes(content)
        response = await describe(f, path)
        assert response.status_code == 200
        assert response.json()["supported"] is False
        assert (
            "absolute_path" not in response.json() and "viewer" not in response.json()
        )


@pytest.mark.asyncio
async def test_stale_pin_and_source_mutation_remain_visible(native_files):
    f = native_files
    assert (
        await describe(f, "preview.png", expected_sha256="a" * 64)
    ).status_code == 409
    (f.root / f.accepted.path).write_text(SOURCE + "\n# external change\n")
    assert (await describe(f, f.accepted.path)).status_code == 409


@pytest.mark.asyncio
async def test_ambiguous_fresh_scope_requires_exact_remembered_session(native_files):
    f = native_files
    f.repository.associate_session(
        "alpha", "desktop-other", agent_id="openai-desktop-harness"
    )
    before = f.repository.list_sessions("alpha")
    path = f.root / f.accepted.path
    assert (await resolve(f, path)).status_code == 409
    remembered = {
        **f.scope,
        "path": f.accepted.path,
        "expected_sha256": f.accepted.storage_digest,
    }
    result = await resolve(f, path, resume=remembered)
    assert result.status_code == 200 and result.json()["session_id"] == "desktop-alpha"
    assert (
        await resolve(f, f.root / "preview.png", resume=remembered)
    ).status_code == 403
    assert f.repository.list_sessions("alpha") == before


@pytest.mark.asyncio
async def test_connection_and_closed_schema_and_feature_gate(native_files):
    f = native_files
    assert (await describe(f, "preview.png", authority="admin")).status_code == 422
    f.backend.clients.clear()
    assert (await describe(f, "preview.png")).status_code == 503
    from desktop_backend import DesktopBackend

    with pytest.raises(ValueError, match="require the native editor"):
        DesktopBackend(f.service, f.state, 5210, native_workspace_files=True)
    disabled = FastAPI()
    disabled.include_router(DesktopBackend(f.service, f.state, 5210).router())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(disabled), base_url="http://test"
    ) as client:
        assert (
            await client.post("/api/desktop/native-files/describe", json={})
        ).status_code == 404


@pytest.mark.asyncio
async def test_runtime_freezes_new_boundary(native_files):
    versions = json.loads((native_files.state / "desktop-versions.json").read_text())
    assert versions["native_workspace_files"] is True
    assert (
        versions["files"]["native_workspace_files"]
        == hashlib.sha256(
            (PROTOTYPE / "native_workspace_files.py").read_bytes()
        ).hexdigest()
    )


@pytest.mark.asyncio
async def test_disappeared_workspace_root_is_a_scope_denial(native_files):
    f = native_files
    root = f.create("gone")
    root.rmdir()
    response = await describe(
        f, "preview.png", workspace_id="gone", session_id="desktop-gone"
    )
    assert response.status_code == 403 and str(root) not in response.text


@pytest.mark.asyncio
async def test_remembered_other_workspace_never_retargets_host_file(native_files):
    f = native_files
    root = f.create("beta")
    (root / "preview.png").write_bytes(PNG)
    response = await resolve(
        f,
        f.root / "preview.png",
        resume={
            "workspace_id": "beta",
            "session_id": "desktop-beta",
            "path": "preview.png",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_real_mcp_http_owner_path_and_continuation(native_files, monkeypatch):
    f = native_files
    from mcp_bridge import WrightDesktopClient, server
    from api.routers.workspace import (
        read_workflow_source_endpoint,
        get_workspace_service,
    )
    from api.schemas.workspace import WorkflowSourceResponse

    # Use the production source endpoint, production MCP client and real owners.
    # ASGI substitutes transport only; no sockets, live API or credentials.
    f.service.ensure_workspace_path_safe = lambda path: str(
        Path(path).resolve(strict=True)
    )
    f.app.dependency_overrides[get_workspace_service] = lambda: f.service
    f.app.add_api_route(
        "/api/workspace/workflow-sources",
        read_workflow_source_endpoint,
        methods=["GET"],
        response_model=WorkflowSourceResponse,
    )
    bridge_client = WrightDesktopClient.__new__(WrightDesktopClient)
    bridge_client.http = f.client
    bridge = server(bridge_client, native_editor=True, native_workspace_files=True)
    tools = {tool.name: tool for tool in await bridge.list_tools()}
    for name in [
        "wright_workspace_file_describe",
        "wright_workflow_file",
        "wright_workflow_file_context",
    ]:
        assert tools[name].annotations.readOnlyHint
        assert tools[name].meta["ui"]["visibility"] == ["app"]
    assert tools["wright_workflow_file"].meta["openai/ui"]["entrypoints"] == [
        {"type": "file", "extensions": [".wflow"]},
    ]
    before = snapshot(f.root)
    body = {**f.scope, "path": f.accepted.path}
    descriptor = (
        await bridge.call_tool("wright_workspace_file_describe", {"request": body})
    )[1]
    assert descriptor["sha256"] == f.accepted.storage_digest
    opened = (await bridge.call_tool("wright_workflow_open", body))[1]
    assert opened["native_workspace_files_enabled"] is True
    assert opened["document"]["storage_digest"] == f.accepted.storage_digest
    metadata = {"openai/resource": {"path": str(f.root / f.accepted.path)}}
    monkeypatch.setattr(
        bridge,
        "get_context",
        lambda: SimpleNamespace(
            request_context=SimpleNamespace(meta=metadata),
        ),
    )
    file_input = {
        "file": {"name": "file.workflow.wflow", "resourceUri": "opaque:not-a-path"}
    }
    assert (await bridge.call_tool("wright_workflow_file", file_input))[1]["file"][
        "resourceUri"
    ] == "opaque:not-a-path"
    observation = {"instance_id": "ordinary-file", "stage": "opened"}
    result = (
        await bridge.call_tool("wright_workflow_file_context", {"request": observation})
    )[1]
    assert result["document"]["source"] == f.accepted.source
    assert result["native_file"]["source_sha256"] == f.accepted.storage_digest
    from mcp.types import RequestParams

    monkeypatch.setattr(
        bridge,
        "get_context",
        lambda: SimpleNamespace(
            request_context=SimpleNamespace(
                meta=RequestParams.Meta.model_validate(metadata)
            ),
        ),
    )
    assert (
        await bridge.call_tool("wright_workflow_file_context", {"request": observation})
    )[1]["document"]["storage_digest"] == f.accepted.storage_digest
    f.repository.associate_session(
        "alpha", "desktop-new", agent_id="openai-desktop-harness"
    )
    with pytest.raises(Exception, match="explicit saved desktop session"):
        await bridge.call_tool("wright_workflow_file_context", {"request": observation})
    resumed = (
        await bridge.call_tool(
            "wright_workflow_file_context",
            {
                "request": {
                    **observation,
                    "resume": {**body, "expected_sha256": f.accepted.storage_digest},
                }
            },
        )
    )[1]
    assert resumed["native_file"]["session_id"] == "desktop-alpha"
    metadata.clear()
    with pytest.raises(Exception, match="Host file path is missing"):
        await bridge.call_tool("wright_workflow_file_context", {"request": observation})
    assert snapshot(f.root) == before


@pytest.mark.asyncio
async def test_new_client_capability_and_all_dependency_bytes_are_frozen(
    native_files, monkeypatch
):
    import mcp_bridge

    f = native_files
    (f.state / "preview.json").write_text(
        json.dumps({"api_url": "http://127.0.0.1:19191"})
    )
    (f.state / ".preview-api-token").write_text("synthetic-test-only")
    # Credential ACL behavior has its own tests; here exercise the real pin checks.
    monkeypatch.setattr(
        mcp_bridge, "read_private_api_credential", lambda path: path.read_text()
    )
    with pytest.raises(ValueError, match="workspace files differ"):
        mcp_bridge.WrightDesktopClient(f.state, native_editor=True)
    client = mcp_bridge.WrightDesktopClient(
        f.state, native_editor=True, native_workspace_files=True
    )
    await client.http.aclose()
    versions_path = f.state / "desktop-versions.json"
    versions = json.loads(versions_path.read_text())
    for name in [
        "native_workspace_files",
        "native_workspace_file_tools",
        "native_file_contracts",
    ]:
        for value in [None, "a" * 64]:
            changed = {**versions, "files": dict(versions["files"])}
            if value is None:
                del changed["files"][name]
            else:
                changed["files"][name] = value
            versions_path.write_text(json.dumps(changed))
            with pytest.raises(ValueError, match="Pinned native editor bytes changed"):
                mcp_bridge.WrightDesktopClient(
                    f.state, native_editor=True, native_workspace_files=True
                )


def test_local_filesystem_must_match_backend_bytes(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(PROTOTYPE))
    from native_workspace_file_tools import verify_local_file

    path = tmp_path / "sample.png"
    path.write_bytes(PNG)
    descriptor = {
        "absolute_path": str(path),
        "sha256": hashlib.sha256(PNG).hexdigest(),
        "bytes": len(PNG),
    }
    verify_local_file(descriptor)
    for bad in [
        {**descriptor, "absolute_path": str(tmp_path / "missing.png")},
        {**descriptor, "sha256": "a" * 64},
        {**descriptor, "bytes": 1},
    ]:
        with pytest.raises(ValueError, match="same execution-host filesystem"):
            verify_local_file(bad)


@pytest.mark.asyncio
async def test_general_and_probe_modes_are_explicit_and_mutually_exclusive(
    native_files,
):
    from mcp_bridge import server

    with pytest.raises(ValueError, match="require the native editor"):
        server(None, native_workspace_files=True)
    with pytest.raises(ValueError, match="Choose general workspace files"):
        server(
            None,
            native_editor=True,
            native_workspace_files=True,
            native_file_tab_probe=Path("anything"),
        )
    disabled = server(None, native_editor=True)
    assert "wright_workspace_file_describe" not in {
        tool.name for tool in await disabled.list_tools()
    }


@pytest.mark.asyncio
async def test_source_reply_from_another_workspace_cannot_bind_same_bytes(
    native_files, monkeypatch
):
    from unittest.mock import AsyncMock
    from mcp.server.fastmcp import FastMCP
    from native_workspace_file_tools import register_native_workspace_file_tools

    f = native_files
    descriptor = (await describe(f, f.accepted.path)).json()
    client = SimpleNamespace(
        scope=AsyncMock(return_value={}),
        call=AsyncMock(
            side_effect=[
                descriptor,
                {
                    "workspace_id": "foreign",
                    "path": f.accepted.path,
                    "storage_digest": descriptor["sha256"],
                },
            ]
        ),
    )
    bridge = FastMCP("native-file-owner-negative-control")
    register_native_workspace_file_tools(
        bridge, client, resource_uri="ui://test/editor.html", working_view_enabled=False
    )
    monkeypatch.setattr(
        bridge,
        "get_context",
        lambda: SimpleNamespace(
            request_context=SimpleNamespace(
                meta={
                    "openai/resource": {"path": str(f.root / f.accepted.path)},
                }
            )
        ),
    )
    with pytest.raises(Exception, match="Accepted source changed"):
        await bridge.call_tool(
            "wright_workflow_file_context",
            {"request": {"instance_id": "test", "stage": "opened"}},
        )
