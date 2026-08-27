"""Planning-contract and promoted-schema invariants."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema.validators import validator_for


CONTRACT_NAMES = (
    "committed-identity-correction.schema.json",
    "transition-input-correction.schema.json",
    "dashboard.schema.json",
    "gate-catalog.schema.json",
    "gate-evidence.schema.json",
    "legacy-compatibility-profile.schema.json",
    "lifecycle-policy.schema.json",
    "validation-report.schema.json",
    "verification-evidence.schema.json",
)


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", CONTRACT_NAMES)
def test_planning_contract_is_valid_draft_2020_12(
    repository_root: Path, name: str
) -> None:
    schema = load(
        repository_root / "specs/076-control-plane-validator/contracts" / name
    )
    validator_for(schema).check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("name", CONTRACT_NAMES)
def test_approved_contract_is_promoted_byte_for_byte(
    repository_root: Path, name: str
) -> None:
    planned = repository_root / "specs/076-control-plane-validator/contracts" / name
    promoted = (
        repository_root / "docs/programs/engineering-process-platform/schemas" / name
    )
    assert promoted.read_bytes() == planned.read_bytes()


def test_frozen_profiles_are_exact_ordered_contract_projections(
    repository_root: Path,
) -> None:
    contract = load(
        repository_root
        / "specs/076-control-plane-validator/contracts/legacy-compatibility-profile.json"
    )
    fixtures = repository_root / "tests/program_control_plane/fixtures"
    frozen = [
        load(fixtures / "epp-bootstrap-v1-r1-r9.json"),
        load(fixtures / "epp-bridge-v1-r10-r19.json"),
    ]
    assert frozen == contract["profiles"]
    assert [(row["from_revision"], row["through_revision"]) for row in frozen] == [
        (1, 9),
        (10, 19),
    ]
    assert frozen[0]["successor"]["target_profile_id"] == frozen[1]["profile_id"]
    assert frozen[1]["successor"] == {
        "event_kind": "lifecycle_transition",
        "kind": "schema_migration",
        "maximum_count": 1,
        "target_schema_version": "2.0",
    }


def test_task_implementation_paths_stay_inside_lease(repository_root: Path) -> None:
    current = load(
        repository_root
        / "docs/programs/engineering-process-platform/program-state.json"
    )
    archived = load(
        repository_root
        / "docs/programs/engineering-process-platform/evidence/states"
        / f"program-state-revision-{current['revision']:04d}.json"
    )
    assert archived == current
    lease = current["active_mutating_lease"]
    if lease is None:
        assert current["feature_state"] in {
            "CANDIDATE_FROZEN",
            "INDEPENDENTLY_VERIFIED",
            "PUSH_AUTHORIZATION_PENDING",
            "PR_READY",
            "DEV_MERGE_READY",
            "DEV_INTEGRATED",
            "DEV_DEPLOYMENT_VERIFIED",
        }
        return
    allowed = lease["allowed_paths"]
    assert "scripts/program_control/**" in allowed
    assert "tests/program_control_plane/**" in allowed
    assert "docs/programs/engineering-process-platform/**" in allowed
    assert "specs/076-control-plane-validator/**" in allowed
    assert "src/**" not in allowed


def test_git_fixture_builder_uses_fixed_identity_space_path_and_raw_mutation(
    git_builder,
) -> None:
    target = git_builder.write_bytes("control/input.json", b'{"value":1}\n')
    commit = git_builder.commit()
    assert len(commit) == 40
    assert " " in str(git_builder.root)
    git_builder.mutate_raw("control/input.json", b"1", b"2")
    assert target.read_bytes() == b'{"value":2}\n'
    assert ("commit", "-q", "-m", "fixture") in git_builder.spy.calls
