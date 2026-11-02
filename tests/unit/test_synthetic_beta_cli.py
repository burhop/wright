"""Mock-only orchestration checks; no customer or VM execution evidence."""

import json
import hashlib
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from scripts.synthetic_beta_testing import cli


@pytest.fixture
def session(tmp_path, monkeypatch):
    lab = tmp_path / "lab"
    root = lab / "machine/sessions/customer-1"
    root.mkdir(parents=True)
    auth = tmp_path / "auth.json"
    auth.write_text('{"fixture":"not-real-credentials"}')
    binary = tmp_path / "codex"
    binary.write_text("fixture binary")
    (tmp_path / "codex-code-mode-host").write_text("fixture adjacent helper")
    cli.JourneyRecorder.begin(
        root,
        json.loads((cli.ASSETS / "first-workflow-journey.json").read_text()),
        boundary="whole_journey",
    )
    task = tmp_path / "task.txt"
    task.write_text("Try the public first-contact journey.")
    state = {"cancelled": False, "calls": [], "cleanup_fail": False}

    class Backend:
        owner = "fixture-owner"

        def __init__(self, path):
            self.root = Path(path)

        def _load(self, identity):
            if not re.fullmatch(r"[A-Za-z0-9_-]+", identity):
                raise cli.VMError("invalid session identity")
            return self.root / "sessions" / identity, {}

        def state(self, identity):
            return {"live": True, "base_sha256": "a" * 64}

    class Visible:
        def __init__(self, *args, **kwargs):
            pass

        def native_pause(self, *args, **kwargs):
            pass

        def cancel(self):
            state["cancelled"] = True

        def __call__(self, *args):
            raise AssertionError("No guest operation expected in orchestration fixture")

    report = {
        "schema_version": 1,
        "session_id": "customer-1",
        "outcome": "justified_stop",
        "expectation": "Help beginning the task",
        "task": "Try Wright",
        "accomplishment": "Stopped at a fixture screen",
        "stopping_reason": "Fixture boundary",
        "positives": [],
        "uncertainties": [],
        "help": [],
        "friction": [],
        "priorities": [],
        "stages": [
            {"id": stage, "status": "not_reached", "evidence_refs": []}
            for stage in cli.audit_report.__globals__["STAGES"]
        ],
    }
    state["final"] = json.dumps(report, indent=3) + "\n\n"
    state["agent_status"] = "completed"

    def fake_agent(
        command,
        instructions,
        task_text,
        tools,
        callback,
        timeout,
        output,
        model,
        effort,
        **kwargs,
    ):
        state["calls"].append(
            {
                "command": command,
                "instructions": instructions,
                "task": task_text,
                "tools": tools,
                "callback": callback,
                "output_schema": kwargs.get("output_schema"),
            }
        )
        output.mkdir()
        (output / "final.txt").write_text(state["final"])
        return {"status": state["agent_status"], "final_text": state["final"]}

    def cleanup(identity, owner):
        if state["cleanup_fail"]:
            raise cli.VMError("Unable to confirm owned cleanup")
        return {"container": identity, "absent": True}

    monkeypatch.setattr(cli, "VMBackend", Backend)
    monkeypatch.setattr(cli, "VisibleSession", Visible)
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda *_: {"uid": 1000, "gid": 1000, "launcher_image": "sha256:" + "1" * 64},
    )
    monkeypatch.setattr(cli, "run_agent", fake_agent)
    monkeypatch.setattr(cli, "cleanup_model", cleanup)
    state.update(lab=lab, root=root, auth=auth, binary=binary, task_path=task)
    return state


def run(session, identity="customer-1"):
    return cli.run_customer(
        session["lab"],
        identity,
        session["task_path"],
        60,
        session["auth"],
        session["binary"],
        "gpt-6.1-sol",
        "medium",
    )


def test_customer_feedback_is_preserved_exactly_and_remains_unreviewed(session):
    before = session["auth"].read_bytes()
    manifest = run(session)
    assert manifest["report_status"] == "valid-unreviewed"
    assert (session["root"] / "report.json").read_text() == session["final"]
    assert (session["root"] / "customer-agent/final.txt").read_text() == session[
        "final"
    ]
    assert not (session["root"] / "verification.json").exists()
    assert session["auth"].read_bytes() == before
    assert session["cancelled"]


