"""Measurement integrity controls; fixtures do not establish customer behavior."""

import importlib
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
view = importlib.import_module("synthetic_beta_testing.dashboard")
ReportError = view.ReportError


@pytest.fixture
def campaign(tmp_path):
    source = ROOT / "artifacts/first-contact/synthetic-beta-001/session-records"
    index = json.loads((source / "index.json").read_text())
    index["sessions"] = [
        x
        for x in index["sessions"]
        if x["session_id"] in {"customer-001", "customer-003", "cal-002"}
    ]
    records = tmp_path / "records"
    records.mkdir()
    for item in index["sessions"]:
        shutil.copytree(source / item["session_id"], records / item["session_id"])
    index_path = records / "index.json"
    index_path.write_text(json.dumps(index))
    (tmp_path / "loop.md").write_text("Fixture operator instructions")
    registry = tmp_path / "campaign.json"
    registry.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "title": "Fixture campaign",
                "benchmark_id": "fixture-v1",
                "baseline_candidate_sha256": "a" * 64,
                "loop_document": "loop.md",
                "record_indexes": [
                    {"path": "records/index.json", "sha256": view.digest(index_path)}
                ],
                "comparisons": [],
                "result_milestone_events": {},
            }
        )
    )
    return registry, tmp_path / "dashboard.html"


def alter(campaign, sid, name, change):
    registry, _ = campaign
    root = registry.parent / "records"
    path = root / sid / name
    value = json.loads(path.read_text())
    change(value)
    path.write_text(json.dumps(value))
    index_path = root / "index.json"
    index = json.loads(index_path.read_text())
    item = next(x for x in index["sessions"] if x["session_id"] == sid)
    item["files"][name] = {"sha256": view.digest(path), "bytes": path.stat().st_size}
    index_path.write_text(json.dumps(index))
    value = json.loads(registry.read_text())
    value["record_indexes"][0]["sha256"] = view.digest(index_path)
    registry.write_text(json.dumps(value))


def test_real_reference_counts_exclude_lab_and_checkpoint(campaign):
    data = view.build_data(*campaign)
    assert data["summary"] == {
        "qualified_journeys": 1,
        "inspected_results": 0,
        "completed_journeys": 0,
        "independent_completions": 0,
        "lab_failures": 1,
        "unreviewed_or_rejected": 0,
    }
    baseline = next(s for s in data["sessions"] if s["id"] == "customer-003")
    assert baseline["elapsed_seconds"] > 1100
    assert baseline["result_seconds"] is None
    assert baseline["stages"]["install_mcp"]["verified"] == "failed"


def test_positive_checkpoint_stages_never_become_full_journey_success(campaign):
    for name in ["report.json", "audit.json", "verification.json"]:

        def change(value):
            for stage in value["stages"]:
                if name in {"report.json", "verification.json"}:
                    stage["status"] = "completed"
                else:
                    stage.update(
                        reported="completed", verified="completed", confirmed=True
                    )

        alter(campaign, "cal-002", name, change)
    data = view.build_data(*campaign)
    checkpoint = next(s for s in data["sessions"] if s["id"] == "cal-002")
    assert (
        not checkpoint["journey_complete"] and not checkpoint["inspected_tool_result"]
    )
    assert data["summary"]["completed_journeys"] == 0


def test_changed_export_fails_instead_of_repainting_status(campaign):
    path = campaign[0].parent / "records/customer-003/report.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(ReportError, match="changed exported evidence"):
        view.build_data(*campaign)


@pytest.mark.parametrize(
    "field,value",
    [
        ("session_id", "other"),
        ("observation_scope", "calibration_checkpoint_v2"),
        ("events_sha256", "0" * 64),
    ],
)
def test_assessment_identity_and_scope_bound_even_after_reindexing(
    campaign, field, value
):
    alter(campaign, "customer-003", "audit.json", lambda d: d.update({field: value}))
    with pytest.raises(ReportError):
        view.build_data(*campaign)


