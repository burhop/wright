from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from core.rivet_mcp import CapabilityBinding, WorkflowBindingSet
from data_vault import RivetMcpRepository, upgrade_database
from structlog.testing import capture_logs
from tool_registry.gateway_models import GatewayToolResult
from workspace_service import (
    AuthorityClaims,
    RivetBoundInvocation,
    RivetGatewayBridge,
    RivetRunAuthorityService,
)
from workspace_service.rivet_evidence import (
    RivetEvidenceError,
    build_run_evidence,
    safe_argument_summary,
    sanitize_gateway_result,
)


RAW_SECRET = "wright-test-secret-7Yf9Q2mN"


def _binding(*, input_schema=None) -> CapabilityBinding:
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
        server_revision="fixture-v1",
        capability_digest="b" * 64,
        validation_evidence_id="validation-1",
        workspace_grant_digest="c" * 64,
        input_schema=input_schema or {"type": "object"},
        output_schema={"type": "object"},
        risk={"required_approvals": []},
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime.now(UTC),
    )


class SecretReturningGateway:
    async def call_tool(self, *_args, progress_callback=None, **_kwargs):
        if progress_callback:
            await progress_callback(
                {"phase": "child", "authorization": f"Bearer {RAW_SECRET}"}
            )
        return GatewayToolResult(
            content=(
                {
                    "type": "text",
                    "text": f"https://fixture.invalid/result?token={RAW_SECRET}",
                },
            ),
            structured_content={"api_key": RAW_SECRET, "result": "ok"},
            meta={"credential": RAW_SECRET},
        )

    def cancel(self, *_args, **_kwargs):
        return True


@pytest.mark.asyncio
async def test_secret_material_is_absent_from_logs_progress_results_and_evidence(
    monkeypatch,
):
    monkeypatch.setenv("WRIGHT_FIXTURE_API_KEY", RAW_SECRET)
    binding = _binding()
    authorities = RivetRunAuthorityService()
    now = datetime.now(UTC)
    audience = "http://127.0.0.1:43123/internal/rivet-mcp/v1"
    issued = authorities.mint(
        AuthorityClaims(
            run_id="run-1",
            generation=1,
            workspace_id="workspace-1",
            session_id="session-1",
            workflow_id="workflow-1",
            workflow_revision=1,
            workflow_digest="a" * 64,
            graph_id="graph-1",
            review_digest="d" * 64,
            binding_set_digest="e" * 64,
            audience=audience,
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=1),
        )
    )
    bridge = RivetGatewayBridge(
        SecretReturningGateway(),
        authorities=authorities,
        resolve_binding=lambda digest: (
            binding if digest == binding.binding_digest else None
        ),
    )
    progress: list[dict] = []
    with capture_logs() as logs:
        result = await bridge.invoke_bound(
            issued.token,
            audience,
            RivetBoundInvocation(
                "run-1",
                1,
                issued.authority_id,
                binding.node_handle,
                binding.binding_digest,
                "request-1",
                {
                    "password": RAW_SECRET,
                    "source": f"https://fixture.invalid/model?api_key={RAW_SECRET}",
                },
            ),
            progress_callback=lambda event: progress.append(dict(event)),
        )
    argument_summary, redactions, _truncated = safe_argument_summary(
        {"authorization": f"Bearer {RAW_SECRET}", "value": 2}
    )
    manifest = {
        "run_id": "run-1",
        "started_at": now.isoformat(),
        "workflow": {"digest": "a" * 64},
        "review_digest": "d" * 64,
        "binding_set_digest": "e" * 64,
        "policy_snapshot_digest": "f" * 64,
        "runtime": {"runner_sha256": "1" * 64},
        "authority": {"authority_id": issued.authority_id},
        "bindings": [binding.canonical()],
        "child_call_ids": [],
        "approval_ids": [],
        "artifacts": [],
        "redaction_count": result.redaction_count + redactions,
    }
    evidence = build_run_evidence(
        manifest=manifest,
        child_calls=(),
        approvals=(),
        events=(
            {
                "sequence": 1,
                "occurred_at": now.isoformat(),
                "kind": "progress",
                "payload": progress[0],
            },
        ),
        current={},
    )
    surfaces = {
        "structured_logs": logs,
        "trace_and_progress_events": progress,
        "api_and_export_evidence": evidence,
        "runner_result": {
            "content": result.result.content,
            "structuredContent": result.result.structured_content,
            "meta": result.result.meta,
        },
        "approval_summary": argument_summary,
        "selected_environment_names": [
            name for name in os.environ if name == "WRIGHT_FIXTURE_API_KEY"
        ],
    }
    encoded = json.dumps(surfaces, sort_keys=True, default=str)
    assert RAW_SECRET not in encoded
    assert issued.token not in encoded
    assert "[redacted]" in encoded.lower()


def test_secret_like_bindings_raw_paths_and_arbitrary_uris_are_rejected():
    with pytest.raises(ValueError, match="secret-like field"):
        _binding(input_schema={"type": "object", "api_key": RAW_SECRET})
    with pytest.raises(ValueError, match="secret-bearing URL"):
        _binding(input_schema={"$id": f"https://user:{RAW_SECRET}@fixture.invalid"})

    for uri in (
        "file:///D:/private/raw-child-output.step",
        "https://fixture.invalid/raw-child-output.step",
        "wright://artifact/other-workspace/raw-child-output.step",
        "wright://artifact/workspace-1/../raw-child-output.step",
    ):
        with pytest.raises(RivetEvidenceError, match="not authorized"):
            sanitize_gateway_result(
                GatewayToolResult(
                    content=(
                        {
                            "type": "resource_link",
                            "uri": uri,
                            "sha256": "a" * 64,
                            "bytes": 1,
                        },
                    )
                ),
                workspace_id="workspace-1",
            )


def test_memory_only_authority_token_never_reaches_workflow_or_sqlite(tmp_path: Path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', ?, 1, 1)""",
            (str(tmp_path),),
        )
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
    RivetMcpRepository(str(database)).save_binding_set(binding_set)
    authorities = RivetRunAuthorityService()
    now = datetime.now(UTC)
    issued = authorities.mint(
        AuthorityClaims(
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
            audience="http://127.0.0.1:43123/internal/rivet-mcp/v1",
            node_bindings={binding.node_handle: binding.binding_digest},
            issued_at=now,
            expires_at=now + timedelta(minutes=1),
        )
    )
    workflow_file = tmp_path / "reviewed-workflow.json"
    workflow_file.write_text(
        json.dumps(
            {
                "workflow_digest": binding.workflow_digest,
                "binding_digest": binding.binding_digest,
                "authority_digest": issued.token_digest,
            }
        ),
        encoding="utf-8",
    )
    assert issued.token.encode() not in database.read_bytes()
    assert issued.token not in workflow_file.read_text(encoding="utf-8")
    ui_source = Path("apps/web/src/components/chat/RivetWorkflowRun.tsx").read_text(
        encoding="utf-8"
    )
    assert issued.token not in ui_source
