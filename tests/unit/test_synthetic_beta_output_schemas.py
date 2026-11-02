"""Schema drift checks; schemas constrain output but do not establish evidence."""

import copy

from jsonschema import Draft202012Validator
import pytest

from scripts.synthetic_beta_testing.output_schemas import (
    customer_schema,
    evaluator_schema,
)
from scripts.synthetic_beta_testing.reports import STAGES


@pytest.fixture
def report():
    return {
        "schema_version": 1,
        "session_id": "customer-1",
        "outcome": "justified_stop",
        "expectation": "Setup help",
        "task": "Try Wright",
        "accomplishment": "Reached setup",
        "stopping_reason": "No next step",
        "positives": [],
        "uncertainties": [],
        "help": [],
        "stages": [
            {"id": stage, "status": "not_reached", "evidence_refs": []}
            for stage in STAGES
        ],
        "friction": [
            {
                "id": "finding-1",
                "stage": "setup",
                "impact": "blocked_progress",
                "observation": "No action",
                "expected": "Guidance",
                "consequence": "Stopped",
                "interpretation": "May need help",
                "suggestion": "Explain",
                "evidence_refs": ["e00001"],
            }
        ],
        "priorities": [{"finding_id": "finding-1", "recommendation": "Explain"}],
    }


def verification(report):
    return {
        "schema_version": 1,
        "session_id": report["session_id"],
        "evaluator_session_id": "review-fixed",
        "events_sha256": "a" * 64,
        "stages": copy.deepcopy(report["stages"]),
        "findings": [
            {
                "finding_id": "finding-1",
                "disposition": "supported",
                "evidence_refs": ["e00001"],
                "reason": "Recorded screen",
                "issue_key": None,
            }
        ],
    }


def test_customer_schema_closes_shape_and_exact_session_without_target_key(report):
    schema = customer_schema("customer-1")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    assert validator.is_valid(report)
    wrong = copy.deepcopy(report)
    wrong["session_id"] = "another"
    assert not validator.is_valid(wrong)
    wrong = copy.deepcopy(report)
    wrong["friction"][0]["issue_key"] = "private-answer-key"
    assert not validator.is_valid(wrong)


@pytest.mark.parametrize(
    "bad_ref", ["captures/e00001.png", "resulting_state_receipts.workspaces", "e1"]
)
def test_customer_refs_have_event_id_shape(report, bad_ref):
    report["friction"][0]["evidence_refs"] = [bad_ref]
    assert not Draft202012Validator(customer_schema("customer-1")).is_valid(report)


def test_evaluator_uses_shared_known_refs_and_exact_provenance(report):
    schema = evaluator_schema(report, ["e00001"], "review-fixed", "a" * 64)
    Draft202012Validator.check_schema(schema)
    value = verification(report)
    assert Draft202012Validator(schema).is_valid(value)
    assert schema["$defs"]["evidence_refs"]["items"]["enum"] == ["e00001"]
    assert schema["properties"]["findings"]["items"]["properties"]["evidence_refs"] == {
        "$ref": "#/$defs/evidence_refs"
    }


@pytest.mark.parametrize(
    "field", ["session_id", "evaluator_session_id", "events_sha256"]
)
def test_evaluator_cannot_change_subject_identities(report, field):
    value = verification(report)
    value[field] += "-invented"
    assert not Draft202012Validator(
        evaluator_schema(report, ["e00001"], "review-fixed", "a" * 64)
    ).is_valid(value)


@pytest.mark.parametrize(
    "bad_ref", ["captures/e00001.png", "resulting_state_receipts.workspaces", "e00099"]
)
def test_evaluator_rejects_paths_receipt_fields_and_unknown_events(report, bad_ref):
    value = verification(report)
    value["findings"][0]["evidence_refs"] = [bad_ref]
    assert not Draft202012Validator(
        evaluator_schema(report, ["e00001"], "review-fixed", "a" * 64)
    ).is_valid(value)


def test_closed_stage_and_finding_identities(report):
    schema = evaluator_schema(report, ["e00001"], "review-fixed", "a" * 64)
    for field, wrong in [("id", "invented_stage"), ("status", "pass")]:
        value = verification(report)
        value["stages"][0][field] = wrong
        assert not Draft202012Validator(schema).is_valid(value)
    value = verification(report)
    value["findings"][0]["finding_id"] = "invented-finding"
    assert not Draft202012Validator(schema).is_valid(value)


def test_target_classification_only_uses_registered_key(report):
    schema = evaluator_schema(
        report, ["e00001"], "review-fixed", "a" * 64, {"issue_key": "registered-issue"}
    )
    Draft202012Validator.check_schema(schema)
    value = verification(report)
    value["findings"][0]["issue_key"] = "registered-issue"
    value["target_observation"] = {
        "issue_key": "registered-issue",
        "present": True,
        "progressed": False,
        "evidence_refs": ["e00001"],
    }
    assert Draft202012Validator(schema).is_valid(value)
    value["target_observation"]["issue_key"] = "another"
    assert not Draft202012Validator(schema).is_valid(value)
    value = verification(report)
    value["target_observation"] = {
        "issue_key": "unregistered",
        "present": False,
        "progressed": True,
        "evidence_refs": [],
    }
    assert not Draft202012Validator(
        evaluator_schema(report, ["e00001"], "review-fixed", "a" * 64)
    ).is_valid(value)


def test_no_events_or_findings_schema_remains_valid_and_requires_empty_arrays(report):
    report["friction"] = []
    schema = evaluator_schema(report, [], "review-fixed", "a" * 64)
    Draft202012Validator.check_schema(schema)
    value = verification(report)
    value["findings"] = []
    assert Draft202012Validator(schema).is_valid(value)
    value["stages"][0]["evidence_refs"] = ["e00001"]
    assert not Draft202012Validator(schema).is_valid(value)


def test_v2_accomplishment_schema_is_explicit_and_v1_shape_unchanged(report):
    v1 = evaluator_schema(report, ["e00001"], "review-fixed", "a" * 64)
    v2 = evaluator_schema(
        report,
        ["e00001"],
        "review-fixed",
        "a" * 64,
        observation_scope="calibration_checkpoint_v2",
    )
    assert "checkpoint_accomplishment" not in v1["properties"]
    assert "checkpoint_accomplishment" in v2["required"]
    value = verification(report)
    assert not Draft202012Validator(v2).is_valid(value)
    value["checkpoint_accomplishment"] = {
        "claim_disposition": "supported",
        "final_state_reached": True,
        "evidence_refs": ["e00001"],
        "reason": "Factual disclosed restoration and observed final task state",
    }
    assert Draft202012Validator(v2).is_valid(value)
    assert not Draft202012Validator(v1).is_valid(value)
    value["checkpoint_accomplishment"]["evidence_refs"] = ["captures/e00001.png"]
    assert not Draft202012Validator(v2).is_valid(value)


def test_no_target_contract_omits_inapplicable_observation(report):
    schema = evaluator_schema(report, ["e00001"], "review-fixed", "a" * 64)
    assert "target_observation" not in schema["required"]
    assert "target_observation" not in schema["properties"]
    value = verification(report)
    assert Draft202012Validator(schema).is_valid(value)
    value["target_observation"] = None
    assert not Draft202012Validator(schema).is_valid(value)