@pytest.mark.parametrize(
    "final", ['["wrong shape"]', '{"session_id":"another"}', "not valid JSON"]
)
def test_invalid_customer_feedback_is_retained_without_success(session, final):
    session["final"] = final
    manifest = run(session)
    assert manifest["report_status"] == "invalid-retained"
    assert (session["root"] / "report.json").read_text() == final
    assert (session["root"] / "customer-agent/final.txt").read_text() == final
    assert not (session["root"] / "report.md").exists()


def test_lab_failure_does_not_create_a_customer_report(session):
    session["agent_status"] = "timed_out"
    manifest = run(session)
    assert manifest["report_status"] == "missing-agent-failure"
    assert not (session["root"] / "report.json").exists()


def test_cleanup_failure_preserves_customer_attempt_manifest(session):
    session["cleanup_fail"] = True
    with pytest.raises(cli.VMError, match="cleanup"):
        run(session)
    manifest = json.loads((session["root"] / "customer-session.json").read_text())
    assert manifest["cleanup"]["absent"] is False
    assert manifest["report_status"] == "valid-unreviewed"
    assert session["cancelled"]


def test_model_receives_only_scoped_binds_and_visible_tools(session):
    run(session)
    call = session["calls"][0]
    mounts = [
        call["command"][i + 1]
        for i, token in enumerate(call["command"])
        if token == "--mount"
    ]
    assert len(mounts) == 3
    assert all(mount.endswith(",readonly") for mount in mounts)
    assert any(f"src={session['auth']}" in mount for mount in mounts)
    assert any(f"src={session['binary']}" in mount for mount in mounts)
    assert any("dst=/usr/local/bin/codex-code-mode-host" in mount for mount in mounts)
    assert all(
        "repos/wright" not in mount and "config.toml" not in mount for mount in mounts
    )
    assert {tool["name"] for tool in call["tools"]} == {
        "desktop",
        "feedback_note",
        "journey_step",
        cli.ACTIVITY_TOOL["name"],
    }
    assert "customer-1" in call["task"]
    assert "registered_target" not in call["task"]
    assert "cap-drop=ALL" in " ".join(call["command"])
    assert call["output_schema"]["properties"]["session_id"]["enum"] == ["customer-1"]


def test_missing_code_mode_helper_fails_before_customer_launch(session):
    session["binary"].with_name("codex-code-mode-host").unlink()
    with pytest.raises(cli.VMError, match="adjacent code-mode helper"):
        run(session)
    assert session["calls"] == []


def test_manifest_pins_adjacent_helper_identity(session):
    result = run(session)
    expected = hashlib.sha256(
        session["binary"].with_name("codex-code-mode-host").read_bytes()
    ).hexdigest()
    assert result["code_mode_helper_sha256"] == expected


def test_controller_checkpoint_scope_is_explicit_and_has_bounded_timeout(session):
    result = cli.run_customer(
        session["lab"],
        "customer-1",
        session["task_path"],
        60,
        session["auth"],
        session["binary"],
        "gpt-6.1-sol",
        "medium",
        observation_scope="calibration_checkpoint",
    )
    assert result["observation_scope"] == "calibration_checkpoint"
    assert result["assistance"] == "none"


@pytest.mark.parametrize(
    "observation_scope", ["calibration_checkpoint", "calibration_checkpoint_v2"]
)
def test_checkpoint_scope_cannot_expand_to_a_full_hour(session, observation_scope):
    with pytest.raises(cli.VMError, match="900-second"):
        cli.run_customer(
            session["lab"],
            "customer-1",
            session["task_path"],
            901,
            session["auth"],
            session["binary"],
            "gpt-6.1-sol",
            "medium",
            observation_scope=observation_scope,
        )
    assert session["calls"] == []


def test_unsafe_session_rejected_before_starting_agent(session):
    with pytest.raises(cli.VMError, match="invalid session"):
        run(session, "../outside")
    assert session["calls"] == []


def test_cleanup_refuses_container_with_different_owner(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "Id": "other-container",
                        "Config": {
                            "Labels": {"wright.synthetic-beta.owner": "someone-else"}
                        },
                    }
                ]
            ),
            stderr="",
        )

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    with pytest.raises(cli.VMError, match="unknown ownership"):
        cli.cleanup_model("fixture", "expected-owner")
    assert len(calls) == 1


