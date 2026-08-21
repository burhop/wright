"""SQLite persistence for engineering model lifecycle identity and evidence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Mapping

from core.model_observability import ModelBoundaryObserver
from core.rivet_mcp import canonical_json, reject_secret_material

from .state_store import connect_state_db

_TERMINAL_OPERATION_STATES = {"blocked", "succeeded", "failed", "cancelled"}
_DECLARATIVE_CREDENTIAL_STATES = {
    "none",
    "read_token_reference",
    "external_action",
}


def _epoch(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp() * 1000)


def _bounded_json(value: Any, *, maximum: int = 64 * 1024) -> str:
    def public_projection(item: Any) -> Any:
        if isinstance(item, Mapping):
            result: dict[str, Any] = {}
            for key, child in item.items():
                name = str(key)
                if name == "credential" and child in _DECLARATIVE_CREDENTIAL_STATES:
                    result["access_requirement_state"] = child
                elif name == "credential_reference_present" and isinstance(child, bool):
                    result["opaque_reference_present"] = child
                else:
                    result[name] = public_projection(child)
            return result
        if isinstance(item, (list, tuple)):
            return [public_projection(child) for child in item]
        return item

    reject_secret_material(public_projection(value))
    encoded = canonical_json(value)
    if len(encoded.encode("utf-8")) > maximum:
        label = "1 MiB" if maximum == 1024 * 1024 else "64 KiB"
        raise ValueError(f"Model repository record exceeds the {label} limit")
    return encoded


def _decode_row(row: Mapping[str, Any] | None, *json_fields: str):
    if row is None:
        return None
    result = dict(row)
    for field in json_fields:
        raw = result.pop(f"{field}_json", None)
        result[field] = json.loads(raw) if raw is not None else None
    return result


class ModelRepository:
    def __init__(
        self, db_path: str, *, observer: ModelBoundaryObserver | None = None
    ) -> None:
        self.db_path = db_path
        self.observer = observer or ModelBoundaryObserver()

    def save_plan(
        self,
        *,
        plan_id: str,
        principal_id: str,
        plan_digest: str,
        state: str,
        plan: Mapping[str, Any],
        created_at: datetime,
        expires_at: datetime,
        trace_id: str = "no-active-span",
    ) -> None:
        document = _bounded_json(plan)
        created = _epoch(created_at)
        expires = _epoch(expires_at)
        if expires <= created:
            raise ValueError("Plan expiry must follow creation")
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM model_install_plans WHERE plan_id=?", (plan_id,)
            ).fetchone()
            if row is not None:
                expected = (
                    principal_id,
                    plan_digest,
                    state,
                    document,
                    created,
                    expires,
                )
                actual = (
                    row["principal_id"],
                    row["plan_digest"],
                    row["state"],
                    row["plan_json"],
                    row["created_at"],
                    row["expires_at"],
                )
                if actual != expected:
                    raise ValueError("Model plan identity is immutable")
                return
            connection.execute(
                """INSERT INTO model_install_plans
                (plan_id, principal_id, plan_digest, state, plan_json, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    plan_id,
                    principal_id,
                    plan_digest,
                    state,
                    document,
                    created,
                    expires,
                ),
            )
        self.observer.record(
            "model.database.plan",
            trace_id=trace_id,
            attributes={
                "plan_id": plan_id,
                "plan_digest": plan_digest,
                "plan_state": state,
            },
        )

    def get_plan(self, plan_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                "SELECT * FROM model_install_plans WHERE plan_id=?", (plan_id,)
            ).fetchone()
        return _decode_row(row, "plan")

    def transition_plan(
        self,
        plan_id: str,
        *,
        expected_state: str,
        state: str,
        trace_id: str = "no-active-span",
    ) -> bool:
        confirmed_at = None
        if state == "confirmed":
            confirmed_at = _epoch(datetime.now(UTC))
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_install_plans SET state=?, confirmed_at=COALESCE(?, confirmed_at)
                WHERE plan_id=? AND state=?""",
                (state, confirmed_at, plan_id, expected_state),
            )
            changed = cursor.rowcount == 1
        if changed:
            self.observer.record(
                "model.database.plan",
                trace_id=trace_id,
                attributes={
                    "plan_id": plan_id,
                    "previous_state": expected_state,
                    "plan_state": state,
                },
            )
        return changed

    def create_operation(
        self,
        *,
        operation_id: str,
        plan_id: str,
        plan_digest: str,
        kind: str,
        trace_id: str,
        created_at: datetime,
    ) -> None:
        at = _epoch(created_at)
        progress = _bounded_json({})
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM model_operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if row is not None:
                if (
                    row["plan_id"],
                    row["plan_digest"],
                    row["kind"],
                    row["trace_id"],
                ) != (plan_id, plan_digest, kind, trace_id):
                    raise ValueError("Model operation identity is immutable")
                return
            connection.execute(
                """INSERT INTO model_operations
                (operation_id, plan_id, plan_digest, kind, state, phase,
                 progress_json, trace_id, cleanup_state, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'prepared', 'prepared', ?, ?, 'not_needed', ?, ?)""",
                (operation_id, plan_id, plan_digest, kind, progress, trace_id, at, at),
            )
        self.observer.record(
            "model.database.operation",
            trace_id=trace_id,
            attributes={
                "operation_id": operation_id,
                "plan_id": plan_id,
                "plan_digest": plan_digest,
                "operation_kind": kind,
                "operation_state": "prepared",
            },
        )

    def transition_operation(
        self,
        operation_id: str,
        *,
        expected_state: str,
        state: str,
        phase: str,
        progress: Mapping[str, Any],
        updated_at: datetime,
        result: Mapping[str, Any] | None = None,
        failure: Mapping[str, Any] | None = None,
        cleanup_state: str = "not_needed",
        cancellation_requested_at: datetime | None = None,
        trace_id: str = "no-active-span",
    ) -> bool:
        if expected_state in _TERMINAL_OPERATION_STATES and state != expected_state:
            raise ValueError("Terminal model operation is immutable")
        progress_json = _bounded_json(progress)
        result_json = _bounded_json(result) if result is not None else None
        failure_json = _bounded_json(failure) if failure is not None else None
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_operations
                SET state=?, phase=?, progress_json=?, result_json=?, failure_json=?,
                    cleanup_state=?, cancellation_requested_at=?, updated_at=?
                WHERE operation_id=? AND state=?""",
                (
                    state,
                    phase,
                    progress_json,
                    result_json,
                    failure_json,
                    cleanup_state,
                    _epoch(cancellation_requested_at)
                    if cancellation_requested_at
                    else None,
                    _epoch(updated_at),
                    operation_id,
                    expected_state,
                ),
            )
            changed = cursor.rowcount == 1
        if changed:
            event = (
                "model.operation.cancel"
                if state in {"cancelling", "cancelled"}
                else "model.database.operation"
            )
            self.observer.record(
                event,
                trace_id=trace_id,
                state="cancelled" if state == "cancelled" else "succeeded",
                attributes={
                    "operation_id": operation_id,
                    "previous_state": expected_state,
                    "operation_state": state,
                    "phase": phase,
                    "cleanup_state": cleanup_state,
                },
            )
        return changed

    def get_operation(self, operation_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                "SELECT * FROM model_operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
        return _decode_row(row, "progress", "result", "failure")

    def find_export_authorization(self, artifact_id: str) -> dict[str, Any] | None:
        """Resolve a bounded successful export without trusting caller-supplied paths."""

        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                """SELECT mo.result_json, mo.updated_at, mp.principal_id
                FROM model_operations mo
                JOIN model_install_plans mp ON mp.plan_id = mo.plan_id
                WHERE mo.kind='export' AND mo.state='succeeded'
                ORDER BY mo.updated_at DESC LIMIT 1000"""
            ).fetchall()
        for row in rows:
            result = json.loads(row["result_json"]) if row["result_json"] else {}
            if result.get("artifact_id") == artifact_id:
                return {
                    "principal_id": row["principal_id"],
                    "updated_at": row["updated_at"],
                }
        return None

    def record_content_object(
        self,
        *,
        content_digest: str,
        size: int,
        state: str,
        storage_key: str,
        verification: Mapping[str, Any],
        observed_at: datetime,
    ) -> None:
        document = _bounded_json(verification)
        at = _epoch(observed_at)
        verified_at = at if state == "verified" else None
        with connect_state_db(self.db_path) as connection:
            row = connection.execute(
                "SELECT size, storage_key FROM model_content_objects WHERE content_digest=?",
                (content_digest,),
            ).fetchone()
            if row is not None and (row["size"], row["storage_key"]) != (
                size,
                storage_key,
            ):
                raise ValueError("Content object identity is immutable")
            connection.execute(
                """INSERT INTO model_content_objects
                (content_digest, size, state, storage_key, verification_json,
                 verified_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_digest) DO UPDATE SET
                    state=excluded.state,
                    verification_json=excluded.verification_json,
                    verified_at=COALESCE(excluded.verified_at, model_content_objects.verified_at),
                    updated_at=excluded.updated_at""",
                (
                    content_digest,
                    size,
                    state,
                    storage_key,
                    document,
                    verified_at,
                    at,
                ),
            )

    def save_installation(
        self,
        *,
        installation_id: str,
        model_id: str,
        package_revision: int,
        variant_id: str,
        manifest_digest: str,
        installation_digest: str,
        runtime_adapter_id: str,
        runtime_adapter_version: str,
        state: str,
        active: bool | None,
        installed_at: datetime,
        predecessor_id: str | None = None,
        package: Mapping[str, Any] | None = None,
    ) -> None:
        at = _epoch(installed_at)
        package_json = _bounded_json(package) if package is not None else None
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM model_installations WHERE installation_id=?",
                (installation_id,),
            ).fetchone()
            identity = (
                model_id,
                package_revision,
                variant_id,
                manifest_digest,
                installation_digest,
                runtime_adapter_id,
                runtime_adapter_version,
            )
            if row is not None:
                actual = tuple(
                    row[key]
                    for key in (
                        "model_id",
                        "package_revision",
                        "variant_id",
                        "manifest_digest",
                        "installation_digest",
                        "runtime_adapter_id",
                        "runtime_adapter_version",
                    )
                )
                if actual != identity:
                    raise ValueError("Model installation identity is immutable")
                return
            effective_active = active
            if effective_active is None:
                effective_active = (
                    connection.execute(
                        "SELECT 1 FROM model_installations WHERE model_id=? AND active_revision=1",
                        (model_id,),
                    ).fetchone()
                    is None
                )
            if effective_active:
                connection.execute(
                    "UPDATE model_installations SET active_revision=0 WHERE model_id=?",
                    (model_id,),
                )
            connection.execute(
                """INSERT INTO model_installations
                (installation_id, model_id, package_revision, variant_id,
                 manifest_digest, package_json, installation_digest, state, runtime_adapter_id,
                 runtime_adapter_version, active_revision, predecessor_id, installed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    installation_id,
                    model_id,
                    package_revision,
                    variant_id,
                    manifest_digest,
                    package_json,
                    installation_digest,
                    state,
                    runtime_adapter_id,
                    runtime_adapter_version,
                    int(effective_active),
                    predecessor_id,
                    at,
                ),
            )

    def get_installation(self, installation_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                "SELECT * FROM model_installations WHERE installation_id=?",
                (installation_id,),
            ).fetchone()
        return _decode_row(row, "package")

    def list_installations(self) -> tuple[dict[str, Any], ...]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                "SELECT * FROM model_installations ORDER BY model_id, installed_at"
            ).fetchall()
        return tuple(_decode_row(row, "package") for row in rows)

    def activate_installation(
        self,
        installation_id: str,
        *,
        predecessor_id: str,
        observed_at: datetime,
    ) -> bool:
        """Atomically switch one tested successor into the active slot."""

        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            target = connection.execute(
                "SELECT model_id, state FROM model_installations WHERE installation_id=?",
                (installation_id,),
            ).fetchone()
            predecessor = connection.execute(
                "SELECT model_id, active_revision FROM model_installations WHERE installation_id=?",
                (predecessor_id,),
            ).fetchone()
            if (
                target is None
                or predecessor is None
                or target["model_id"] != predecessor["model_id"]
                or target["state"] != "ready"
                or not predecessor["active_revision"]
            ):
                return False
            connection.execute(
                "UPDATE model_installations SET active_revision=0 WHERE model_id=?",
                (target["model_id"],),
            )
            cursor = connection.execute(
                """UPDATE model_installations
                SET active_revision=1, predecessor_id=?, last_verified_at=COALESCE(last_verified_at, ?)
                WHERE installation_id=? AND state='ready'""",
                (predecessor_id, _epoch(observed_at), installation_id),
            )
            connection.execute(
                """UPDATE model_capability_bindings SET state='stale', updated_at=?
                WHERE installation_id=? AND state='enabled'""",
                (_epoch(observed_at), predecessor_id),
            )
            return cursor.rowcount == 1

    def prepare_installation_retest(
        self, installation_id: str, *, observed_at: datetime
    ) -> bool:
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_installations
                SET state='installed', standard_test_evidence_id=NULL, active_revision=0,
                    last_verified_at=?
                WHERE installation_id=? AND active_revision=0
                  AND state IN ('ready', 'disabled', 'unhealthy')""",
                (_epoch(observed_at), installation_id),
            )
            return cursor.rowcount == 1

    def set_installation_lifecycle_state(
        self,
        installation_id: str,
        *,
        expected_states: tuple[str, ...],
        state: str,
        active: bool,
        observed_at: datetime,
    ) -> bool:
        if not expected_states:
            raise ValueError("Expected installation states are required")
        placeholders = ",".join("?" for _ in expected_states)
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                f"""UPDATE model_installations
                SET state=?, active_revision=?, last_verified_at=?
                WHERE installation_id=? AND state IN ({placeholders})""",  # noqa: S608
                (
                    state,
                    int(active),
                    _epoch(observed_at),
                    installation_id,
                    *expected_states,
                ),
            )
            if cursor.rowcount == 1 and state in {"disabled", "uninstalled"}:
                connection.execute(
                    """UPDATE model_capability_bindings SET state='disabled', updated_at=?
                    WHERE installation_id=? AND state='enabled'""",
                    (_epoch(observed_at), installation_id),
                )
            return cursor.rowcount == 1

    def mark_installation_tested(
        self,
        installation_id: str,
        *,
        expected_state: str,
        state: str,
        adapter_version: str,
        evidence_id: str | None,
        observed_at: datetime,
    ) -> bool:
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_installations
                SET state=?, runtime_adapter_version=?, standard_test_evidence_id=?,
                    last_verified_at=?
                WHERE installation_id=? AND state=?""",
                (
                    state,
                    adapter_version,
                    evidence_id,
                    _epoch(observed_at),
                    installation_id,
                    expected_state,
                ),
            )
            return cursor.rowcount == 1

    def installation_artifacts(
        self, installation_id: str
    ) -> tuple[dict[str, Any], ...]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                """SELECT * FROM model_installation_artifacts
                WHERE installation_id=? ORDER BY artifact_path""",
                (installation_id,),
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def record_installation_artifacts(
        self,
        installation_id: str,
        artifacts: Mapping[str, str],
        *,
        created_at: datetime,
    ) -> None:
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for path, digest in sorted(artifacts.items()):
                row = connection.execute(
                    """SELECT content_digest FROM model_installation_artifacts
                    WHERE installation_id=? AND artifact_path=?""",
                    (installation_id, path),
                ).fetchone()
                if row is not None:
                    if row["content_digest"] != digest:
                        raise ValueError(
                            "Model installation artifact identity is immutable"
                        )
                    continue
                connection.execute(
                    """INSERT INTO model_installation_artifacts
                    (installation_id, artifact_path, content_digest, created_at)
                    VALUES (?, ?, ?, ?)""",
                    (installation_id, path, digest, _epoch(created_at)),
                )

    def bind_workspace(
        self,
        *,
        binding_id: str,
        workspace_id: str,
        installation_id: str,
        task_id: str,
        tool_name: str,
        binding_digest: str,
        policy_snapshot_digest: str,
        state: str,
        created_at: datetime,
    ) -> None:
        at = _epoch(created_at)
        with connect_state_db(self.db_path) as connection:
            connection.execute(
                """INSERT INTO model_capability_bindings
                (binding_id, workspace_id, installation_id, task_id, tool_name,
                 binding_digest, policy_snapshot_digest, state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    binding_id,
                    workspace_id,
                    installation_id,
                    task_id,
                    tool_name,
                    binding_digest,
                    policy_snapshot_digest,
                    state,
                    at,
                    at,
                ),
            )

    def get_binding(self, binding_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                "SELECT * FROM model_capability_bindings WHERE binding_id=?",
                (binding_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def get_binding_by_digest(self, binding_digest: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                "SELECT * FROM model_capability_bindings WHERE binding_digest=?",
                (binding_digest,),
            ).fetchone()
        return dict(row) if row is not None else None

    def set_binding_state(
        self,
        binding_id: str,
        *,
        expected_state: str,
        state: str,
        observed_at: datetime,
    ) -> bool:
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_capability_bindings SET state=?, updated_at=?
                WHERE binding_id=? AND state=?""",
                (state, _epoch(observed_at), binding_id, expected_state),
            )
            return cursor.rowcount == 1

    def list_bindings(self, workspace_id: str) -> tuple[dict[str, Any], ...]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                """SELECT * FROM model_capability_bindings
                WHERE workspace_id=? ORDER BY tool_name""",
                (workspace_id,),
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def add_reference(
        self,
        *,
        reference_id: str,
        content_digest: str | None,
        installation_id: str | None,
        kind: str,
        owner_id: str,
        created_at: datetime,
        access_scope: str | None = None,
    ) -> None:
        with connect_state_db(self.db_path) as connection:
            row = connection.execute(
                "SELECT * FROM model_references WHERE reference_id=?",
                (reference_id,),
            ).fetchone()
            identity = (
                content_digest,
                installation_id,
                kind,
                owner_id,
                access_scope,
            )
            if row is not None:
                actual = tuple(
                    row[key]
                    for key in (
                        "content_digest",
                        "installation_id",
                        "kind",
                        "owner_id",
                        "access_scope",
                    )
                )
                if actual != identity:
                    raise ValueError("Model reference identity is immutable")
                return
            connection.execute(
                """INSERT INTO model_references
                (reference_id, content_digest, installation_id, kind, owner_id,
                 state, access_scope, created_at)
                VALUES (?, ?, ?, ?, ?, 'active', ?, ?)""",
                (
                    reference_id,
                    content_digest,
                    installation_id,
                    kind,
                    owner_id,
                    access_scope,
                    _epoch(created_at),
                ),
            )

    def detach_reference(self, reference_id: str, *, detached_at: datetime) -> bool:
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_references SET state='detached', detached_at=?
                WHERE reference_id=? AND state='active'""",
                (_epoch(detached_at), reference_id),
            )
            return cursor.rowcount == 1

    def set_reference_state(
        self, reference_id: str, *, state: str, observed_at: datetime
    ) -> dict[str, Any] | None:
        if state not in {"detached", "archived"}:
            raise ValueError("Reference state is invalid")
        with connect_state_db(self.db_path) as connection:
            connection.execute(
                """UPDATE model_references SET state=?, detached_at=?
                WHERE reference_id=? AND state='active'""",
                (state, _epoch(observed_at), reference_id),
            )
            row = connection.execute(
                "SELECT * FROM model_references WHERE reference_id=?",
                (reference_id,),
            ).fetchone()
        return dict(row) if row is not None else None

    def list_references(self, installation_id: str) -> tuple[dict[str, Any], ...]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                """SELECT * FROM model_references
                WHERE installation_id=? ORDER BY state, kind, owner_id, reference_id""",
                (installation_id,),
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def removal_snapshot(
        self, installation_id: str, *, at: datetime
    ) -> dict[str, Any] | None:
        """Return an exact, transactionally observed purge preview."""

        observed = _epoch(at)
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            installation = connection.execute(
                "SELECT * FROM model_installations WHERE installation_id=?",
                (installation_id,),
            ).fetchone()
            if installation is None:
                return None
            connection.execute(
                """UPDATE model_leases SET state='expired'
                WHERE state='active' AND expires_at<=?""",
                (observed,),
            )
            artifacts = connection.execute(
                """SELECT ia.artifact_path, ia.content_digest, co.size, co.state
                FROM model_installation_artifacts ia
                JOIN model_content_objects co ON co.content_digest=ia.content_digest
                WHERE ia.installation_id=? ORDER BY ia.artifact_path""",
                (installation_id,),
            ).fetchall()
            digests = tuple(sorted({str(row["content_digest"]) for row in artifacts}))
            references = connection.execute(
                """SELECT * FROM model_references
                WHERE installation_id=? ORDER BY state, kind, owner_id, reference_id""",
                (installation_id,),
            ).fetchall()
            blockers: list[dict[str, Any]] = []
            active_installation_refs = [
                row for row in references if row["state"] == "active"
            ]
            for row in active_installation_refs:
                blockers.append(
                    {
                        "kind": row["kind"],
                        "owner_id": row["owner_id"],
                        "reference_id": row["reference_id"],
                        "content_digest": row["content_digest"],
                    }
                )
            blocked_digests: set[str] = {
                str(row["content_digest"])
                for row in active_installation_refs
                if row["content_digest"]
            }
            for digest in digests:
                rows = connection.execute(
                    """SELECT kind, owner_id, reference_id FROM model_references
                    WHERE content_digest=? AND state='active' AND installation_id IS NULL""",
                    (digest,),
                ).fetchall()
                for row in rows:
                    blockers.append(
                        {
                            "kind": row["kind"],
                            "owner_id": row["owner_id"],
                            "reference_id": row["reference_id"],
                            "content_digest": digest,
                        }
                    )
                    blocked_digests.add(digest)
                leases = connection.execute(
                    """SELECT lease_id, owner_id FROM model_leases
                    WHERE content_digest=? AND state='active' AND expires_at>?""",
                    (digest, observed),
                ).fetchall()
                for lease in leases:
                    blockers.append(
                        {
                            "kind": "lease",
                            "owner_id": lease["owner_id"],
                            "lease_id": lease["lease_id"],
                            "content_digest": digest,
                        }
                    )
                    blocked_digests.add(digest)
                other = connection.execute(
                    """SELECT mi.installation_id FROM model_installation_artifacts ia
                    JOIN model_installations mi ON mi.installation_id=ia.installation_id
                    WHERE ia.content_digest=? AND ia.installation_id<>?
                      AND mi.state NOT IN ('uninstalled', 'missing')""",
                    (digest, installation_id),
                ).fetchall()
                for row in other:
                    blockers.append(
                        {
                            "kind": "package",
                            "owner_id": row["installation_id"],
                            "content_digest": digest,
                        }
                    )
                    blocked_digests.add(digest)
            if active_installation_refs:
                blocked_digests.update(digests)
            sizes = {str(row["content_digest"]): int(row["size"]) for row in artifacts}
            reclaimable = sum(
                sizes[digest]
                for digest in digests
                if digest not in blocked_digests
                and any(
                    row["content_digest"] == digest and row["state"] == "verified"
                    for row in artifacts
                )
            )
        return {
            "installation": dict(installation),
            "artifacts": [dict(row) for row in artifacts],
            "references": [dict(row) for row in references],
            "blockers": sorted(
                blockers,
                key=lambda item: (
                    str(item.get("kind")),
                    str(item.get("owner_id")),
                    str(item.get("reference_id", item.get("lease_id", ""))),
                ),
            ),
            "reclaimable_bytes": reclaimable,
        }

    def mark_content_missing(
        self, content_digest: str, *, observed_at: datetime
    ) -> bool:
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_content_objects SET state='missing', updated_at=?
                WHERE content_digest=? AND state='verified'""",
                (_epoch(observed_at), content_digest),
            )
            return cursor.rowcount == 1

    def acquire_lease(
        self,
        *,
        lease_id: str,
        content_digest: str,
        owner_id: str,
        expires_at: datetime,
        observed_at: datetime,
    ) -> None:
        at = _epoch(observed_at)
        with connect_state_db(self.db_path) as connection:
            connection.execute(
                """INSERT INTO model_leases
                (lease_id, content_digest, owner_id, state, expires_at,
                 heartbeat_at, created_at)
                VALUES (?, ?, ?, 'active', ?, ?, ?)""",
                (lease_id, content_digest, owner_id, _epoch(expires_at), at, at),
            )

    def release_lease(self, lease_id: str) -> bool:
        at = _epoch(datetime.now(UTC))
        with connect_state_db(self.db_path) as connection:
            cursor = connection.execute(
                """UPDATE model_leases SET state='released', released_at=?
                WHERE lease_id=? AND state='active'""",
                (at, lease_id),
            )
            return cursor.rowcount == 1

    def content_hold_count(self, content_digest: str, *, at: datetime) -> int:
        observed = _epoch(at)
        with connect_state_db(self.db_path) as connection:
            connection.execute(
                """UPDATE model_leases SET state='expired'
                WHERE state='active' AND expires_at<=?""",
                (observed,),
            )
            refs = connection.execute(
                """SELECT COUNT(*) FROM model_references
                WHERE content_digest=? AND state='active'""",
                (content_digest,),
            ).fetchone()[0]
            leases = connection.execute(
                """SELECT COUNT(*) FROM model_leases
                WHERE content_digest=? AND state='active' AND expires_at>?""",
                (content_digest, observed),
            ).fetchone()[0]
        return int(refs) + int(leases)

    def record_test_evidence(
        self,
        *,
        evidence_id: str,
        installation_id: str,
        vector_id: str,
        material_digest: str,
        observation_digest: str,
        state: str,
        evidence: Mapping[str, Any],
        created_at: datetime,
        trace_id: str = "no-active-span",
    ) -> None:
        document = _bounded_json(evidence, maximum=1024 * 1024)
        with connect_state_db(self.db_path) as connection:
            connection.execute(
                """INSERT INTO model_test_evidence
                (evidence_id, installation_id, vector_id, material_digest,
                 observation_digest, state, evidence_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evidence_id,
                    installation_id,
                    vector_id,
                    material_digest,
                    observation_digest,
                    state,
                    document,
                    _epoch(created_at),
                ),
            )
        self.observer.record(
            "model.evidence.record",
            trace_id=trace_id,
            state="succeeded" if state == "passed" else "failed",
            attributes={
                "evidence_id": evidence_id,
                "installation_id": installation_id,
                "vector_id": vector_id,
                "material_digest": material_digest,
                "observation_digest": observation_digest,
                "evidence_state": state,
            },
        )

    def list_test_evidence(self, installation_id: str) -> tuple[dict[str, Any], ...]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                """SELECT * FROM model_test_evidence
                WHERE installation_id=? ORDER BY created_at, evidence_id""",
                (installation_id,),
            ).fetchall()
        return tuple(_decode_row(row, "evidence") for row in rows)


__all__ = ["ModelRepository"]
