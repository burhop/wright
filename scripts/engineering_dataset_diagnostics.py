"""Read-only operational diagnostics; never awards campaign achievement credit.

Evidence comes from the campaign ledger, optional runner checkpoints and native
lifecycle repository. Missing observations remain unknown. A recovery journal
may supply explicit queue/fix/readiness facts; filesystem mtimes are not facts.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone


def timestamp(value):
    try:
        result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return result if result.tzinfo else result.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def seconds(start, end):
    first, last = timestamp(start), timestamp(end)
    return max(0, round((last - first).total_seconds(), 1)) if first and last else None


def read_json(path, issues):
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("expected a JSON object")
        return value
    except (OSError, ValueError) as error:
        issues.append(f"{path.name}: {type(error).__name__}; observation unavailable")
        return {}


def read_only(path):
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=2)
    connection.execute("PRAGMA query_only=ON")
    return connection


def accepted(receipt):
    return (
        receipt.get("accepted_by_runtime") is True
        and isinstance(receipt.get("run_id"), str) and bool(receipt["run_id"])
        and receipt.get("execution_kind") in {"live", "integration"}
    )


def failure_class(receipt, runner):
    """Codes are observed; broad categories are explicitly a display inference."""
    code = runner.get("reason_code") or receipt.get("error_code")
    error = str(receipt.get("error") or receipt.get("blocker") or "")
    if not code and not error:
        return None
    text = f"{code} {error}".lower()
    categories = (
        (("owner_missing", "outcome_unknown", "shared_resource_unresolved"), "Unresolved ownership / outcome"),
        (("context", "token limit"), "Model context limit"),
        (("import", "roundedrectangle", "attributeerror", "unexpected keyword"), "Source / SDK contract"),
        (("e_pointer", "comexception", "native"), "Native operation"),
        (("timeout", "deadline"), "Deadline / timeout"),
        (("safe_mode", "script guard", "approval"), "Approval / execution guard"),
    )
    category = next((label for needles, label in categories if any(n in text for n in needles)), "Runtime failure")
    return {"code": code, "category": category, "category_inferred": True, "detail": error[:1200]}


def stage_diagnostics(receipt):
    events = sorted(
        (event for event in receipt.get("step_events", []) if isinstance(event, dict) and timestamp(event.get("at"))),
        key=lambda event: timestamp(event["at"]),
    )
    current, last, starts, durations = None, None, {}, []
    for event in events:
        task = event.get("task_id")
        if not task:
            continue
        if event.get("kind") in {"step_started", "approval_requested"}:
            current = task
            starts[task] = event["at"]
        elif event.get("kind") == "step_completed":
            last = task
            durations.append({"task_id": task, "seconds": seconds(starts.get(task), event["at"])})
            if current == task:
                current = None
    return {"last_successful_stage": last, "current_or_failed_stage": current, "stage_durations": durations}


def native_diagnostics(path, issues):
    if path is None or not path.is_file():
        return {"available": False, "sessions": [], "reason": "Native lifecycle source is not configured or available."}
    try:
        with read_only(path) as database:
            tables = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if "native_application_sessions" not in tables:
                return {"available": False, "sessions": [], "reason": "Native lifecycle records have not been initialized."}
            sessions = [json.loads(row[0]) for row in database.execute("SELECT record FROM native_application_sessions")]
            leases = [json.loads(row[0]) for row in database.execute("SELECT record FROM native_application_leases")]
            cleanups = [json.loads(row[0]) for row in database.execute("SELECT record FROM native_application_cleanup")]
        result = []
        for session in sessions:
            session_id = session.get("session_id")
            cleanup = sorted((row for row in cleanups if row.get("session_id") == session_id), key=lambda row: row.get("completed_at") or "")
            identity = session.get("identity") or {}
            result.append({
                "session_id": session_id, "app_kind": session.get("app_kind"),
                "version": session.get("version"), "host": session.get("host"),
                "ownership": session.get("ownership"), "state": session.get("state"),
                "identity": {key: identity.get(key) for key in ("pid", "creation_time", "executable")},
                "heartbeat_at": session.get("heartbeat_at"), "idle_deadline": session.get("idle_deadline"),
                "active_operation": bool(session.get("active_operation")),
                "leases": [{key: lease.get(key) for key in ("lease_id", "resource_id", "owner_id", "case_id", "attempt", "state")}
                           for lease in leases if lease.get("session_id") == session_id],
                "cleanup": {key: cleanup[-1].get(key) for key in ("status", "reason", "blocker", "completed_at")} if cleanup else None,
            })
        return {"available": True, "sessions": result, "reason": None}
    except (OSError, sqlite3.Error, ValueError, TypeError, AttributeError):
        issues.append("Native lifecycle repository could not be read; state is unknown.")
        return {"available": False, "sessions": [], "reason": issues[-1]}


def build_diagnostics(campaign, *, runner_root=None, native_database=None, recovery_path=None, observed_at=None):
    """Project persisted evidence afresh on every poll, including after restart.

    Optional recovery journal: {families: {template_id: {readiness, next_action,
    queued_at, fixes: [{at, evidence}]}}, scenarios: {scenario_id: {queued_at}}}.
    Only timestamped fixes with an evidence reference qualify for fix age/counts.
    """
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    issues = []
    recovery = read_json(recovery_path, issues)
    # A campaign can retain diagnostic sessions in a separate WAL database.
    # Resolve this live journal setting only within its own diagnostics folder.
    if "native_database_path" in recovery:
        relative = recovery["native_database_path"]
        allowed = (campaign.db.parent / "diagnostics").resolve()
        if isinstance(relative, str) and not any(char in relative for char in ("\\", ":")):
            candidate = (campaign.db.parent / relative).resolve()
            if candidate.is_relative_to(allowed) and candidate.suffix in {".sqlite3", ".db"}:
                native_database = candidate
            else:
                issues.append("Native database journal path must remain within campaign diagnostics.")
        else:
            issues.append("Native database journal path must be a relative POSIX path.")
    for section in ("families", "scenarios"):
        if not isinstance(recovery.get(section, {}), dict):
            issues.append(f"Recovery {section} must be an object; observation unavailable.")
            recovery[section] = {}
        recovery[section] = {key: value for key, value in recovery.get(section, {}).items() if isinstance(value, dict)}
    with campaign.lock, read_only(campaign.db) as database:
        datasets = [json.loads(row[0]) for row in database.execute("SELECT document FROM datasets ORDER BY id")]
        receipts = [json.loads(row[0]) for row in database.execute("SELECT document FROM attempts ORDER BY id")]
    by_run = {receipt["run_id"]: receipt for receipt in receipts if accepted(receipt)}
    runs = list(by_run.values())
    runners = {}
    if runner_root is not None:
        for receipt in receipts:
            scenario, attempt = receipt.get("scenario_id"), receipt.get("attempt_id")
            # Ledger identities must be a single safe path component.
            if all(isinstance(value, str) and value not in {".", ".."} and not any(c in value for c in "/\\:") for value in (scenario, attempt)):
                runners[(scenario, attempt)] = read_json(runner_root / scenario / f"{attempt}.json", issues)
    summary = read_json(runner_root / "summary.json", issues) if runner_root else {}
    rows = []
    for dataset in datasets:
        scenario, family = dataset["scenario_id"], dataset["template_id"]
        history = [receipt for receipt in runs if receipt.get("scenario_id") == scenario]
        current = [receipt for receipt in receipts if receipt.get("scenario_id") == scenario
                   and receipt.get("dataset_digest") == dataset["digest"]
                   and receipt.get("template_digest") == dataset["template_digest"]]
        current.sort(key=lambda receipt: receipt.get("started_at") or "")
        latest = current[-1] if current else {}
        runner = runners.get((scenario, latest.get("attempt_id")), {})
        family_plan = recovery.get("families", {}).get(family, {})
        candidate_fixes = family_plan.get("fixes") or []
        fixes = [fix for fix in candidate_fixes if isinstance(fix, dict) and timestamp(fix.get("at")) and fix.get("evidence")]
        last_fix = max(fixes, key=lambda fix: timestamp(fix["at"])) if fixes else None
        queued_at = recovery.get("scenarios", {}).get(scenario, {}).get("queued_at") or family_plan.get("queued_at")
        terminal = latest.get("status") in {"failed", "cancelled", "timed_out", "completed", "succeeded", "blocked"}
        end = latest.get("finished_at") or (runner.get("updated_at") if terminal else None)
        completed = any(receipt.get("completed_with_outputs") for receipt in current)
        usage = latest.get("usage") or {}
        tokens = usage.get("total_tokens")
        rows.append({
            "scenario_id": scenario, "template_id": family, "completed_current_revision": completed,
            "accepted_attempts": len(history), "attempt_id": latest.get("attempt_id"), "run_id": latest.get("run_id"),
            "runtime_status": latest.get("status", "not_run"), "runner_phase": runner.get("phase"),
            "runner_observed_at": runner.get("updated_at"), "failure": failure_class(latest, runner),
            **stage_diagnostics(latest),
            "duration_seconds": seconds(latest.get("started_at"), end),
            "duration_source": "runtime timestamps" if latest.get("finished_at") else "runner terminal observation (upper bound)" if end else None,
            "native_duration_seconds": latest.get("native_duration_seconds"),
            "model_duration_seconds": latest.get("model_duration_seconds"),
            "total_tokens": tokens if isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0 else None,
            "last_fix_at": last_fix["at"] if last_fix else None,
            "fix_evidence": last_fix["evidence"] if last_fix else None,
            "fix_age_seconds": seconds(last_fix["at"], observed_at) if last_fix else None,
            "attempts_since_fix": sum(timestamp(receipt.get("started_at")) >= timestamp(last_fix["at"]) for receipt in history if timestamp(receipt.get("started_at"))) if last_fix else None,
            "queue_age_seconds": seconds(queued_at, observed_at) if not completed else None,
            "readiness": "complete" if completed else family_plan.get("readiness", "not recorded"),
            "next_action": family_plan.get("next_action"),
        })
    finished = [receipt["finished_at"] for receipt in runs if receipt.get("completed_with_outputs") and timestamp(receipt.get("finished_at"))]
    last_completion = max(finished, key=timestamp) if finished else None
    unresolved = [receipt for receipt in runs if runners.get((receipt.get("scenario_id"), receipt.get("attempt_id")), {}).get("phase") == "outcome_unknown"]
    recorded_running = [receipt for receipt in runs if receipt.get("status") == "running"]
    families = [{"template_id": family, "completed": sum(row["completed_current_revision"] for row in rows if row["template_id"] == family),
                 "total": sum(row["template_id"] == family for row in rows), **recovery.get("families", {}).get(family, {})}
                for family in sorted({row["template_id"] for row in rows})]
    return {
        "schema_version": 1, "observed_at": observed_at, "read_only": True,
        "accepted_attempts": len(runs), "recorded_running_attempts": len(recorded_running),
        "unresolved_attempts": [{"scenario_id": receipt["scenario_id"], "attempt_id": receipt["attempt_id"],
                                 "run_id": receipt["run_id"], "reason": runners[(receipt["scenario_id"], receipt["attempt_id"])].get("reason_code")} for receipt in unresolved],
        "last_completion_at": last_completion, "since_last_completion_seconds": seconds(last_completion, observed_at),
        "runner": {"paused": (runner_root / "pause-after-current").is_file() if runner_root and runner_root.is_dir() else None,
                   "summary_observed_at": summary.get("updated_at"), "next_scenario_id": summary.get("next_scenario_id"),
                   "worker_health": "unknown"},
        "native": native_diagnostics(native_database, issues), "families": families, "scenarios": rows,
        "issues": issues,
    }
