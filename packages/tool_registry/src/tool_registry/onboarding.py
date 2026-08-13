from __future__ import annotations

import inspect
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog

from .capability_models import InstallPlan
from .catalog_snapshots import get_catalog_state
from .compatibility import load_latest_machine_observation
from .install_plans import (
    InstallPlanError,
    _persist,
    get_install_plan,
    validate_plan_for_apply,
)

logger = structlog.get_logger(__name__)


class OnboardingError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _connect(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    return connection


def _invoke(adapter, method: str, plan: InstallPlan) -> dict[str, Any]:
    callable_method = getattr(adapter, method)
    signature = inspect.signature(callable_method)
    result = (
        callable_method() if len(signature.parameters) == 0 else callable_method(plan)
    )
    if not isinstance(result, dict):
        raise OnboardingError(
            "onboarding_adapter_contract",
            f"Adapter {method} returned invalid evidence.",
        )
    return result


def _run_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "plan_id": row["plan_id"],
        "plan_digest": row["plan_digest"],
        "state": row["state"],
        "adapter_kind": row["adapter_kind"],
        "adapter_version": row["adapter_version"],
        "started_at": datetime.fromtimestamp(row["started_at"], UTC).isoformat(),
        "completed_at": datetime.fromtimestamp(row["completed_at"], UTC).isoformat()
        if row["completed_at"]
        else None,
        "effects": json.loads(row["effects_json"]),
        "validation_evidence_id": row["validation_evidence_id"],
        "trace_id": row["trace_id"],
        "failure_code": row["failure_code"],
        "rollback_state": row["rollback_state"],
    }


def get_onboarding_run(database_path: str | Path, run_id: str) -> dict[str, Any]:
    with _connect(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM mcp_onboarding_runs WHERE run_id=?", (run_id,)
        ).fetchone()
    if row is None:
        raise OnboardingError(
            "onboarding_run_not_found", "Onboarding run was not found.", status_code=404
        )
    return _run_from_row(row)


def apply_install_plan(
    database_path: str | Path,
    plan_id: str,
    digest: str,
    *,
    adapters: dict[str, Any],
    actor: str,
    now: datetime,
    trace_id: str,
) -> dict[str, Any]:
    plan = get_install_plan(database_path, plan_id)
    run_id = f"run-{plan.plan_digest[:20]}"
    try:
        existing = get_onboarding_run(database_path, run_id)
        if existing["plan_digest"] == digest:
            return existing
    except OnboardingError:
        pass
    state = get_catalog_state(database_path)
    observation = load_latest_machine_observation(database_path, now=now)
    if observation is None:
        raise InstallPlanError(
            "machine_observation_stale", "Machine observation is missing or stale."
        )
    validate_plan_for_apply(
        plan,
        digest,
        now=now,
        active_snapshot_id=state["active_snapshot_id"],
        observation_digest=observation.digest,
    )
    adapter = adapters.get(plan.backend_kind)
    if adapter is None:
        raise OnboardingError(
            "onboarding_adapter_missing",
            f"No {plan.backend_kind} adapter is configured.",
        )
    logger.info(
        "onboarding_apply_started",
        trace_id=trace_id,
        plan_id=plan_id,
        actor=actor,
        adapter=plan.backend_kind,
    )
    effects: list[dict[str, Any]] = []
    started = int(now.timestamp())
    with _connect(database_path) as connection:
        connection.execute(
            """INSERT INTO mcp_onboarding_runs (
                run_id, plan_id, plan_digest, state, adapter_kind, adapter_version,
                started_at, completed_at, effects_json, validation_evidence_id,
                trace_id, failure_code, rollback_state
            ) VALUES (?, ?, ?, 'applying', ?, ?, ?, NULL, '[]', NULL, ?, NULL, NULL)""",
            (run_id, plan_id, digest, adapter.kind, adapter.version, started, trace_id),
        )
    _persist(database_path, plan.model_copy(update={"state": "applying"}))
    final_state = "completed"
    failure_code = None
    rollback_state = None
    try:
        for method in ("prepare", "apply", "validate"):
            logger.info(
                "onboarding_effect_started",
                trace_id=trace_id,
                run_id=run_id,
                effect=method,
            )
            result = _invoke(adapter, method, plan)
            effects.append({"kind": method, "status": "succeeded", "result": result})
        _persist(database_path, plan.model_copy(update={"state": "completed"}))
    except Exception as error:
        failure_code = "onboarding_effect_failed"
        effects.append(
            {"kind": "apply", "status": "failed", "error": type(error).__name__}
        )
        final_state = "failed"
        try:
            rollback = _invoke(adapter, "rollback", plan)
            effects.append(
                {"kind": "rollback", "status": "rolled_back", "result": rollback}
            )
            rollback_state = "rolled_back"
            final_state = "rolled_back"
            _persist(database_path, plan.model_copy(update={"state": "rolled_back"}))
        except Exception as rollback_error:
            effects.append(
                {
                    "kind": "rollback",
                    "status": "failed",
                    "error": type(rollback_error).__name__,
                }
            )
            rollback_state = "rollback_failed"
            final_state = "rollback_failed"
            _persist(
                database_path, plan.model_copy(update={"state": "rollback_failed"})
            )
    completed = int(now.timestamp())
    with _connect(database_path) as connection:
        connection.execute(
            """UPDATE mcp_onboarding_runs SET state=?, completed_at=?, effects_json=?,
                      failure_code=?, rollback_state=? WHERE run_id=?""",
            (
                final_state,
                completed,
                json.dumps(effects, sort_keys=True),
                failure_code,
                rollback_state,
                run_id,
            ),
        )
    logger.info(
        "onboarding_apply_finished",
        trace_id=trace_id,
        run_id=run_id,
        state=final_state,
        rollback_state=rollback_state,
    )
    return get_onboarding_run(database_path, run_id)


def cancel_onboarding_run(
    database_path: str | Path,
    run_id: str,
    *,
    adapters: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    run = get_onboarding_run(database_path, run_id)
    if run["state"] in {"completed", "rolled_back", "rollback_failed"}:
        raise OnboardingError(
            "onboarding_run_finished", "Completed onboarding cannot be cancelled."
        )
    plan = get_install_plan(database_path, run["plan_id"])
    adapter = adapters.get(run["adapter_kind"])
    if adapter is None:
        raise OnboardingError(
            "onboarding_adapter_missing", "The onboarding adapter is unavailable."
        )
    result = _invoke(adapter, "rollback", plan)
    effects = [
        *run["effects"],
        {"kind": "cancel", "status": "rolled_back", "result": result},
    ]
    with _connect(database_path) as connection:
        connection.execute(
            """UPDATE mcp_onboarding_runs SET state='rolled_back', completed_at=?,
                      effects_json=?, rollback_state='rolled_back' WHERE run_id=?""",
            (int(now.timestamp()), json.dumps(effects, sort_keys=True), run_id),
        )
    return get_onboarding_run(database_path, run_id)