def test_original_stage_claim_cannot_be_reinterpreted(campaign):
    alter(
        campaign,
        "customer-003",
        "report.json",
        lambda d: d["stages"][2].update(status="completed"),
    )
    with pytest.raises(ReportError, match="original stage claim"):
        view.build_data(*campaign)


def test_rejected_assessment_excluded_from_product_denominator(campaign):
    alter(
        campaign,
        "customer-003",
        "audit.json",
        lambda d: d.update(disposition="rejected"),
    )
    data = view.build_data(*campaign)
    assert data["summary"]["qualified_journeys"] == 0
    assert data["summary"]["unreviewed_or_rejected"] == 1


def test_early_screenshot_cannot_supply_time_to_missing_result(campaign):
    path = campaign[0]
    registry = json.loads(path.read_text())
    registry["result_milestone_events"] = {"customer-003": "e00001"}
    path.write_text(json.dumps(registry))
    with pytest.raises(ReportError, match="reviewed result screen"):
        view.build_data(*campaign)


def test_candidate_changes_do_not_hide_model_context_changes(campaign):
    before = next(
        s for s in view.build_data(*campaign)["sessions"] if s["id"] == "customer-003"
    )
    alter(
        campaign,
        "customer-003",
        "resulting-state.json",
        lambda d: d["installation"].update(artifact_sha256="b" * 64),
    )
    product = next(
        s for s in view.build_data(*campaign)["sessions"] if s["id"] == "customer-003"
    )
    assert product["cohort"] == before["cohort"]
    assert product["candidate_sha256"] != before["candidate_sha256"]
    alter(
        campaign,
        "customer-003",
        "customer-agent/agent-result.json",
        lambda d: d.update(resolved_model="different-model"),
    )
    model = next(
        s for s in view.build_data(*campaign)["sessions"] if s["id"] == "customer-003"
    )
    assert model["cohort"] != before["cohort"]


def test_comparison_cannot_substitute_another_verdict(campaign):
    registry, _ = campaign
    audit = json.loads((registry.parent / "records/cal-002/audit.json").read_text())
    audit["target_observation"]["present"] = True
    path = registry.parent / "comparison.json"
    path.write_text(
        json.dumps(
            {
                "protocol_id": "fixture",
                "disposition": "pass",
                "reasons": [],
                "sessions": [{"session_id": "cal-002", "audit": audit, "passed": True}],
            }
        )
    )
    config = json.loads(registry.read_text())
    config["comparisons"] = [{"path": path.name, "sha256": view.digest(path)}]
    registry.write_text(json.dumps(config))
    with pytest.raises(ReportError, match="comparison evidence mismatch"):
        view.build_data(*campaign)


def test_render_cannot_execute_customer_feedback(campaign):
    payload = "</script><script>globalThis.injected=true</script>"
    alter(
        campaign, "customer-003", "report.json", lambda d: d.update(expectation=payload)
    )
    document = view.render(view.build_data(*campaign))
    assert payload not in document
    assert "\\u003c/script\\u003e" in document
    assert ".textContent=text" in document


def test_export_never_overwrites_original_evidence(campaign):
    registry, _ = campaign
    original = registry.parent / "records/customer-003/audit.json"
    before = original.read_bytes()
    with pytest.raises(ReportError, match="evidence source"):
        view.export(registry, original.with_suffix(".html"))
    assert original.read_bytes() == before


def test_record_path_traversal_rejected():
    with pytest.raises(ReportError, match="unsafe record path"):
        view.relative_file(Path("/tmp"), "../private.json")


def test_verifier_stage_cannot_be_upgraded_by_audit_only(campaign):
    alter(
        campaign,
        "customer-003",
        "verification.json",
        lambda d: d["stages"][0].update(status="failed"),
    )
    with pytest.raises(ReportError, match="independent verification"):
        view.build_data(*campaign)