def test_evaluator_rejects_wrong_session_report_before_model_call(session):
    report = json.loads(session["final"])
    report["session_id"] = "some-other-session"
    (session["root"] / "report.json").write_text(json.dumps(report))
    with pytest.raises(cli.VMError, match="differs"):
        cli.evaluate(session["lab"], "customer-1", session["auth"], session["binary"])
    assert session["calls"] == []


@pytest.mark.parametrize(
    "observation_scope", ["first_contact", "calibration_checkpoint_v2"]
)
def test_evaluation_preserves_original_report_and_restricts_evidence_access(
    session, monkeypatch, observation_scope
):
    run(session)
    if observation_scope == "calibration_checkpoint_v2":
        manifest = json.loads((session["root"] / "customer-session.json").read_text())
        manifest["observation_scope"] = observation_scope
        (session["root"] / "customer-session.json").write_text(json.dumps(manifest))
    original = (session["root"] / "report.json").read_bytes()
    capture = session["root"] / "capture.png"
    capture.write_bytes(b"fixture screenshot bytes, not real UI evidence")
    event = {
        "id": "e00001",
        "session_id": "customer-1",
        "time": "2026-10-25T12:00:00Z",
        "action": {"tool": "desktop", "action": "screenshot"},
        "observed_result": "Fixture screen",
        "captures": [
            {
                "path": "capture.png",
                "sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
            }
        ],
    }
    (session["root"] / "events.jsonl").write_text(json.dumps(event) + "\n")

    def reviewer(
        command,
        instructions,
        task,
        tools,
        view,
        timeout,
        output,
        model,
        effort,
        **kwargs,
    ):
        assert effort == "high"
        assert {tool["name"] for tool in tools} == {"view_evidence"}
        assert view("view_evidence", {"event_id": "e00001"})["image_url"].startswith(
            "data:image/png;base64,"
        )
        with pytest.raises(cli.VMError, match="Unknown evidence"):
            view("view_evidence", {"event_id": "../other-session"})
        with pytest.raises(cli.VMError, match="only session-scoped"):
            view("host_shell", {"event_id": "e00001"})
        request = json.loads(task.split("\n", 1)[1])
        assert request["allowed_event_ids"] == ["e00001"]
        assert "exact known event IDs only" in request["evidence_refs_format"]
        assert "ONLY exact event IDs" in instructions
        assert kwargs["output_schema"]["properties"]["evaluator_session_id"][
            "enum"
        ] == [request["evaluator_session_id"]]
        verification = {
            "schema_version": 1,
            "session_id": "customer-1",
            "evaluator_session_id": request["evaluator_session_id"],
            "events_sha256": request["events_sha256"],
            "stages": request["required_verification_shape"]["stages"],
            "findings": [],
        }
        if observation_scope == "calibration_checkpoint_v2":
            assert "version 5" in instructions
            assert "checkpoint_accomplishment" in kwargs["output_schema"]["required"]
            verification["checkpoint_accomplishment"] = {
                "claim_disposition": "supported",
                "final_state_reached": False,
                "evidence_refs": ["e00001"],
                "reason": "The fixture reports a truthful stop at this checkpoint.",
            }
        else:
            assert "version 4" in instructions
        final = json.dumps(verification)
        output.mkdir()
        (output / "final.txt").write_text(final)
        return {"status": "completed", "final_text": final}

    monkeypatch.setattr(cli, "run_agent", reviewer)
    audit = cli.evaluate(
        session["lab"], "customer-1", session["auth"], session["binary"]
    )
    assert audit["disposition"] == "supported"
    assert (session["root"] / "report.json").read_bytes() == original
    assert (session["root"] / "verification.json").exists()
    configurations = list(session["root"].glob("review-*-configuration.json"))
    assert len(configurations) == 1
    assert (
        json.loads(configurations[0].read_text())["code_mode_helper_sha256"]
        == hashlib.sha256(
            session["binary"].with_name("codex-code-mode-host").read_bytes()
        ).hexdigest()
    )
    assert "Separate evidence audit" in (session["root"] / "report.md").read_text()
    first_verification = (session["root"] / "verification.json").read_bytes()
    first_audit = (session["root"] / "audit.json").read_bytes()
    first_id = json.loads(first_verification)["evaluator_session_id"]
    cli.evaluate(session["lab"], "customer-1", session["auth"], session["binary"])
    assert (
        session["root"] / first_id / "verification.json"
    ).read_bytes() == first_verification
    assert (session["root"] / first_id / "audit.json").read_bytes() == first_audit
    assert (
        json.loads((session["root"] / "verification.json").read_text())[
            "evaluator_session_id"
        ]
        != first_id
    )
    assert (session["root"] / "report.json").read_bytes() == original


