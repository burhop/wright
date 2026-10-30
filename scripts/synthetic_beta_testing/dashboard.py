"""Read-only golden-hour reporting from hash-bound, already reviewed exports.

This does not run customers, repair Wright, re-review pixels or grant acceptance.
The original report, independent audit and controller manifest remain authorities.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
from statistics import median
import tempfile
from urllib.parse import quote

from .reports import OBSERVATION_SCOPES, STAGES, ReportError, validate_report
from .campaign_reporting import project_activity
from .journey import CATEGORIES, project as project_journey
from .journey_stages import TAXONOMY, TAXONOMY_PATH, project_stages
from .activity_diary import ACTIVITY_STATES


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ReportError("timestamp must include its timezone")
    return parsed


def relative_file(root, name):
    rel = PurePosixPath(name)
    if rel.is_absolute() or ".." in rel.parts or "\\" in name or ":" in name:
        raise ReportError("unsafe record path")
    path = root / name
    if path.resolve() != path or not path.is_file():
        raise ReportError("record missing or symlinked: " + name)
    return path


def read_bound(path, expected, sources, *, json_lines=False):
    if path.resolve() != path or not path.is_file() or digest(path) != expected:
        raise ReportError("source digest/path mismatch: " + str(path))
    sources[str(path)] = expected
    if json_lines:
        return [json.loads(line) for line in path.read_text().splitlines()]
    return json.loads(path.read_text())


def link(path, output):
    return quote(os.path.relpath(path, output.parent), safe="/.-_")


def project_session(root, item, campaign, output, sources, intended_candidate=None):
    sid = item["session_id"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
        raise ReportError("invalid session identity")
    root = root / sid
    values = {}
    for name, identity in item["files"].items():
        path = relative_file(root, name)
        if (
            path.stat().st_size != identity["bytes"]
            or digest(path) != identity["sha256"]
        ):
            raise ReportError("changed exported evidence: " + str(path))
        sources[str(path)] = identity["sha256"]
        if path.suffix == ".json":
            values[name] = json.loads(path.read_text())
    report = validate_report(values["report.json"])
    manifest = values["customer-session.json"]
    if report["session_id"] != sid or manifest["session_id"] != sid:
        raise ReportError("cross-session report/controller record")
    scope = manifest.get("observation_scope", "first_contact")
    if scope not in OBSERVATION_SCOPES:
        raise ReportError("unknown observation scope")
    if scope != "first_contact":
        intended_candidate = None
    started, finished = stamp(manifest["started_at"]), stamp(manifest["finished_at"])
    if finished < started:
        raise ReportError("negative session duration")
    audit = values.get("audit.json")
    verification = values.get("verification.json")
    stages = {
        x["id"]: {"reported": x["status"], "verified": None, "confirmed": False}
        for x in report["stages"]
    }
    if audit is not None:
        if (
            audit["session_id"] != sid
            or audit.get("observation_scope", "first_contact") != scope
            or verification is None
            or verification["session_id"] != sid
        ):
            raise ReportError("cross-session or cross-scope assessment")
        events = relative_file(root, "events.jsonl")
        if audit["events_sha256"] != digest(events) or verification[
            "events_sha256"
        ] != digest(events):
            raise ReportError("assessment does not bind these events")
        if set(x["id"] for x in audit["stages"]) != set(STAGES) or len(
            audit["stages"]
        ) != len(STAGES):
            raise ReportError("assessment must account for six distinct stages")
        observed = {x["id"]: x for x in verification["stages"]}
        if set(observed) != set(STAGES) or len(verification["stages"]) != len(STAGES):
            raise ReportError("independent verification must account for six stages")
        for entry in audit["stages"]:
            if entry["reported"] != stages[entry["id"]]["reported"]:
                raise ReportError("assessment differs from original stage claim")
            if (
                type(entry["confirmed"]) is not bool
                or entry["verified"] != observed[entry["id"]]["status"]
                or entry["confirmed"]
                and entry["reported"] != entry["verified"]
            ):
                raise ReportError("assessment differs from independent verification")
            stages[entry["id"]] = entry
    lab_failure = report["outcome"] == "lab_failure"
    qualified = bool(not lab_failure and audit and audit["disposition"] == "supported")
    exclusion = (
        "lab failure"
        if lab_failure
        else "assessment unavailable or not fully supported"
    )
    agent = values.get("customer-agent/agent-result.json", {})
    state = values.get("resulting-state.json", {})
    candidate = (state.get("installation") or {}).get("artifact_sha256")
    candidate_basis = "installed artifact receipt"
    if not candidate and scope == "first_contact":
        candidate = intended_candidate
        candidate_basis = (
            "declared intended artifact; installation not established"
            if candidate
            else "candidate identity unavailable"
        )
    if (
        scope == "first_contact"
        and qualified
        and (not candidate or intended_candidate and candidate != intended_candidate)
    ):
        qualified = False
        exclusion = "candidate identity missing or differs from registered intent"
    context = {
        "benchmark": campaign["benchmark_id"],
        "baseline": manifest.get("base_sha256"),
        "task": manifest.get("task_digest"),
        "customer_instructions": manifest.get("instructions_digest"),
        "model": agent.get("resolved_model", manifest.get("model")),
        "effort": agent.get("resolved_effort", manifest.get("effort")),
        "cli": manifest.get("binary_sha256"),
        "helper": manifest.get("code_mode_helper_sha256"),
        "reviewer_instructions": None,
        "reviewer_model": None,
        "reviewer_effort": None,
        "reviewer_target_field": None,
    }
    if manifest.get("journey_plan_sha256"):
        context["journey_plan"] = manifest["journey_plan_sha256"]
    if manifest.get("tools_sha256"):
        context["customer_tools"] = manifest["tools_sha256"]
        context["customer_controller"] = manifest.get("controller_files_sha256")
    if verification:
        reviewer = values.get(
            verification["evaluator_session_id"] + "/agent-result.json", {}
        )
        context["reviewer_instructions"] = reviewer.get("instructions_sha256")
        context["reviewer_model"] = reviewer.get("resolved_model")
        context["reviewer_effort"] = reviewer.get("resolved_effort")
        context["reviewer_target_field"] = "target_observation" in verification
    cohort = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()[
        :12
    ]

    def completed(stage):
        s = stages[stage]
        return qualified and s["confirmed"] is True and s["verified"] == "completed"

    inspected = (
        scope == "first_contact"
        and completed("call_mcp")
        and completed("inspect_result")
    )
    complete = (
        scope == "first_contact"
        and all(completed(s) for s in STAGES)
        and report["outcome"]
        in {
            "independent_completion",
            "completion_with_help",
        }
    )
    result_seconds = None
    anchor = campaign.get("result_milestone_events", {}).get(sid)
    if anchor:
        rows = [
            json.loads(line)
            for line in (root / "events.jsonl").read_text().splitlines()
        ]
        event = next((row for row in rows if row["id"] == anchor), None)
        inspection = (
            next(s for s in verification["stages"] if s["id"] == "inspect_result")
            if verification
            else {}
        )
        if (
            not inspected
            or not event
            or not event["captures"]
            or anchor not in inspection.get("evidence_refs", [])
        ):
            raise ReportError(
                "result timing needs a reviewed result screen and completed inspection"
            )
        observed = stamp(event["time"])
        if not started <= observed <= finished:
            raise ReportError("result milestone outside observation")
        result_seconds = (observed - started).total_seconds()
    finding_states = (
        {x["id"]: x["disposition"] for x in audit["findings"]} if audit else {}
    )
    findings = [
        {**f, "review": finding_states.get(f["id"], "unreviewed")}
        for f in report["friction"]
    ]
    events = (
        [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
        if "events.jsonl" in item["files"]
        else []
    )
    detail = campaign.get("resolved_run_details", {}).get(sid)
    if detail:
        if detail["report_sha256"] != digest(root / "report.json"):
            raise ReportError("result details differ from the original report")
        observed_events = {event["id"]: event for event in events}
        for prompt in detail.get("prompts", []):
            event = observed_events.get(prompt["evidence_ref"], {})
            observed = event.get("action", {})
            if observed.get("action") != "type_text" or observed.get("text") != prompt["text"]:
                raise ReportError("displayed customer request differs from recorded typing")
            prompt["at"] = event["time"]
        for artifact in detail.get("artifacts", []):
            if artifact["kind"] == "image" and not any(
                c["sha256"] == artifact["sha256"]
                for c in observed_events.get(artifact["evidence_ref"], {}).get("captures", [])
            ):
                raise ReportError("result screenshot differs from customer evidence")
            artifact["at"] = observed_events.get(artifact["evidence_ref"], {}).get("time")
    callback_seconds = 0.0
    wait_seconds = 0.0
    for event in events:
        seconds = event.get("elapsed_seconds", 0)
        if (
            type(seconds) not in (int, float)
            or not math.isfinite(seconds)
            or seconds < 0
        ):
            raise ReportError("invalid recorded interaction duration")
        callback_seconds += seconds
        if event.get("action", {}).get("action") == "wait":
            wait_seconds += seconds
    elapsed_seconds = (finished - started).total_seconds()
    interaction_timing = {
        "available": bool(events)
        and all("elapsed_seconds" in event for event in events),
        "wait_callbacks_seconds": wait_seconds,
        "other_callbacks_seconds": callback_seconds - wait_seconds,
        "outside_callbacks_seconds": max(0, elapsed_seconds - callback_seconds),
        "basis": "Recorded callbacks, including screen capture; explicit waits can overlap product work. Outside callbacks includes AI/controller time, final feedback and cleanup, not measured Wright latency.",
    }
    usage = (agent.get("usage") or {}).get("total")
    journey = {
        "available": False,
        "reason": "Step boundaries were not recorded. Session duration includes AI/controller time; it is not time to a workflow result.",
    }
    if "journey-plan.json" in values or "journey-clock.jsonl" in item["files"]:
        if (
            "journey-plan.json" not in values
            or "journey-clock.jsonl" not in item["files"]
        ):
            raise ReportError("journey export must contain plan and clock")
        if manifest.get("journey_plan_sha256") != digest(root / "journey-plan.json"):
            raise ReportError("journey plan differs from customer session")
        journey = project_journey(
            values["journey-plan.json"],
            [
                json.loads(line)
                for line in (root / "journey-clock.jsonl").read_text().splitlines()
            ],
        )
        if journey["session_id"] != sid:
            raise ReportError("cross-session journey timing")
    resource_calls = []
    for name, value in values.items():
        if not name.endswith("agent-result.json") or not value.get("thread_id"):
            continue
        total = (value.get("usage") or {}).get("total") or {}
        tokens = total.get("totalTokens")
        resource_calls.append(
            {
                "thread_id": value["thread_id"],
                "role": "customer"
                if name == "customer-agent/agent-result.json"
                else "reviewer",
                "tokens": tokens if type(tokens) is int and tokens >= 0 else None,
            }
        )
    return {
        "id": sid,
        "scope": scope,
        "started_at": manifest["started_at"],
        "finished_at": manifest["finished_at"],
        "elapsed_seconds": (finished - started).total_seconds(),
        "journey_timing": journey,
        "stage_timing": project_stages(journey),
        "interaction_timing": interaction_timing,
        "outcome": report["outcome"],
        "lab_failure": lab_failure,
        "qualified": qualified,
        "exclusion_reason": None if qualified else exclusion,
        "audit": audit["disposition"] if audit else "unreviewed",
        "stages": stages,
        "checkpoint_accomplishment": (audit or {}).get("checkpoint_accomplishment"),
        "audit_value_sha256": hashlib.sha256(
            json.dumps(audit, sort_keys=True).encode()
        ).hexdigest(),
        "inspected_tool_result": inspected,
        "journey_complete": complete,
        "independent_completion": complete
        and report["outcome"] == "independent_completion"
        and manifest.get("assistance") == "none",
        "result_seconds": result_seconds,
        "candidate_sha256": candidate,
        "intended_candidate_sha256": intended_candidate,
        "candidate_basis": candidate_basis,
        "cohort": cohort,
        "context": context,
        "profile_label": campaign.get("task_labels", {}).get(
            manifest.get("task_digest")
        ),
        "findings": findings,
        "requested_task": report["task"],
        "task_assignment": campaign.get("resolved_task_sources", {}).get(manifest.get("task_digest")),
        "result_details": campaign.get("resolved_run_details", {}).get(sid),
        "expectation": report["expectation"],
        "accomplishment": report["accomplishment"],
        "stopping_reason": report["stopping_reason"],
        "help": report["help"],
        "uncertainties": report["uncertainties"],
        "reported_tokens": usage,
        "resource_calls": resource_calls,
        "report_url": link(root / "report.md", output),
        "report_data_url": link(root / "report.json", output),
        "result_state_url": link(root / "resulting-state.json", output) if "resulting-state.json" in values else None,
        "audit_url": link(root / "audit.json", output) if audit else None,
        "record_index_url": link(root.parent / "index.json", output),
    }


def candidate_history(sessions):
    """Aggregate recorded observations, keeping experiment contexts distinct."""
    groups = {}
    for session in sessions:
        if session["scope"] != "first_contact":
            continue
        key = session["cohort"], session["candidate_sha256"]
        groups.setdefault(key, []).append(session)
    history = []
    for (cohort, candidate), attempts in groups.items():
        attempts.sort(key=lambda s: stamp(s["started_at"]))
        reviewed = [s for s in attempts if s["qualified"]]
        times = [
            s["result_seconds"]
            for s in reviewed
            if s["inspected_tool_result"] and s["result_seconds"] is not None
        ]
        token_samples = [
            s["reported_tokens"]["totalTokens"]
            for s in attempts
            if isinstance(s.get("reported_tokens"), dict)
            and type(s["reported_tokens"].get("totalTokens")) is int
            and s["reported_tokens"]["totalTokens"] >= 0
        ]
        findings = [
            f for s in reviewed for f in s["findings"] if f["review"] == "supported"
        ]
        calls = {}
        for s in attempts:
            for call in s.get("resource_calls", []):
                key = call["thread_id"]
                previous = calls.get(key)
                if previous and previous["role"] != call["role"]:
                    raise ReportError("resource thread has conflicting roles")
                current_tokens = -1 if call["tokens"] is None else call["tokens"]
                previous_tokens = (
                    -1
                    if not previous or previous["tokens"] is None
                    else previous["tokens"]
                )
                if not previous or current_tokens > previous_tokens:
                    calls[key] = call
        measured = [c for c in calls.values() if c["tokens"] is not None]
        all_tokens = sum(c["tokens"] for c in measured) if measured else None
        completions = sum(s["independent_completion"] for s in reviewed)
        history.append(
            {
                "cohort": cohort,
                "profile_label": attempts[0].get("profile_label"),
                "candidate_sha256": candidate,
                "first_observed_at": attempts[0]["started_at"],
                "last_observed_at": attempts[-1]["started_at"],
                "session_ids": [s["id"] for s in attempts],
                "attempts": len(attempts),
                "reviewed": len(reviewed),
                "inspected_results": sum(s["inspected_tool_result"] for s in reviewed),
                "independent_completions": sum(
                    s["independent_completion"] for s in reviewed
                ),
                "lab_failures": sum(s["lab_failure"] for s in attempts),
                "other_excluded": sum(
                    not s["qualified"] and not s["lab_failure"] for s in attempts
                ),
                "result_time_samples": len(times),
                "median_result_seconds": median(times) if times else None,
                "supported_findings": len(findings),
                "blocking_findings": sum(
                    f["impact"] == "blocked_progress" for f in findings
                ),
                "stage_completions": {
                    stage: sum(
                        s["stages"][stage]["confirmed"] is True
                        and s["stages"][stage]["verified"] == "completed"
                        for s in reviewed
                    )
                    for stage in STAGES
                },
                "customer_tokens": sum(token_samples) if token_samples else None,
                "token_samples": len(token_samples),
                "observed_model_tokens": all_tokens,
                "observed_threads": len(calls),
                "measured_threads": len(measured),
                "reviewer_tokens": sum(
                    c["tokens"] for c in measured if c["role"] == "reviewer"
                ),
                "tokens_per_independent_completion": all_tokens / completions
                if completions and measured and len(measured) == len(calls)
                else None,
            }
        )
    return sorted(history, key=lambda row: stamp(row["first_observed_at"]))


def resource_allocation(sessions):
    calls = {}
    for session in sessions:
        for call in session.get("resource_calls", []):
            role = (
                "independent review"
                if call["role"] == "reviewer"
                else (
                    "full-journey customer"
                    if session["scope"] == "first_contact"
                    else "checkpoint customer"
                )
            )
            key = call["thread_id"]
            old = calls.get(key)
            if old and old["role"] != role:
                raise ReportError("resource thread crosses accounting roles")
            n = -1 if call["tokens"] is None else call["tokens"]
            old_n = -1 if not old or old["tokens"] is None else old["tokens"]
            if old is None or n > old_n:
                calls[key] = {"role": role, "tokens": call["tokens"]}
    return [
        {
            "role": role,
            "threads": sum(c["role"] == role for c in calls.values()),
            "measured_threads": sum(
                c["role"] == role and c["tokens"] is not None for c in calls.values()
            ),
            "tokens": sum(
                c["tokens"]
                for c in calls.values()
                if c["role"] == role and c["tokens"] is not None
            ),
        }
        for role in sorted({c["role"] for c in calls.values()})
    ]


def quality_cost_history(campaign, registry, output, sources):
    """Present existing paired QA measurements, separate from customer outcomes."""
    experiments = []
    for ref in campaign.get("quality_cost_experiments", []):
        path = (registry.parent / ref["path"]).resolve(strict=True)
        report = read_bound(path, ref["sha256"], sources)
        pairs = []
        for pair in report["pairs"]:
            numbers = [pair["baseline_seconds"], pair["candidate_seconds"]]
            if any(
                type(n) not in (int, float) or not 0 < n < float("inf") for n in numbers
            ):
                raise ReportError("QA measurements need finite positive durations")
            pairs.append(
                {
                    "attempt": pair["attempt"],
                    "baseline_seconds": numbers[0],
                    "candidate_seconds": numbers[1],
                }
            )
        if not pairs:
            raise ReportError("QA comparison requires measured pairs")
        experiments.append(
            {
                "label": ref["label"],
                "source_commit": report["source_commit"],
                "environment": report["environment"],
                "pairs": pairs,
                "unique_coverage_reported_equal": report[
                    "unique_ids_markers_fixtures_sources_equal"
                ],
                "runtime_and_coverage_reported_equal": report[
                    "coverage_and_runtime_outcomes_equal_all_three_pairs"
                ],
                "negative_controls": [
                    {
                        "control": c["control"],
                        "returncode": c["returncode"],
                        "continued": c["continued"],
                    }
                    for c in report["negative_controls"]
                ],
                "limits": report["limits"],
                "url": link(path, output),
            }
        )
    return experiments


def bounded_workloads(campaign, registry, output, sources):
    """Read measured technical workloads; never count them as customer outcomes."""
    experiments = []
    for ref in campaign.get("bounded_workloads", []):
        rows = []
        for phase in ("baseline", "candidate"):
            binding = ref[phase]
            path = (registry.parent / binding["path"]).resolve(strict=True)
            value = read_bound(path, binding["sha256"], sources)
            requested, completed, limit = (
                value[k]
                for k in (
                    "iterations_requested",
                    "iterations_completed",
                    "handle_limit",
                )
            )
            if (
                any(type(n) is not int for n in (requested, completed, limit))
                or not 0 <= completed <= requested
                or requested < 1
                or limit < 1
            ):
                raise ReportError("invalid bounded workload measurement")
            rows.append(
                {
                    "phase": phase,
                    "requested": requested,
                    "completed": completed,
                    "limit": limit,
                    "error": value.get("error"),
                    "url": link(path, output),
                }
            )
        if (
            rows[0]["requested"] != rows[1]["requested"]
            or rows[0]["limit"] != rows[1]["limit"]
        ):
            raise ReportError("bounded workload conditions differ")
        experiments.append({"label": ref["label"], "scope": ref["scope"], "rows": rows})
    return experiments


def engineering_reports(campaign, registry, output, sources):
    """Display backend assessment snapshots, without new currentness or approval."""
    reports = []
    for ref in campaign.get("engineering_reports", []):
        from core.process_validation import ValidationReport

        path = (registry.parent / ref["path"]).resolve(strict=True)
        value = read_bound(path, ref["sha256"], sources)
        try:
            report = ValidationReport.model_validate(value)
        except ValueError as exc:
            raise ReportError("invalid backend engineering report") from exc
        reports.append(
            {
                "label": ref["label"],
                "url": link(path, output),
                "assessment_id": report.assessment.id,
                "assessment_digest": report.assessment_digest,
                "attempt_id": report.assessment.attempt_id,
                "currentness": report.currentness.model_dump(mode="json"),
                "subjects": [
                    x.model_dump(mode="json", exclude={"value"})
                    for x in report.assessment.request.subjects
                ],
                "checks": [x.model_dump(mode="json") for x in report.assessment.checks],
                "requirements": [
                    x.model_dump(mode="json")
                    for x in report.assessment.profile.baseline.requirements
                ],
                "summary": report.assessment.summary.model_dump(mode="json"),
            }
        )
    return reports


def current_visit(ref, root, output, sources):
    """A dated customer observation, including unfinished visits; never run authority."""
    path = (root / ref["path"]).resolve(strict=True)
    visit = read_bound(path, ref["sha256"], sources)
    if visit.get("schema_version") != 1:
        raise ReportError("unknown current visit snapshot")
    def bound(key, lines=False):
        item = visit[key]
        return read_bound((path.parent / item["path"]).resolve(strict=True),
                          item["sha256"], sources, json_lines=lines)
    timing = project_journey(bound("plan"), bound("clock", True))
    if timing["session_id"] != visit["session_id"]:
        raise ReportError("current visit clock crosses customer identity")
    events = {e["id"]: e for e in bound("events", True)}
    if any(e["session_id"] != visit["session_id"] for e in events.values()):
        raise ReportError("current visit evidence crosses customer identity")
    stamp(visit["observed_at"])
    for prompt in visit.get("prompts", []):
        event = events[prompt["evidence_ref"]]
        if event["action"].get("action") != "type_text" or event["action"].get("text") != prompt["text"]:
            raise ReportError("current customer prompt differs from recorded typing")
        prompt["at"] = event["time"]
    for item in visit.get("artifacts", []):
        event = events[item["evidence_ref"]]
        target = (path.parent / item["path"]).resolve(strict=True)
        if item["kind"] != "image" or digest(target) != item["sha256"] or not any(
            c["sha256"] == item["sha256"] for c in event.get("captures", [])
        ):
            raise ReportError("current customer screen differs from recorded evidence")
        sources[str(target)] = item["sha256"]
        item.update(url=link(target, output), at=event["time"])
    return {**visit, "journey_timing": timing, "stage_timing": project_stages(timing)}


def engineering_cases(campaign, registry, output, sources, sessions):
    """Evidence-linked editorial context, never execution or approval authority."""
    cases = []
    by_id = {s["id"]: s for s in sessions}
    for ref in campaign.get("case_sources", []):
        path = (registry.parent / ref["path"]).resolve(strict=True)
        case = read_bound(path, ref["sha256"], sources)
        if case.get("schema_version") != 1:
            raise ReportError("unknown engineering case version")
        stamp(case["as_of"])
        for sid in case["session_ids"]:
            if sid not in by_id:
                raise ReportError("engineering case refers to an unavailable session")
        artifacts = []
        for artifact in case.get("artifacts", []):
            if artifact["kind"] not in {"model", "image", "document", "text", "pdf", "data", "download"}:
                raise ReportError("unknown engineering attachment kind")
            if artifact["origin"] not in {"local_experiment", "operator", "supporting", "workflow_run"}:
                raise ReportError("unknown engineering attachment origin")
            # A label must never turn an ad-hoc file into a managed run result.
            if artifact["origin"] == "workflow_run" and not artifact.get("run_id"):
                raise ReportError("managed result needs its actual run identity")
            target = (path.parent / artifact["path"]).resolve(strict=True)
            if digest(target) != artifact["sha256"]:
                raise ReportError("engineering case attachment digest mismatch")
            sources[str(target)] = artifact["sha256"]
            if artifact.get("session_id") not in case["session_ids"] + [None]:
                raise ReportError("engineering case attachment crosses session")
            artifacts.append({**artifact, "url": link(target, output)})
        comparison = None
        if case.get("comparison_artifact"):
            artifact = next(a for a in artifacts if a["id"] == case["comparison_artifact"])
            comparison = json.loads((path.parent / artifact["path"]).read_text())
        followups = []
        for attempt in case.get("followup_runs", []):
            record_path = (path.parent / attempt["path"]).resolve(strict=True)
            record = read_bound(record_path, attempt["sha256"], sources)
            if record.get("run_id") != attempt["run_id"]:
                raise ReportError("engineering follow-up run identity mismatch")
            started = record["started_at"]
            finished = record.get("completed_at") or record.get("execution_ended_at")
            elapsed = (stamp(finished) - stamp(started)).total_seconds() if finished else None
            if elapsed is not None and elapsed < 0:
                raise ReportError("engineering follow-up has negative duration")
            artifact_id = attempt.get("artifact_id")
            if artifact_id and not any(a["id"] == artifact_id for a in artifacts):
                raise ReportError("engineering follow-up attachment missing")
            followups.append({
                **attempt, "started_at": started, "finished_at": finished,
                "status": record["status"], "elapsed_seconds": elapsed,
                "record_url": link(record_path, output),
            })
        followups.sort(key=lambda item: stamp(item["started_at"]))
        visit = current_visit(case["current_visit_ref"], path.parent, output, sources) if case.get("current_visit_ref") else None
        cases.append({**case, "artifacts": artifacts, "comparison": comparison,
                      "current_visit": visit,
                      "followup_runs": followups,
                      "url": link(path, output)})
    current_id = campaign.get("current_case_id")
    if current_id and not any(case["id"] == current_id for case in cases):
        raise ReportError("current engineering case is missing")
    return cases


def build_data(registry_path, output_path):
    registry = Path(registry_path).resolve(strict=True)
    output = Path(output_path).absolute()
    if output.resolve() != output:
        raise ReportError("output cannot traverse symlinks")
    campaign = json.loads(registry.read_text())
    if campaign.get("schema_version") != 1:
        raise ReportError("unknown campaign registry version")
    sources = {str(registry): digest(registry)}
    # Match the original assignment to the controller's frozen task identity.
    # Reports remain customer observations, not independent result acceptance.
    campaign["resolved_task_sources"] = {}
    for ref in campaign.get("task_sources", []):
        path = (registry.parent / ref["path"]).resolve(strict=True)
        if digest(path) != ref["sha256"]:
            raise ReportError("task source digest mismatch")
        sources[str(path)] = ref["sha256"]
        campaign["resolved_task_sources"][ref["sha256"]] = {
            "text": path.read_text(), "url": link(path, output)
        }
    campaign["resolved_run_details"] = {}
    for ref in campaign.get("run_detail_sources", []):
        path = (registry.parent / ref["path"]).resolve(strict=True)
        detail = read_bound(path, ref["sha256"], sources)
        attachments = []
        for artifact in detail.get("artifacts", []):
            target = (path.parent / artifact["path"]).resolve(strict=True)
            if digest(target) != artifact["sha256"]:
                raise ReportError("result attachment digest mismatch")
            sources[str(target)] = artifact["sha256"]
            attachments.append({**artifact, "url": link(target, output),
                                "text": target.read_text() if artifact["kind"] == "text" else None})
        campaign["resolved_run_details"][detail["session_id"]] = {
            **detail, "artifacts": attachments
        }
    activity_history = []
    activity_event_ids = set()
    for ref in campaign.get("activity_sources", []):
        path = (registry.parent / ref["path"]).resolve(strict=True)
        snapshot = read_bound(path, ref["sha256"], sources)
        binding_path = (registry.parent / ref["bindings_path"]).resolve(strict=True)
        bindings = read_bound(binding_path, ref["bindings_sha256"], sources)
        for event in snapshot["events"]:
            if event["id"] in activity_event_ids:
                raise ReportError(
                    "overlapping activity exports would double count events"
                )
            activity_event_ids.add(event["id"])
            if event["feature"] != ref["feature"]:
                raise ReportError("activity export crosses its registered campaign")
        activity_history.append(
            {
                "label": ref["label"],
                "url": link(path, output),
                "bindings_url": link(binding_path, output),
                **project_activity(snapshot, bindings),
            }
        )
    sessions = []
    seen = set()
    for ref in campaign["record_indexes"]:
        path = (registry.parent / ref["path"]).resolve(strict=True)
        index = read_bound(path, ref["sha256"], sources)
        for item in index["sessions"]:
            if item["session_id"] in seen:
                raise ReportError("repeated session: " + item["session_id"])
            seen.add(item["session_id"])
            intended = ref.get("intended_candidate_sha256")
            if intended and not re.fullmatch(r"[0-9a-f]{64}", intended):
                raise ReportError("invalid intended candidate digest")
            sessions.append(
                project_session(path.parent, item, campaign, output, sources, intended)
            )
    sessions.sort(key=lambda s: stamp(s["started_at"]))
    journey_attempts = []
    for ref in campaign.get("journey_sources", []):
        # Startup failures may never create a customer/model report. Retain their
        # clocks without inventing a product observation or review.
        plan_path = (registry.parent / ref["plan_path"]).resolve(strict=True)
        plan = read_bound(plan_path, ref["plan_sha256"], sources)
        clock_path = (registry.parent / ref["clock_path"]).resolve(strict=True)
        events = read_bound(clock_path, ref["clock_sha256"], sources, json_lines=True)
        timing = project_journey(plan, events)
        if timing["session_id"] in seen:
            raise ReportError("journey clock duplicates a registered customer session")
        seen.add(timing["session_id"])
        failure = None
        manifest = {}
        if ref.get("failure_record_path"):
            failure_path = (registry.parent / ref["failure_record_path"]).resolve(strict=True)
            failure = read_bound(failure_path, ref["failure_record_sha256"], sources)
            if failure.get("status") not in {"failed", "timed_out"}:
                raise ReportError("Interrupted clock does not bind a failed agent record")
        if ref.get("customer_manifest_path"):
            manifest_path = (registry.parent / ref["customer_manifest_path"]).resolve(strict=True)
            manifest = read_bound(manifest_path, ref["customer_manifest_sha256"], sources)
            if manifest["session_id"] != timing["session_id"]:
                raise ReportError("interrupted journey manifest crosses session identity")
        journey_attempts.append(
            {
                "id": timing["session_id"],
                "scope": "first_contact" if failure else "laboratory_timing",
                "profile_label": ref["label"],
                "journey_timing": timing,
                "stage_timing": project_stages(timing),
                "elapsed_seconds": timing["elapsed_seconds"],
                "started_at": timing["started_at"],
                "outcome": "lab_failure" if failure else "no_customer_report",
                "lab_failure": bool(failure),
                "measured_failure": bool(failure) and ref.get("include_in_timing_metrics") is True,
                "failure_reason": failure.get("error") if failure else None,
                "task_assignment": campaign["resolved_task_sources"].get(manifest.get("task_digest")),
                "resource_calls": [{"thread_id": failure["thread_id"], "role": "customer",
                                    "tokens": (failure.get("usage") or {}).get("total", {}).get("totalTokens")}]
                                  if failure and failure.get("thread_id") else [],
                "cohort": "laboratory timing only",
                "report_url": link(clock_path, output),
                "stopping_reason": next(
                    (
                        s["note"]
                        for s in timing["steps"]
                        if s["status"] in {"blocked", "interrupted", "abandoned"}
                    ),
                    "No customer report registered; timing alone establishes no product outcome.",
                ),
            }
        )
    annotations = {}
    for ref in campaign.get("experience_annotations", []):
        path = (registry.parent / ref["path"]).resolve(strict=True)
        annotation = read_bound(path, ref["sha256"], sources)
        for item in annotation["findings"]:
            key = (item["session_id"], item["finding_id"])
            if key in annotations or any(
                c not in CATEGORIES for c in item["categories"]
            ):
                raise ReportError("invalid or duplicate experience classification")
            session = next((s for s in sessions if s["id"] == key[0]), None)
            finding = (
                next((f for f in session["findings"] if f["id"] == key[1]), None)
                if session
                else None
            )
            if (
                not finding
                or hashlib.sha256(finding["observation"].encode()).hexdigest()
                != item["observation_sha256"]
            ):
                raise ReportError(
                    "experience classification does not bind its observation"
                )
            annotations[key] = item["categories"]
    for session in sessions:
        for finding in session["findings"]:
            finding["experience_categories"] = annotations.get(
                (session["id"], finding["id"]), ["unclassified"]
            )
    experience = []
    for key, label in CATEGORIES.items():
        rows = [
            (s, f)
            for s in sessions
            if s["scope"] == "first_contact"
            for f in s["findings"]
            if key in f["experience_categories"]
        ]
        for session in sessions:
            if session["scope"] != "first_contact":
                continue
            for issue in session["journey_timing"].get("issues", []):
                if key in issue["categories"]:
                    rows.append(
                        (
                            session,
                            {
                                "id": "journey-marker-" + str(issue["sequence"]),
                                "review": "self-reported",
                                "impact": "unreviewed",
                                "observation": issue["note"],
                            },
                        )
                    )
        experience.append(
            {
                "id": key,
                "label": label,
                "affected_sessions": len({s["id"] for s, f in rows}),
                "supported_findings": sum(f["review"] == "supported" for s, f in rows),
                "other_findings": sum(f["review"] != "supported" for s, f in rows),
                "blocking_findings": sum(
                    f["review"] == "supported" and f["impact"] == "blocked_progress"
                    for s, f in rows
                ),
                "findings": [
                    {
                        "session_id": s["id"],
                        "finding_id": f["id"],
                        "observation": f["observation"],
                        "review": f["review"],
                        "url": s["report_url"],
                    }
                    for s, f in rows
                ],
            }
        )
    experience.sort(
        key=lambda r: (-r["blocking_findings"], -r["affected_sessions"], r["label"])
    )
    comparisons = []
    by_id = {s["id"]: s for s in sessions}
    for ref in campaign.get("comparisons", []):
        path = (registry.parent / ref["path"]).resolve(strict=True)
        comparison = read_bound(path, ref["sha256"], sources)
        for item in comparison["sessions"]:
            actual = by_id.get(item["session_id"])
            if not actual or actual["scope"] == "first_contact":
                raise ReportError("checkpoint comparison cannot credit a full journey")
            # Reuse the exact saved assessment; no replacement evaluator here.
            if (
                hashlib.sha256(
                    json.dumps(item["audit"], sort_keys=True).encode()
                ).hexdigest()
                != actual["audit_value_sha256"]
            ):
                raise ReportError("comparison evidence mismatch")
        comparisons.append(
            {
                "protocol_id": comparison["protocol_id"],
                "disposition": comparison["disposition"],
                "reasons": comparison["reasons"],
                "sessions": len(comparison["sessions"]),
                "passed_sessions": sum(
                    s["passed"] is True for s in comparison["sessions"]
                ),
                "url": link(path, output),
            }
        )
    metric_scope = campaign.get("performance_scope", "all_first_contact")
    if metric_scope not in {"all_first_contact", "timed_whole_journeys"}:
        raise ReportError("Unknown performance measurement scope")
    for session in sessions:
        timing = session["journey_timing"]
        session["performance_eligible"] = session["scope"] == "first_contact" and (
            metric_scope == "all_first_contact"
            or (timing.get("available") and timing.get("boundary") == "whole_journey")
        )
        if session["performance_eligible"] and metric_scope == "timed_whole_journeys":
            if not session["stage_timing"]["coverage_complete"] or any(
                row["id"] == "unmapped" for row in session["stage_timing"]["stages"]
            ):
                raise ReportError("Measured journey needs complete shared-stage timing: " + session["id"])
    for attempt in journey_attempts:
        # Explicitly registered timed interruptions stay visible, separately from
        # product outcome denominators. Historical lab clocks remain archived.
        attempt["performance_eligible"] = bool(attempt.get("measured_failure"))
    full = [s for s in sessions if s["performance_eligible"]]
    qualified = [s for s in full if s["qualified"]]
    sources[str(TAXONOMY_PATH.resolve())] = digest(TAXONOMY_PATH)
    cases = engineering_cases(campaign, registry, output, sources, sessions)
    reports = engineering_reports(campaign, registry, output, sources)
    loop_path = (registry.parent / campaign["loop_document"]).resolve(strict=True)
    sources[str(loop_path)] = digest(loop_path)
    # This optional local bundle uses the same passive document/STL viewers as
    # Wright. No model, workflow, provider or action is called from this page.
    viewer = output.parent / "evidence-viewer.js"
    if viewer.is_file():
        if viewer.resolve() != viewer:
            raise ReportError("viewer bundle cannot be symlinked")
        sources[str(viewer)] = digest(viewer)
    documents = {
        link(Path(name), output): {
            "text": Path(name).read_text(),
            "format": {".md": "markdown", ".json": "record"}.get(Path(name).suffix.lower(), "text"),
        }
        for name in sources
        if Path(name).suffix.lower() in {".md", ".txt", ".json"}
        and Path(name).stat().st_size <= 512_000
    }
    return {
        "schema_version": 1,
        "measurement_version": "golden-hour-projection-5",
        "title": campaign["title"],
        "display_timezone": campaign.get("display_timezone", "UTC"),
        "benchmark_id": campaign["benchmark_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "refresh_url": output.with_name(output.stem + "-status.json").name,
        "summary": {
            "measured_attempts": len(full) + sum(s["performance_eligible"] for s in journey_attempts),
            "excluded_earlier_attempts": sum(
                s["scope"] == "first_contact" and not s["performance_eligible"] for s in sessions
            ),
            "qualified_journeys": len(qualified),
            "inspected_results": sum(s["inspected_tool_result"] for s in qualified),
            "completed_journeys": sum(s["journey_complete"] for s in qualified),
            "independent_completions": sum(
                s["independent_completion"] for s in qualified
            ),
            "lab_failures": sum(s["lab_failure"] for s in full) + sum(s["performance_eligible"] for s in journey_attempts),
            "unreviewed_or_rejected": sum(
                not s["qualified"] and not s["lab_failure"] for s in full
            ),
        },
        "sessions": sessions,
        "candidate_history": candidate_history(full),
        "performance_scope": metric_scope,
        "candidate_notes": campaign.get("candidate_notes", {}),
        "resource_allocation": resource_allocation(sessions + journey_attempts),
        "activity_history": activity_history,
        "experience_categories": experience,
        "journey_attempts": journey_attempts,
        "journey_stages": TAXONOMY,
        "activity_states": ACTIVITY_STATES,
        "engineering_cases": cases,
        "demonstration_readiness": campaign.get("demonstration_readiness", []),
        "current_case_id": campaign.get("current_case_id"),
        "documents": documents,
        "record_urls": [link(Path(name), output) for name in sources if Path(name).suffix.lower() == ".json"],
        "viewer_url": link(viewer, output) if viewer.is_file() else None,
        "journey_template": json.loads(
            (Path(__file__).parent / "assets/first-workflow-journey.json").read_text()
        ),
        "quality_cost_experiments": quality_cost_history(
            campaign, registry, output, sources
        ),
        "bounded_workloads": bounded_workloads(campaign, registry, output, sources),
        "engineering_reports": reports,
        "comparisons": comparisons,
        "notes": [
            "Counts describe synthetic observations, not human conversion or satisfaction.",
            "Checkpoint/calibration sessions never enter the full-journey denominator.",
            "Session duration is not time to result. Failed/stopped attempts have no result time.",
            "Cohorts match recorded task/model/VM/instruction identities; site/help and controller comparability still need protocol review.",
            "Historical observations are reference evidence, not a preregistered product-improvement experiment.",
            "Dashboard verifies export hashes and recorded assessment bindings, not raw screenshot truth or engineering fitness.",
        ],
        "source_sha256": sources,
        "loop_url": link(
            (registry.parent / campaign["loop_document"]).resolve(strict=True), output
        ),
    }


def render(data):
    template = (Path(__file__).parent / "assets/golden-hour-dashboard.html").read_text()
    payload = (
        json.dumps(data, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    assets = Path(__file__).parent / "assets"
    return (template.replace("__GOLDEN_HOUR_DATA__", payload)
            .replace("__GOLDEN_HOUR_ENGINEERING_CSS__", (assets / "golden-hour-engineering.css").read_text())
            .replace("__GOLDEN_HOUR_ENGINEERING_JS__", (assets / "golden-hour-engineering.js").read_text()))


def export(registry_path, output_path):
    output = Path(output_path).absolute()
    data = build_data(registry_path, output)
    targets = [output, output.with_suffix(".json"),
               output.with_name(output.stem + "-status.json")]
    record_roots = {
        str(Path(p).parent) for p in data["source_sha256"] if p.endswith("/report.json")
    }
    for target in targets:
        if str(target) in data["source_sha256"] or any(
            target.is_relative_to(p) for p in record_roots
        ):
            raise ReportError("cannot overwrite an evidence source")
        if target.is_symlink():
            raise ReportError("output cannot be a symlink")
    output.parent.mkdir(parents=True, exist_ok=True)
    for target, contents in zip(
        targets, [render(data), json.dumps(data, indent=2) + "\n",
                  json.dumps({"schema_version": 1, "generated_at": data["generated_at"]}) + "\n"]
    ):
        with tempfile.NamedTemporaryFile(
            mode="w", dir=target.parent, delete=False
        ) as f:
            f.write(contents)
            temporary = f.name
        os.replace(temporary, target)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = export(args.registry, args.output)
    print(json.dumps({"output": str(args.output), "summary": data["summary"]}))


if __name__ == "__main__":
    main()
