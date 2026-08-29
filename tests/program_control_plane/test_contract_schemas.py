"""Planning-contract and promoted-schema invariants."""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import pytest
from jsonschema.validators import validator_for


CONTRACT_NAMES = (
    "checkpoint-evidence-correction.schema.json",
    "committed-identity-correction.schema.json",
    "preflight-evidence-correction.schema.json",
    "transition-input-correction.schema.json",
    "v8-discovery-evidence.schema.json",
    "dashboard.schema.json",
    "gate-catalog.schema.json",
    "gate-evidence.schema.json",
    "legacy-compatibility-profile.schema.json",
    "lifecycle-policy.schema.json",
    "validation-report.schema.json",
    "verification-evidence.schema.json",
)


def test_f01b_activation_correction_is_closed_to_three_tr0070_digests(
    repository_root: Path,
) -> None:
    root = repository_root / "docs/programs/engineering-process-platform"
    schema = load(root / "schemas/f01b-activation-correction.schema.json")
    profile = load(
        root / "evidence/corrections/COR-EPP-F01B-ACTIVATION-RAW-IDENTITY-001.json"
    )

    validator_for(schema).check_schema(schema)
    validator_for(schema)(schema).validate(profile)
    assert profile["expected_claim_count"] == 3
    assert [claim["json_pointer"] for claim in profile["claims"]] == [
        "/outputs/3/sha256",
        "/outputs/4/sha256",
        "/outputs/5/sha256",
    ]


def test_v8_checkpoint_correction_is_closed_and_schema_valid(
    repository_root: Path,
) -> None:
    schema = load(
        repository_root
        / "docs/programs/engineering-process-platform/schemas"
        / "checkpoint-evidence-correction.schema.json"
    )
    profile = load(
        repository_root
        / "docs/programs/engineering-process-platform/evidence/corrections"
        / "COR-EPP-F01-T072-CHECKPOINT-EVIDENCE-001.json"
    )
    validator_for(schema)(schema).validate(profile)
    assert profile["expected_claim_count"] == 3
    assert [claim["claim_id"] for claim in profile["claims"]] == [
        "TR0047-README-OUTPUT-DIGEST-001",
        "TR0047-APPROVAL-OUTPUT-DIGEST-001",
        "TR0050-EVENT-RULE-001",
    ]


def test_v9_preflight_correction_is_closed_and_externally_validates_discovery(
    repository_root: Path,
) -> None:
    schemas = repository_root / "docs/programs/engineering-process-platform/schemas"
    evidence = repository_root / "docs/programs/engineering-process-platform/evidence"
    correction_schema = load(schemas / "preflight-evidence-correction.schema.json")
    profile = load(evidence / "corrections/COR-EPP-F01-V9-PREFLIGHT-EVIDENCE-001.json")
    validator_for(correction_schema)(correction_schema).validate(profile)
    assert profile["expected_claim_count"] == 2
    assert [claim["claim_id"] for claim in profile["claims"]] == [
        "V8-DISCOVERY-SCHEMA-REFERENCE-001",
        "TR0051-MANIFEST-ORDER-001",
    ]

    discovery_schema = load(schemas / "v8-discovery-evidence.schema.json")
    discovery = load(evidence / "verification/EPP-F01-V8-discovery.json")
    validator_for(discovery_schema)(discovery_schema).validate(discovery)
    assert "$schema" not in discovery


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
            "BLOCKED",
            "CANDIDATE_FROZEN",
            "INDEPENDENTLY_VERIFIED",
            "PUSH_AUTHORIZATION_PENDING",
            "PR_READY",
            "DEV_MERGE_READY",
            "DEV_INTEGRATED",
            "DEV_DEPLOYMENT_VERIFIED",
        }
        if current["feature_state"] == "BLOCKED":
            assert all(
                action["requires_human_approval"]
                for action in current["next_eligible_actions"]
            )
        return
    allowed = lease["allowed_paths"]
    assert "docs/programs/engineering-process-platform/**" in allowed
    assert "src/**" not in allowed
    if lease["lease_mode"] == "planning":
        assert any(path.startswith("specs/") for path in allowed)
        assert "scripts/program_control/**" not in allowed
        assert "tests/program_control_plane/**" not in allowed
    else:
        assert lease["feature_id"] == current["current_feature"]
        assert "edit_allowlisted_paths" in lease["allowed_actions"]
        task_contracts = [
            path
            for path in (repository_root / "specs").glob("*/tasks.md")
            if any(
                line.startswith("**Authority**:") and lease["feature_id"] in line
                for line in path.read_text("utf-8").splitlines()
            )
        ]
        assert len(task_contracts) == 1
        task_text = task_contracts[0].read_text("utf-8")
        task_paths = {
            token.rstrip("/")
            for token in re.findall(r"`([^`]+)`", task_text)
            if token.startswith(
                (
                    "apps/",
                    "docs/",
                    "packages/",
                    "scripts/",
                    "specs/",
                    "src/",
                    "tests/",
                    "pyproject.toml",
                )
            )
            and " " not in token
            and not token.startswith("http")
        }
        assert task_paths
        uncovered = {
            path
            for path in task_paths
            if not any(
                fnmatch.fnmatchcase(path, pattern)
                or (pattern.endswith("/**") and path == pattern[:-3])
                for pattern in allowed
            )
        }
        assert uncovered == set()


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