@pytest.mark.parametrize(
    "field", ["session_id", "evaluator_session_id", "events_sha256"]
)
def test_mismatched_review_identity_is_retained_without_canonical_promotion(
    session, monkeypatch, field
):
    run(session)
    (session["root"] / "events.jsonl").write_text("")

    def reviewer(
        command,
        instructions,
        task,
        tools,
        view,
        timeout,
        output,
        model,
        effort,
        **kwargs,
    ):
        request = json.loads(task.split("\n", 1)[1])
        verification = dict(request["required_verification_shape"], findings=[])
        verification[field] += "-invented"
        output.mkdir()
        final = json.dumps(verification)
        (output / "final.txt").write_text(final)
        return {"status": "completed", "final_text": final}

    monkeypatch.setattr(cli, "run_agent", reviewer)
    with pytest.raises(cli.VMError, match="exact controller-supplied"):
        cli.evaluate(session["lab"], "customer-1", session["auth"], session["binary"])
    attempts = list(session["root"].glob("review-*/verification.json"))
    assert len(attempts) == 1
    assert json.loads(attempts[0].read_text())[field].endswith("-invented")
    assert (attempts[0].parent / "audit-error.json").exists()
    assert not (session["root"] / "verification.json").exists()


def test_path_reference_is_rejected_and_never_rewritten(session, monkeypatch):
    run(session)
    (session["root"] / "events.jsonl").write_text("")

    def reviewer(
        command,
        instructions,
        task,
        tools,
        view,
        timeout,
        output,
        model,
        effort,
        **kwargs,
    ):
        request = json.loads(task.split("\n", 1)[1])
        verification = dict(request["required_verification_shape"], findings=[])
        verification["stages"][0]["evidence_refs"] = ["captures/e00024.png"]
        output.mkdir()
        final = json.dumps(verification)
        (output / "final.txt").write_text(final)
        return {"status": "completed", "final_text": final}

    monkeypatch.setattr(cli, "run_agent", reviewer)
    audit = cli.evaluate(
        session["lab"], "customer-1", session["auth"], session["binary"]
    )
    assert audit["disposition"] == "rejected"
    assert any(
        "unknown event references" in reason for reason in audit["rejected_claims"]
    )
    latest = json.loads((session["root"] / "verification.json").read_text())
    assert latest["stages"][0]["evidence_refs"] == ["captures/e00024.png"]


def test_archive_maps_legacy_identity_suffix_by_exact_original_response(session):
    attempt = session["root"] / "review-0123456789ab"
    attempt.mkdir()
    raw = '{"evaluator_session_id":"review-0123456789ab-independent-01","session_id":"customer-1"}'
    (attempt / "final.txt").write_text(raw)
    (session["root"] / "verification.json").write_text(raw + "\n")
    audit = '{"disposition":"rejected","scope":"fixture legacy review"}\n'
    (session["root"] / "audit.json").write_text(audit)
    archived = cli.archive_latest_review(session["root"])
    assert archived["evaluator_session_id"] == attempt.name
    assert (attempt / "verification.json").read_text() == raw + "\n"
    assert (attempt / "audit.json").read_text() == audit
    assert (attempt / "final.txt").read_text() == raw


def test_customer_clock_closes_and_labels_missing_startup(session):
    result = run(session)
    assert result["journey_clock_boundary"] == "whole_journey"
    root = session["root"]
    assert result["journey_plan_sha256"] == cli.sha256(root / "journey-plan.json")
    assert (
        json.loads((root / "journey-clock.jsonl").read_text().splitlines()[-1])["kind"]
        == "end"
    )


def test_clock_failure_cannot_prevent_container_cleanup(session, monkeypatch):
    def failure(self):
        raise ValueError("Fixture clock failure")

    monkeypatch.setattr(cli.JourneyRecorder, "finish", failure)
    result = run(session)
    assert result["cleanup"]["absent"]
    assert result["journey_clock_error"] == "Fixture clock failure"
