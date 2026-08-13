from datetime import UTC, datetime, timedelta

import pytest
from data_vault import upgrade_database
from fixtures.onboarding_adapters import FakeOnboardingAdapter
from tool_registry.capability_models import MachineCompatibilityObservation
from tool_registry.canonical_catalog import load_canonical_entries
from tool_registry.catalog_snapshots import bootstrap_bundled_snapshot
from tool_registry.compatibility import save_machine_observation
from tool_registry.install_plans import approve_install_plan, create_install_plan
from tool_registry.installers import (
    HostBridgeAdapter,
    LocalCommandAdapter,
    LocalPackageAdapter,
    RemoteEndpointAdapter,
)
from tool_registry.installers.host_bridge import HostBridgeError
from tool_registry.installers.local import LocalAdapterError
from tool_registry.onboarding import apply_install_plan

NOW = datetime(2026, 8, 12, 12, tzinfo=UTC)


def observation() -> MachineCompatibilityObservation:
    return MachineCompatibilityObservation(
        observation_id="machine-adapter",
        observed_at=NOW,
        expires_at=NOW + timedelta(minutes=15),
        platform_key="linux_x64",
        os_name="Linux",
        os_version="test",
        architecture="x86_64",
        distribution_mode="test",
        runtimes={"python": {"available": True}, "node": {"available": True}},
        package_managers={"npm": {"available": True}},
        network_policy="allowed",
        digest="c" * 64,
    )


@pytest.fixture
def approved_plan(tmp_path):
    database = tmp_path / "onboarding.db"
    upgrade_database(database)
    snapshot = bootstrap_bundled_snapshot(database)
    observed = observation()
    save_machine_observation(database, observed)
    entry = next(
        item for item in load_canonical_entries() if item.id == "nvidia-elements-mcp"
    )
    entry = entry.model_copy(
        update={
            "host_software_required": [],
            "license": "MIT",
            "approval_gates": [],
            "installability_tier": "tested",
        }
    )
    plan = create_install_plan(
        database,
        snapshot_id=snapshot.snapshot_id,
        observation=observed,
        entry=entry,
        actor="engineer",
        requested_scope="global_registered",
        now=NOW,
    )
    assert plan.state == "reviewable"
    plan = approve_install_plan(
        database, plan.plan_id, plan.plan_digest, actor="administrator", now=NOW
    )
    return database, plan


def test_local_adapters_require_exact_reviewed_literal_recipe(approved_plan) -> None:
    _, plan = approved_plan
    calls = []
    adapter = LocalPackageAdapter(
        reviewed_recipes={plan.capability_id: {"command": plan.source["command"]}},
        effect_handler=lambda effect: (
            calls.append(effect["kind"]) or {"status": "succeeded"}
        ),
    )
    assert adapter.prepare(plan)["status"] == "succeeded"
    adapter.apply(plan)
    adapter.rollback(plan)
    assert "create_isolated_environment" in calls
    assert "remove" in calls

    command_plan = plan.model_copy(
        update={
            "backend_kind": "local_command",
            "capability_id": "import:draft-1",
            "source": {"command": "python", "arguments": ["server.py"]},
        }
    )
    command_adapter = LocalCommandAdapter(
        reviewed_recipes={
            "import:draft-1": {"command": "python", "arguments": ["server.py"]}
        },
        effect_handler=lambda effect: {"status": "succeeded"},
    )
    assert command_adapter.prepare(command_plan)["status"] == "succeeded"
    with pytest.raises(LocalAdapterError):
        LocalCommandAdapter(reviewed_recipes={}).prepare(command_plan)


