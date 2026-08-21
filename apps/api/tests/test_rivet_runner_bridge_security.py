from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import pytest
from api.rivet_runner_bridge import RivetRunnerBridgeApplication
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from workspace_service import (
    AuthorityClaims,
    RivetMcpGatewaySettings,
    RivetRunAuthorityService,
)


def _binding() -> CapabilityBinding:
    return CapabilityBinding.build(
        binding_id="binding-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
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


class Repository:
    def __init__(self, binding_set: WorkflowBindingSet) -> None:
        self.binding_set = binding_set

    def get_binding_set_by_digest(self, digest: str):
        if digest == self.binding_set.binding_set_digest:
            return self.binding_set
        return None


class RevalidatingBridge:
    def __init__(self, authorities: RivetRunAuthorityService) -> None:
        self.authorities = authorities
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def invoke_bound(self, token, audience, invocation, *, progress_callback):
        del progress_callback
        self.started.set()
        await self.release.wait()
        self.authorities.validate(
            token,
            audience=audience,
            run_id=invocation.run_id,
            generation=invocation.generation,
            node_handle=invocation.node_handle,
            binding_digest=invocation.binding_digest,
        )
        raise AssertionError("revoked authority accepted a late result")

    def cancel_authority(self, _authority_id, *, reason):
        del reason
        return 0

    def active_count(self, _authority_id):
        return 0


def _setup():
    binding = _binding()
    binding_set = WorkflowBindingSet.build(
        binding_set_id="set-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="graph-1",
        bindings=(binding,),
        discovery_snapshot_digest="d" * 64,
        policy_snapshot_digest="e" * 64,
        created_at=datetime.now(UTC),
    )
    authorities = RivetRunAuthorityService()
    bridge = RevalidatingBridge(authorities)
    application = RivetRunnerBridgeApplication(
        bridge=bridge,  # type: ignore[arg-type]
        authorities=authorities,
        repository=Repository(binding_set),  # type: ignore[arg-type]
        settings=RivetMcpGatewaySettings(
            enabled=True, maximum_request_bytes=1024, maximum_event_bytes=512
        ),
    )
    return application, authorities, bridge, binding_set, binding


def _claims(audience, binding_set, binding):
    now = datetime.now(UTC)
    return AuthorityClaims(
        run_id="run-1",
        generation=1,
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="graph-1",
        review_digest="f" * 64,
        binding_set_digest=binding_set.binding_set_digest,
        audience=audience,
        node_bindings={binding.node_handle: binding.binding_digest},
        issued_at=now,
        expires_at=now + timedelta(minutes=1),
    )


async def _raw(audience: str, request: bytes) -> tuple[str, str]:
    target = urlsplit(audience)
    reader, writer = await asyncio.open_connection(target.hostname, target.port)
    writer.write(request)
    await writer.drain()
    if not request.endswith(b"\r\n\r\n"):
        try:
            writer.write_eof()
        except (AttributeError, OSError):
            pass
    response = await asyncio.wait_for(reader.read(), timeout=2)
    writer.close()
    await writer.wait_closed()
    head, _, body = response.partition(b"\r\n\r\n")
    return head.decode(errors="replace"), body.decode(errors="replace")


def _request(
    audience,
    token,
    *,
    method="POST",
    path="discover",
    content_type="application/json",
    host=None,
    origin=None,
    body=None,
):
    target = urlsplit(audience)
    payload = body or {
        "authorityId": "placeholder",
        "runId": "run-1",
        "discoveryHandle": "wright-workspace",
        "requestId": "request-1",
    }
    encoded = json.dumps(payload, separators=(",", ":")).encode()
    headers = [
        f"{method} {target.path}/{path} HTTP/1.1",
        f"Host: {host or target.netloc}",
        f"Authorization: Bearer {token}",
        f"Content-Type: {content_type}",
        f"Content-Length: {len(encoded)}",
        "Connection: close",
    ]
    if origin:
        headers.append(f"Origin: {origin}")
    return ("\r\n".join(headers) + "\r\n\r\n").encode() + encoded


@pytest.mark.asyncio
async def test_hostile_method_path_content_type_origin_and_host_are_denied():
    application, authorities, _bridge, binding_set, binding = _setup()
    audience = await application.ensure_started()
    issued = authorities.mint(_claims(audience, binding_set, binding))
    try:
        cases = (
            {"method": "GET"},
            {"path": "../calls"},
            {"content_type": "text/plain"},
            {"origin": "https://hostile.example"},
            {"host": "hostile.example"},
        )
        for values in cases:
            head, body = await _raw(
                audience, _request(audience, issued.token, **values)
            )
            assert not head.startswith("HTTP/1.1 200")
            assert "RIVET_MCP_" in body
            assert issued.token not in body
    finally:
        await application.close()


@pytest.mark.asyncio
async def test_oversized_malformed_duplicate_and_streaming_requests_are_denied():
    application, authorities, _bridge, binding_set, binding = _setup()
    audience = await application.ensure_started()
    issued = authorities.mint(_claims(audience, binding_set, binding))
    target = urlsplit(audience)
    try:
        valid = _request(audience, issued.token)
        cases = (
            valid.replace(
                b"Content-Length: ",
                b"Transfer-Encoding: chunked\r\nContent-Length: ",
                1,
            ),
            valid.replace(b"Host: ", b"Host: duplicate\r\nHost: ", 1),
            valid.replace(b"{", b"[", 1),
            (
                f"POST {target.path}/calls HTTP/1.1\r\nHost: {target.netloc}\r\n"
                f"Authorization: Bearer {issued.token}\r\nContent-Type: application/json\r\n"
                "Content-Length: 2048\r\nConnection: close\r\n\r\n{}"
            ).encode(),
            f"POST {target.path}/calls HTTP/1.1\r\nHost: {target.netloc}\r\n".encode(),
        )
        for request in cases:
            head, body = await _raw(audience, request)
            assert not head.startswith("HTTP/1.1 200")
            assert issued.token not in body
    finally:
        await application.close()


@pytest.mark.asyncio
async def test_terminal_token_replay_and_concurrent_revocation_cannot_succeed():
    application, authorities, bridge, binding_set, binding = _setup()
    audience = await application.ensure_started()
    issued = authorities.mint(_claims(audience, binding_set, binding))
    call_body = {
        "authorityId": issued.authority_id,
        "runId": "run-1",
        "nodeHandle": binding.node_handle,
        "bindingDigest": binding.binding_digest,
        "requestId": "call-1",
        "arguments": {},
    }
    try:
        in_flight = asyncio.create_task(
            _raw(
                audience, _request(audience, issued.token, path="calls", body=call_body)
            )
        )
        await bridge.started.wait()
        authorities.revoke(issued.authority_id, reason="concurrent cancellation")
        bridge.release.set()
        head, body = await in_flight
        assert "application/x-ndjson" in head.lower()
        assert "RIVET_MCP_AUTHORITY_REVOKED" in body

        authorities.terminal(issued.authority_id, reason="finished")
        replay_head, replay_body = await _raw(
            audience, _request(audience, issued.token, path="calls", body=call_body)
        )
        assert not replay_head.startswith("HTTP/1.1 200")
        assert "RIVET_MCP_AUTHORITY_UNAVAILABLE" in replay_body
        assert issued.token not in replay_body
    finally:
        await application.close()
