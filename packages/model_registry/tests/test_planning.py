from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from fixture_factory import generate_affine_fixture
from model_registry.planning import (
    ModelPlanError,
    confirm_effect_plan,
    create_effect_plan,
)
from model_registry.policy import HostObservation


NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


def test_install_plan_is_complete_canonical_and_principal_bound(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    plan = create_effect_plan(
        fixture.package,
        variant_id="json-cpu-f64",
        snapshot_id="wright-models-bundled-1",
        principal_id="engineer-1",
        host=HostObservation.reference(),
        now=NOW,
        ttl=timedelta(minutes=10),
    )

    assert plan.state == "confirmable"
    assert plan.principal_id == "engineer-1"
    assert plan.manifest_digest == fixture.manifest_digest
    assert len(plan.plan_digest) == 64
    assert plan.requirements.model_dump() == {
        "network": "none",
        "credential": "none",
        "license_action": "none",
        "runtime_change": "separate_plan_only",
    }
    assert {effect.kind for effect in plan.effects} >= {"read", "write", "activate"}
    assert (
        sum(effect.exact_bytes or 0 for effect in plan.effects if effect.kind == "read")
        == fixture.package.variant("json-cpu-f64").resources.download_bytes
    )
    assert all(
        effect.safe_location for effect in plan.effects if effect.kind == "write"
    )
    assert plan.rollback and plan.cleanup and plan.prompts
    assert plan.expires_at == NOW + timedelta(minutes=10)
    assert "token" not in plan.model_dump_json().lower()

    same = create_effect_plan(
        fixture.package,
        variant_id="json-cpu-f64",
        snapshot_id="wright-models-bundled-1",
        principal_id="engineer-1",
        host=HostObservation.reference(),
        now=NOW,
        ttl=timedelta(minutes=10),
    )
    assert same == plan


def test_plan_reports_cache_reuse_references_and_all_policy_blockers(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    variant = fixture.package.variant("json-cpu-f64")
    host = HostObservation(
        platform="linux",
        architecture="aarch64",
        available_disk_bytes=1,
        available_ram_bytes=1,
        accelerators=frozenset(),
        runtime_adapters={},
    )
    plan = create_effect_plan(
        fixture.package,
        variant_id=variant.variant_id,
        snapshot_id="snapshot-1",
        principal_id="engineer-1",
        host=host,
        now=NOW,
        cached_digests={variant.artifacts[0].sha256},
        references=({"kind": "workflow", "owner_id": "flow-1", "effect": "retain"},),
    )

    assert plan.state == "blocked"
    assert {item.category for item in plan.blockers} >= {
        "insufficient_disk",
        "insufficient_resources",
        "runtime_missing",
    }
    assert any(effect.kind == "cache_reuse" for effect in plan.effects)
    assert plan.references[0].owner_id == "flow-1"


def test_confirmation_is_digest_principal_expiry_and_current_conditions_bound(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    plan = create_effect_plan(
        fixture.package,
        variant_id="json-cpu-f64",
        snapshot_id="snapshot-1",
        principal_id="engineer-1",
        host=HostObservation.reference(),
        now=NOW,
    )

    confirmed = confirm_effect_plan(
        plan,
        principal_id="engineer-1",
        plan_digest=plan.plan_digest,
        now=NOW + timedelta(seconds=1),
        current_plan=plan,
    )
    assert confirmed.state == "confirmed"

    cases = [
        {"principal_id": "engineer-2", "plan_digest": plan.plan_digest, "now": NOW},
        {"principal_id": "engineer-1", "plan_digest": "0" * 64, "now": NOW},
        {
            "principal_id": "engineer-1",
            "plan_digest": plan.plan_digest,
            "now": plan.expires_at,
        },
    ]
    for arguments in cases:
        with pytest.raises(ModelPlanError, match="fresh plan") as raised:
            confirm_effect_plan(plan, current_plan=plan, **arguments)
        assert raised.value.code == "plan_invalidated"

    changed = create_effect_plan(
        fixture.package,
        variant_id="json-cpu-f64",
        snapshot_id="snapshot-2",
        principal_id="engineer-1",
        host=HostObservation.reference(),
        now=NOW,
    )
    with pytest.raises(ModelPlanError) as raised:
        confirm_effect_plan(
            plan,
            principal_id="engineer-1",
            plan_digest=plan.plan_digest,
            now=NOW,
            current_plan=changed,
        )
    assert raised.value.code == "plan_invalidated"


def test_blocked_or_already_confirmed_plan_cannot_be_confirmed(tmp_path) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    blocked = create_effect_plan(
        fixture.package,
        variant_id="json-cpu-f64",
        snapshot_id="snapshot-1",
        principal_id="engineer-1",
        host=HostObservation(
            platform="other",
            architecture="other",
            available_disk_bytes=0,
            available_ram_bytes=0,
            accelerators=frozenset(),
            runtime_adapters={},
        ),
        now=NOW,
    )
    with pytest.raises(ModelPlanError) as raised:
        confirm_effect_plan(
            blocked,
            principal_id="engineer-1",
            plan_digest=blocked.plan_digest,
            now=NOW,
            current_plan=blocked,
        )
    assert raised.value.code == "plan_blocked"
