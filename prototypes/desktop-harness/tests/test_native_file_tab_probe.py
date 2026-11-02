import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def probe(tmp_path, monkeypatch, request):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from native_file_tab_probe import register_native_file_tab_probe

    source = tmp_path / "inputs" / "part.workflow.wflow"
    source.parent.mkdir()
    source.write_text("workflow { title: Test }\n")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    html = tmp_path / "launcher.html"
    newline = getattr(request, "param", "\n")
    html.write_bytes(
        f"<!doctype html>{newline}<title>Native tab probe — Connecting…</title>".encode(
            "utf-8"
        )
    )
    evidence = tmp_path / "observations.jsonl"
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "wright.native-file-tabs-probe/1",
                "launcher_html": str(html),
                "evidence_path": str(evidence),
                "files": [
                    {
                        "absolute_path": str(source),
                        "sha256": digest,
                        "kind": "workflow",
                        "label": "Part",
                        "workspace_id": "workspace",
                        "session_id": "session",
                        "path": "workflows/part.workflow.wflow",
                    }
                ],
            }
        )
    )
    client = SimpleNamespace(
        scope=AsyncMock(return_value={"workspace_id": "workspace"}),
        call=AsyncMock(
            return_value={
                "path": "workflows/part.workflow.wflow",
                "storage_digest": digest,
            }
        ),
    )
    server = FastMCP("native-tab-test")
    register_native_file_tab_probe(
        server,
        client,
        manifest_path=manifest,
        resource_uri="ui://wright/workflow/test.html",
        working_view_enabled=True,
    )
    metadata = {"openai/resource": {"path": str(source)}}
    monkeypatch.setattr(
        server,
        "get_context",
        lambda: SimpleNamespace(request_context=SimpleNamespace(meta=metadata)),
    )
    return SimpleNamespace(
        server=server,
        client=client,
        source=source,
        evidence=evidence,
        digest=digest,
        metadata=metadata,
        manifest=manifest,
        html=html,
    )


def call(probe, payload=None):
    return asyncio.run(
        probe.server.call_tool(
            "wright_workflow_file_context",
            {"request": payload or {"instance_id": "instance-one", "stage": "opened"}},
        )
    )[1]


def test_host_path_resolves_exact_existing_owner_without_writes(probe):
    result = call(
        probe,
        {
            "instance_id": "instance-one",
            "stage": "rendered",
            "capabilities": {"files": True, "resources": True},
            "observed_source_digest": probe.digest,
            "editor_has_unsaved_changes": True,
        },
    )
    probe.client.scope.assert_awaited_once_with("workspace", "session")
    probe.client.call.assert_awaited_once_with(
        "GET",
        "/api/workspace/workflow-sources",
        params={"session_id": "session", "path": "workflows/part.workflow.wflow"},
    )
    assert result["native_file"]["instance_id"] == "instance-one"
    assert hashlib.sha256(probe.source.read_bytes()).hexdigest() == probe.digest
    records = [json.loads(line) for line in probe.evidence.read_text().splitlines()]
    assert records[0]["ui_observation"]["editor_has_unsaved_changes"] is True
    assert records[0]["ui_observation_trust"].startswith("self-reported")
    assert "workflow {" not in probe.evidence.read_text()


def test_actual_sdk_metadata_model_preserves_host_extension(probe, monkeypatch):
    from mcp.types import RequestParams

    meta = RequestParams.Meta.model_validate(probe.metadata)
    monkeypatch.setattr(
        probe.server,
        "get_context",
        lambda: SimpleNamespace(request_context=SimpleNamespace(meta=meta)),
    )
    assert call(probe)["native_file"]["path"] == "workflows/part.workflow.wflow"


def test_fixed_probe_verifies_remembered_scope_before_reading_source(probe):
    remembered = {
        "workspace_id": "workspace",
        "session_id": "session",
        "path": "workflows/part.workflow.wflow",
        "expected_sha256": probe.digest,
    }
    assert (
        call(
            probe, {"instance_id": "reopened", "stage": "opened", "resume": remembered}
        )["native_file"]["sha256"]
        == probe.digest
    )
    for patch in [
        {"workspace_id": "other"},
        {"session_id": "other"},
        {"path": "workflows/other.workflow.wflow"},
        {"expected_sha256": "a" * 64},
    ]:
        probe.client.scope.reset_mock()
        probe.client.call.reset_mock()
        with pytest.raises(Exception, match="Remembered scope differs"):
            call(
                probe,
                {
                    "instance_id": "reopened",
                    "stage": "opened",
                    "resume": {**remembered, **patch},
                },
            )
        probe.client.scope.assert_not_awaited()
        probe.client.call.assert_not_awaited()


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        {"openai/resource": {}},
        {
            "openai/resource": {"path": "/tmp/unallowlisted.workflow.wflow"},
        },
    ],
)
def test_missing_or_unallowlisted_host_path_never_reads_source(probe, metadata):
    probe.metadata.clear()
    probe.metadata.update(metadata)
    with pytest.raises(Exception, match="Host file path"):
        call(probe)
    probe.client.scope.assert_not_awaited()
    probe.client.call.assert_not_awaited()