def test_wrong_candidate_never_credited_to_declared_candidate(campaign):
    registry = campaign[0]
    config = json.loads(registry.read_text())
    config["record_indexes"][0]["intended_candidate_sha256"] = "f" * 64
    registry.write_text(json.dumps(config))
    data = view.build_data(*campaign)
    assert data["summary"]["qualified_journeys"] == 0
    baseline = next(s for s in data["sessions"] if s["id"] == "customer-003")
    assert "registered intent" in baseline["exclusion_reason"]


def test_successful_fixture_uses_reviewed_screen_time_not_session_end(campaign):
    # Artificial success metadata tests projection math, not actual engineering.
    for name in ["report.json", "audit.json", "verification.json"]:

        def change(value):
            for stage in value["stages"]:
                if name == "audit.json":
                    stage.update(
                        reported="completed", verified="completed", confirmed=True
                    )
                else:
                    stage["status"] = "completed"
                    if name == "verification.json" and stage["id"] == "inspect_result":
                        stage["evidence_refs"] = ["e00146"]
            if name == "report.json":
                value["outcome"] = "independent_completion"

        alter(campaign, "customer-003", name, change)
    registry = campaign[0]
    config = json.loads(registry.read_text())
    config["result_milestone_events"] = {"customer-003": "e00146"}
    registry.write_text(json.dumps(config))
    data = view.build_data(*campaign)
    baseline = next(s for s in data["sessions"] if s["id"] == "customer-003")
    assert data["summary"]["inspected_results"] == 1
    assert data["summary"]["completed_journeys"] == 1
    assert 0 < baseline["result_seconds"] < baseline["elapsed_seconds"]


def history_session(sid, candidate, day, *, inspected=False, seconds=None):
    """Artificial reporting data only; never exported as customer evidence."""
    return {
        "id": sid,
        "scope": "first_contact",
        "cohort": "fixed-context",
        "candidate_sha256": candidate * 64,
        "started_at": f"2026-10-{day:02}T12:00:00+00:00",
        "qualified": True,
        "lab_failure": False,
        "inspected_tool_result": inspected,
        "independent_completion": inspected,
        "result_seconds": seconds,
        "reported_tokens": {"totalTokens": 100},
        "findings": []
        if inspected
        else [{"review": "supported", "impact": "blocked_progress"}],
        "stages": {
            stage: {
                "confirmed": True,
                "verified": "completed" if inspected else "not_reached",
            }
            for stage in view.STAGES
        },
    }


def test_candidate_history_supports_repeats_improvements_and_regressions():
    attempts = [
        history_session("baseline", "a", 20),
        history_session("better-1", "b", 21, inspected=True, seconds=300),
        history_session("better-2", "b", 22, inspected=True, seconds=500),
        history_session("better-3", "b", 23),
        history_session("regression", "c", 24),
    ]
    lab = history_session("lab", "b", 25)
    lab.update(qualified=False, lab_failure=True)
    checkpoint = history_session("checkpoint", "d", 26, inspected=True, seconds=1)
    checkpoint["scope"] = "calibration_checkpoint_v2"
    rows = view.candidate_history(list(reversed(attempts + [lab, checkpoint])))
    assert [r["candidate_sha256"] for r in rows] == ["a" * 64, "b" * 64, "c" * 64]
    assert [r["inspected_results"] for r in rows] == [0, 2, 0]
    assert [r["reviewed"] for r in rows] == [1, 3, 1]
    improved = rows[1]
    assert improved["attempts"] == 4 and improved["lab_failures"] == 1
    assert (
        improved["median_result_seconds"] == 400
        and improved["result_time_samples"] == 2
    )
    assert improved["stage_completions"]["inspect_result"] == 2
    assert improved["blocking_findings"] == 1
    assert improved["customer_tokens"] == 400
    assert rows[2]["median_result_seconds"] is None


