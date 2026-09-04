"""Opt-in local protocol proof, distinct from mocked native/gateway unit tests.

WRIGHT_NATIVE_MCP_PROTOCOL=1 enables one disposable stdio Python server. This is
native integration evidence, not clean-container catalog qualification.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from core.redaction import redact_mapping
from data_vault import GatewayRepository, upgrade_database
from data_vault.secret_provider import FileSecretProvider
from data_vault.workspace_repository import WorkspaceRepository
from tool_registry.db import insert_server, insert_tools
from tool_registry.gateway_adapters import (
    DatabaseGatewayAudit,
    DatabaseGatewayCatalog,
    DatabaseGatewayWorkspace,
    EngineGatewayLifecycle,
)
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService
from tool_registry.manager import McpEngine
from tool_registry.models import McpServer, McpTool
from tool_registry.runners.stdio import StdioRunner
from workspace_service.native_process_mcp import NativeMcpAdapter
from workspace_service.service import WorkspaceService


pytestmark = [
    pytest.mark.mcp_protocol,
    pytest.mark.skipif(
        os.getenv("WRIGHT_NATIVE_MCP_PROTOCOL") != "1",
        reason="explicit opt-in disposable local MCP protocol proof",
    ),
]


@pytest.mark.asyncio
async def test_native_adapter_real_stdio_protocol(tmp_path, monkeypatch):
    monkeypatch.delenv("WRIGHT_TESTING", raising=False)
    database = str(tmp_path / "state.db")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    fixture_data = workspace / "fixture-data.json"
    fixture_data.write_text('{"multiplier":2.5}', encoding="utf-8")
    original_data = fixture_data.read_bytes()
    transcript = tmp_path / "protocol.jsonl"
    fixture_script = Path(__file__).with_name("fixtures") / "native_stdio_mcp.py"
    input_schema = {
        "type": "object",
        "properties": {"value": {"type": "number", "minimum": 0.25}},
        "required": ["value"],
        "additionalProperties": False,
    }
    output_schema = {
        "type": "object",
        "properties": {"value": {"type": "number"}},
        "required": ["value"],
        "additionalProperties": False,
    }
    upgrade_database(database)
    WorkspaceRepository(
        database, secrets=FileSecretProvider(tmp_path / "secrets.json")
    ).create(
        "native-proof-workspace",
        "native-proof-session",
        str(workspace),
        workspace_name="Native local proof",
    )
    insert_server(
        database,
        McpServer(
            server_id="native-proof",
            name="native-proof",
            type="stdio",
            command=[sys.executable, "-I", "-u", str(fixture_script), str(transcript)],
            is_installed=True,
            is_active=False,
            status="inactive",
            risk_level="low",
            created_at=1,
            updated_at=1,
        ),
    )
    insert_tools(
        database,
        [
            McpTool(
                tool_id="native-proof-measure",
                server_id="native-proof",
                name="measure",
                description="Measure a safe local fixture",
                input_schema=input_schema,
                output_schema=output_schema,
                is_enabled=True,
                created_at=1,
            )
        ],
    )
    engine = McpEngine(database, operation_timeout=3)
    repository = GatewayRepository(database)
    gateway = GatewayService(
        workspaces=DatabaseGatewayWorkspace(repository),
        catalog=DatabaseGatewayCatalog(database),
        lifecycle=EngineGatewayLifecycle(engine),
        audit=DatabaseGatewayAudit(repository),
        notifier=GatewayNotificationHub(),
    )
    workspaces = WorkspaceService(
        database,
        parent_dir_provider=lambda: str(tmp_path),
        protected_roots_provider=lambda: (str(tmp_path / "application"),),
    )
    adapter = NativeMcpAdapter(gateway, workspaces.require_safe_session_workspace)
    process = None
    try:
        descriptor = adapter.discover("native-proof-session")["bindings"][0]
        binding = {
            key: descriptor[key]
            for key in (
                "server_id",
                "tool_name",
                "input_schema_digest",
                "output_schema_digest",
            )
        }
        adapter.preflight("native-proof-session", binding)
        assert engine.lifecycle.runner_for("native-proof") is None
        assert not transcript.exists()
        result = await adapter.call(
            "native-proof-session",
            binding,
            {"value": 0.5},
            3,
            "native-local-protocol-trace",
        )
        assert result == '{"value":1.25}'
        runner = engine.lifecycle.runner_for("native-proof")
        assert isinstance(runner, StdioRunner)
        process = runner.process
        assert process and process.pid != os.getpid() and process.returncode is None
        assert fixture_data.read_bytes() == original_data
        messages = [
            json.loads(line)
            for line in transcript.read_text(encoding="utf-8").splitlines()
        ]
        methods = [
            item["message"]["method"]
            for item in messages
            if item["direction"] == "request"
        ]
        assert methods == [
            "initialize",
            "notifications/initialized",
            "tools/list",
            "tools/call",
        ]
        calls = [
            item
            for item in messages
            if item["direction"] == "request"
            and item["message"]["method"] == "tools/call"
        ]
        assert calls[0]["message"]["params"]["name"] == "measure"
        internal_session = next(iter(adapter._owned_sessions))
        audit = repository.list_audit(internal_session)
        success = next(
            item
            for item in audit
            if item["operation"] == "tool.call" and item["outcome"] == "succeeded"
        )
        assert (
            success["server_id"] == "native-proof"
            and success["target_name"] == "measure"
        )
        assert (
            json.loads(success["metadata_json"])["trace_id"]
            == "native-local-protocol-trace"
        )
        evidence = redact_mapping(
            {
                "scope": "disposable local stdio native adapter integration; not catalog qualification",
                "occurred_at": datetime.now(UTC).isoformat(),
                "python_version": sys.version.split()[0],
                "platform": sys.platform,
                "protocol": messages,
                "binding": binding,
                "native_result_text": result,
                "fixture_content_sha256": hashlib.sha256(original_data).hexdigest(),
                "fixture_unchanged": True,
                "audit": [
                    {
                        key: item[key]
                        for key in (
                            "operation",
                            "server_id",
                            "target_name",
                            "outcome",
                            "metadata_json",
                        )
                    }
                    for item in audit
                    if item["operation"] == "tool.call"
                ],
            }
        )
    finally:
        await adapter.close()
        await gateway.shutdown()
    assert process is not None and process.returncode is not None
    evidence["child_exited"] = True
    target = os.getenv("WRIGHT_NATIVE_MCP_EVIDENCE")
    if target:
        evidence_path = Path(target).resolve()
        assert evidence_path.is_relative_to(Path.cwd().resolve()), (
            "Evidence must remain in the test worktree"
        )
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
