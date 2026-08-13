from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from datetime import UTC, datetime
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from core.secrets import configure_default_secret_provider
from data_vault import upgrade_database
from data_vault.secret_provider import (
    FileSecretProvider,
    create_default_secret_provider,
)
from tool_registry.capability_views import (
    build_capability_views,
    find_capability,
    load_workspace_membership,
)
from tool_registry.catalog_models import CatalogEntry
from tool_registry.catalog_reconcile import (
    reconcile_active_engineering_catalog,
    reconcile_engineering_catalog_document,
)
from tool_registry.catalog_signing import CatalogTrustRoot
from tool_registry.catalog_snapshots import (
    bootstrap_bundled_snapshot,
    get_catalog_state,
    known_catalog_server_ids,
    load_active_catalog,
)
from tool_registry.catalog_updates import (
    activate_catalog_update,
    preview_catalog_update,
    rollback_catalog,
)
from tool_registry.compatibility import observe_machine
from tool_registry.secrets import read_secrets, write_secrets
from tool_registry.services import list_registered_servers

_FIXTURE_PATH = (
    Path(__file__).parents[2] / "data_vault" / "tests" / "capability_library_v12.py"
)
_FIXTURE_SPEC = spec_from_file_location("capability_library_v12", _FIXTURE_PATH)
assert _FIXTURE_SPEC is not None and _FIXTURE_SPEC.loader is not None
_FIXTURE = module_from_spec(_FIXTURE_SPEC)
_FIXTURE_SPEC.loader.exec_module(_FIXTURE)
CUSTOM_SERVER_ID = _FIXTURE.CUSTOM_SERVER_ID
ERROR_SERVER_ID = _FIXTURE.ERROR_SERVER_ID
LEGACY_CATALOG_SERVER_ID = _FIXTURE.LEGACY_CATALOG_SERVER_ID
LEGACY_TOOL_ID = _FIXTURE.LEGACY_TOOL_ID
WORKSPACE_ID = _FIXTURE.WORKSPACE_ID
create_capability_library_v12_database = _FIXTURE.create_capability_library_v12_database
_CATALOG_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "catalog_updates.py"
_CATALOG_FIXTURE_SPEC = spec_from_file_location(
    "capability_catalog_updates", _CATALOG_FIXTURE_PATH
)
assert _CATALOG_FIXTURE_SPEC is not None and _CATALOG_FIXTURE_SPEC.loader is not None
_CATALOG_FIXTURE = module_from_spec(_CATALOG_FIXTURE_SPEC)
_CATALOG_FIXTURE_SPEC.loader.exec_module(_CATALOG_FIXTURE)
TEST_KEY_ID = _CATALOG_FIXTURE.TEST_KEY_ID
TEST_PUBLIC_KEY = _CATALOG_FIXTURE.TEST_PUBLIC_KEY
prior_69_catalog = _CATALOG_FIXTURE.prior_69_catalog
signed_catalog = _CATALOG_FIXTURE.signed_catalog

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
ROOT = CatalogTrustRoot("test", TEST_KEY_ID, TEST_PUBLIC_KEY)
WORKSPACE_ONLY_SERVER_ID = "zoo-dev-cloud-cad"


def _observation():
    return observe_machine(
        clock=lambda: NOW,
        which=lambda _name: None,
        version_reader=lambda _path: None,
        system_reader=lambda: "Linux",
        version_system_reader=lambda: "test",
        architecture_reader=lambda: "x86_64",
        network_policy="offline",
    )


def _user_owned_state(database) -> dict[str, object]:
    with sqlite3.connect(database) as connection:
        catalog_user_state = connection.execute(
            """SELECT server_id, is_active, is_installed, status, error_message,
                      installed_version, env_vars, credentials_required,
                      default_enabled, created_at
               FROM mcp_servers WHERE server_id IN (?, ?)
               ORDER BY server_id""",
            (LEGACY_CATALOG_SERVER_ID, WORKSPACE_ONLY_SERVER_ID),
        ).fetchall()
        custom_rows = connection.execute(
            "SELECT * FROM mcp_servers WHERE server_id IN (?, ?) ORDER BY server_id",
            (CUSTOM_SERVER_ID, ERROR_SERVER_ID),
        ).fetchall()
        tool = connection.execute(
            "SELECT * FROM mcp_tools WHERE tool_id=?", (LEGACY_TOOL_ID,)
        ).fetchone()
        workspace = connection.execute(
            "SELECT * FROM engineering_workspaces WHERE workspace_id=?",
            (WORKSPACE_ID,),
        ).fetchone()
    return {
        "catalog_user_state": catalog_user_state,
        "custom_rows": custom_rows,
        "tool": tool,
        "workspace": workspace,
        "secrets": read_secrets(LEGACY_CATALOG_SERVER_ID),
    }