def test_remote_adapter_separates_registration_from_read_only_probe(
    approved_plan,
) -> None:
    _, plan = approved_plan
    calls = []
    remote_plan = plan.model_copy(
        update={
            "backend_kind": "remote_endpoint",
            "source": {"endpoint": "https://example.invalid/mcp"},
        }
    )
    adapter = RemoteEndpointAdapter(
        register=lambda endpoint, _: (
            calls.append(("register", endpoint)) or {"status": "succeeded"}
        ),
        unregister=lambda endpoint, _: (
            calls.append(("unregister", endpoint)) or {"status": "succeeded"}
        ),
        read_only_probe=lambda endpoint, _: (
            calls.append(("probe", endpoint)) or {"status": "succeeded"}
        ),
    )
    adapter.prepare(remote_plan)
    assert calls == []
    adapter.apply(remote_plan)
    adapter.validate(remote_plan)
    adapter.rollback(remote_plan)
    assert [item[0] for item in calls] == ["register", "probe", "unregister"]


def test_host_bridge_only_detects_and_verifies_allowlisted_host(approved_plan) -> None:
    _, plan = approved_plan
    host_plan = plan.model_copy(
        update={
            "backend_kind": "host_bridge",
            "requirements": plan.requirements.model_copy(
                update={"host": ["Solid Edge"]}
            ),
        }
    )
    adapter = HostBridgeAdapter(
        host_detectors={"Solid Edge": lambda: {"available": True, "version": "test"}},
        addon_verifiers={"Solid Edge": lambda: {"available": True}},
        handshake=lambda _: {"connected": True, "read_only": True},
        register=lambda _: {"registered": True},
        unregister=lambda _: {"removed": True},
    )
    assert adapter.prepare(host_plan)["hosts"][0]["host"] == "Solid Edge"
    assert adapter.apply(host_plan)["status"] == "succeeded"
    assert adapter.rollback(host_plan)["status"] == "succeeded"

    with pytest.raises(HostBridgeError, match="unavailable"):
        HostBridgeAdapter(
            host_detectors={"Solid Edge": lambda: {"available": False}},
            addon_verifiers={},
        ).prepare(host_plan)


def test_apply_is_idempotent_and_failure_rolls_back_with_redacted_residue(
    approved_plan,
) -> None:
    database, plan = approved_plan
    adapter = FakeOnboardingAdapter(kind="local_package")
    first = apply_install_plan(
        database,
        plan.plan_id,
        plan.plan_digest,
        adapters={"local_package": adapter},
        actor="administrator",
        now=NOW,
        trace_id="trace-apply",
    )
    second = apply_install_plan(
        database,
        plan.plan_id,
        plan.plan_digest,
        adapters={"local_package": adapter},
        actor="administrator",
        now=NOW,
        trace_id="trace-retry",
    )
    assert first == second
    assert adapter.calls == ["prepare", "apply", "validate"]
    assert first["state"] == "completed"


def test_apply_failure_invokes_rollback(approved_plan) -> None:
    database, plan = approved_plan
    adapter = FakeOnboardingAdapter(kind="local_package", fail_at="apply")
    result = apply_install_plan(
        database,
        plan.plan_id,
        plan.plan_digest,
        adapters={"local_package": adapter},
        actor="administrator",
        now=NOW,
        trace_id="trace-failure",
    )
    assert adapter.calls == ["prepare", "apply", "rollback"]
    assert result["state"] == "rolled_back"
    assert result["rollback_state"] == "rolled_back"
    assert result["failure_code"] == "onboarding_effect_failed"


def test_rollback_failure_records_residue_without_exception_text(approved_plan) -> None:
    database, plan = approved_plan

    class ResidueAdapter(FakeOnboardingAdapter):
        def apply(self):
            self.calls.append("apply")
            raise RuntimeError("sensitive injected apply detail")

        def rollback(self):
            self.calls.append("rollback")
            raise RuntimeError("sensitive injected rollback detail")

    adapter = ResidueAdapter(kind="local_package")
    result = apply_install_plan(
        database,
        plan.plan_id,
        plan.plan_digest,
        adapters={"local_package": adapter},
        actor="administrator",
        now=NOW,
        trace_id="trace-residue",
    )
    assert result["state"] == "rollback_failed"
    assert result["rollback_state"] == "rollback_failed"
    assert "sensitive injected" not in str(result)
