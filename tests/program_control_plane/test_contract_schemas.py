"""Planning-contract and promoted-schema invariants."""

from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

import pytest
from jsonschema.validators import validator_for

from program_control.validation import _validate_documents


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

EPP_F01B_CONTRACT_NAMES = (
    "program-status-bundle.schema.json",
    "program-status-source-catalog.schema.json",
    "work-registry.schema.json",
    "use-case-registry.schema.json",
    "test-run-ledger.schema.json",
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


@pytest.mark.parametrize("name", EPP_F01B_CONTRACT_NAMES)
def test_epp_f01b_planning_contract_is_valid_draft_2020_12(
    repository_root: Path, name: str
) -> None:
    schema = load(repository_root / "specs/077-browser-program-status/contracts" / name)
    validator_for(schema).check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_epp_f01b_source_catalog_is_closed_to_twenty_sources(
    repository_root: Path,
) -> None:
    contracts = repository_root / "specs/077-browser-program-status/contracts"
    schema = load(contracts / "program-status-source-catalog.schema.json")
    catalog = load(contracts / "program-status-source-catalog.json")
    validator_for(schema)(schema).validate(catalog)
    assert list(catalog["sources"]) == catalog["conflict_policy"]["source_precedence"]
    assert len(catalog["sources"]) == 20
    assert list(catalog["sources"])[-5:] == [
        "work_registry",
        "use_case_registry",
        "test_run_ledger",
        "customer_story_catalog",
        "feature_tasks",
    ]
    assert (
        "https://wright.local/programs/epp/f01b-activation-correction.schema.json"
        in catalog["sources"]["correction_evidence"]["schema_ids"]
    )
    stage_policy = catalog["conflict_policy"]["use_case_stage_policy"]
    assert stage_policy["definition"]["allowed_sources"] == [
        "roadmap",
        "customer_story_catalog",
    ]
    assert stage_policy["progress"]["allowed_sources"] == [
        "transition_evidence",
        "work_registry",
        "feature_tasks",
    ]
    assert stage_policy["customer_acceptance"]["allowed_sources"] == [
        "gate_evidence",
        "verification_evidence",
    ]
    assert stage_policy["test"]["allowed_sources"] == [
        "test_run_ledger",
        "verification_evidence",
    ]
    assert stage_policy["independent_verification"]["allowed_sources"] == [
        "verification_evidence"
    ]
    assert stage_policy["benchmark_qualification"]["allowed_sources"] == [
        "dashboard",
        "benchmark_coverage",
        "gate_evidence",
        "verification_evidence",
    ]


def test_epp_f02_source_admission_is_exact_and_parity_bound(
    repository_root: Path,
) -> None:
    planning = repository_root / "specs/077-browser-program-status/contracts"
    packaged = repository_root / "src/wright_engineering/static/program-status"
    program = repository_root / "docs/programs/engineering-process-platform"

    planning_bundle = load(planning / "program-status-bundle.schema.json")
    packaged_bundle = load(packaged / "program-status-bundle.schema.json")
    assert planning_bundle == packaged_bundle
    bundle_pattern = planning_bundle["$defs"]["relativePath"]["pattern"]
    assert re.fullmatch(bundle_pattern, "specs/078-process-definition-view/tasks.md")
    assert (
        re.fullmatch(bundle_pattern, "specs/079-process-definition-view/tasks.md")
        is None
    )

    use_case_schemas = [
        load(planning / "use-case-registry.schema.json"),
        load(packaged / "use-case-registry.schema.json"),
        load(program / "schemas/use-case-registry.schema.json"),
    ]
    assert use_case_schemas[0] == use_case_schemas[1] == use_case_schemas[2]
    use_case_pattern = use_case_schemas[0]["$defs"]["relativePath"]["pattern"]
    assert re.fullmatch(use_case_pattern, "specs/078-process-definition-view/tasks.md")
    assert (
        re.fullmatch(use_case_pattern, "specs/078-process-definition-viewish/tasks.md")
        is None
    )

    planning_catalog = load(planning / "program-status-source-catalog.json")
    packaged_catalog = load(packaged / "program-status-source-catalog.json")
    assert planning_catalog == packaged_catalog
    assert len(planning_catalog["sources"]) == 20
    feature_tasks = planning_catalog["sources"]["feature_tasks"]
    assert feature_tasks["path"] == "specs/078-process-definition-view/tasks.md"
    assert "EPP-F02" in feature_tasks["selection_rule"]
    assert "EPP-F01B task graph" not in feature_tasks["selection_rule"]

    work_registry = load(program / "work-registry.json")
    active = [
        row for row in work_registry["task_sources"] if row["active_feature"] is True
    ]
    assert active == [
        {
            "feature_id": "EPP-F02",
            "tasks_path": "specs/078-process-definition-view/tasks.md",
            "roadmap_item_id": "EPP-F02",
            "active_feature": True,
        }
    ]

    use_case_registry = load(program / "use-case-registry.json")
    assert len(use_case_registry["use_cases"]) == 1
    use_case = use_case_registry["use_cases"][0]
    assert use_case["id"] == "EPP-UC-001"
    assert use_case["process_100_id"] is None
    assert use_case["definition_evidence"] == []
    assert use_case["progress_evidence"] == []
    assert len(use_case["acceptance_evidence"]) == 1
    assert len(use_case["test_evidence"]) == 1
    assert len(use_case["independent_verification_evidence"]) == 1
    assert use_case["benchmark_qualification_evidence"] == []

    verification_schema_id = (
        "https://wright.local/programs/epp/epp-f02-verification-evidence.schema.json"
    )
    assert (
        verification_schema_id
        in planning_catalog["sources"]["verification_evidence"]["schema_ids"]
    )
    verification_schema = load(
        program / "schemas/epp-f02-verification-evidence.schema.json"
    )
    validator_for(verification_schema).check_schema(verification_schema)
    candidate = load(program / "evidence/verification/EPP-F02-candidate.json")
    independent = load(program / "evidence/verification/EPP-F02-independent.json")
    validator_for(verification_schema)(verification_schema).validate(candidate)
    validator_for(verification_schema)(verification_schema).validate(independent)

    acceptance = use_case["acceptance_evidence"][0]
    tested = use_case["test_evidence"][0]
    verified = use_case["independent_verification_evidence"][0]
    assert acceptance["subject_id"] == candidate["evidence_id"]
    assert tested["subject_id"] == "CANDIDATE-TEST-MATRIX"
    assert verified["subject_id"] == independent["evidence_id"]
    assert verified["acceptance_subject_id"] == candidate["evidence_id"]
    assert acceptance["evidence_author"] == candidate["actor"]["identity"]
    assert tested["evidence_author"] == candidate["actor"]["identity"]
    assert verified["evidence_author"] == candidate["actor"]["identity"]
    assert verified["independent_verifier"] == independent["actor"]["identity"]
    assert verified["evidence_author"] != verified["independent_verifier"]


def test_epp_f01b_registry_documents_use_only_their_frozen_schemas(
    repository_root: Path,
) -> None:
    program_root = "docs/programs/engineering-process-platform"
    registry_names = (
        "work-registry.json",
        "use-case-registry.json",
        "test-run-ledger.json",
    )
    paths = [
        f"{program_root}/schemas/{name.removesuffix('.json')}.schema.json"
        for name in registry_names
    ] + [f"{program_root}/{name}" for name in registry_names]
    blobs = {path: (repository_root / path).read_bytes() for path in paths}

    class BlobReader:
        def blob(self, _commit: str, path: str) -> bytes:
            return blobs[path]

    findings = []
    documents = _validate_documents(
        BlobReader(),  # type: ignore[arg-type]
        "f" * 40,
        program_root,
        [{"path": path} for path in paths],
        findings,
    )

    assert all(f"{program_root}/{name}" in documents for name in registry_names)
    assert not [
        finding
        for finding in findings
        if finding.artifact in {f"{program_root}/{name}" for name in registry_names}
        and finding.code
        in {
            "SCHEMA_VERSION_INVALID",
            "SCHEMA_REFERENCE_MISSING",
            "SCHEMA_VALIDATION_FAILED",
        }
    ]


@pytest.mark.parametrize(
    "registry_name",
    ("work-registry.json", "use-case-registry.json", "test-run-ledger.json"),
)
def test_epp_f01b_registry_routing_is_exact_to_the_authoritative_program_root(
    repository_root: Path, registry_name: str
) -> None:
    program_root = "docs/programs/alternate-engineering-program"
    target = f"{program_root}/{registry_name}"
    blobs = {target: b'{"schema_version":"1.0.0"}\n'}

    class BlobReader:
        def blob(self, _commit: str, path: str) -> bytes:
            return blobs[path]

    findings = []
    _validate_documents(
        BlobReader(),  # type: ignore[arg-type]
        "f" * 40,
        program_root,
        [{"path": target}],
        findings,
    )

    assert any(
        finding.code == "SCHEMA_VERSION_INVALID" and finding.artifact == target
        for finding in findings
    )


def test_lifecycle_policy_projects_exact_operating_limits(
    repository_root: Path,
) -> None:
    root = repository_root / "docs/programs/engineering-process-platform"
    schema = load(root / "schemas/lifecycle-policy.schema.json")
    policy = load(root / "lifecycle-policy.json")
    catalog = load(
        repository_root
        / "specs/077-browser-program-status/contracts/program-status-source-catalog.json"
    )

    validator_for(schema)(schema).validate(policy)
    assert policy["wip_limits"] == {
        "mutating_leases": 1,
        "implementing_or_repairing_features": 1,
        "read_only_auditors": 3,
        "wip_max": 1,
        "repair_max": 2,
        "push_max": 2,
    }
    assert (
        "/supplement/governance/limits"
        in catalog["sources"]["lifecycle_policy"]["projects_to"]
    )


def test_epp_f01b_progress_contract_carries_independently_checkable_inputs(
    repository_root: Path,
) -> None:
    contracts = repository_root / "specs/077-browser-program-status/contracts"
    use_cases = load(contracts / "use-case-registry.schema.json")
    test_ledger = load(contracts / "test-run-ledger.schema.json")
    bundle = load(contracts / "program-status-bundle.schema.json")
    tasks = (repository_root / "specs/077-browser-program-status/tasks.md").read_text(
        encoding="utf-8"
    )

    assert "tests/" not in use_cases["$defs"]["relativePath"]["pattern"]
    assert (
        use_cases["$defs"]["useCase"]["properties"]["process_100_id"]["pattern"]
        == r"^EPP-PROC-(?:00[1-9]|0[1-9][0-9]|100)$"
    )
    assert "source_name" in use_cases["$defs"]["stageEvidence"]["required"]
    assert "acceptance_subject_id" in use_cases["$defs"]["stageEvidence"]["required"]
    assert "evidence_author" in use_cases["$defs"]["stageEvidence"]["required"]
    assert "independent_verifier" in use_cases["$defs"]["stageEvidence"]["required"]

    assert use_cases["$defs"]["definitionEvidence"]["allOf"][1]["properties"][
        "source_name"
    ]["enum"] == ["roadmap", "customer_story_catalog"]
    assert (
        use_cases["$defs"]["verificationEvidence"]["allOf"][1]["properties"][
            "source_name"
        ]["const"]
        == "verification_evidence"
    )

    ledger_required = test_ledger["required"]
    assert {"ledger_revision", "prior_ledger", "runs_sha256", "run_key_rule"} <= set(
        ledger_required
    )
    assert test_ledger["properties"]["identity_digest_rule"]["const"].startswith(
        "wright_test_id_set_v1_lf"
    )
    assert test_ledger["properties"]["run_key_rule"]["const"].startswith(
        "wright_test_run_key_v1_lf"
    )
    assert test_ledger["properties"]["runs_digest_rule"]["const"].startswith(
        "wright_json_c14n_v1_nfc_sha256"
    )
    run_required = test_ledger["$defs"]["run"]["required"]
    assert {"run_key", "test_case_ids", "test_case_set_sha256", "counts"} <= set(
        run_required
    )
    suite_required = bundle["$defs"]["testSuiteSource"]["required"]
    assert {
        "run_key",
        "observed_at",
        "terminal",
        "aggregate_role",
        "test_case_ids",
        "test_case_set_sha256",
        "counts",
    } <= set(suite_required)
    generic_path = bundle["$defs"]["relativePath"]["pattern"]
    test_result_path = bundle["$defs"]["testResultPath"]["pattern"]
    assert re.fullmatch(generic_path, "test-results/program-status/unit.json") is None
    assert re.fullmatch(test_result_path, "test-results/program-status/unit.json")
    assert (
        re.fullmatch(
            test_result_path,
            "docs/programs/engineering-process-platform/test-run-ledger.json",
        )
        is None
    )
    assert bundle["$defs"]["testSuiteSource"]["properties"]["evidence"]["items"] == {
        "oneOf": [
            {"$ref": "#/$defs/evidenceRef"},
            {"$ref": "#/$defs/testResultEvidenceRef"},
        ]
    }
    assert bundle["$defs"]["supplement"]["properties"]["evidence_index"]["items"] == {
        "oneOf": [
            {"$ref": "#/$defs/evidenceDetail"},
            {"$ref": "#/$defs/testResultEvidenceDetail"},
        ]
    }
    assert "items" in bundle["$defs"]["useCases"]["required"]
    assert {"identity_digest_rule", "run_key_rule", "runs_digest_rule"} <= set(
        bundle["$defs"]["testHistory"]["required"]
    )
    assert (
        "docs/programs/engineering-process-platform/schemas/dashboard.schema.json"
        in tasks
    )


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
