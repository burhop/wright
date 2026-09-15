"""Export observer receipts only from persisted canonical integration-run evidence.

This helper does not run workflows or accept execution/completion booleans. It
checks file identity and runtime lineage, not engineering content correctness.
Callers supply the independently compiled definition's entire required step set.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import time


class EvidenceError(ValueError):
    pass


EXPORTER_REVISION = 5


def _public_error(record):
    message = record.get("error")
    if not isinstance(message,str) or not message.strip():
        return {}
    # Only the recorder's browser-facing error and code are exposed. Never copy
    # nested tool payloads, model prompts, arguments, environment or tracebacks.
    message = re.sub(r"[\x00-\x08\x0b-\x1f]", " ", message)[:4096]
    message = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[redacted]", message)
    message = re.sub(r'(?i)((?:api[_-]?key|access[_-]?token|access[_-]?code|password|authorization|secret)\s*[\"\']?\s*[:=]\s*)(?:\"[^\"]*\"|\'[^\']*\'|[^\s,;}]+)', r"\1[redacted]", message)
    code = record.get("code")
    code = code if isinstance(code,str) and re.fullmatch(r"[A-Za-z0-9_:-]{1,100}",code) else "RUNTIME_FAILURE"
    return {"error":message,"error_code":code}


def _require(condition, message):
    if not condition:
        raise EvidenceError(message)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _publish(temporary, destination):
    for attempt in range(10):
        try:
            temporary.replace(destination)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(.02 * (attempt+1))


def _digest(value):
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "Invalid immutable digest")
    return value


def _relative(value):
    _require(isinstance(value, str) and bool(value) and "\\" not in value and ":" not in value,
             "Artifact paths must be relative POSIX paths")
    path = PurePosixPath(value)
    _require(not path.is_absolute() and all(p not in {"..", "."} for p in path.parts), "Path escapes its root")
    return path


def _scoped(root, relative):
    path = root.joinpath(*_relative(relative).parts).resolve()
    _require(path != root and path.is_relative_to(root), "Path escapes its root")
    return path


def _time(value):
    try:
        time = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _require(time.tzinfo is not None, "Evidence timestamps need a timezone")
        return time.timestamp()
    except (ValueError, TypeError, AttributeError):
        raise EvidenceError("Invalid evidence timestamp") from None


def _model_usage(events):
    observed_requests = sum(
        event.get("execution_kind") == "ai"
        for event in events
        if event.get("kind") == "step_started"
    ) + sum(
        isinstance(event.get("available_tools"), list)
        and type(event.get("tool_calls")) is int
        for event in events
        if event.get("kind") == "task_progress"
    )
    reports = [
        event["usage"]
        for event in events
        if event.get("kind") == "model_usage"
        and isinstance(event.get("usage"), dict)
    ]
    # A persisted usage event is itself evidence that a model request occurred,
    # including older run records that predate request-marker enrichment.
    requests = max(observed_requests, len(reports))
    models = sorted(
        {
            usage["model"]
            for usage in reports
            if isinstance(usage.get("model"), str) and usage["model"]
        }
    )
    fields = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    )
    totals = {}
    for field in fields:
        values = [usage.get(field) for usage in reports]
        totals[field] = (
            sum(values)
            if reports
            and len(reports) == requests
            and all(type(value) is int and value >= 0 for value in values)
            else None
        )
    return {
        "status": "reported" if reports and len(reports) == requests else "unknown",
        "request_count": requests,
        "reported_request_count": len(reports),
        "models": models,
        **totals,
    }


def _results(result, depth=0):
    _require(isinstance(result, dict) and depth <= 8, "Invalid nested artifact result")
    yield result
    for child in result.get("exports", []):
        yield from _results(child, depth+1)


def lifecycle_observation(record, relative_log, raw_digest, response, observed_at):
    """Match a normal API lease projection to an exact persisted run snapshot.

    The recent-runs API may omit run_id before any result exists. In that case
    the unique log path, immutable source and exact durable start bind identity.
    This supplies uncertainty evidence only, never terminal execution evidence.
    """
    context = record.get("execution_context", {})
    _require(record.get("status") == "running", "Lifecycle projection requires a running raw record")
    _require(isinstance(record.get("run_id"), str) and record["run_id"], "Lifecycle observation requires a persisted run identity")
    _require(isinstance(response, dict) and response.get("workflow_path") == record.get("workflow_path")
             and response.get("workspace_id") == context.get("workspace_id")
             and isinstance(context.get("workspace_id"), str) and context["workspace_id"],
             "Lifecycle API workspace/source identity mismatch")
    starts = [e for e in record.get("events", []) if e.get("kind") == "run_started"]
    _require(len(starts) == 1 and starts[0].get("run_id") == record.get("run_id")
             and starts[0].get("run_log_path") == relative_log
             and starts[0].get("at") == record.get("started_at"),
             "Lifecycle observation requires an exact durable run_started")
    rows = response.get("runs")
    _require(isinstance(rows, list), "Lifecycle API run list is invalid")
    matches = [r for r in rows if isinstance(r, dict) and r.get("path") == relative_log]
    _require(len(matches) == 1, "Lifecycle API run path is missing or ambiguous")
    row = matches[0]
    _require(row.get("source_digest") == record.get("source_digest")
             and row.get("started_at") == record.get("started_at")
             and row.get("source_matches_current") is True
             and row.get("run_id") in {None, record.get("run_id")},
             "Lifecycle API run/source/start identity mismatch")
    _require(row.get("status") in {"running", "interrupted"},
             "Lifecycle observation cannot assert failed or completed execution")
    execution = row.get("execution", {})
    _require(isinstance(execution, dict) and type(execution.get("event_count")) is int
             and execution["event_count"] == len(record.get("events", [])),
             "Lifecycle API event snapshot differs from raw evidence")
    _require(_time(observed_at) >= max(_time(e.get("at")) for e in record["events"])
             and _time(observed_at) <= time.time() + 5,
             "Lifecycle observation timestamp is stale or in the future")
    _digest(raw_digest)
    return {"schema_version": 1, "kind": "wright.normal-api-run-lifecycle.v1",
        "endpoint": "/api/workspace/workflow-sources/runs", "observed_at": observed_at,
        "runtime_evidence": {"path": relative_log, "sha256": raw_digest},
        "matched_run_id": record["run_id"],
        "matching_mode": "run_id_and_log_source_start" if row.get("run_id") else "log_source_start_run_id_unavailable",
        "workspace_id": response["workspace_id"], "workflow_path": response["workflow_path"],
        "run": {k: row.get(k) for k in ("path", "run_id", "status", "started_at", "source_digest", "source_matches_current")},
        "execution": {"event_count": execution["event_count"]}}


def lifecycle_fingerprint(observation):
    if observation is None:
        return None
    return _sha(json.dumps({k:v for k,v in observation.items() if k != "observed_at"}, sort_keys=True).encode())


def validate_lifecycle_observation(record, relative_log, raw_digest, observation):
    _require(isinstance(observation, dict), "Invalid lifecycle observation")
    _require(isinstance(observation.get("run"), dict), "Invalid lifecycle run observation")
    response = {"workspace_id": observation.get("workspace_id"), "workflow_path": observation.get("workflow_path"),
                "runs": [{**observation.get("run", {}), "execution": observation.get("execution")} ]}
    expected = lifecycle_observation(record, relative_log, raw_digest, response, observation.get("observed_at"))
    _require(observation == expected, "Lifecycle evidence differs from the immutable run snapshot")
    return expected


def export_run_evidence(run_record_path, *, workspace_root, export_root,
                        scenario_id, attempt_id, dataset_digest, template_digest,
                        definition_digest, required_step_ids, output_root, lifecycle=None):
    """Write <export_root>/<scenario>/<attempt>/run.json after all evidence checks.

    run_record_path may be absolute but must be a file inside workspace_root/runs.
    export_root is normally artifacts/engineering-workflow-datasets/output.
    All other identity arguments come from the campaign manifest/compiled source,
    never a workflow response. Returns the exact observer-compatible receipt.
    """
    for value in (scenario_id, attempt_id):
        _require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}", value), "Invalid scenario/attempt identity")
    for value in (dataset_digest, template_digest, definition_digest):
        _digest(value)
    required = list(required_step_ids)
    _require(required and len(required) == len(set(required)) and all(isinstance(s,str) and s for s in required), "Required step identities must be complete and unique")
    workspace = Path(workspace_root).resolve()
    run_path = Path(run_record_path)
    run_path = (workspace/run_path).resolve() if not run_path.is_absolute() else run_path.resolve()
    _require(run_path.is_relative_to(workspace / "runs") and run_path.is_file(), "Evidence must be a persisted canonical run file")
    raw = run_path.read_bytes()
    _require(0 < len(raw) <= 32 * 1024 * 1024, "Run evidence size exceeds limit")
    record = json.loads(raw)
    context = record.get("execution_context", {})
    run_id = record.get("run_id")
    _require(isinstance(run_id,str) and bool(run_id), "Persisted run has no reserved run identity")
    _require(record.get("source_digest") == definition_digest, "Definition digest differs from runtime record")
    for field, value in {"dataset_id":scenario_id, "dataset_digest":dataset_digest,
                         "source_digest":definition_digest, "output_root":output_root,
                         "execution_kind":"integration"}.items():
        _require(context.get(field) == value, "Integration execution context differs from campaign identity")
    _require(isinstance(context.get("campaign_id"),str) and context["campaign_id"], "No campaign identity")
    _require(context.get("actor") == "integration_test:" + context["campaign_id"], "Missing attributed integration actor")
    _digest(context.get("integration_policy_digest"))
    _require(record.get("workflow_path") == context.get("source_path"), "Runtime workflow path differs from enrolled source")
    source_path = _scoped(workspace, context["source_path"])
    _require(source_path.is_file() and _sha(source_path.read_bytes()) == definition_digest,
             "Saved source differs from this run's immutable definition")
    _require(set(record.get("required_step_ids", [])) == set(required) and len(record["required_step_ids"]) == len(required), "Runtime required step set differs from full canonical definition")
    input_files = context.get("input_files")
    _require(isinstance(input_files,dict) and input_files, "Run has no enrolled input identities")
    for path, identity in input_files.items():
        _relative(path)
        _digest(identity)
    input_hashes = set(input_files.values())
    events = record.get("events")
    _require(isinstance(events,list) and all(isinstance(e,dict) for e in events), "Missing durable events")
    starts = [e for e in events if e.get("kind") == "run_started"]
    _require(len(starts) == 1 and starts[0].get("run_id") == run_id, "Missing or mismatched durable run_started identity")
    start = starts[0]
    relative_log = run_path.relative_to(workspace).as_posix()
    _require(start.get("run_log_path") == relative_log, "Start event belongs to another persisted run path")
    started_at = start.get("at")
    start_time = _time(started_at)
    _require(record.get("started_at") == started_at, "Record start time differs from durable event")
    completed, started, evidence_results = set(), set(), {}
    terminal = None
    for event in events:
        kind, task = event.get("kind"), event.get("task_id")
        if "run_id" in event:
            _require(event["run_id"] == run_id, "Cross-run event rejected")
        _require(_time(event.get("at")) >= start_time, "Event predates runtime start")
        if kind in {"step_started", "approval_requested", "review_requested"}:
            terminal = None
            _require(task in required, "Event executes an undeclared step")
            started.add(task)
            completed.discard(task)
            evidence_results = {k:v for k,v in evidence_results.items() if v["provenance"]["task_id"] != task}
        elif kind == "design_revision":
            invalidated = set(event.get("invalidated_task_ids", []))
            completed -= invalidated
            started -= invalidated
            evidence_results = {k:v for k,v in evidence_results.items() if v["provenance"]["task_id"] not in invalidated}
        elif kind == "step_completed":
            _require(task in started, "Step completion has no preceding start or approval checkpoint")
            completed.add(task)
        elif kind == "result_ready":
            for artifact in _results(event.get("engineering_result")):
                provenance = artifact.get("provenance", {})
                _require(provenance.get("run_id") == run_id and provenance.get("task_id") in started, "Cross-run or unstarted artifact result")
                _require(artifact.get("id") == f"{run_id}:{provenance['task_id']}:{provenance.get('output_port')}", "Artifact ID does not match runtime provenance")
                evidence_results[artifact["id"]] = artifact
        elif kind == "run_completed":
            _require(set(event.get("required_steps_completed", [])) == set(required), "Terminal event omits required canonical steps")
            _require(completed == set(required), "Terminal event occurs before all steps complete")
            terminal = event
        elif kind in {"run_resumed", "step_started"}:
            terminal = None
    result = record.get("result") or {}
    _require(not result or result.get("run_id") == run_id, "Final result belongs to another run")
    for final in result.get("results", []):
        for artifact in _results(final):
            provenance = artifact.get("provenance", {})
            _require(provenance.get("run_id") == run_id, "Final artifact belongs to another run")
            file_reps = [r for r in artifact.get("representations", []) if r.get("kind") == "workspace_file"]
            if file_reps:
                observed = evidence_results.get(artifact.get("id"))
                _require(observed is not None, "Final artifact has no durable result_ready evidence")
                observed_reps = observed.get("representations", [])
                _require(all(r in observed_reps for r in file_reps), "Final artifact differs from durable result evidence")
    is_complete = record.get("status") == "completed"
    if is_complete:
        _require(terminal is not None and completed == set(required), "Completion lacks durable full-graph terminal evidence")
        steps = result.get("steps", [])
        ids = [s.get("task_id") for s in steps]
        _require(len(ids) == len(required) and set(ids) == set(required), "Completed result omits or duplicates required steps")
        _require(result.get("status") == "completed", "Final result does not assert completed execution")
    else:
        _require(terminal is None, "Terminal event conflicts with nonterminal record")
    output_path = _scoped(workspace, output_root)
    approval_steps = {s["task_id"]:s for s in result.get("steps", []) if s.get("execution_kind") == "approval"}
    approved_paths = {}
    has_test_handoff = False
    for task, step in approval_steps.items():
        action = step.get("external_action", {})
        if action.get("outcome") == "dispatched":
            action_evidence = action.get("evidence", {})
            for output in action_evidence.get("produced_files", []):
                _require(action_evidence.get("operation") == "test_handoff"
                         and action_evidence.get("integration_test") is True
                         and action_evidence.get("simulated_handoff") is True,
                         "Integration receipt lacks explicitly simulated handoff evidence")
                approved_paths[output["output_path"]] = (task, output, step)
                has_test_handoff = True
    candidates = []
    excluded_artifacts = []
    for artifact in evidence_results.values():
        if artifact.get("artifact_role") == "diagnostic":
            continue
        task = artifact["provenance"]["task_id"]
        for representation in artifact.get("representations", []):
            if representation.get("kind") != "workspace_file":
                continue
            location = representation.get("location")
            path = _scoped(workspace, location)
            _require(path.is_relative_to(output_path) and path != output_path, "Artifact lies outside this attempt output root")
            _require(path.is_file(), "Recorded artifact is missing")
            data = path.read_bytes()
            actual = _sha(data)
            _require(data and len(data) <= 100*1024*1024, "Recorded artifact is empty or too large")
            _require(actual == representation.get("sha256") and len(data) == representation.get("size_bytes"), "Recorded artifact hash or size drift")
            if actual in input_hashes and not is_complete:
                # Keep actual running/failure status observable without exporting
                # a copied input as an engineering deliverable. A completed run
                # still fails this boundary; exclusion cannot grant completion.
                excluded_artifacts.append({"artifact_id": artifact["id"],
                                           "workspace_path": location, "reason_code": "input_copy"})
                continue
            _require(actual not in input_hashes, "Input copy cannot substitute for generated artifact")
            _require(path.stat().st_mtime >= start_time, "Artifact predates this runtime attempt")
            if artifact.get("artifact_role") == "external_action_receipt" or task in approval_steps:
                _require(location in approved_paths and approved_paths[location][0] == task, "Handoff receipt lacks dispatched same-run action evidence")
                _, output, step = approved_paths[location]
                _require(output.get("sha256") == actual and output.get("output_bytes") == len(data), "Handoff receipt differs from dispatched evidence")
                handoff = json.loads(data)
                _require(handoff.get("integration_test") is True and handoff.get("simulated_handoff") is True
                         and handoff.get("network_dispatch") is False,
                         "Receipt does not represent an isolated test handoff")
                _require(handoff.get("run_id") == run_id and handoff.get("step_id") == task
                         and handoff.get("dataset_id") == scenario_id
                         and handoff.get("campaign_id") == context["campaign_id"]
                         and handoff.get("integration_policy_digest") == context["integration_policy_digest"]
                         and handoff.get("checkpoint_id") == step.get("checkpoint_id")
                         and handoff.get("subject_digest") == step.get("subject_digest"),
                         "Receipt identity differs from same-run approved checkpoint")
                _require(isinstance(handoff.get("action_id"), str) and bool(handoff["action_id"])
                         and handoff["action_id"] == step["external_action"].get("action_id"),
                         "Receipt action identity differs from dispatched action")
                destination = handoff.get("destination", {})
                _require(destination.get("kind") in {"integration_test", "test"}
                         and destination.get("id") in context.get("test_destinations", [])
                         and str(destination.get("id", "")).startswith("test://"),
                         "Receipt destination was not enrolled as an exact test destination")
            candidates.append(({"artifact_id":artifact["id"], "path":path.relative_to(output_path).as_posix(),
                "workspace_path":location, "sha256":actual, "size_bytes":len(data), "run_id":run_id,
                "task_id":task, "artifact_role":artifact.get("artifact_role","deliverable")}, data))
    status = record.get("status")
    mapping = {"continuation_ready":"awaiting_approval", "changes_requested":"blocked",
               "external_action_not_dispatched":"blocked", "awaiting_external_outcome":"outcome_unknown",
               "external_action_outcome_unknown":"outcome_unknown"}
    status = mapping.get(status,status)
    if lifecycle is not None:
        lifecycle = validate_lifecycle_observation(record, relative_log, _sha(raw), lifecycle)
        if lifecycle["run"]["status"] == "interrupted":
            status = "outcome_unknown"
    _require(status in {"running","awaiting_approval","pending_review","failed","cancelled","timed_out","outcome_unknown","completed","blocked"}, "Unsupported runtime state")
    receipt = {"schema_version":1, "scenario_id":scenario_id, "attempt_id":attempt_id,
        "evidence_exporter_revision":EXPORTER_REVISION, **_public_error(record),
        "dataset_digest":dataset_digest, "template_digest":template_digest, "definition_digest":definition_digest,
        "run_id":run_id, "status":status, "accepted_by_runtime":True, "execution_kind":"integration",
        "started_at":started_at, "finished_at":record.get("completed_at") if is_complete else None,
        "terminal_step_reached":is_complete, "all_required_steps_succeeded":is_complete,
        "external_effects":"test_destinations" if has_test_handoff else "none", "content_validated":False,
        "required_step_ids":required, "completed_step_ids":sorted(completed),
        "produced_files":[v for v,_ in candidates], "runtime_evidence":{"path":relative_log,"sha256":_sha(raw)},
        "excluded_artifacts": excluded_artifacts,
        "integration_policy_digest":context["integration_policy_digest"], "approval_actor":context["actor"],
        "campaign_id":context["campaign_id"], "usage": _model_usage(events),
        "approval_evidence":[{"task_id":task, "checkpoint_id":s.get("checkpoint_id"),
            "subject_digest":s.get("subject_digest"), "action_id":s.get("external_action",{}).get("action_id"),
            "outcome":s.get("external_action",{}).get("outcome"),
            "operation":s.get("external_action",{}).get("evidence",{}).get("operation")}
            for task,s in approval_steps.items()],
        "step_events":[{k:e[k] for k in ("kind","at","task_id","run_id","checkpoint_id","subject_digest") if k in e}
                       for e in events if e.get("kind") in {"run_started","run_resumed","run_completed","step_started","step_completed","approval_requested","approval_decided","external_action_reconciled"}],
    }
    if is_complete:
        _require(_time(receipt["finished_at"]) >= _time(terminal["at"]), "Completion timestamp predates terminal event")
    target = _scoped(Path(export_root).resolve(), scenario_id + "/" + attempt_id)
    receipt_path = target / "run.json"
    if receipt_path.exists():
        old = json.loads(receipt_path.read_text())
        _require(all(old.get(k) == receipt[k] for k in ("run_id","scenario_id","attempt_id","dataset_digest","template_digest","definition_digest")), "Attempt export identity is immutable")
        if (old.get("status_projection", {}).get("reason_code") == "normal_api_owner_interrupted"
                and old.get("runtime_evidence") == receipt["runtime_evidence"]):
            _require(lifecycle is not None, "Matched lifecycle evidence is required to refresh an interrupted snapshot")
        if lifecycle is not None and old.get("lifecycle_observed_at"):
            _require(_time(lifecycle["observed_at"]) >= _time(old["lifecycle_observed_at"]), "Lifecycle observation predates the published observation")
    _require(_sha(run_path.read_bytes()) == _sha(raw), "Raw runtime snapshot changed during evidence observation")
    if lifecycle is not None:
        lifecycle_bytes = (json.dumps(lifecycle, sort_keys=True, indent=2) + "\n").encode()
        lifecycle_hash = _sha(lifecycle_bytes)
        lifecycle_relative = "lifecycle/" + lifecycle_hash + ".json"
        lifecycle_path = _scoped(target, lifecycle_relative)
        lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
        if lifecycle_path.exists():
            _require(lifecycle_path.read_bytes() == lifecycle_bytes, "Immutable lifecycle evidence changed")
        else:
            with lifecycle_path.open("xb") as stream:
                stream.write(lifecycle_bytes)
        receipt.update(lifecycle_evidence={"path": lifecycle_relative, "sha256": lifecycle_hash},
                       lifecycle_observed_at=lifecycle["observed_at"], raw_runtime_status=record["status"])
        if status == "outcome_unknown":
            receipt["status_projection"] = {"from": "running", "to": "outcome_unknown", "reason_code": "normal_api_owner_interrupted"}
    for entry, data in candidates:
        destination = _scoped(target / "artifacts", entry["path"])
        if destination.is_file() and _sha(destination.read_bytes()) == entry["sha256"]:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".evidence-tmp")
        temporary.write_bytes(data)
        _publish(temporary,destination)
    target.mkdir(parents=True, exist_ok=True)
    _require(_sha(run_path.read_bytes()) == _sha(raw), "Raw runtime snapshot changed before receipt publication")
    temporary = target / "run.json.evidence-tmp"
    temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    _publish(temporary,receipt_path)
    return receipt
