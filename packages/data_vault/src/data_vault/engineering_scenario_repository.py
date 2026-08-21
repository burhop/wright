"""SQLite persistence for bounded engineering scenario reports."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Mapping, Sequence

from core.engineering_scenarios import (
    AssertionResult,
    ScenarioState,
    assert_bounded_sequence,
)
from core.rivet_mcp import canonical_digest, canonical_json, reject_secret_material

from .state_store import connect_state_db


_TERMINAL = {"blocked", "passed", "failed", "cancelled", "error"}


def _epoch(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp())


def _json(value: Any) -> str:
    reject_secret_material(value)
    encoded = canonical_json(value)
    if len(encoded.encode("utf-8")) > 1024 * 1024:
        raise ValueError("Scenario report field exceeds the 1 MiB limit")
    return encoded


class EngineeringScenarioRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def create_draft(
        self,
        *,
        scenario_run_id: str,
        workflow_run_id: str,
        workspace_id: str,
        session_id: str,
        scenario_id: str,
        scenario_revision: int,
        manifest_digest: str,
        workflow_digest: str,
        binding_set_digest: str | None,
        identity: Mapping[str, Any],
        environment: Mapping[str, Any],
        created_at: datetime,
    ) -> None:
        identity_json = _json(identity)
        environment_json = _json(environment)
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            existing = connection.execute(
                "SELECT identity_json FROM engineering_scenario_runs WHERE scenario_run_id=?",
                (scenario_run_id,),
            ).fetchone()
            if existing is not None:
                if str(existing[0]) != identity_json:
                    raise ValueError("Scenario run identity is immutable")
                return
            connection.execute(
                """INSERT INTO engineering_scenario_runs
                (scenario_run_id, workflow_run_id, workspace_id, session_id,
                 scenario_id, scenario_revision, manifest_digest, workflow_digest,
                 binding_set_digest, state, identity_json, environment_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'running', ?, ?, ?)""",
                (
                    scenario_run_id,
                    workflow_run_id,
                    workspace_id,
                    session_id,
                    scenario_id,
                    scenario_revision,
                    manifest_digest,
                    workflow_digest,
                    binding_set_digest,
                    identity_json,
                    environment_json,
                    _epoch(created_at),
                ),
            )

    def finalize(
        self,
        *,
        scenario_run_id: str,
        state: ScenarioState | str,
        artifacts: Sequence[Mapping[str, Any]],
        assertions: Sequence[AssertionResult],
        cleanup_state: str,
        residue: Mapping[str, Any],
        finalized_at: datetime,
    ) -> str:
        terminal = str(state)
        if terminal not in _TERMINAL:
            raise ValueError("Scenario report requires a terminal state")
        assert_bounded_sequence(artifacts, "Artifacts")
        assert_bounded_sequence(assertions, "Assertions")
        artifact_json = _json(tuple(artifacts))
        residue_json = _json(residue)
        assertion_documents = tuple(value.canonical() for value in assertions)
        report_material = {
            "scenario_run_id": scenario_run_id,
            "state": terminal,
            "artifacts": tuple(artifacts),
            "assertions": assertion_documents,
            "cleanup_state": cleanup_state,
            "residue": residue,
        }
        report_digest = canonical_digest(report_material)
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                "SELECT state, report_digest FROM engineering_scenario_runs WHERE scenario_run_id=?",
                (scenario_run_id,),
            ).fetchone()
            if row is None:
                raise KeyError(scenario_run_id)
            if str(row["state"]) in _TERMINAL:
                if str(row["report_digest"]) != report_digest:
                    raise ValueError("Terminal scenario report is immutable")
                return report_digest
            connection.execute(
                """UPDATE engineering_scenario_runs SET state=?, artifacts_json=?,
                cleanup_state=?, residue_json=?, report_digest=?, finalized_at=?
                WHERE scenario_run_id=?""",
                (
                    terminal,
                    artifact_json,
                    cleanup_state,
                    residue_json,
                    report_digest,
                    _epoch(finalized_at),
                    scenario_run_id,
                ),
            )
            for sequence, result in enumerate(assertions, 1):
                result_json = _json(result.canonical())
                connection.execute(
                    """INSERT INTO engineering_scenario_assertions
                    (result_id, scenario_run_id, sequence, assertion_id, state,
                     result_digest, result_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"{scenario_run_id}:{sequence}",
                        scenario_run_id,
                        sequence,
                        result.assertion_id,
                        str(result.state),
                        result.digest,
                        result_json,
                        _epoch(finalized_at),
                    ),
                )
        return report_digest

    def get(self, scenario_run_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                "SELECT * FROM engineering_scenario_runs WHERE scenario_run_id=?",
                (scenario_run_id,),
            ).fetchone()
            if row is None:
                return None
            assertion_rows = connection.execute(
                """SELECT result_json FROM engineering_scenario_assertions
                WHERE scenario_run_id=? ORDER BY sequence""",
                (scenario_run_id,),
            ).fetchall()
        return {
            **dict(row),
            "identity": json.loads(row["identity_json"]),
            "artifacts": json.loads(row["artifacts_json"]),
            "environment": json.loads(row["environment_json"]),
            "residue": json.loads(row["residue_json"]),
            "assertions": tuple(json.loads(value[0]) for value in assertion_rows),
        }

    def get_by_workflow_run(self, workflow_run_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                "SELECT scenario_run_id FROM engineering_scenario_runs WHERE workflow_run_id=?",
                (workflow_run_id,),
            ).fetchone()
        return self.get(str(row[0])) if row is not None else None
