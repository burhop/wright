import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from mcp.server.fastmcp import FastMCP

from core.process_validation import canonical_digest
from core.workflow_bundle import WorkflowBundle


@pytest.fixture
def export_port(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from native_source_tools import register_native_source_tools

    source = 'workflow transfer { name = "Preserved definition" }'
    bundle = WorkflowBundle(
        mode="source",
        source=source,
        source_digest=hashlib.sha256(source.encode()).hexdigest(),
    )
    result = {
        "bundle": bundle.model_dump(mode="json"),
        "bundle_digest": canonical_digest(bundle),
    }
    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock(return_value=result))
    server = FastMCP("workflow-export-test")
    register_native_source_tools(server, client)
    request = {
        "workspace_id": "workspace",
        "session_id": "session",
        "path": "workflows/design.workflow.wflow",
        "expected_storage_digest": bundle.source_digest,
    }
    return server, client, request, result


def invoke(server, request):
    return asyncio.run(
        server.call_tool("wright_workflow_export", {"request": request})
    )[1]


def test_export_preserves_owner_bytes_and_exact_scope(export_port):
    server, client, request, result = export_port
    assert invoke(server, request) == {"ok": True, **result}
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "POST",
        "/api/workspace/workflow-bundles/export",
        json={
            **{key: value for key, value in request.items() if key != "workspace_id"},
            "mode": "source",
            "selected_reference_paths": [],
            "selected_ui_ids": [],
        },
    )


def test_selected_dependencies_forwarded_without_adding_authority(export_port):
    server, client, request, result = export_port
    result["bundle"]["mode"] = "bundle"
    result["bundle_digest"] = canonical_digest(result["bundle"])
    assert invoke(
        server,
        {
            **request,
            "mode": "bundle",
            "selected_reference_paths": ["inputs/requirements.json"],
            "selected_ui_ids": ["saved-ui"],
        },
    )["ok"]
    payload = client.call.call_args.kwargs["json"]
    assert payload["selected_reference_paths"] == ["inputs/requirements.json"]
    assert payload["selected_ui_ids"] == ["saved-ui"]
    assert "approval" not in payload


def test_scope_denial_never_reaches_export_owner(export_port):
    server, client, request, _ = export_port
    client.scope.side_effect = PermissionError("private cross-workspace detail")
    result = invoke(server, request)
    assert result["ok"] is False
    assert "private" not in str(result)
    client.call.assert_not_awaited()


@pytest.mark.parametrize(
    "fault", ["digest", "source", "other-source", "mode", "extra-authority", "timeout"]
)
def test_invalid_or_missing_reply_never_claims_download_or_retries(export_port, fault):
    server, client, request, result = export_port
    if fault == "digest":
        result["bundle_digest"] = "0" * 64
    elif fault == "source":
        result["bundle"]["source"] += "changed"
    elif fault == "other-source":
        result["bundle"]["source"] += "changed"
        result["bundle"]["source_digest"] = hashlib.sha256(
            result["bundle"]["source"].encode()
        ).hexdigest()
        result["bundle_digest"] = canonical_digest(result["bundle"])
    elif fault == "mode":
        result["bundle"]["mode"] = "bundle"
        result["bundle_digest"] = canonical_digest(result["bundle"])
    elif fault == "extra-authority":
        result["approval"] = "granted"
    else:
        client.call.side_effect = httpx.ReadTimeout("private transport detail")
    reply = invoke(server, request)
    assert reply["ok"] is False
    assert reply["error"]["code"] == "EXPORT_UNAVAILABLE"
    assert "No download is confirmed" in reply["error"]["message"]
    assert "private" not in str(reply)
    assert client.call.await_count == 1


def test_unknown_request_fields_do_not_reach_owner(export_port):
    server, client, request, _ = export_port
    with pytest.raises(Exception):
        invoke(server, {**request, "url": "https://unrelated.example/export"})
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_export_is_ui_only_read_operation(export_port):
    server, *_ = export_port
    tool = next(
        tool
        for tool in asyncio.run(server.list_tools())
        if tool.name == "wright_workflow_export"
    )
    assert tool.meta["ui"]["visibility"] == ["app"]
    assert tool.annotations.readOnlyHint
    assert not tool.annotations.destructiveHint


def import_args(request, exported):
    return {
        "workspace_id": request["workspace_id"],
        "session_id": request["session_id"],
        "destination_path": "workflows/imported.workflow.wflow",
        "bundle": exported["bundle"],
        "expected_bundle_digest": exported["bundle_digest"],
    }


def import_call(server, args):
    return asyncio.run(server.call_tool("wright_workflow_import", {"request": args}))[1]


def inspection(exported):
    return {
        "bundle_digest": exported["bundle_digest"],
        "can_import": True,
        "can_run": False,
        "diagnostics": [],
        "external_dependencies": [],
        "requirements": [],
    }


