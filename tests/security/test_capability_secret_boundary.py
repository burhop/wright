from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from core.secrets import configure_default_secret_provider
from data_vault import upgrade_database
from data_vault.secret_provider import (
    FileSecretProvider,
    create_default_secret_provider,
)
from tool_registry.capability_models import MachineCompatibilityObservation
from tool_registry.catalog_snapshots import bootstrap_bundled_snapshot
from tool_registry.compatibility import save_machine_observation
from tool_registry.config_import import preview_configuration
from tool_registry.install_plans import create_install_plan
from tool_registry.secrets import write_secrets
from tool_registry.validation_runner import run_capability_validation

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
RAW_SECRET = "wright-capability-secret-sentinel-9127"


class SecretReturningProbe:
    async def initialize(self):
        return {"serverInfo": {"name": "fixture"}, "debug": RAW_SECRET}

    async def initialized(self):
        return None

    async def list_tools(self):
        return [
            {
                "name": "health",
                "description": RAW_SECRET,
                "inputSchema": {"type": "object"},
            }
        ]

    async def call_tool(self, name, arguments):
        return {"name": name, "arguments": arguments, "token": RAW_SECRET}


def _observation() -> MachineCompatibilityObservation:
    return MachineCompatibilityObservation(
        observation_id="machine-secret-boundary",
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=15),
        platform_key="linux_x64",
        os_name="Linux",
        os_version="test",
        architecture="x86_64",
        distribution_mode="test",
        runtimes={"python": {"available": True}},
        package_managers={},
        network_policy="offline",
        digest="a" * 64,
    )


@pytest.mark.asyncio
async def test_raw_credentials_stay_inside_secret_provider_across_capability_artifacts(
    tmp_path, capsys
) -> None:
    database = tmp_path / "secret-boundary.db"
    upgrade_database(database)
    snapshot = bootstrap_bundled_snapshot(database)
    observation = _observation()
    save_machine_observation(database, observation)
    configure_default_secret_provider(
        lambda: FileSecretProvider(tmp_path / "authorized-secrets.json")
    )
    try:
        write_secrets("secret-fixture", {"API_TOKEN": RAW_SECRET})
        preview = preview_configuration(
            {
                "name": "secret-fixture",
                "command": "python",
                "args": ["server.py"],
                "env": {"API_TOKEN": RAW_SECRET},
            },
            now=NOW,
        )
        plan = create_install_plan(
            database,
            snapshot_id=snapshot.snapshot_id,
            observation=observation,
            import_draft=preview["drafts"][0],
            actor="engineer",
            requested_scope="workspace",
            workspace_id="workspace-secret-scan",
            now=NOW,
        )
        evidence = await run_capability_validation(
            database,
            capability_id="secret-fixture",
            server_id="secret-fixture",
            snapshot_id=snapshot.snapshot_id,
            capability_document={"id": "secret-fixture", "transport": "stdio"},
            observation=observation,
            server_revision="1.0.0",
            credential_status={"API_TOKEN": True},
            client=SecretReturningProbe(),
            read_only_probe={
                "name": "health",
                "arguments": {},
                "limitation": "Read-only fixture",
            },
            clock=lambda: NOW,
            trace_id="trace-secret-boundary",
        )
        workflow = {"capability_id": "secret-fixture", "nodes": []}
        with sqlite3.connect(database) as connection:
            connection.execute(
                """INSERT INTO engineering_workspaces (
                    workspace_id, session_id, local_path, enabled_tools,
                    created_at, updated_at, workspace_name
                ) VALUES ('workspace-secret-scan', 'session-secret-scan',
                          'D:/workspace/safe', '["secret-fixture"]', 1, 1,
                          'Secret boundary fixture')"""
            )
            connection.execute(
                """INSERT INTO workspace_workflows (
                    workspace_id, workflow_id, slug, revision, digest, state,
                    updated_at
                ) VALUES ('workspace-secret-scan', 'workflow-secret-scan',
                          'safe-workflow', 1, 'safe-digest', 'active', 1)"""
            )
            connection.commit()
            database_dump = "\n".join(connection.iterdump())
            stored = {
                "snapshots": connection.execute(
                    "SELECT payload_json, envelope_json FROM catalog_snapshots"
                ).fetchall(),
                "plans": connection.execute(
                    "SELECT plan_json FROM mcp_install_plans"
                ).fetchall(),
                "evidence": connection.execute(
                    "SELECT evidence_json FROM mcp_validation_evidence"
                ).fetchall(),
                "workspaces": connection.execute(
                    "SELECT enabled_tools FROM engineering_workspaces"
                ).fetchall(),
                "workflows": connection.execute(
                    "SELECT workflow_id, slug, digest FROM workspace_workflows"
                ).fetchall(),
            }

        public_artifacts = json.dumps(
            {
                "preview": preview,
                "plan": plan.model_dump(mode="json"),
                "evidence": evidence.model_dump(mode="json"),
                "workflow": workflow,
                "stored": stored,
            },
            default=str,
        )
        captured_logs = capsys.readouterr().out
        assert RAW_SECRET not in public_artifacts
        assert RAW_SECRET not in database_dump
        assert RAW_SECRET not in captured_logs
        assert plan.requirements.credentials == ["API_TOKEN"]
        assert len(evidence.credential_binding_digest) == 64
    finally:
        configure_default_secret_provider(create_default_secret_provider)
