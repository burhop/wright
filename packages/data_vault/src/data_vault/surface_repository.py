"""Scoped SQLite repository for Workspace Surface descriptors."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from opentelemetry import trace

from core.surfaces.models import (
    generation_provenance_from_dict,
    generation_provenance_to_dict,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
    surface_source_from_dict,
    surface_source_to_dict,
)
from core.surfaces.errors import SurfaceOptimisticLockError
from core.surfaces.telemetry import (
    SurfaceDiagnosticEvent,
    SurfaceSeverity,
    TraceCorrelation,
)
from core.telemetry import current_trace_fields

from .state_store import connect_state_db


class SurfaceRevisionConflict(SurfaceOptimisticLockError):
    """The persisted descriptor no longer has the expected revision."""


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _optional_json(value: Any) -> str | None:
    return None if value is None else _json(value)


def _descriptor_from_row(row) -> SurfaceDescriptor:
    return SurfaceDescriptor(
        schema_version=int(row["schema_version"]),
        surface_id=SurfaceId(row["surface_id"]),
        workspace_id=row["workspace_id"],
        source=surface_source_from_dict(json.loads(row["source_json"])),
        title=row["title"],
        lifecycle=SurfaceLifecycle(row["lifecycle"]),
        revision=SurfaceRevision(int(row["revision"])),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        instance=json.loads(row["instance_json"]) if row["instance_json"] else None,
        presentations=tuple(json.loads(row["presentations_json"])),
        capabilities=tuple(json.loads(row["capabilities_json"])),
        diagnostic_summary=(
            json.loads(row["diagnostic_summary_json"])
            if row["diagnostic_summary_json"]
            else None
        ),
        generation_provenance=(
            generation_provenance_from_dict(
                json.loads(row["generation_provenance_json"])
            )
            if row["generation_provenance_json"]
            else None
        ),
    )


class _SurfaceRepositoryBase:
    def __init__(self, db_path: str | Path, *, tracer=None) -> None:
        self.db_path = str(db_path)
        self.tracer = tracer or trace.get_tracer(__name__)

    def _attributes(self, workspace_id: str) -> dict[str, str]:
        return {"wright.workspace_id": workspace_id}

    def _outbox(
        self,
        connection,
        descriptor: SurfaceDescriptor,
        event_type: str,
    ) -> None:
        trace_id = current_trace_fields().get("trace_id", "no-active-span")
        connection.execute(
            """INSERT INTO surface_outbox (
                event_id, workspace_id, aggregate_id, aggregate_revision,
                event_type, payload_json, trace_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(uuid.uuid4()),
                descriptor.workspace_id,
                str(descriptor.surface_id),
                int(descriptor.revision),
                event_type,
                _json(
                    {
                        "surface_id": str(descriptor.surface_id),
                        "workspace_id": descriptor.workspace_id,
                        "lifecycle": descriptor.lifecycle.value,
                        "revision": int(descriptor.revision),
                    }
                ),
                trace_id,
                descriptor.updated_at.isoformat(),
            ),
        )

    def create(
        self,
        descriptor: SurfaceDescriptor,
        *,
        user_id: str,
        session_id: str,
        idempotency_key: str | None = None,
    ) -> SurfaceDescriptor:
        with self.tracer.start_as_current_span(
            "surface.sqlite.create",
            attributes=self._attributes(descriptor.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                if idempotency_key:
                    existing = connection.execute(
                        """SELECT * FROM workspace_surfaces
                        WHERE user_id=? AND workspace_id=? AND session_id=?
                          AND idempotency_key=?""",
                        (
                            user_id,
                            descriptor.workspace_id,
                            session_id,
                            idempotency_key,
                        ),
                    ).fetchone()
                    if existing is not None:
                        if existing["surface_id"] != str(descriptor.surface_id):
                            raise ValueError(
                                "idempotency key is already bound to another surface"
                            )
                        return _descriptor_from_row(existing)
                source = surface_source_to_dict(descriptor.source)
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        """INSERT INTO workspace_surfaces (
                            surface_id, workspace_id, user_id, session_id,
                            schema_version, source_kind, source_id, source_version,
                            source_json, title, lifecycle, instance_json,
                            presentations_json, capabilities_json,
                            diagnostic_summary_json, generation_provenance_json,
                            revision, idempotency_key, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            str(descriptor.surface_id),
                            descriptor.workspace_id,
                            user_id,
                            session_id,
                            descriptor.schema_version,
                            descriptor.source.kind.value,
                            descriptor.source.source_id,
                            descriptor.source.source_version,
                            _json(source),
                            descriptor.title,
                            descriptor.lifecycle.value,
                            _optional_json(descriptor.instance),
                            _json(descriptor.presentations),
                            _json(descriptor.capabilities),
                            _optional_json(descriptor.diagnostic_summary),
                            _optional_json(
                                generation_provenance_to_dict(
                                    descriptor.generation_provenance
                                )
                                if descriptor.generation_provenance
                                else None
                            ),
                            int(descriptor.revision),
                            idempotency_key,
                            descriptor.created_at.isoformat(),
                            descriptor.updated_at.isoformat(),
                        ),
                    )
                    self._outbox(connection, descriptor, "surface.declared")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
        return descriptor


@dataclass(frozen=True, slots=True)
class PresentationPreferenceRecord:
    user_id: str
    workspace_id: str
    source_id: str
    source_version: str
    preferred_kind: str
    revision: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class SurfaceRuntimeRecord:
    runtime_id: str
    instance_id: str
    surface_id: str
    workspace_id: str
    generation: int
    ownership: str
    platform: str
    state: str
    manifest_hash: str | None
    lifetime: dict[str, Any]
    limits: dict[str, Any]
    revision: int
    created_at: datetime
    updated_at: datetime
    process_identity: dict[str, Any] | None = None
    target_pin: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SurfaceGrantRecord:
    grant_id: str
    user_id: str
    workspace_id: str
    source_id: str
    source_version: str
    instance_id: str | None
    capability: str
    operation: str
    constraints: dict[str, Any]
    risk_tier: str
    persistence: str
    decision: str
    decision_source: str
    expires_at: datetime | None
    created_at: datetime
    revoked_at: datetime | None = None
    used_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GenerationProvenanceReference:
    artifact_id: str
    workspace_id: str
    mode: str
    prompt_vault_digest: str | None
    no_prompt: bool
    constraints_vault_digest: str
    script_vault_digest: str
    script_content_hash: str
    script_revision: int
    task_id: str
    execution_id: str
    trace_id: str
    created_at: datetime


class _ScopedRepository:
    def __init__(self, db_path: str | Path, *, tracer=None) -> None:
        self.db_path = str(db_path)
        self.tracer = tracer or trace.get_tracer(__name__)

    @staticmethod
    def _attributes(workspace_id: str) -> dict[str, str]:
        return {"wright.workspace_id": workspace_id}


def _preference_from_row(row) -> PresentationPreferenceRecord:
    return PresentationPreferenceRecord(
        user_id=row["user_id"],
        workspace_id=row["workspace_id"],
        source_id=row["source_id"],
        source_version=row["source_version"],
        preferred_kind=row["preferred_kind"],
        revision=int(row["revision"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


class SurfacePreferenceRepository(_ScopedRepository):
    def get(
        self, *, user_id: str, workspace_id: str, source_id: str
    ) -> PresentationPreferenceRecord | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.preference.get",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT * FROM surface_preferences
                    WHERE user_id=? AND workspace_id=? AND source_id=?""",
                    (user_id, workspace_id, source_id),
                ).fetchone()
        return _preference_from_row(row) if row is not None else None

    def compare_and_set(
        self,
        record: PresentationPreferenceRecord,
        *,
        expected_revision: int | None,
    ) -> PresentationPreferenceRecord:
        with self.tracer.start_as_current_span(
            "surface.sqlite.preference.compare_and_set",
            attributes=self._attributes(record.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    if expected_revision is None:
                        if record.revision != 1:
                            raise ValueError("new preference revision must be 1")
                        try:
                            connection.execute(
                                """INSERT INTO surface_preferences (
                                    user_id, workspace_id, source_id, source_version,
                                    preferred_kind, revision, created_at, updated_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (
                                    record.user_id,
                                    record.workspace_id,
                                    record.source_id,
                                    record.source_version,
                                    record.preferred_kind,
                                    record.revision,
                                    record.created_at.isoformat(),
                                    record.updated_at.isoformat(),
                                ),
                            )
                        except Exception as error:
                            if error.__class__.__name__ == "IntegrityError":
                                raise SurfaceRevisionConflict(
                                    "preference already exists"
                                ) from error
                            raise
                    else:
                        current = connection.execute(
                            """SELECT revision FROM surface_preferences
                            WHERE user_id=? AND workspace_id=? AND source_id=?""",
                            (
                                record.user_id,
                                record.workspace_id,
                                record.source_id,
                            ),
                        ).fetchone()
                        if current is None:
                            raise KeyError(record.source_id)
                        if int(current["revision"]) != expected_revision:
                            raise SurfaceRevisionConflict(
                                f"expected preference revision {expected_revision}, "
                                f"current revision is {int(current['revision'])}"
                            )
                        if record.revision != expected_revision + 1:
                            raise ValueError(
                                "preference revision must increment exactly once"
                            )
                        cursor = connection.execute(
                            """UPDATE surface_preferences SET
                                source_version=?, preferred_kind=?, revision=?,
                                updated_at=?
                            WHERE user_id=? AND workspace_id=? AND source_id=?
                              AND revision=?""",
                            (
                                record.source_version,
                                record.preferred_kind,
                                record.revision,
                                record.updated_at.isoformat(),
                                record.user_id,
                                record.workspace_id,
                                record.source_id,
                                expected_revision,
                            ),
                        )
                        if cursor.rowcount != 1:
                            raise SurfaceRevisionConflict(
                                f"expected preference revision {expected_revision}"
                            )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
        return record


class SurfaceRepository(_SurfaceRepositoryBase):
    def get(
        self,
        surface_id: SurfaceId,
        *,
        workspace_id: str,
        user_id: str,
        session_id: str,
    ) -> SurfaceDescriptor | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.get", attributes=self._attributes(workspace_id)
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT * FROM workspace_surfaces
                    WHERE surface_id=? AND workspace_id=? AND user_id=? AND session_id=?""",
                    (str(surface_id), workspace_id, user_id, session_id),
                ).fetchone()
        return _descriptor_from_row(row) if row is not None else None

    def get_by_idempotency(
        self,
        *,
        workspace_id: str,
        user_id: str,
        session_id: str,
        idempotency_key: str,
    ) -> SurfaceDescriptor | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.get_by_idempotency",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT * FROM workspace_surfaces
                    WHERE workspace_id=? AND user_id=? AND session_id=?
                      AND idempotency_key=?""",
                    (workspace_id, user_id, session_id, idempotency_key),
                ).fetchone()
        return _descriptor_from_row(row) if row is not None else None

    def list(
        self, *, workspace_id: str, user_id: str, session_id: str
    ) -> list[SurfaceDescriptor]:
        with self.tracer.start_as_current_span(
            "surface.sqlite.list", attributes=self._attributes(workspace_id)
        ):
            with connect_state_db(self.db_path) as connection:
                rows = connection.execute(
                    """SELECT * FROM workspace_surfaces
                    WHERE workspace_id=? AND user_id=? AND session_id=?
                    ORDER BY created_at, surface_id""",
                    (workspace_id, user_id, session_id),
                ).fetchall()
        return [_descriptor_from_row(row) for row in rows]

    def compare_and_set(
        self,
        descriptor: SurfaceDescriptor,
        *,
        expected_revision: SurfaceRevision,
        user_id: str,
        session_id: str,
    ) -> SurfaceDescriptor:
        with self.tracer.start_as_current_span(
            "surface.sqlite.compare_and_set",
            attributes=self._attributes(descriptor.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    cursor = connection.execute(
                        """UPDATE workspace_surfaces SET
                            lifecycle=?, instance_json=?, presentations_json=?,
                            capabilities_json=?, diagnostic_summary_json=?,
                            generation_provenance_json=?, revision=?, updated_at=?
                        WHERE surface_id=? AND workspace_id=? AND user_id=?
                          AND session_id=? AND revision=?""",
                        (
                            descriptor.lifecycle.value,
                            _optional_json(descriptor.instance),
                            _json(descriptor.presentations),
                            _json(descriptor.capabilities),
                            _optional_json(descriptor.diagnostic_summary),
                            _optional_json(
                                generation_provenance_to_dict(
                                    descriptor.generation_provenance
                                )
                                if descriptor.generation_provenance
                                else None
                            ),
                            int(descriptor.revision),
                            descriptor.updated_at.isoformat(),
                            str(descriptor.surface_id),
                            descriptor.workspace_id,
                            user_id,
                            session_id,
                            int(expected_revision),
                        ),
                    )
                    if cursor.rowcount != 1:
                        current = connection.execute(
                            """SELECT revision FROM workspace_surfaces
                            WHERE surface_id=? AND workspace_id=? AND user_id=?
                              AND session_id=?""",
                            (
                                str(descriptor.surface_id),
                                descriptor.workspace_id,
                                user_id,
                                session_id,
                            ),
                        ).fetchone()
                        if current is None:
                            raise KeyError(str(descriptor.surface_id))
                        raise SurfaceRevisionConflict(
                            f"expected revision {int(expected_revision)}, "
                            f"current revision is {int(current['revision'])}"
                        )
                    self._outbox(connection, descriptor, "surface.updated")
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
        return descriptor


def _runtime_from_row(row) -> SurfaceRuntimeRecord:
    return SurfaceRuntimeRecord(
        runtime_id=row["runtime_id"],
        instance_id=row["instance_id"],
        surface_id=row["surface_id"],
        workspace_id=row["workspace_id"],
        generation=int(row["generation"]),
        ownership=row["ownership"],
        platform=row["platform"],
        state=row["state"],
        manifest_hash=row["manifest_hash"],
        lifetime=json.loads(row["lifetime_json"]),
        limits=json.loads(row["limits_json"]),
        revision=int(row["revision"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        process_identity=(
            json.loads(row["process_identity_json"])
            if row["process_identity_json"]
            else None
        ),
        target_pin=(
            json.loads(row["target_pin_json"]) if row["target_pin_json"] else None
        ),
    )


class _SurfaceRuntimeRepositoryBase(_ScopedRepository):
    def create(
        self, record: SurfaceRuntimeRecord, *, user_id: str, session_id: str
    ) -> SurfaceRuntimeRecord:
        if record.revision != 1:
            raise ValueError("new runtime revision must be 1")
        with self.tracer.start_as_current_span(
            "surface.sqlite.runtime.create",
            attributes=self._attributes(record.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    """INSERT INTO surface_runtimes (
                        runtime_id, instance_id, surface_id, workspace_id,
                        generation, ownership, platform, state,
                        process_identity_json, manifest_hash, lifetime_json,
                        limits_json, target_pin_json, revision, created_at, updated_at
                    ) SELECT ?, ?, surface_id, workspace_id, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    FROM workspace_surfaces
                    WHERE surface_id=? AND workspace_id=? AND user_id=? AND session_id=?""",
                    (
                        record.runtime_id,
                        record.instance_id,
                        record.generation,
                        record.ownership,
                        record.platform,
                        record.state,
                        _optional_json(record.process_identity),
                        record.manifest_hash,
                        _json(record.lifetime),
                        _json(record.limits),
                        _optional_json(record.target_pin),
                        record.revision,
                        record.created_at.isoformat(),
                        record.updated_at.isoformat(),
                        record.surface_id,
                        record.workspace_id,
                        user_id,
                        session_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise KeyError(record.surface_id)
                connection.commit()
        return record


def _grant_from_row(row) -> SurfaceGrantRecord:
    return SurfaceGrantRecord(
        grant_id=row["grant_id"],
        user_id=row["user_id"],
        workspace_id=row["workspace_id"],
        source_id=row["source_id"],
        source_version=row["source_version"],
        instance_id=row["instance_id"],
        capability=row["capability"],
        operation=row["operation"],
        constraints=json.loads(row["constraints_json"]),
        risk_tier=row["risk_tier"],
        persistence=row["persistence"],
        decision=row["decision"],
        decision_source=row["decision_source"],
        expires_at=(
            datetime.fromisoformat(row["expires_at"]) if row["expires_at"] else None
        ),
        created_at=datetime.fromisoformat(row["created_at"]),
        revoked_at=(
            datetime.fromisoformat(row["revoked_at"]) if row["revoked_at"] else None
        ),
        used_at=(datetime.fromisoformat(row["used_at"]) if row["used_at"] else None),
    )


class SurfaceGrantRepository(_ScopedRepository):
    def create(self, record: SurfaceGrantRecord) -> SurfaceGrantRecord:
        with self.tracer.start_as_current_span(
            "surface.sqlite.grant.create",
            attributes=self._attributes(record.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                connection.execute(
                    """INSERT INTO surface_capability_grants (
                        grant_id, user_id, workspace_id, source_id, source_version,
                        instance_id, capability, operation, constraints_json,
                        risk_tier, persistence, decision, decision_source,
                        expires_at, revoked_at, used_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.grant_id,
                        record.user_id,
                        record.workspace_id,
                        record.source_id,
                        record.source_version,
                        record.instance_id,
                        record.capability,
                        record.operation,
                        _json(record.constraints),
                        record.risk_tier,
                        record.persistence,
                        record.decision,
                        record.decision_source,
                        record.expires_at.isoformat() if record.expires_at else None,
                        record.revoked_at.isoformat() if record.revoked_at else None,
                        record.used_at.isoformat() if record.used_at else None,
                        record.created_at.isoformat(),
                    ),
                )
                connection.commit()
        return record

    def list(
        self,
        *,
        user_id: str,
        workspace_id: str,
        source_id: str,
        source_version: str,
    ) -> list[SurfaceGrantRecord]:
        with self.tracer.start_as_current_span(
            "surface.sqlite.grant.list",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                rows = connection.execute(
                    """SELECT * FROM surface_capability_grants
                    WHERE user_id=? AND workspace_id=? AND source_id=?
                      AND source_version=?
                    ORDER BY created_at, grant_id""",
                    (user_id, workspace_id, source_id, source_version),
                ).fetchall()
        return [_grant_from_row(row) for row in rows]


def _provenance_from_row(row) -> GenerationProvenanceReference:
    return GenerationProvenanceReference(
        artifact_id=row["artifact_id"],
        workspace_id=row["workspace_id"],
        mode=row["mode"],
        prompt_vault_digest=row["prompt_vault_digest"],
        no_prompt=bool(row["no_prompt"]),
        constraints_vault_digest=row["constraints_vault_digest"],
        script_vault_digest=row["script_vault_digest"],
        script_content_hash=row["script_content_hash"],
        script_revision=int(row["script_revision"]),
        task_id=row["task_id"],
        execution_id=row["execution_id"],
        trace_id=row["trace_id"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class GenerationProvenanceRepository(_ScopedRepository):
    def create(
        self, record: GenerationProvenanceReference, *, user_id: str
    ) -> GenerationProvenanceReference:
        with self.tracer.start_as_current_span(
            "surface.sqlite.provenance.create",
            attributes=self._attributes(record.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                cursor = connection.execute(
                    """INSERT INTO surface_generation_provenance (
                        artifact_id, workspace_id, mode, prompt_vault_digest,
                        no_prompt, constraints_vault_digest, script_vault_digest,
                        script_content_hash, script_revision, task_id, execution_id,
                        trace_id, created_at
                    ) SELECT artifact.artifact_id, artifact.workspace_id,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    FROM surface_display_artifacts AS artifact
                    JOIN workspace_surfaces AS surface
                      ON surface.surface_id=artifact.surface_id
                     AND surface.workspace_id=artifact.workspace_id
                    WHERE artifact.artifact_id=? AND artifact.workspace_id=?
                      AND surface.user_id=?""",
                    (
                        record.mode,
                        record.prompt_vault_digest,
                        int(record.no_prompt),
                        record.constraints_vault_digest,
                        record.script_vault_digest,
                        record.script_content_hash,
                        record.script_revision,
                        record.task_id,
                        record.execution_id,
                        record.trace_id,
                        record.created_at.isoformat(),
                        record.artifact_id,
                        record.workspace_id,
                        user_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise KeyError(record.artifact_id)
                connection.commit()
        return record

    def get(
        self, *, artifact_id: str, workspace_id: str, user_id: str
    ) -> GenerationProvenanceReference | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.provenance.get",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT provenance.*
                    FROM surface_generation_provenance AS provenance
                    JOIN surface_display_artifacts AS artifact
                      ON artifact.artifact_id=provenance.artifact_id
                     AND artifact.workspace_id=provenance.workspace_id
                    JOIN workspace_surfaces AS surface
                      ON surface.surface_id=artifact.surface_id
                     AND surface.workspace_id=artifact.workspace_id
                    WHERE provenance.artifact_id=? AND provenance.workspace_id=?
                      AND surface.user_id=?""",
                    (artifact_id, workspace_id, user_id),
                ).fetchone()
        return _provenance_from_row(row) if row is not None else None


class SurfaceRuntimeRepository(_SurfaceRuntimeRepositoryBase):
    def get(
        self,
        *,
        runtime_id: str,
        workspace_id: str,
        user_id: str,
        session_id: str,
    ) -> SurfaceRuntimeRecord | None:
        with self.tracer.start_as_current_span(
            "surface.sqlite.runtime.get",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                row = connection.execute(
                    """SELECT runtime.* FROM surface_runtimes AS runtime
                    JOIN workspace_surfaces AS surface
                      ON surface.surface_id=runtime.surface_id
                     AND surface.workspace_id=runtime.workspace_id
                    WHERE runtime.runtime_id=? AND runtime.workspace_id=?
                      AND surface.user_id=? AND surface.session_id=?""",
                    (runtime_id, workspace_id, user_id, session_id),
                ).fetchone()
        return _runtime_from_row(row) if row is not None else None

    def compare_and_set(
        self,
        record: SurfaceRuntimeRecord,
        *,
        expected_revision: int,
        user_id: str,
        session_id: str,
    ) -> SurfaceRuntimeRecord:
        with self.tracer.start_as_current_span(
            "surface.sqlite.runtime.compare_and_set",
            attributes=self._attributes(record.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                current = connection.execute(
                    """SELECT runtime.revision FROM surface_runtimes AS runtime
                    JOIN workspace_surfaces AS surface
                      ON surface.surface_id=runtime.surface_id
                     AND surface.workspace_id=runtime.workspace_id
                    WHERE runtime.runtime_id=? AND runtime.surface_id=?
                      AND runtime.workspace_id=? AND surface.user_id=?
                      AND surface.session_id=?""",
                    (
                        record.runtime_id,
                        record.surface_id,
                        record.workspace_id,
                        user_id,
                        session_id,
                    ),
                ).fetchone()
                if current is None:
                    raise KeyError(record.runtime_id)
                if int(current["revision"]) != expected_revision:
                    raise SurfaceRevisionConflict(
                        f"expected runtime revision {expected_revision}, "
                        f"current revision is {int(current['revision'])}"
                    )
                if record.revision != expected_revision + 1:
                    raise ValueError("runtime revision must increment exactly once")
                cursor = connection.execute(
                    """UPDATE surface_runtimes SET
                        state=?, process_identity_json=?, lifetime_json=?,
                        limits_json=?, target_pin_json=?, revision=?, updated_at=?
                    WHERE runtime_id=? AND surface_id=? AND workspace_id=?
                      AND revision=? AND EXISTS (
                        SELECT 1 FROM workspace_surfaces AS surface
                        WHERE surface.surface_id=surface_runtimes.surface_id
                          AND surface.workspace_id=surface_runtimes.workspace_id
                          AND surface.user_id=? AND surface.session_id=?
                      )""",
                    (
                        record.state,
                        _optional_json(record.process_identity),
                        _json(record.lifetime),
                        _json(record.limits),
                        _optional_json(record.target_pin),
                        record.revision,
                        record.updated_at.isoformat(),
                        record.runtime_id,
                        record.surface_id,
                        record.workspace_id,
                        expected_revision,
                        user_id,
                        session_id,
                    ),
                )
                if cursor.rowcount != 1:
                    raise SurfaceRevisionConflict(
                        f"expected runtime revision {expected_revision}"
                    )
                connection.commit()
        return record


def _diagnostic_from_row(row) -> SurfaceDiagnosticEvent:
    return SurfaceDiagnosticEvent(
        timestamp=datetime.fromisoformat(row["occurred_at"]),
        severity=SurfaceSeverity(row["severity"]),
        code=row["code"],
        message=row["message"],
        correlation=TraceCorrelation(
            correlation_id=row["correlation_id"],
            trace_id=row["trace_id"],
            span_id=row["span_id"],
        ),
        retryable=bool(row["retryable"]),
        user_id=row["user_id"],
        workspace_id=row["workspace_id"],
        session_id=row["session_id"],
        surface_id=row["surface_id"],
        instance_id=row["instance_id"],
        presentation_id=row["presentation_id"],
        runtime_id=row["runtime_id"],
        attributes=json.loads(row["attributes_json"]),
    )


class SurfaceDiagnosticRepository(_ScopedRepository):
    def record(
        self, event: SurfaceDiagnosticEvent, *, retention_class: str
    ) -> SurfaceDiagnosticEvent:
        with self.tracer.start_as_current_span(
            "surface.sqlite.diagnostic.record",
            attributes=self._attributes(event.workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                connection.execute(
                    """INSERT INTO surface_diagnostic_events (
                        event_id, occurred_at, severity, code, message, user_id,
                        workspace_id, session_id, surface_id, instance_id,
                        presentation_id, runtime_id, transition_json,
                        attributes_json, trace_id, span_id, correlation_id,
                        retryable, retention_class
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        event.timestamp.isoformat(),
                        event.severity.value,
                        event.code,
                        event.message,
                        event.user_id,
                        event.workspace_id,
                        event.session_id,
                        event.surface_id,
                        event.instance_id,
                        event.presentation_id,
                        event.runtime_id,
                        None,
                        _json(event.attributes),
                        event.correlation.trace_id,
                        event.correlation.span_id,
                        event.correlation.correlation_id,
                        int(event.retryable),
                        retention_class,
                    ),
                )
                connection.commit()
        return event

    def list(
        self,
        *,
        workspace_id: str,
        user_id: str,
        surface_id: str | None = None,
        limit: int = 100,
    ) -> list[SurfaceDiagnosticEvent]:
        bounded_limit = min(max(limit, 1), 500)
        with self.tracer.start_as_current_span(
            "surface.sqlite.diagnostic.list",
            attributes=self._attributes(workspace_id),
        ):
            with connect_state_db(self.db_path) as connection:
                statement = """SELECT * FROM surface_diagnostic_events
                    WHERE workspace_id=? AND user_id=?"""
                parameters: list[Any] = [workspace_id, user_id]
                if surface_id is not None:
                    statement += " AND surface_id=?"
                    parameters.append(surface_id)
                statement += " ORDER BY occurred_at DESC, event_id DESC LIMIT ?"
                parameters.append(bounded_limit)
                rows = connection.execute(statement, parameters).fetchall()
        return [_diagnostic_from_row(row) for row in reversed(rows)]
