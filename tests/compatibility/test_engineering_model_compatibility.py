from __future__ import annotations

import sqlite3
import time
import tomllib
from pathlib import Path

import pytest
from data_vault import (
    MIGRATIONS,
    ModelArtifactStore,
    ModelRepository,
    create_backup,
    database_status,
    restore_backup,
    upgrade_database,
)
from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_resources import GatewayResourceProvider
from tool_registry.gateway_service import GatewayService
from tool_registry.models import McpServer
from workspace_service import EngineeringModelService, RivetCapabilityService


REPO_ROOT = Path(__file__).resolve().parents[2]


def _table_names(database: Path) -> set[str]:
    with sqlite3.connect(database) as connection:
        return {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }


def test_migration_15_to_16_is_additive_and_preserves_existing_settings(
    tmp_path,
) -> None:
    database = tmp_path / "migration-15.db"
    upgrade_database(database, migrations=MIGRATIONS[:15])
    before = _table_names(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO system_settings(key, value) VALUES (?, ?)",
            ("llm_provider", "openai-compatible"),
        )
    result = upgrade_database(database, migrations=MIGRATIONS[:16])
    after = _table_names(database)

    assert result.starting_version == 15
    assert result.ending_version == 16
    assert before <= after
    assert {
        "model_install_plans",
        "model_operations",
        "model_installations",
        "model_capability_bindings",
        "model_references",
    } <= after
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT value FROM system_settings WHERE key='llm_provider'"
        ).fetchone() == ("openai-compatible",)


class Workspaces:
    def resolve_binding(self, *, session_id, principal_id, workspace_id):
        assert (session_id, principal_id, workspace_id) == (
            "session-one",
            "wright-rivet",
            "workspace-one",
        )
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": "/workspace",
        }

    def enabled_server_ids(self, _session):
        return {"cad"}


class Catalog:
    def __init__(self) -> None:
        now = int(time.time())
        self.server = McpServer(
            server_id="cad",
            name="Existing CAD MCP",
            type="stdio",
            command="cad",
            is_active=True,
            is_installed=True,
            status="active",
            created_at=now,
            updated_at=now,
        )

    def servers(self):
        return (self.server,)

    def tools(self, server_id):
        assert server_id == "cad"
        return (
            GatewayTool(
                name="cad__inspect",
                server_id="cad",
                tool_name="inspect",
                description="Inspect existing deterministic CAD state.",
                input_schema={"type": "object", "additionalProperties": False},
                output_schema={"type": "object"},
                provenance={"server_revision": "existing-cad-v1"},
            ),
        )

    def resources(self, _session):
        return ()


class Lifecycle:
    async def ensure_started(self, *_args, **_kwargs):
        return None

    async def call_tool(self, server_id, tool_name, arguments, **_kwargs):
        return {
            "server": server_id,
            "tool": tool_name,
            "arguments": dict(arguments),
        }

    async def shutdown(self):
        return None


class Audit:
    def __init__(self) -> None:
        self.events = []

    def record(self, event):
        self.events.append(dict(event))


@pytest.mark.asyncio
async def test_existing_gateway_mcp_and_rivet_discovery_remain_compatible() -> None:
    gateway = GatewayService(
        workspaces=Workspaces(),
        catalog=Catalog(),
        lifecycle=Lifecycle(),
        audit=Audit(),
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
    )
    gateway.open_session(
        session_id="session-one",
        principal_id="wright-rivet",
        workspace_id="workspace-one",
        transport="legacy",
    )
    gateway.initialize_session(
        "session-one",
        protocol_version="2025-11-25",
        client_name="wright-rivet",
        client_version="2",
        client_capabilities={},
    )
    assert [tool.name for tool in gateway.list_tools("session-one")] == ["cad__inspect"]
    result = await gateway.call_tool("session-one", "request-one", "cad__inspect", {})
    assert result.structured_content == {
        "server": "cad",
        "tool": "inspect",
        "arguments": {},
    }
    rivet = RivetCapabilityService(
        gateway, session_resolver=lambda _session, _workspace: "session-one"
    ).discover(session_id="session-one", workspace_id="workspace-one")
    assert [tool.qualified_tool_name for tool in rivet.tools] == ["cad__inspect"]
    await gateway.shutdown()