def _views(database, document):
    entries = [CatalogEntry.model_validate(item) for item in document["servers"]]
    return build_capability_views(
        entries,
        list_registered_servers(str(database)),
        _observation(),
        workspace_membership=load_workspace_membership(database),
        known_catalog_ids=frozenset(known_catalog_server_ids(database)),
    )


def test_v12_state_survives_activate_restart_removed_entries_and_rollback(
    tmp_path,
) -> None:
    database = create_capability_library_v12_database(tmp_path / "legacy-v12.db")
    upgrade_database(database)
    prior = prior_69_catalog()
    bootstrap_bundled_snapshot(database, payload=prior)
    reconcile_engineering_catalog_document(str(database), prior)
    secret_path = tmp_path / "secrets.json"
    configure_default_secret_provider(lambda: FileSecretProvider(secret_path))
    write_secrets(LEGACY_CATALOG_SERVER_ID, {"APS_CLIENT_ID": "preserve-me"})

    try:
        with sqlite3.connect(database) as connection:
            enabled = json.loads(
                connection.execute(
                    "SELECT enabled_tools FROM engineering_workspaces WHERE workspace_id=?",
                    (WORKSPACE_ID,),
                ).fetchone()[0]
            )
            enabled.append(WORKSPACE_ONLY_SERVER_ID)
            connection.execute(
                "UPDATE engineering_workspaces SET enabled_tools=? WHERE workspace_id=?",
                (json.dumps(enabled), WORKSPACE_ID),
            )
            connection.commit()

        initial_views = _views(database, prior)
        canonical = find_capability(initial_views, "aps-mcp-server-nodejs")
        legacy_alias = find_capability(initial_views, LEGACY_CATALOG_SERVER_ID)
        assert canonical is not None and legacy_alias is canonical
        assert canonical.user_state.server_id == LEGACY_CATALOG_SERVER_ID
        before = _user_owned_state(database)

        candidate = deepcopy(prior)
        candidate["servers"] = [
            item
            for item in candidate["servers"]
            if item["id"] not in {"aps-mcp-server-nodejs", "zoo-mcp"}
        ]
        preview = preview_catalog_update(
            database,
            signed_catalog(candidate, issued_at=NOW),
            trust_root=ROOT,
            actor="admin-preservation",
            now=NOW,
            trace_id="trace-preservation-preview",
        )
        activate_catalog_update(
            database,
            preview["preview_id"],
            preview["preview_digest"],
            actor="admin-preservation",
            now=NOW,
            trace_id="trace-preservation-activate",
        )
        assert _user_owned_state(database) == before

        active, diagnostic = load_active_catalog(database)
        assert diagnostic is None
        assert len(active["servers"]) == 67
        removed_views = _views(database, active)
        removed_installed = find_capability(removed_views, LEGACY_CATALOG_SERVER_ID)
        removed_workspace = find_capability(removed_views, WORKSPACE_ONLY_SERVER_ID)
        assert removed_installed is not None and removed_installed.custom is True
        assert removed_workspace is not None and removed_workspace.custom is True
        assert removed_workspace.user_state.enabled_workspaces[0]["workspace_id"] == (
            WORKSPACE_ID
        )

        count, restart_diagnostic = reconcile_active_engineering_catalog(str(database))
        assert count == 67
        assert restart_diagnostic is None
        assert _user_owned_state(database) == before
        restarted, diagnostic = load_active_catalog(database)
        assert diagnostic is None
        assert len(restarted["servers"]) == 67

        state = get_catalog_state(database)
        rollback_catalog(
            database,
            expected_active_snapshot_id=state["active_snapshot_id"],
            expected_previous_snapshot_id=state["previous_snapshot_id"],
            actor="admin-preservation",
            now=NOW,
            trace_id="trace-preservation-rollback",
        )
        assert _user_owned_state(database) == before
        restored, diagnostic = load_active_catalog(database)
        assert diagnostic is None
        assert len(restored["servers"]) == 69
        restored_view = find_capability(
            _views(database, restored), LEGACY_CATALOG_SERVER_ID
        )
        assert restored_view is not None and restored_view.custom is False
        assert restored_view.user_state.installed is True
    finally:
        configure_default_secret_provider(create_default_secret_provider)