def test_import_keeps_owner_source_and_requires_local_readiness(export_port):
    server, client, request, exported = export_port
    args = import_args(request, exported)
    owner = {
        "source": {
            "workspace_id": "workspace",
            "path": args["destination_path"],
            "source": exported["bundle"]["source"],
            "storage_digest": exported["bundle"]["source_digest"],
            "metadata_authority": "wright_host",
        },
        "imported_paths": ["imported-assets/imported/manifest.json"],
        "inspection": inspection(exported),
    }
    client.call.return_value = owner
    assert import_call(server, args) == {"ok": True, "document": owner}
    assert client.call.call_args.args == (
        "POST",
        "/api/workspace/workflow-bundles/import",
    )
    assert client.call.await_count == 1
    assert not owner["inspection"]["can_run"]


@pytest.mark.parametrize("fault", ["timeout", "owner-422", "malformed-reply"])
def test_unconfirmed_import_is_unknown_and_never_replayed(export_port, fault):
    from native_source_tools import WrightRequestRejected

    server, client, request, exported = export_port
    if fault == "timeout":
        client.call.side_effect = httpx.ReadTimeout("private detail")
    elif fault == "owner-422":
        client.call.side_effect = WrightRequestRejected(422, "partial file write")
    else:
        client.call.return_value = {"source": {"path": "other"}}
    result = import_call(server, import_args(request, exported))
    assert result["error"]["code"] == "OUTCOME_UNKNOWN"
    assert not result["error"]["outcome_known"]
    assert client.call.await_count == 1
    assert "private" not in str(result)


@pytest.mark.parametrize("fault", ["changed-bundle", "scope"])
def test_rejected_import_before_dispatch_has_no_effect(export_port, fault):
    server, client, request, exported = export_port
    args = import_args(request, exported)
    if fault == "changed-bundle":
        args["expected_bundle_digest"] = "0" * 64
    else:
        client.scope.side_effect = PermissionError("wrong workspace")
    result = import_call(server, args)
    assert result["error"]["outcome_known"]
    assert result["error"]["code"] == "IMPORT_REJECTED"
    client.call.assert_not_awaited()


def test_inspection_cannot_claim_readiness_or_change_bundle(export_port):
    server, client, request, exported = export_port
    args = import_args(request, exported)
    del args["expected_bundle_digest"]
    client.call.return_value = inspection(exported)
    _, reply = asyncio.run(
        server.call_tool("wright_workflow_import_inspect", {"request": args})
    )
    assert reply["can_import"] and not reply["can_run"]
    for change in ({"can_run": True}, {"bundle_digest": "0" * 64}):
        client.call.return_value = {**inspection(exported), **change}
        with pytest.raises(Exception):
            asyncio.run(
                server.call_tool("wright_workflow_import_inspect", {"request": args})
            )


@pytest.mark.parametrize("kind", ["references", "interfaces"])
def test_asset_discovery_reads_existing_owners_for_exact_source(export_port, kind):
    server, client, request, _ = export_port
    source = {
        "workspace_id": "workspace",
        "path": request["path"],
        "storage_digest": request["expected_storage_digest"],
    }
    candidates = (
        {
            "workspace_id": "workspace",
            "files": [{"path": "inputs/brief.txt", "name": "brief.txt"}],
        }
        if kind == "references"
        else {"interfaces": []}
    )
    client.call.side_effect = [source, candidates]
    _, reply = asyncio.run(
        server.call_tool(
            "wright_workflow_transfer_assets", {"request": {**request, "kind": kind}}
        )
    )
    assert reply == candidates
    assert client.call.await_count == 2
    assert all(call.args[0] == "GET" for call in client.call.call_args_list)


def test_changed_source_never_lists_transfer_assets(export_port):
    server, client, request, _ = export_port
    client.call.return_value = {
        "workspace_id": "workspace",
        "path": request["path"],
        "storage_digest": "0" * 64,
    }
    with pytest.raises(Exception, match="saved workflow changed"):
        asyncio.run(
            server.call_tool(
                "wright_workflow_transfer_assets",
                {"request": {**request, "kind": "references"}},
            )
        )
    assert client.call.await_count == 1


def test_other_workspace_reference_list_is_rejected(export_port):
    server, client, request, _ = export_port
    client.call.side_effect = [
        {
            "workspace_id": "workspace",
            "path": request["path"],
            "storage_digest": request["expected_storage_digest"],
        },
        {"workspace_id": "other", "files": []},
    ]
    with pytest.raises(Exception, match="invalid reference file list"):
        asyncio.run(
            server.call_tool(
                "wright_workflow_transfer_assets",
                {"request": {**request, "kind": "references"}},
            )
        )