def test_model_lifecycle_does_not_change_conversational_provider_setup(
    tmp_path,
) -> None:
    database = tmp_path / "provider-state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO system_settings(key, value) VALUES (?, ?)",
            ("llm_provider", "openai-codex"),
        )
    service = EngineeringModelService(
        repository=ModelRepository(str(database)),
        artifact_store=ModelArtifactStore(tmp_path / "models"),
    )
    plan = service.create_plan(
        operation_kind="install",
        model_id="wright-affine-test",
        variant_id="json-cpu-f64",
        principal_id="engineer-one",
    )
    service.confirm_plan(
        plan["plan_id"],
        principal_id="engineer-one",
        plan_digest=plan["plan_digest"],
        trace_id="trace-provider-compatibility",
    )
    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT value FROM system_settings WHERE key='llm_provider'"
        ).fetchone() == ("openai-codex",)

    app_source = (REPO_ROOT / "apps/web/src/App.tsx").read_text(encoding="utf-8")
    assert 'path="/setup/model"' in app_source
    assert 'path="/engineering-models"' in app_source


def test_backup_restore_preserves_model_state_and_verified_content(tmp_path) -> None:
    database = tmp_path / "backup-state.db"
    upgrade_database(database)
    store = ModelArtifactStore(tmp_path / "models")
    service = EngineeringModelService(
        repository=ModelRepository(str(database)), artifact_store=store
    )
    plan = service.create_plan(
        operation_kind="install",
        model_id="wright-affine-test",
        variant_id="json-cpu-f64",
        principal_id="engineer-one",
    )
    installed = service.confirm_plan(
        plan["plan_id"],
        principal_id="engineer-one",
        plan_digest=plan["plan_digest"],
        trace_id="trace-backup",
    )
    installation_id = installed["result"]["installation_id"]
    backup = create_backup(database, output_dir=tmp_path / "backups")
    service.maintenance.disable(installation_id)
    assert (
        ModelRepository(str(database)).get_installation(installation_id)["state"]
        == "disabled"
    )

    restored = restore_backup(database, backup.manifest_path)
    installation = ModelRepository(str(database)).get_installation(installation_id)
    assert restored.ready is True
    assert installation is not None and installation["state"] == "installed"
    assert all(
        store.has_verified(str(row["content_digest"]))
        for row in ModelRepository(str(database)).installation_artifacts(
            installation_id
        )
    )


def test_native_and_docker_package_manifests_include_model_registry_without_payloads() -> (
    None
):
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    members = set(project["tool"]["uv"]["workspace"]["members"])
    wheel_packages = set(
        project["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    )
    testpaths = set(project["tool"]["pytest"]["ini_options"]["testpaths"])
    assert "packages/model_registry" in members
    assert "packages/model_registry/src/model_registry" in wheel_packages
    assert "packages/model_registry/tests" in testpaths

    expected_manifests = {
        "apps/api/pyproject.toml",
        "hermes-plugin-wright/pyproject.toml",
        "packages/core/pyproject.toml",
        "packages/agent_adapters/pyproject.toml",
        "packages/tool_registry/pyproject.toml",
        "packages/data_vault/pyproject.toml",
        "packages/model_registry/pyproject.toml",
        "packages/workspace_service/pyproject.toml",
    }
    for dockerfile in ("docker/Dockerfile", "docker/Dockerfile.dev"):
        text = (REPO_ROOT / dockerfile).read_text(encoding="utf-8")
        assert all(manifest in text for manifest in expected_manifests)
        assert ".onnx" not in text
        assert ".safetensors" not in text

    assert (
        database_status(REPO_ROOT / ".nonexistent-compatibility.db").target_version
        == 17
    )
