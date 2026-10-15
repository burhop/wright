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