def test_candidate_history_keeps_contexts_and_missing_measurements_distinct():
    old = history_session("old", "a", 20, inspected=True)
    old["reported_tokens"] = None
    new = history_session("new-model", "a", 21, inspected=True, seconds=60)
    new["cohort"] = "changed-model"
    rejected = history_session("rejected", "a", 22, inspected=True, seconds=1)
    rejected["qualified"] = False
    rows = view.candidate_history([old, new, rejected])
    assert len(rows) == 2
    assert rows[0]["reviewed"] == 1 and rows[0]["other_excluded"] == 1
    assert rows[0]["inspected_results"] == 1
    assert rows[0]["median_result_seconds"] is None
    assert rows[0]["result_time_samples"] == 0
    assert rows[0]["customer_tokens"] == 100 and rows[0]["token_samples"] == 1
    assert rows[1]["median_result_seconds"] == 60
    assert view.candidate_history([]) == []


def test_appending_fresh_record_index_populates_history_without_editing_old_records(
    campaign,
):
    registry, output = campaign
    config = json.loads(registry.read_text())
    original_index = registry.parent / "records/index.json"
    original_bytes = original_index.read_bytes()
    index = json.loads(original_bytes)
    item = deepcopy(
        next(x for x in index["sessions"] if x["session_id"] == "customer-003")
    )
    item["session_id"] = "fixture-followup"
    fresh = registry.parent / "future/fixture-followup"
    shutil.copytree(registry.parent / "records/customer-003", fresh)
    for name in (
        "report.json",
        "customer-session.json",
        "audit.json",
        "verification.json",
    ):
        path = fresh / name
        value = json.loads(path.read_text())
        value["session_id"] = "fixture-followup"
        if name == "customer-session.json":
            for field in ("started_at", "finished_at"):
                value[field] = (
                    view.stamp(value[field]) + timedelta(days=1)
                ).isoformat()
        path.write_text(json.dumps(value))
    path = fresh / "resulting-state.json"
    value = json.loads(path.read_text())
    value["installation"]["artifact_sha256"] = "b" * 64
    path.write_text(json.dumps(value))
    for name in item["files"]:
        path = fresh / name
        item["files"][name] = {
            "sha256": view.digest(path),
            "bytes": path.stat().st_size,
        }
    fresh_index = fresh.parent / "index.json"
    index["sessions"] = [item]
    fresh_index.write_text(json.dumps(index))
    config["record_indexes"].append(
        {
            "path": "future/index.json",
            "sha256": view.digest(fresh_index),
            "intended_candidate_sha256": "b" * 64,
        }
    )
    registry.write_text(json.dumps(config))
    data = view.export(registry, output)
    assert data["summary"]["qualified_journeys"] == 2
    baseline = next(
        r for r in data["candidate_history"] if "customer-003" in r["session_ids"]
    )
    followup = next(
        r for r in data["candidate_history"] if "fixture-followup" in r["session_ids"]
    )
    assert baseline["cohort"] == followup["cohort"]
    assert baseline["candidate_sha256"] != followup["candidate_sha256"]
    assert original_index.read_bytes() == original_bytes
    assert "fixture-followup" in output.read_text()


def test_resource_accounting_deduplicates_cumulative_threads_and_retains_zero():
    first = history_session("first", "a", 20, inspected=True, seconds=100)
    first["resource_calls"] = [
        {"thread_id": "customer", "role": "customer", "tokens": 100},
        {"thread_id": "reviewer", "role": "reviewer", "tokens": None},
    ]
    second = history_session("second", "a", 21)
    second["resource_calls"] = [
        {"thread_id": "customer", "role": "customer", "tokens": 150},
        {"thread_id": "reviewer", "role": "reviewer", "tokens": 0},
        {"thread_id": "failed-review", "role": "reviewer", "tokens": 50},
    ]
    row = view.candidate_history([first, second])[0]
    assert row["observed_model_tokens"] == 200
    assert row["observed_threads"] == row["measured_threads"] == 3
    assert row["reviewer_tokens"] == 50
    assert row["tokens_per_independent_completion"] == 200
    roles = {r["role"]: r for r in view.resource_allocation([first, second])}
    assert roles["full-journey customer"]["tokens"] == 150
    assert roles["independent review"]["tokens"] == 50
    second["resource_calls"][-1]["tokens"] = None
    assert (
        view.candidate_history([first, second])[0]["tokens_per_independent_completion"]
        is None
    )


