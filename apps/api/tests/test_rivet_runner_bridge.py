from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import pytest
from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from data_vault import RivetMcpRepository
from data_vault.migrations import upgrade_database
from tool_registry.gateway_models import GatewayToolResult
from workspace_service import (
    AuthorityClaims,
    RivetRunAuthorityService,
    RivetMcpGatewaySettings,
)
from workspace_service.rivet_gateway_bridge import RivetBridgeResult


HEX = "a" * 64


def _binding() -> CapabilityBinding:
    return CapabilityBinding.build(
        binding_id="binding-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=HEX,
        graph_id="graph-1",
        node_id="node-1",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="alpha__inspect",
        server_id="alpha",
        server_revision="1",
        capability_digest="b" * 64,
        validation_evidence_id="evidence-1",
        workspace_grant_digest="c" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={"required_approvals": []},
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime.now(UTC),
    )


def _repository(tmp_path) -> tuple[RivetMcpRepository, WorkflowBindingSet]:
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', 'D:/workspace', 1, 1)"""
        )
    repository = RivetMcpRepository(str(path))
    binding = _binding()
    binding_set = WorkflowBindingSet.build(
        binding_set_id="set-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=HEX,
        graph_id="graph-1",
        bindings=(binding,),
        discovery_snapshot_digest="d" * 64,
        policy_snapshot_digest="e" * 64,
        created_at=datetime.now(UTC),
    )
    repository.save_binding_set(binding_set)
    return repository, binding_set


class Bridge:
    def __init__(self, binding: CapabilityBinding) -> None:
        self.binding = binding
        self.invocations = []

    async def invoke_bound(self, token, audience, invocation, *, progress_callback):
        self.invocations.append((token, audience, invocation))
        await progress_callback({"type": "progress", "phase": "child", "progress": 0.5})
        return RivetBridgeResult(
            GatewayToolResult(
                content=({"type": "text", "text": "ok"},),
                structured_content={"value": 2},
            ),
            self.binding,
            (),
            0,
        )

    def cancel_authority(self, authority_id, *, reason):
        return 0


async def _post(base_url: str, path: str, token: str, payload: dict):
    target = urlsplit(base_url)
    reader, writer = await asyncio.open_connection(target.hostname, target.port)
    body = json.dumps(payload, separators=(",", ":")).encode()
    writer.write(
        f"POST {target.path}/{path} HTTP/1.1\r\n".encode()
        + f"Host: 127.0.0.1:{target.port}\r\n".encode()
        + f"Authorization: Bearer {token}\r\n".encode()
        + b"Content-Type: application/json\r\n"
        + f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode()
        + body
    )
    await writer.drain()
    response = await reader.read()
    writer.close()
    await writer.wait_closed()
    head, raw_body = response.split(b"\r\n\r\n", 1)
    return head.decode(), [json.loads(line) for line in raw_body.splitlines()]


@pytest.mark.asyncio
async def test_loopback_bridge_discovers_only_authorized_bindings_and_streams_calls(
    tmp_path,
):
    repository, binding_set = _repository(tmp_path)
    authority = RivetRunAuthorityService()
    bridge = Bridge(binding_set.bindings[0])
    application = RivetRunnerBridgeApplication(
        bridge=bridge,  # type: ignore[arg-type]
        authorities=authority,
        repository=repository,
        settings=RivetMcpGatewaySettings(enabled=True),
    )
    audience = await application.ensure_started()
    now = datetime.now(UTC)
    issued = authority.mint(
        AuthorityClaims(
            run_id="run-1",
            generation=1,
            workspace_id="workspace-1",
            session_id="gateway-session",
            workflow_id="workflow-1",
            workflow_revision=1,
            workflow_digest=HEX,
            graph_id="graph-1",
            review_digest="f" * 64,
            binding_set_digest=binding_set.binding_set_digest,
            audience=audience,
            node_bindings={
                binding_set.bindings[0].node_handle: binding_set.bindings[
                    0
                ].binding_digest
            },
            issued_at=now,
            expires_at=now + timedelta(minutes=1),
        )
    )
    try:
        head, events = await _post(
            audience,
            "discover",
            issued.token,
            {
                "authorityId": issued.authority_id,
                "runId": "run-1",
                "discoveryHandle": "wright-workspace",
                "requestId": "discover-1",
            },
        )
        assert "200 OK" in head
        assert "access-control" not in head.lower()
        assert [tool["name"] for tool in events[-1]["structuredContent"]["tools"]] == [
            "alpha__inspect"
        ]

        _head, call_events = await _post(
            audience,
            "calls",
            issued.token,
            {
                "authorityId": issued.authority_id,
                "runId": "run-1",
                "nodeHandle": binding_set.bindings[0].node_handle,
                "bindingDigest": binding_set.bindings[0].binding_digest,
                "requestId": "call-1",
                "arguments": {"value": 2},
            },
        )
        assert [event["type"] for event in call_events] == ["progress", "result"]
        assert call_events[-1]["structuredContent"] == {"value": 2}
        assert bridge.invocations[0][2].arguments == {"value": 2}
    finally:
        await application.close()


@pytest.mark.asyncio
async def test_loopback_bridge_rejects_wrong_token_extra_authority_and_oversize(
    tmp_path,
):
    repository, binding_set = _repository(tmp_path)
    authority = RivetRunAuthorityService()
    application = RivetRunnerBridgeApplication(
        bridge=Bridge(binding_set.bindings[0]),  # type: ignore[arg-type]
        authorities=authority,
        repository=repository,
        settings=RivetMcpGatewaySettings(
            enabled=True, maximum_request_bytes=1024, maximum_event_bytes=512
        ),
    )
    audience = await application.ensure_started()
    now = datetime.now(UTC)
    issued = authority.mint(
        AuthorityClaims(
            run_id="run-1",
            generation=1,
            workspace_id="workspace-1",
            session_id="gateway-session",
            workflow_id="workflow-1",
            workflow_revision=1,
            workflow_digest=HEX,
            graph_id="graph-1",
            review_digest="f" * 64,
            binding_set_digest=binding_set.binding_set_digest,
            audience=audience,
            node_bindings={
                binding_set.bindings[0].node_handle: binding_set.bindings[
                    0
                ].binding_digest
            },
            issued_at=now,
            expires_at=now + timedelta(minutes=1),
        )
    )
    try:
        head, events = await _post(
            audience,
            "discover",
            "wrong-token-value-that-is-long-enough-for-the-runner",
            {
                "authorityId": "missing",
                "runId": "run-1",
                "discoveryHandle": "wright-workspace",
                "requestId": "request",
            },
        )
        assert "401 Error" in head
        assert events[-1]["error"]["code"] == "RIVET_MCP_AUTHORITY_UNAVAILABLE"
        assert "wrong-token" not in json.dumps(events)

        _head, extra = await _post(
            audience,
            "discover",
            issued.token,
            {
                "authorityId": issued.authority_id,
                "runId": "run-1",
                "discoveryHandle": "wright-workspace",
                "requestId": "request",
                "serverId": "alpha",
            },
        )
        assert extra[-1]["error"]["code"] == "RIVET_MCP_BINDING_MISMATCH"

        oversize_head, oversize = await _post(
            audience, "calls", issued.token, {"padding": "x" * 2000}
        )
        assert "413 Error" in oversize_head
        assert oversize[-1]["error"]["code"] == "RIVET_MCP_REQUEST_TOO_LARGE"
    finally:
        await application.close()
