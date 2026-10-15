import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta

import pytest
from data_vault import upgrade_database
from tool_registry.capability_models import MachineCompatibilityObservation
from tool_registry.canonical_catalog import load_canonical_entries
from tool_registry.catalog_snapshots import bootstrap_bundled_snapshot
from tool_registry.compatibility import save_machine_observation
from tool_registry.config_import import preview_configuration
from tool_registry.install_plans import (
    InstallPlanError,
    approve_install_plan,
    create_install_plan,
    get_install_plan,
    plan_digest,
    validate_plan_for_apply,
)

NOW = datetime(2026, 8, 12, 12, tzinfo=UTC)


def observation(
    *, expires_at: datetime | None = None
) -> MachineCompatibilityObservation:
    return MachineCompatibilityObservation(
        observation_id="machine-test",
        observed_at=NOW,
        expires_at=expires_at or NOW + timedelta(minutes=15),
        platform_key="linux_x64",
        os_name="Linux",
        os_version="test",
        architecture="x86_64",
        distribution_mode="test",
        runtimes={"python": {"available": True}, "node": {"available": True}},
        package_managers={
            "uv": {"available": True},
            "pip": {"available": True},
            "npm": {"available": True},
        },
        container_runtime={"available": True},
        network_policy="allowed",
        host_observations={},
        digest="a" * 64,
    )


@pytest.fixture
def plan_database(tmp_path):
    database = tmp_path / "plans.db"
    upgrade_database(database)
    snapshot = bootstrap_bundled_snapshot(database)
    current_observation = observation()
    save_machine_observation(database, current_observation)
    return database, snapshot, current_observation


def test_local_remote_host_and_command_plans_are_complete(plan_database) -> None:
    database, snapshot, current_observation = plan_database
    entries = {entry.id: entry for entry in load_canonical_entries()}
    local_package = entries["nvidia-elements-mcp"].model_copy(
        update={"host_software_required": []}
    )
    sources = [
        (local_package, "local_package"),
        (entries["onshape-labs-featurescript-mcp"], "remote_endpoint"),
        (entries["ansys-fluent-mcp"], "host_bridge"),
    ]
    for entry, expected_backend in sources:
        plan = create_install_plan(
            database,
            snapshot_id=snapshot.snapshot_id,
            observation=current_observation,
            entry=entry,
            actor="engineer",
            requested_scope="global_registered",
            independently_completed_license=True,
            now=NOW,
        )
        assert plan.backend_kind == expected_backend
        assert (
            plan.effects
            and plan.steps
            and plan.validation_steps
            and plan.rollback_steps
        )
        assert plan.plan_digest == plan_digest(plan)
        assert plan.expires_at == NOW + timedelta(minutes=30)

    draft = preview_configuration(
        {"name": "custom", "command": "python", "args": ["server.py"]}, now=NOW
    )["drafts"][0]
    imported = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=current_observation,
        import_draft=draft,
        actor="engineer",
        requested_scope="workspace",
        workspace_id="workspace-a",
        now=NOW,
    )
    assert imported.backend_kind == "local_command"
    assert imported.import_draft_digest == draft["draft_digest"]
    assert "advanced_local_command_approval" in imported.approval_gates


@pytest.mark.parametrize(
    "identity,code",
    [
        ("revit-mcp", "catalog_retired"),
        ("webmcp-standard", "catalog_not_an_implementation"),
    ],
)
def test_research_records_cannot_create_an_executable_install_plan(
    plan_database, identity, code
):
    database, snapshot, current_observation = plan_database
    entry = next(item for item in load_canonical_entries() if item.id == identity)
    plan = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=current_observation,
        entry=entry,
        actor="engineer",
        requested_scope="global_registered",
        now=NOW,
    )
    assert plan.state == "blocked"
    assert any(reason.code == code for reason in plan.blocking_reasons)


def test_qualified_autocad_mcp_license_metadata_allows_review(plan_database) -> None:
    database, snapshot, current_observation = plan_database
    entry = next(
        item for item in load_canonical_entries() if item.id == "autocad-mcp-u-c4n"
    )

    plan = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=current_observation,
        entry=entry,
        actor="engineer",
        requested_scope="global_registered",
        now=NOW,
    )

    assert plan.state == "reviewable"
    assert plan.requirements.license.state == "known"
    assert plan.requirements.license.reference == "MIT"
    assert plan.blocking_reasons == []