def test_paired_quality_cost_evidence_is_bound_and_measurements_are_not_invented(
    campaign,
):
    registry, _ = campaign
    source = ROOT / "artifacts/first-contact/084/quality-cost/summary.json"
    path = registry.parent / "qa.json"
    shutil.copyfile(source, path)
    config = json.loads(registry.read_text())
    config["quality_cost_experiments"] = [
        {
            "label": "Fixture reference to measured QA work",
            "path": "qa.json",
            "sha256": view.digest(path),
        }
    ]
    registry.write_text(json.dumps(config))
    experiment = view.build_data(*campaign)["quality_cost_experiments"][0]
    assert len(experiment["pairs"]) == 3
    assert experiment["unique_coverage_reported_equal"] is True
    assert (
        experiment["pairs"][0]["baseline_seconds"]
        > experiment["pairs"][0]["candidate_seconds"]
    )
    value = json.loads(path.read_text())
    value["pairs"][0]["candidate_seconds"] = -1
    path.write_text(json.dumps(value))
    with pytest.raises(ReportError, match="digest/path mismatch"):
        view.build_data(*campaign)
    config["quality_cost_experiments"][0]["sha256"] = view.digest(path)
    registry.write_text(json.dumps(config))
    with pytest.raises(ReportError, match="finite positive durations"):
        view.build_data(*campaign)


def test_bounded_workload_retains_negative_control_and_checks_conditions(campaign):
    registry, _ = campaign
    config = json.loads(registry.read_text())
    reports = {}
    for phase, completed, error in [
        ("baseline", 23, "unable to open database file"),
        ("candidate", 1000, None),
    ]:
        path = registry.parent / (phase + ".json")
        path.write_text(
            json.dumps(
                {
                    "iterations_requested": 1000,
                    "iterations_completed": completed,
                    "handle_limit": 96,
                    "error": error,
                }
            )
        )
        reports[phase] = {"path": path.name, "sha256": view.digest(path)}
    config["bounded_workloads"] = [
        {"label": "Fixture only", "scope": "Technical", **reports}
    ]
    registry.write_text(json.dumps(config))
    rows = view.build_data(*campaign)["bounded_workloads"][0]["rows"]
    assert [r["completed"] for r in rows] == [23, 1000]
    assert rows[0]["error"] == "unable to open database file"
    path = registry.parent / "candidate.json"
    value = json.loads(path.read_text())
    value["handle_limit"] = 128
    path.write_text(json.dumps(value))
    config["bounded_workloads"][0]["candidate"]["sha256"] = view.digest(path)
    registry.write_text(json.dumps(config))
    with pytest.raises(ReportError, match="conditions differ"):
        view.build_data(*campaign)


def test_backend_engineering_report_is_separate_and_rejects_invented_verdict(campaign):
    registry, _ = campaign
    source = (
        ROOT / "specs/082-output-content-validation/contracts/examples/pass.report.json"
    )
    path = registry.parent / "assessment.json"
    shutil.copyfile(source, path)
    config = json.loads(registry.read_text())
    config["engineering_reports"] = [
        {
            "label": "Schema fixture, not a customer result",
            "path": path.name,
            "sha256": view.digest(path),
        }
    ]
    registry.write_text(json.dumps(config))
    before = view.build_data(*campaign)
    assert len(before["engineering_reports"]) == 1
    assert before["summary"]["inspected_results"] == 0
    report = json.loads(path.read_text())
    report["assessment"]["summary"]["release_eligible"] = False
    path.write_text(json.dumps(report))
    config["engineering_reports"][0]["sha256"] = view.digest(path)
    registry.write_text(json.dumps(config))
    with pytest.raises(ReportError, match="invalid backend engineering report"):
        view.build_data(*campaign)


