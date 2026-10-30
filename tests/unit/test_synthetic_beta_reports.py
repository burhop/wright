"""Fixture integrity tests; these establish no real customer or VM behavior."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


MODULE = (
    Path(__file__).resolve().parents[2] / "scripts/synthetic_beta_testing/reports.py"
)
SPEC = importlib.util.spec_from_file_location("synthetic_beta_reports", MODULE)
reports = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reports)


def recorded(tmp_path, session_id="customer-1", obstacle=True, completed=False):
    root = tmp_path / session_id
    root.mkdir()
    image = root / "screen.txt"
    image.write_text("Fixture visible screen; not a live customer observation.")
    event = {
        "id": "event-1",
        "session_id": session_id,
        "time": "2026-10-25T12:00:01Z",
        "action": "Read tool setup",
        "observed_result": "No route onward"
        if obstacle
        else "Tool configuration opened",
        "captures": [
            {
                "path": image.name,
                "sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
            }
        ],
    }
    evidence = root / "events.jsonl"
    evidence.write_text(json.dumps(event) + "\n")
    stages = [
        {
            "id": stage,
            "status": "completed" if completed else "not_reached",
            "evidence_refs": ["event-1"] if completed else [],
        }
        for stage in reports.STAGES
    ]
    report = {
        "schema_version": 1,
        "session_id": session_id,
        "outcome": "independent_completion" if completed else "justified_stop",
        "expectation": "I expected guidance to install a tool.",
        "task": "Begin the handle example.",
        "accomplishment": "I reached the setup dialog.",
        "stopping_reason": "No next step was apparent."
        if obstacle
        else "Observation ended at the matched checkpoint.",
        "positives": [],
        "uncertainties": [],
        "help": [],
        "stages": stages,
        "friction": [
            {
                "id": "finding-1",
                "issue_key": "missing-tool-handoff",
                "stage": "tool_setup",
                "impact": "blocked_progress",
                "observation": "No configuration route appeared.",
                "expected": "A route to tool setup.",
                "consequence": "I could not continue setup.",
                "interpretation": "I may need to leave the task.",
                "suggestion": "Provide setup guidance.",
                "evidence_refs": ["event-1"],
            }
        ]
        if obstacle
        else [],
        "priorities": [
            {
                "finding_id": "finding-1",
                "recommendation": "Show configuration guidance.",
            }
        ]
        if obstacle
        else [],
    }
    verification = {
        "schema_version": 1,
        "session_id": session_id,
        "evaluator_session_id": "evaluator-" + session_id,
        "events_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        "stages": copy.deepcopy(stages),
        "findings": [
            {
                "finding_id": "finding-1",
                "issue_key": "missing-tool-handoff",
                "disposition": "supported",
                "reason": "The retained fixture shows the missing route.",
                "evidence_refs": ["event-1"],
            }
        ]
        if obstacle
        else [],
        "target_observation": {
            "issue_key": "missing-tool-handoff",
            "present": obstacle,
            "progressed": not obstacle,
            "evidence_refs": ["event-1"],
        },
    }
    return root, report, verification


def comparison(tmp_path):
    context = {key: "fixed-" + key for key in reports.CONTEXT_KEYS}
    protocol = {
        "protocol_id": "protocol-1",
        "preregistered_at": "2026-10-25T11:00:00Z",
        "target_issue": "missing-tool-handoff",
        "context": context,
        "variants": [
            {"id": "opaque-a", "candidate_sha256": "a" * 64, "has_obstacle": True},
            {"id": "opaque-b", "candidate_sha256": "b" * 64, "has_obstacle": False},
        ],
    }
    sessions = []
    for index, variant in enumerate(
        [
            protocol["variants"][0],
            protocol["variants"][1],
            protocol["variants"][1],
            protocol["variants"][0],
        ]
    ):
        identity = f"customer-{index}"
        root, report, verification = recorded(
            tmp_path, identity, variant["has_obstacle"]
        )
        sessions.append(
            {
                "session_id": identity,
                "reset_id": f"reset-{index}",
                "variant_id": variant["id"],
                "protocol_id": protocol["protocol_id"],
                "candidate_sha256": variant["candidate_sha256"],
                "context": copy.deepcopy(context),
                "status": "completed",
                "customer_context_isolated": True,
                "variant_blinded": True,
                "started_at": "2026-10-25T12:00:00Z",
                "root": root,
                "report": report,
                "verification": verification,
            }
        )
    return protocol, sessions


def test_preserves_original_feedback_and_renders_distinct_sections(tmp_path):
    root, report, verification = recorded(tmp_path)
    original = copy.deepcopy(report)
    audit = reports.audit_report(report, root, verification=verification)
    assert audit["disposition"] == "supported"
    rendered = reports.render_report(report, audit)
    assert all(
        label in rendered
        for label in (
            "Observation:",
            "Interpretation:",
            "Suggestion:",
            "Separate evidence audit",
        )
    )
    assert report == original


def test_self_certified_completion_is_rejected(tmp_path):
    root, report, _ = recorded(tmp_path, completed=True)
    audit = reports.audit_report(report, root)
    assert audit["disposition"] == "rejected"
    assert (
        sum("unsupported completion" in message for message in audit["rejected_claims"])
        == 6
    )


def test_completion_requires_all_independently_verified_stages(tmp_path):
    root, report, verification = recorded(tmp_path, completed=True)
    assert (
        reports.audit_report(report, root, verification=verification)["disposition"]
        == "supported"
    )
    verification["stages"][-1] = {
        "id": "reopen_workspace",
        "status": "not_reached",
        "evidence_refs": [],
    }
    audit = reports.audit_report(report, root, verification=verification)
    assert audit["disposition"] == "rejected"
    assert any(
        "reopen_workspace: unsupported completion" in message
        for message in audit["rejected_claims"]
    )


def test_checkpoint_completion_uses_trusted_scope_and_real_target_progress(tmp_path):
    root, report, verification = recorded(tmp_path, obstacle=False)
    report["outcome"] = "independent_completion"
    report["observation_scope"] = (
        "calibration_checkpoint"  # Customer prose has no authority.
    )
    default = reports.audit_report(report, root, verification=verification)
    assert default["disposition"] == "rejected"
    scoped = reports.audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint",
    )
    assert scoped["disposition"] == "supported"
    assert all(stage["reported"] == "not_reached" for stage in scoped["stages"])
    verification["target_observation"]["progressed"] = False
    failed = reports.audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint",
    )
    assert any(
        "checkpoint completion lacks" in message
        for message in failed["calibration_blockers"]
    )


def test_checkpoint_scope_does_not_permit_fabricated_earlier_stage_completion(tmp_path):
    root, report, verification = recorded(tmp_path, obstacle=False)
    report["outcome"] = "independent_completion"
    report["stages"][0] = {
        "id": "install_wright",
        "status": "completed",
        "evidence_refs": ["event-1"],
    }
    audit = reports.audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint",
    )
    assert any(
        "install_wright: unsupported completion" in message
        for message in audit["calibration_blockers"]
    )


def test_ordinary_product_help_does_not_create_external_intervention(tmp_path):
    root, report, verification = recorded(tmp_path, obstacle=False, completed=True)
    report["help"] = [
        {
            "text": "Read the product guide and asked Hermes for normal help",
            "evidence_refs": ["event-1"],
        }
    ]
    original = copy.deepcopy(report)
    assert (
        reports.audit_report(report, root, verification=verification)["disposition"]
        == "supported"
    )
    external = reports.audit_report(
        report, root, verification=verification, assistance="external"
    )
    assert any(
        "controller-recorded external assistance" in message
        for message in external["calibration_blockers"]
    )
    assert report == original


def test_forged_event_reference_rejected(tmp_path):
    root, report, verification = recorded(tmp_path)
    report["friction"][0]["evidence_refs"] = ["invented"]
    audit = reports.audit_report(report, root, verification=verification)
    assert audit["disposition"] == "rejected"
    assert any(
        "unknown event references" in message for message in audit["rejected_claims"]
    )


def test_failure_or_not_reached_claim_conflicting_with_evaluator_is_rejected(tmp_path):
    root, report, verification = recorded(tmp_path)
    verification["stages"][0] = {
        "id": "install_wright",
        "status": "completed",
        "evidence_refs": ["event-1"],
    }
    audit = reports.audit_report(report, root, verification=verification)
    assert audit["disposition"] == "rejected"
    assert any(
        "conflicts with evaluator" in message for message in audit["rejected_claims"]
    )


def test_capture_hash_tamper_rejected(tmp_path):
    root, report, verification = recorded(tmp_path)
    (root / "screen.txt").write_text("Different bytes")
    with pytest.raises(reports.ReportError, match="digest mismatch"):
        reports.audit_report(report, root, verification=verification)


def test_audits_actual_structured_visible_desktop_event(tmp_path):
    root, report, verification = recorded(tmp_path)
    events_path = root / "events.jsonl"
    event = json.loads(events_path.read_text())
    event["action"] = {"tool": "desktop", "action": "click", "x": 12, "y": 34}
    events_path.write_text(json.dumps(event) + "\n")
    verification["events_sha256"] = hashlib.sha256(events_path.read_bytes()).hexdigest()
    assert (
        reports.audit_report(report, root, verification=verification)["disposition"]
        == "supported"
    )


@pytest.mark.parametrize(
    "capture_path",
    ["../outside.txt", "/etc/passwd", "C:\\secrets", "captures/../../secret"],
)
def test_unsafe_paths_rejected(tmp_path, capture_path):
    root, report, verification = recorded(tmp_path)
    event = json.loads((root / "events.jsonl").read_text())
    event["captures"][0]["path"] = capture_path
    (root / "events.jsonl").write_text(json.dumps(event) + "\n")
    with pytest.raises(reports.ReportError, match="unsafe capture path"):
        reports.audit_report(report, root, verification=verification)


def test_symlink_capture_rejected_even_inside_root(tmp_path):
    root, report, verification = recorded(tmp_path)
    target = root / "actual.txt"
    (root / "screen.txt").rename(target)
    (root / "screen.txt").symlink_to(target)
    with pytest.raises(reports.ReportError, match="symlink capture"):
        reports.audit_report(report, root, verification=verification)


@pytest.mark.parametrize("mutation", ["session", "evaluator", "digest"])
def test_wrong_evaluator_scope_rejected(tmp_path, mutation):
    root, report, verification = recorded(tmp_path, completed=True)
    if mutation == "session":
        verification["session_id"] = "other"
    elif mutation == "evaluator":
        verification["evaluator_session_id"] = report["session_id"]
    else:
        verification["events_sha256"] = "0" * 64
    audit = reports.audit_report(report, root, verification=verification)
    assert audit["disposition"] == "rejected"


def test_report_must_retain_not_reached_stages(tmp_path):
    _, report, _ = recorded(tmp_path)
    report["stages"].pop()
    with pytest.raises(reports.ReportError, match="all six"):
        reports.validate_report(report)


def test_textual_success_without_capture_cannot_establish_completion(tmp_path):
    root, report, verification = recorded(tmp_path, completed=True)
    event = json.loads((root / "events.jsonl").read_text())
    event["captures"] = []
    (root / "events.jsonl").write_text(json.dumps(event) + "\n")
    verification["events_sha256"] = hashlib.sha256(
        (root / "events.jsonl").read_bytes()
    ).hexdigest()
    assert (
        reports.audit_report(report, root, verification=verification)["disposition"]
        == "rejected"
    )


def test_blinded_comparison_passes_only_full_two_by_two(tmp_path):
    protocol, sessions = comparison(tmp_path)
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "pass"
    assert result["counts"] == {"opaque-a": 2, "opaque-b": 2}
    assert "no statistical" in result["scope"]


def test_missing_session_is_incomplete(tmp_path):
    protocol, sessions = comparison(tmp_path)
    assert (
        reports.compare_calibration(protocol, sessions[:-1])["disposition"]
        == "incomplete"
    )


def test_private_evaluator_mapping_calibrates_unlabelled_customer_feedback(tmp_path):
    protocol, sessions = comparison(tmp_path)
    for session in sessions:
        for finding in session["report"]["friction"]:
            finding.pop("issue_key", None)
    originals = [copy.deepcopy(session["report"]) for session in sessions]
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "pass"
    assert [session["report"] for session in sessions] == originals
    obstacle_audit = result["sessions"][0]["audit"]["findings"][0]
    assert obstacle_audit["issue_key"] == protocol["target_issue"]
    assert obstacle_audit["customer_issue_hint"] is None


def test_customer_target_tag_cannot_replace_independent_private_mapping(tmp_path):
    protocol, sessions = comparison(tmp_path)
    for session in sessions:
        for finding in session["verification"]["findings"]:
            finding.pop("issue_key", None)
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "fail"
    obstacle_audit = result["sessions"][0]["audit"]["findings"][0]
    assert obstacle_audit["issue_key"] is None
    assert obstacle_audit["customer_issue_hint"] == protocol["target_issue"]


def test_failed_session_is_incomplete(tmp_path):
    protocol, sessions = comparison(tmp_path)
    sessions[-1]["status"] = "lab_failure"
    assert (
        reports.compare_calibration(protocol, sessions)["disposition"] == "incomplete"
    )


def test_reported_lab_failure_cannot_qualify_even_with_asserted_target_success(
    tmp_path,
):
    protocol, sessions = comparison(tmp_path)
    session = sessions[0]
    session["report"]["outcome"] = "lab_failure"
    session["verification"]["target_observation"]["progressed"] = True
    original = copy.deepcopy(session["report"])
    account = reports.audit_report(
        session["report"], session["root"], verification=session["verification"]
    )
    assert (
        account["disposition"] == "supported"
    )  # Valid lab account, not product evidence.
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "incomplete"
    assert any(
        "lab failure is not a qualified" in reason for reason in result["reasons"]
    )
    assert session["report"] == original


@pytest.mark.parametrize(
    "mutation", ["reset", "context", "artifact", "blind", "preregistration"]
)
def test_calibration_rejects_scope_or_independence_violation(tmp_path, mutation):
    protocol, sessions = comparison(tmp_path)
    if mutation == "reset":
        sessions[-1]["reset_id"] = sessions[0]["reset_id"]
    elif mutation == "context":
        sessions[-1]["context"]["effort"] = "changed"
    elif mutation == "artifact":
        sessions[-1]["candidate_sha256"] = "f" * 64
    elif mutation == "blind":
        sessions[-1]["variant_blinded"] = False
    else:
        sessions[-1]["started_at"] = "2026-10-25T10:00:00Z"
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "fail"


def test_corrected_variant_requires_observed_progress(tmp_path):
    protocol, sessions = comparison(tmp_path)
    sessions[1]["verification"]["target_observation"]["progressed"] = False
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "fail"


def test_comparison_accepts_truthful_checkpoint_completion_from_controller_manifest(
    tmp_path,
):
    protocol, sessions = comparison(tmp_path)
    for session in sessions:
        (session["root"] / "customer-session.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "session_id": session["session_id"],
                    "observation_scope": "calibration_checkpoint",
                    "assistance": "none",
                }
            )
        )
        if not session["verification"]["target_observation"]["present"]:
            session["report"]["outcome"] = "independent_completion"
            session["report"]["help"] = [
                {"text": "Read normal product guidance", "evidence_refs": ["event-1"]}
            ]
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "pass"
    sessions[1]["verification"]["target_observation"]["progressed"] = False
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "fail"


def test_comparison_metadata_cannot_grant_checkpoint_scope_without_controller_record(
    tmp_path,
):
    protocol, sessions = comparison(tmp_path)
    sessions[1]["observation_scope"] = "calibration_checkpoint"
    sessions[1]["report"]["outcome"] = "independent_completion"
    assert (
        reports.compare_calibration(protocol, sessions)["disposition"] == "incomplete"
    )


@pytest.mark.parametrize(
    "registered_scope,changed_scope",
    [
        (registered, changed)
        for registered in sorted(reports.OBSERVATION_SCOPES)
        for changed in sorted(reports.OBSERVATION_SCOPES)
        if registered != changed
    ],
)
def test_preregistered_scope_binds_controller_and_matching_session_metadata(
    tmp_path, registered_scope, changed_scope
):
    protocol, sessions = comparison(tmp_path)
    protocol["observation_scope"] = registered_scope
    for session in sessions:
        session["observation_scope"] = registered_scope
        (session["root"] / "customer-session.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "session_id": session["session_id"],
                    "observation_scope": registered_scope,
                    "assistance": "none",
                }
            )
        )
        if registered_scope == "calibration_checkpoint_v2":
            v2_accomplishment(session["verification"])
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "pass"
    original_reports = [copy.deepcopy(session["report"]) for session in sessions]
    changed = sessions[-1]
    changed["observation_scope"] = changed_scope
    manifest_path = changed["root"] / "customer-session.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["observation_scope"] = changed_scope
    manifest_path.write_text(json.dumps(manifest))
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "incomplete"
    assert len(result["sessions"]) == 3
    assert any(
        "controller observation scope differs from preregistered protocol" in reason
        for reason in result["reasons"]
    )
    assert [session["report"] for session in sessions] == original_reports


@pytest.mark.parametrize("invalid_scope", [None, "checkpoint", "", []])
def test_protocol_cannot_declare_an_unknown_observation_scope(tmp_path, invalid_scope):
    protocol, sessions = comparison(tmp_path)
    protocol["observation_scope"] = invalid_scope
    with pytest.raises(reports.ReportError, match="protocol.*observation scope"):
        reports.compare_calibration(protocol, sessions)


@pytest.mark.parametrize("disposition", ["unsupported", "uncertain"])
def test_minor_non_target_friction_remains_in_audit_without_alone_failing_calibration(
    tmp_path, disposition
):
    protocol, sessions = comparison(tmp_path)
    finding = copy.deepcopy(sessions[0]["report"]["friction"][0])
    finding.update(id="minor-1", impact="minor_friction")
    finding.pop("issue_key", None)
    sessions[0]["report"]["friction"].append(finding)
    sessions[0]["verification"]["findings"].append(
        {
            "finding_id": "minor-1",
            "disposition": disposition,
            "evidence_refs": ["event-1"],
            "reason": "Preference not established by this capture",
        }
    )
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "pass"
    audit = result["sessions"][0]["audit"]
    assert audit["disposition"] == (
        "rejected" if disposition == "unsupported" else "uncertain"
    )
    assert audit["findings"][-1]["disposition"] == disposition
    assert audit["calibration_blockers"] == []


@pytest.mark.parametrize(
    "impact",
    ["blocked_progress", "caused_rework", "required_help", "caused_uncertainty"],
)
def test_every_non_minor_unsupported_finding_still_blocks_calibration(tmp_path, impact):
    protocol, sessions = comparison(tmp_path)
    sessions[0]["report"]["friction"][0]["impact"] = impact
    sessions[0]["verification"]["findings"][0]["disposition"] = "unsupported"
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "fail"


def test_unsubstantiated_high_impact_finding_fails_calibration(tmp_path):
    protocol, sessions = comparison(tmp_path)
    sessions[0]["verification"]["findings"][0]["disposition"] = "uncertain"
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "fail"


def test_raw_html_is_escaped_in_report(tmp_path):
    _, report, _ = recorded(tmp_path)
    report["expectation"] = "<script>alert('bad')</script>"
    assert "<script>" not in reports.render_report(report)


def test_omitted_high_impact_finding_evaluation_does_not_silently_pass(tmp_path):
    protocol, sessions = comparison(tmp_path)
    sessions[0]["verification"]["findings"] = []
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "fail"
    assert result["sessions"][0]["audit"]["findings"][0]["disposition"] == "uncertain"


def test_unknown_evaluator_findings_cannot_be_silently_ignored(tmp_path):
    protocol, sessions = comparison(tmp_path)
    sessions[0]["verification"]["findings"].append(
        {
            "finding_id": "unmapped-high-impact-claim",
            "disposition": "unsupported",
            "evidence_refs": ["event-1"],
            "reason": "This finding ID does not map to the original account.",
        }
    )
    result = reports.compare_calibration(protocol, sessions)
    assert result["disposition"] == "incomplete"
    assert any("unknown customer finding" in reason for reason in result["reasons"])


def test_customer_markdown_cannot_embed_remote_media(tmp_path):
    _, report, _ = recorded(tmp_path)
    report["expectation"] = "![remote](https://example.invalid/private)"
    rendered = reports.render_report(report)
    assert "![remote](" not in rendered
    assert r"\!\[remote\]\(" in rendered


def v2_accomplishment(verification, *, disposition="supported", final_state=True):
    verification["checkpoint_accomplishment"] = {
        "claim_disposition": disposition,
        "final_state_reached": final_state,
        "evidence_refs": ["event-1"],
        "reason": "Fixture account discloses restoration and the declared final state is visible.",
    }


def test_v2_honest_restoration_is_separate_from_target_friction(tmp_path):
    root, report, verification = recorded(tmp_path)
    report["outcome"] = "independent_completion"
    report["accomplishment"] = (
        "The choice was lost; I restored Side and reached the same job guidance."
    )
    original = copy.deepcopy(report)
    v2_accomplishment(verification)
    old = reports.audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint",
    )
    corrected = reports.audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint_v2",
    )
    assert old["disposition"] == "rejected"
    assert corrected["disposition"] == "supported"
    assert corrected["target_observation"]["present"] is True
    assert corrected["target_observation"]["progressed"] is False
    assert corrected["checkpoint_accomplishment"]["final_state_reached"] is True
    assert report == original


@pytest.mark.parametrize("disposition", ["unsupported", "uncertain"])
def test_v2_false_or_uncertain_preservation_account_still_rejected(
    tmp_path, disposition
):
    root, report, verification = recorded(tmp_path)
    report["outcome"] = "independent_completion"
    report["accomplishment"] = "Side stayed preserved throughout."
    v2_accomplishment(verification, disposition=disposition)
    verification["checkpoint_accomplishment"]["reason"] = (
        "Fixture contradicts uninterrupted preservation; restoration was omitted."
    )
    audit = reports.audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint_v2",
    )
    assert audit["disposition"] == "rejected"
    assert any("factual account" in reason for reason in audit["calibration_blockers"])


@pytest.mark.parametrize("defect", ["missing", "no_final_state", "unknown_refs"])
def test_v2_completion_requires_separate_actual_accomplishment_proof(tmp_path, defect):
    root, report, verification = recorded(tmp_path)
    report["outcome"] = "independent_completion"
    v2_accomplishment(verification)
    if defect == "missing":
        verification.pop("checkpoint_accomplishment")
    elif defect == "no_final_state":
        verification["checkpoint_accomplishment"]["final_state_reached"] = False
    else:
        verification["checkpoint_accomplishment"]["evidence_refs"] = ["invented"]
    audit = reports.audit_report(
        report,
        root,
        verification=verification,
        observation_scope="calibration_checkpoint_v2",
    )
    assert audit["disposition"] == "rejected"
    assert audit["calibration_blockers"]


def test_v2_comparison_preserves_corrected_friction_free_rule(tmp_path):
    protocol, sessions = comparison(tmp_path)
    for session in sessions:
        (session["root"] / "customer-session.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "session_id": session["session_id"],
                    "observation_scope": "calibration_checkpoint_v2",
                    "assistance": "none",
                }
            )
        )
        session["report"]["outcome"] = "independent_completion"
        session["report"]["accomplishment"] = (
            "Reached the final task state; any restoration was disclosed."
        )
        v2_accomplishment(session["verification"])
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "pass"
    # Eventual task completion cannot substitute for friction-free correction.
    sessions[1]["verification"]["target_observation"]["progressed"] = False
    assert reports.compare_calibration(protocol, sessions)["disposition"] == "fail"


@pytest.mark.parametrize(
    "scope,expected",
    [
        (
            "first_contact",
            "db7b300d80f79d93c69526692c31e3500e2433d2b972a80824d00f45394a1532",
        ),
        (
            "calibration_checkpoint",
            "2dee7f9b651d32bf6ebf7a26955d1bdf0e12917b2ea430aea21c7ed3b7be86a4",
        ),
    ],
)
def test_v1_serialized_audit_replay_unchanged(tmp_path, scope, expected):
    root, report, verification = recorded(tmp_path)
    report["outcome"] = "independent_completion"
    audit = reports.audit_report(
        report, root, verification=verification, observation_scope=scope
    )
    assert "checkpoint_accomplishment" not in audit
    serialized = json.dumps(audit, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(serialized).hexdigest() == expected