def test_catalog_license_review_can_clear_missing_metadata(plan_database) -> None:
    database, snapshot, current_observation = plan_database
    entry = next(
        item for item in load_canonical_entries() if item.id == "autocad-mcp-u-c4n"
    ).model_copy(update={"license": None})

    plan = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=current_observation,
        entry=entry,
        actor="engineer",
        requested_scope="global_registered",
        independently_completed_license=True,
        now=NOW,
    )

    assert plan.state == "reviewable"
    assert plan.requirements.license.state == "unknown"
    assert plan.requirements.license.independent_completion_recorded_at == NOW
    assert plan.blocking_reasons == []


def test_external_terms_require_independent_completion_and_never_accept_in_wright(
    plan_database,
) -> None:
    database, snapshot, current_observation = plan_database
    entry = next(
        item
        for item in load_canonical_entries()
        if item.id == "onshape-labs-featurescript-mcp"
    )
    blocked = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=current_observation,
        entry=entry,
        actor="engineer",
        requested_scope="global_registered",
        now=NOW,
    )
    assert blocked.state == "blocked"
    assert blocked.requirements.license.state == "external_acceptance_required"
    assert blocked.requirements.license.independent_completion_recorded_at is None
    assert "external_license_incomplete" in {
        item.code for item in blocked.blocking_reasons
    }
    with pytest.raises(InstallPlanError, match="Blocked"):
        approve_install_plan(
            database,
            blocked.plan_id,
            blocked.plan_digest,
            actor="administrator",
            now=NOW,
        )


def test_digest_approval_expiry_and_material_change_fail_closed(plan_database) -> None:
    database, snapshot, current_observation = plan_database
    draft = preview_configuration(
        {"name": "remote", "type": "http", "url": "https://example.invalid/mcp"},
        now=NOW,
    )["drafts"][0]
    plan = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=current_observation,
        import_draft=draft,
        actor="engineer",
        requested_scope="global_registered",
        now=NOW,
    )
    assert (
        plan.state == "blocked"
    )  # imported source requires independent license review

    # Record the imported source's unknown license as a reviewed test fixture.
    material = plan.model_dump(mode="json")
    material["blocking_reasons"] = []
    material["state"] = "reviewable"
    material["requirements"]["license"] = {
        "state": "not_applicable",
        "reference": None,
        "independent_completion_required": False,
        "independent_completion_recorded_at": None,
    }
    material["plan_digest"] = plan_digest(material)
    from tool_registry.capability_models import InstallPlan

    reviewable = InstallPlan.model_validate(material)
    from tool_registry.install_plans import _persist

    _persist(database, reviewable)
    approved = approve_install_plan(
        database,
        reviewable.plan_id,
        reviewable.plan_digest,
        actor="administrator",
        now=NOW,
    )
    assert approved.state == "approved"
    assert get_install_plan(database, plan.plan_id).approved_by == "administrator"
    validate_plan_for_apply(
        approved,
        approved.plan_digest,
        now=NOW,
        active_snapshot_id=snapshot.snapshot_id,
        observation_digest=current_observation.digest,
    )
    with pytest.raises(InstallPlanError) as stale:
        validate_plan_for_apply(
            approved,
            approved.plan_digest,
            now=NOW,
            active_snapshot_id="changed",
            observation_digest=current_observation.digest,
        )
    assert stale.value.code == "install_plan_invalidated"

    changed = deepcopy(approved.model_dump(mode="json"))
    changed["source"]["endpoint"] = "https://changed.invalid/mcp"
    assert plan_digest(changed) != approved.plan_digest

    with pytest.raises(InstallPlanError) as expired:
        validate_plan_for_apply(
            approved,
            approved.plan_digest,
            now=NOW + timedelta(hours=1),
            active_snapshot_id=snapshot.snapshot_id,
            observation_digest=current_observation.digest,
        )
    assert expired.value.code == "install_plan_expired"


def test_plan_serialization_contains_no_import_secret(plan_database) -> None:
    database, snapshot, current_observation = plan_database
    draft = preview_configuration(
        {
            "name": "local",
            "command": "uvx",
            "args": ["safe-mcp"],
            "env": {"API_TOKEN": "super-secret"},
        },
        now=NOW,
    )["drafts"][0]
    plan = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=current_observation,
        import_draft=draft,
        actor="engineer",
        requested_scope="global_registered",
        now=NOW,
    )
    assert "super-secret" not in json.dumps(plan.model_dump(mode="json"))
    assert plan.requirements.credentials == ["API_TOKEN"]