def test_client_supplied_path_does_not_override_host_metadata(probe):
    probe.metadata.clear()
    with pytest.raises(Exception):
        call(probe, {"instance_id": "x", "stage": "opened", "path": str(probe.source)})
    probe.client.call.assert_not_awaited()


def test_pin_changes_fail_closed_without_owner_read(probe):
    probe.source.write_text("changed source")
    with pytest.raises(Exception, match="changed from"):
        call(probe)
    probe.client.call.assert_not_awaited()


def test_symlink_replacement_rejected_even_with_matching_bytes(probe, tmp_path):
    target = tmp_path / "replacement.wflow"
    target.write_bytes(probe.source.read_bytes())
    probe.source.unlink()
    try:
        probe.source.symlink_to(target)
    except OSError as error:
        if os.name != "nt" or error.winerror != 1314:
            raise
        # Retain actual reparse-point coverage without requiring Developer Mode.
        replacement = tmp_path / "replacement-directory"
        replacement.mkdir()
        (replacement / probe.source.name).write_bytes(target.read_bytes())
        probe.source.parent.rmdir()
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(probe.source.parent), str(replacement)],
            check=True,
            capture_output=True,
        )
        assert probe.source.parent.is_junction()
    assert probe.source.read_bytes() == target.read_bytes()
    with pytest.raises(Exception, match="without symlinks"):
        call(probe)
    probe.client.call.assert_not_awaited()


def test_scope_denial_does_not_read_or_record_success(probe):
    probe.client.scope.side_effect = PermissionError("workspace scope denied")
    with pytest.raises(Exception, match="scope denied"):
        call(probe)
    probe.client.call.assert_not_awaited()
    assert not probe.evidence.exists()


def test_source_owner_identity_mismatch_remains_detected(probe):
    probe.client.call.return_value["storage_digest"] = "f" * 64
    with pytest.raises(Exception, match="owner differs"):
        call(probe)
    assert not probe.evidence.exists()


def test_file_entrypoint_is_separate_and_app_context_not_model_visible(probe):
    tools = {tool.name: tool for tool in asyncio.run(probe.server.list_tools())}
    assert tools["wright_workflow_file"].meta["openai/ui"] == {
        "entrypoints": [{"type": "file", "extensions": [".wflow"]}],
    }
    assert tools["wright_workflow_file_context"].meta["ui"]["visibility"] == ["app"]
    assert "ctx" not in tools["wright_workflow_file_context"].inputSchema["properties"]
    _, result = asyncio.run(
        probe.server.call_tool(
            "wright_workflow_file",
            {
                "file": {
                    "name": "part.workflow.wflow",
                    "resourceUri": "host-resource://opaque",
                },
            },
        )
    )
    assert result["view"] == "native-workflow-file"
    probe.client.call.assert_not_awaited()
    _, status = asyncio.run(
        probe.server.call_tool("wright_native_tabs_probe_status", {})
    )
    assert status["native_visual_acceptance"] == "unverified"
    assert status["observations"][0]["boundary"] == "file-entrypoint-invocation"


def test_current_file_registration_matches_previously_observed_probe(probe):
    """Compare real MCP declarations; this cannot establish host selection."""
    from native_workspace_file_tools import register_native_workspace_file_tools

    current = FastMCP("current-file-handler-test")
    register_native_workspace_file_tools(
        current,
        probe.client,
        resource_uri="ui://wright/workflow/current.html",
        working_view_enabled=True,
    )
    previous_tool = {
        tool.name: tool for tool in asyncio.run(probe.server.list_tools())
    }["wright_workflow_file"]
    current_tool = {tool.name: tool for tool in asyncio.run(current.list_tools())}[
        "wright_workflow_file"
    ]
    assert current_tool.meta["openai/ui"] == previous_tool.meta["openai/ui"]
    assert (
        current_tool.meta["ui"]["visibility"] == previous_tool.meta["ui"]["visibility"]
    )
    assert current_tool.inputSchema == previous_tool.inputSchema
    assert current_tool.annotations == previous_tool.annotations


@pytest.mark.parametrize("probe", ["\n", "\r\n"], indirect=True)
def test_launcher_resource_preserves_exact_utf8_bytes_and_identity(probe):
    tools = {tool.name: tool for tool in asyncio.run(probe.server.list_tools())}
    uri = tools["wright_native_tabs_probe"].meta["ui"]["resourceUri"]
    expected = probe.html.read_bytes()
    assert hashlib.sha256(expected).hexdigest() in uri
    resource = asyncio.run(probe.server.read_resource(uri))[0]
    assert resource.content.encode("utf-8") == expected


@pytest.mark.parametrize(
    "extra",
    [
        {"stage": "unauthorized"},
        {"instance_id": "x" * 81},
        {"observed_source_digest": "bad"},
        {"capabilities": {"files": True, "resources": True, "other": True}},
        {"editor_has_unsaved_changes": "true"},
    ],
)
def test_observations_are_strictly_bounded(probe, extra):
    with pytest.raises(Exception):
        call(probe, {"instance_id": "x", "stage": "opened", **extra})
    probe.client.call.assert_not_awaited()
