from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from tool_registry.windows_qualification_models import (
    EMPTY_DIGEST,
    QUALIFICATION_STAGES,
    SafetyPreflight,
    ServerQualificationEvidence,
    StageEvidence,
    WindowsQualificationStatus,
    WindowsQualificationSummary,
    qualification_staleness_reasons,
)


def _stage(name: str, result: str = "passed") -> StageEvidence:
    return StageEvidence(
        stage=name,
        result=result,
        reason_code=f"{name}_{result}",
        summary=f"{name}: {result}",
        recovery="No recovery required." if result == "passed" else "Review evidence.",
    )


def _evidence(**changes) -> ServerQualificationEvidence:
    data = {
        "evidence_id": "windows-brep-1",
        "server_id": "brep-mcp",
        "policy_version": "windows-allowlist-v1",
        "recipe_digest": EMPTY_DIGEST,
        "source_revision": "abc",
        "package_version": "1.0.0",
        "package_digest": EMPTY_DIGEST,
        "tool_schema_digest": EMPTY_DIGEST,
        "machine_digest": EMPTY_DIGEST,
        "credential_binding_digest": EMPTY_DIGEST,
        "observed_at": datetime(2026, 8, 13, tzinfo=UTC),
        "safety_preflight": SafetyPreflight(
            decision="approved",
            reason_code="reviewed",
            reviewed_at=datetime(2026, 8, 13, tzinfo=UTC),
        ),
        "stages": [_stage(stage) for stage in QUALIFICATION_STAGES],
        "attempted_server_ids": ["brep-mcp"],
        "terminal_classification": "passed",
    }
    data.update(changes)
    return ServerQualificationEvidence.model_validate(data)


def test_evidence_requires_exactly_eight_unique_ordered_stages() -> None:
    evidence = _evidence()
    assert [stage.stage for stage in evidence.stages] == list(QUALIFICATION_STAGES)

    with pytest.raises(ValidationError, match="qualification stages"):
        _evidence(stages=[_stage(stage) for stage in QUALIFICATION_STAGES[:-1]])

    duplicate = [_stage(stage) for stage in QUALIFICATION_STAGES]
    duplicate[-1] = _stage("source_current")
    with pytest.raises(ValidationError, match="qualification stages"):
        _evidence(stages=duplicate)


def test_evidence_rejects_non_allowlisted_action_identity() -> None:
    with pytest.raises(ValidationError):
        _evidence(attempted_server_ids=["onshape-mcp-hedless"])

    with pytest.raises(ValidationError, match="non-allowlisted"):
        _evidence(non_allowlist_actions=["install:onshape-mcp-hedless"])


def test_no_problems_claim_requires_all_install_lifecycle_groups() -> None:
    passed = WindowsQualificationStatus(
        result="passed", label="Passed", reason_code="passed"
    )
    partial = WindowsQualificationStatus(
        result="partial", label="Host needed", reason_code="host_required"
    )
    data = {
        "observed_at": datetime(2026, 8, 13, tzinfo=UTC),
        "evidence_path": "docs/mcp-catalog/evidence/example.json",
        "evidence_digest": EMPTY_DIGEST,
        "source": passed,
        "package_or_registration": passed,
        "startup": passed,
        "protocol": passed,
        "host_or_backend": partial,
        "wright_setup": passed,
        "gateway": partial,
        "cleanup": passed,
        "claim": "Installs on Windows with no problems",
    }
    summary = WindowsQualificationSummary.model_validate(data)
    assert summary.claim == "Installs on Windows with no problems"

    data["protocol"] = partial
    with pytest.raises(ValidationError, match="no-problems claim"):
        WindowsQualificationSummary.model_validate(data)


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"recipe_digest": "1" * 64}, "qualification_recipe_changed"),
        ({"source_revision": "def"}, "qualification_source_changed"),
        ({"package_version": "2.0.0"}, "qualification_package_changed"),
        ({"tool_schema_digest": "2" * 64}, "qualification_schema_changed"),
        ({"machine_digest": "3" * 64}, "qualification_machine_changed"),
        (
            {"credential_binding_digest": "4" * 64},
            "qualification_credential_binding_changed",
        ),
    ],
)
def test_material_identity_changes_make_evidence_stale(change, reason) -> None:
    evidence = _evidence()
    current = {
        "recipe_digest": evidence.recipe_digest,
        "source_revision": evidence.source_revision,
        "package_version": evidence.package_version,
        "tool_schema_digest": evidence.tool_schema_digest,
        "machine_digest": evidence.machine_digest,
        "credential_binding_digest": evidence.credential_binding_digest,
        "now": evidence.observed_at + timedelta(hours=1),
    }
    current.update(change)
    assert reason in qualification_staleness_reasons(evidence, **current)


def test_evidence_age_makes_claim_stale() -> None:
    evidence = _evidence()
    reasons = qualification_staleness_reasons(
        evidence,
        recipe_digest=evidence.recipe_digest,
        source_revision=evidence.source_revision,
        package_version=evidence.package_version,
        tool_schema_digest=evidence.tool_schema_digest,
        machine_digest=evidence.machine_digest,
        credential_binding_digest=evidence.credential_binding_digest,
        now=evidence.observed_at + timedelta(hours=25),
    )
    assert reasons == ["qualification_evidence_expired"]