def test_saved_plan_discovery_is_bounded_and_workspace_provider_scoped(plan_database):
    from tool_registry.install_plans import list_workspace_install_plans

    database, snapshot, obs = plan_database
    entry = next(
        entry
        for entry in load_canonical_entries()
        if entry.id == "onshape-labs-featurescript-mcp"
    )
    plans = []
    for workspace, scope in [
        ("a", "workspace"),
        ("a", "workspace"),
        ("b", "workspace"),
        (None, "global_registered"),
    ]:
        plans.append(
            create_install_plan(
                database,
                snapshot_id=snapshot.snapshot_id,
                observation=obs,
                entry=entry,
                actor="engineer",
                requested_scope=scope,
                workspace_id=workspace,
                independently_completed_license=True,
                now=NOW + timedelta(seconds=len(plans)),
            )
        )
    found = list_workspace_install_plans(database, "a", plans[0].capability_id)
    assert [plan.plan_id for plan in found] == [plans[1].plan_id, plans[0].plan_id]
    assert (
        len(
            list_workspace_install_plans(database, "a", plans[0].capability_id, limit=1)
        )
        == 1
    )
    assert list_workspace_install_plans(database, "a", "other-provider") == []
    assert get_install_plan(database, plans[0].plan_id) == plans[0]
    with pytest.raises(ValueError):
        list_workspace_install_plans(database, "a", plans[0].capability_id, limit=1000)


def test_workspace_discovery_recovers_imported_plan_without_provider_identity(
    plan_database,
):
    from tool_registry.install_plans import list_workspace_install_plans

    database, snapshot, observation = plan_database
    plans = []
    for workspace, scope in [
        ("a", "workspace"),
        ("b", "workspace"),
        (None, "global_registered"),
        ("a", "workspace"),
    ]:
        draft = preview_configuration(
            {
                "name": f"remote-{len(plans)}",
                "type": "http",
                "url": "https://example.invalid/mcp",
            },
            now=NOW,
        )["drafts"][0]
        plans.append(
            create_install_plan(
                database,
                snapshot_id=snapshot.snapshot_id,
                observation=observation,
                import_draft=draft,
                actor="engineer",
                requested_scope=scope,
                workspace_id=workspace,
                now=NOW + timedelta(seconds=len(plans)),
            )
        )
    # Simulate losing the create response: discovery needs only the workspace.
    found = list_workspace_install_plans(database, "a")
    assert [plan.plan_id for plan in found] == [plans[3].plan_id, plans[0].plan_id]
    assert all(plan.capability_id.startswith("import:") for plan in found)
    assert all(plan.state == "blocked" for plan in found)
    assert [
        plan.plan_id for plan in list_workspace_install_plans(database, "a", limit=1)
    ] == [plans[3].plan_id]
    assert list_workspace_install_plans(database, "missing") == []
    assert list_workspace_install_plans(database, "a", "") == []
    assert list_workspace_install_plans(database, "a", plans[0].capability_id) == [
        plans[0]
    ]
    assert get_install_plan(database, plans[0].plan_id) == plans[0]
    for limit in (0, -1, 51):
        with pytest.raises(ValueError):
            list_workspace_install_plans(database, "a", limit=limit)


def test_imported_publisher_review_records_completion_without_approval_or_transfer(
    plan_database,
):
    database, snapshot, observation = plan_database
    draft = preview_configuration(
        {"name": "Remote", "type": "http", "url": "https://example.invalid/mcp"},
        now=NOW,
    )["drafts"][0]
    arguments = dict(
        database_path=database,
        snapshot_id=snapshot.snapshot_id,
        observation=observation,
        import_draft=draft,
        actor="engineer",
        requested_scope="workspace",
        workspace_id="a",
        now=NOW,
    )
    blocked = create_install_plan(**arguments)
    assert blocked.state == "blocked"
    reviewed = create_install_plan(**arguments, independently_completed_license=True)
    assert reviewed.state == "reviewable"
    assert reviewed.requirements.license.state == "unknown"
    assert reviewed.requirements.license.independent_completion_required
    assert reviewed.requirements.license.independent_completion_recorded_at == NOW
    assert reviewed.import_draft_digest == draft["draft_digest"]
    assert reviewed.approved_by is None
    assert reviewed.plan_digest != blocked.plan_digest
    assert get_install_plan(database, blocked.plan_id) == blocked
    with pytest.raises(InstallPlanError):
        approve_install_plan(
            database,
            reviewed.plan_id,
            blocked.plan_digest,
            actor="administrator",
            now=NOW,
        )
    changed = preview_configuration(
        {"name": "Remote", "type": "http", "url": "https://other.invalid/mcp"},
        now=NOW,
    )["drafts"][0]
    changed_plan = create_install_plan(**{**arguments, "import_draft": changed})
    assert changed_plan.state == "blocked"
    assert changed_plan.requirements.license.independent_completion_recorded_at is None