def test_startup_failure_clock_is_visible_without_fabricated_customer_report(campaign):
    from synthetic_beta_testing.journey import JourneyRecorder

    registry, output = campaign
    root = registry.parent / "startup-failure"
    root.mkdir()
    recorder = JourneyRecorder.begin(
        root,
        {
            "schema_version": 1,
            "id": "startup",
            "label": "Startup fixture",
            "steps": [{"id": "boot", "label": "Start VM"}],
        },
    )
    recorder.step("boot", "started")
    recorder.step("boot", "blocked", "Guest desktop never appeared", ["setup_access"])
    recorder.finish()
    config = json.loads(registry.read_text())
    config["journey_sources"] = [
        {
            "label": "Startup fixture",
            "plan_path": "startup-failure/journey-plan.json",
            "plan_sha256": view.digest(root / "journey-plan.json"),
            "clock_path": "startup-failure/journey-clock.jsonl",
            "clock_sha256": view.digest(root / "journey-clock.jsonl"),
        }
    ]
    registry.write_text(json.dumps(config))
    data = view.build_data(registry, output)
    assert (
        data["journey_attempts"][0]["journey_timing"]["steps"][0]["status"] == "blocked"
    )
    assert data["journey_attempts"][0]["outcome"] == "no_customer_report"
    assert data["summary"]["qualified_journeys"] == 1
    assert data["summary"]["completed_journeys"] == 0
    config["journey_sources"].append(dict(config["journey_sources"][0]))
    registry.write_text(json.dumps(config))
    with pytest.raises(ReportError, match="duplicates"):
        view.build_data(registry, output)


def test_timed_completion_never_overrules_independent_assessment(campaign):
    from synthetic_beta_testing.journey import JourneyRecorder

    registry, output = campaign
    root = registry.parent / "records/customer-003"
    recorder = JourneyRecorder.begin(
        root,
        {
            "schema_version": 1,
            "id": "job",
            "label": "Fixture",
            "steps": [{"id": "result", "label": "Get result"}],
        },
    )
    recorder.step("result", "started", actor="customer")
    recorder.step("result", "completed", actor="customer")
    recorder.finish()
    alter(
        campaign,
        "customer-003",
        "customer-session.json",
        lambda m: m.update(journey_plan_sha256=view.digest(root / "journey-plan.json")),
    )
    index_path = root.parent / "index.json"
    index = json.loads(index_path.read_text())
    item = next(x for x in index["sessions"] if x["session_id"] == "customer-003")
    for name in ("journey-plan.json", "journey-clock.jsonl"):
        item["files"][name] = {
            "sha256": view.digest(root / name),
            "bytes": (root / name).stat().st_size,
        }
    index_path.write_text(json.dumps(index))
    config = json.loads(registry.read_text())
    config["record_indexes"][0]["sha256"] = view.digest(index_path)
    registry.write_text(json.dumps(config))
    data = view.build_data(registry, output)
    s = next(s for s in data["sessions"] if s["id"] == "customer-003")
    assert s["journey_timing"]["steps"][0]["status"] == "completed"
    assert not s["journey_complete"]
    assert s["result_seconds"] is None
    assert "journey_plan" in s["context"]
    assert s["interaction_timing"]["available"]
    assert sum(
        s["interaction_timing"][key]
        for key in (
            "wait_callbacks_seconds",
            "other_callbacks_seconds",
            "outside_callbacks_seconds",
        )
    ) == pytest.approx(s["elapsed_seconds"])
