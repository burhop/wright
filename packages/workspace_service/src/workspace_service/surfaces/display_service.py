"""Validated, durable Python display ingestion and verification."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import math
import re
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.surfaces.models import (
    DisplaySurfaceSource,
    SurfaceDescriptor,
    SurfaceId,
    SurfaceLifecycle,
    SurfaceRevision,
    surface_source_to_dict,
)
from data_vault import SurfaceRepository, SurfaceVault
from data_vault.state_store import connect_state_db

from .ports import SurfaceEventPublisherPort


logger = logging.getLogger(__name__)


_DISPLAY_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_MEDIA_ENCODINGS = {
    "text/plain": "utf-8",
    "text/html": "utf-8",
    "image/png": "base64",
    "image/jpeg": "base64",
    "image/svg+xml": "utf-8",
    "application/vnd.wright.table+json": "json",
    "application/vnd.plotly.v1+json": "json",
}


class DisplayContractError(ValueError):
    pass


class DisplayRevisionConflict(RuntimeError):
    def __init__(self, display_id: str, *, expected: int, received: int) -> None:
        super().__init__(
            f"stale display revision for {display_id}: expected {expected}, "
            f"received {received}"
        )
        self.display_id = display_id
        self.expected = expected
        self.received = received


class DisplayDeletionNotConfirmed(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class DisplayEnvelopeLimits:
    maximum_encoded_bytes: int = 16 * 1024 * 1024
    maximum_json_depth: int = 32
    maximum_json_items: int = 1_000_000
    validation_seconds: float = 1.0
    maximum_representations: int = 12


@dataclass(frozen=True, slots=True)
class DisplayRepresentationValue:
    media_type: str
    encoding: str
    data: Any
    metadata: dict[str, Any]
    active_html: bool
    fallback_rank: int


@dataclass(frozen=True, slots=True)
class DisplayEnvelopeValue:
    display_id: str
    revision: int
    idempotency_key: str
    title: str | None
    durability: str
    description: str
    representations: tuple[DisplayRepresentationValue, ...]


@dataclass(frozen=True, slots=True)
class DisplayExecutionContext:
    user_id: str
    workspace_id: str
    session_id: str
    task_id: str
    execution_id: str
    prompt: str | None
    no_prompt: bool
    effective_constraints: dict[str, Any]
    script: str
    script_revision: int
    trace_id: str


@dataclass(frozen=True, slots=True)
class DisplayIngestResult:
    descriptor: SurfaceDescriptor
    created: bool


@dataclass(frozen=True, slots=True)
class DisplayArtifactProjection:
    artifact_id: str
    revision: int
    current: bool
    representations: tuple[dict[str, Any], ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class DisplayDeletionResult:
    deleted: bool
    recoverable: bool
    retention_status: str


def _json_metrics(
    value: Any,
    *,
    depth: int,
    deadline: float,
) -> tuple[int, int]:
    if time.monotonic() > deadline:
        raise DisplayContractError("display validation exceeded its time limit")
    if isinstance(value, float) and not math.isfinite(value):
        raise DisplayContractError("display JSON numbers must be finite")
    if value is None or isinstance(value, (str, int, float, bool)):
        return depth, 1
    if isinstance(value, dict):
        maximum, count = depth, 1
        for key, item in value.items():
            if not isinstance(key, str):
                raise DisplayContractError("display JSON keys must be strings")
            child_depth, child_count = _json_metrics(
                item, depth=depth + 1, deadline=deadline
            )
            maximum = max(maximum, child_depth)
            count += child_count
        return maximum, count
    if isinstance(value, list):
        maximum, count = depth, 1
        for item in value:
            child_depth, child_count = _json_metrics(
                item, depth=depth + 1, deadline=deadline
            )
            maximum = max(maximum, child_depth)
            count += child_count
        return maximum, count
    raise DisplayContractError(
        f"display JSON contains unsupported {type(value).__name__}"
    )


def _exact_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unexpected = set(value) - allowed
    if unexpected:
        raise DisplayContractError(
            f"{label} contains unsupported field {sorted(unexpected)[0]}"
        )


def validate_display_envelope(
    value: dict[str, Any], *, limits: DisplayEnvelopeLimits | None = None
) -> DisplayEnvelopeValue:
    effective = limits or DisplayEnvelopeLimits()
    started = time.monotonic()
    deadline = started + effective.validation_seconds
    if not isinstance(value, dict):
        raise DisplayContractError("display envelope must be an object")
    _exact_keys(
        value,
        {
            "schemaVersion",
            "displayId",
            "revision",
            "idempotencyKey",
            "title",
            "durability",
            "dimensions",
            "accessibility",
            "representations",
            "producerMetadata",
        },
        "display envelope",
    )
    if value.get("schemaVersion") != 1:
        raise DisplayContractError("schemaVersion must be 1")
    display_id = value.get("displayId")
    if not isinstance(display_id, str) or not _DISPLAY_ID.fullmatch(display_id):
        raise DisplayContractError("displayId is invalid")
    revision = value.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise DisplayContractError("revision must be a positive integer")
    idempotency_key = value.get("idempotencyKey")
    if not isinstance(idempotency_key, str) or not 16 <= len(idempotency_key) <= 128:
        raise DisplayContractError("idempotencyKey must contain 16 to 128 characters")
    title = value.get("title")
    if title is not None and (not isinstance(title, str) or len(title) > 256):
        raise DisplayContractError("title must be at most 256 characters")
    durability = value.get("durability", "durable")
    if durability not in {"durable", "session", "ephemeral"}:
        raise DisplayContractError("durability is invalid")
    accessibility = value.get("accessibility")
    if not isinstance(accessibility, dict):
        raise DisplayContractError("accessibility is required")
    _exact_keys(
        accessibility, {"description", "dataTableRepresentation"}, "accessibility"
    )
    description = accessibility.get("description")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 4096:
        raise DisplayContractError("accessibility description is required and bounded")
    raw_representations = value.get("representations")
    if (
        not isinstance(raw_representations, list)
        or not 1 <= len(raw_representations) <= effective.maximum_representations
    ):
        raise DisplayContractError("representations must contain 1 to 12 items")
    representations: list[DisplayRepresentationValue] = []
    for index, raw in enumerate(raw_representations):
        if not isinstance(raw, dict):
            raise DisplayContractError(f"representation {index} must be an object")
        _exact_keys(
            raw,
            {
                "mediaType",
                "encoding",
                "data",
                "metadata",
                "activeHtml",
                "fallbackRank",
            },
            f"representation {index}",
        )
        media_type = raw.get("mediaType")
        encoding = raw.get("encoding")
        expected = _MEDIA_ENCODINGS.get(media_type)
        if expected is None or encoding != expected:
            raise DisplayContractError(
                f"representation {index} media type or encoding is unsupported"
            )
        active_html = raw.get("activeHtml", False)
        if not isinstance(active_html, bool) or (
            active_html and media_type != "text/html"
        ):
            raise DisplayContractError("active HTML is valid only for text/html")
        data = raw.get("data")
        if encoding == "utf-8" and not isinstance(data, str):
            raise DisplayContractError("utf-8 display data must be a string")
        if encoding == "base64":
            if not isinstance(data, str):
                raise DisplayContractError("base64 display data must be a string")
            try:
                base64.b64decode(data, validate=True)
            except (ValueError, binascii.Error) as error:
                raise DisplayContractError("display data is not valid base64") from error
        if encoding == "json":
            depth, items = _json_metrics(data, depth=1, deadline=deadline)
            if depth > effective.maximum_json_depth:
                raise DisplayContractError("display JSON exceeds the maximum depth")
            if items > effective.maximum_json_items:
                raise DisplayContractError("display JSON exceeds the maximum item count")
        metadata = raw.get("metadata", {})
        if not isinstance(metadata, dict) or len(metadata) > 32:
            raise DisplayContractError("representation metadata is invalid")
        fallback_rank = raw.get("fallbackRank", 0)
        if (
            isinstance(fallback_rank, bool)
            or not isinstance(fallback_rank, int)
            or not 0 <= fallback_rank <= 100
        ):
            raise DisplayContractError("fallbackRank must be between 0 and 100")
        representations.append(
            DisplayRepresentationValue(
                media_type=media_type,
                encoding=encoding,
                data=data,
                metadata=metadata,
                active_html=active_html,
                fallback_rank=fallback_rank,
            )
        )
    try:
        encoded = json.dumps(
            value, allow_nan=False, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DisplayContractError("display envelope contains invalid JSON") from error
    if len(encoded) > effective.maximum_encoded_bytes:
        raise DisplayContractError("display envelope exceeds the maximum encoded bytes")
    if time.monotonic() > deadline:
        raise DisplayContractError("display validation exceeded its time limit")
    return DisplayEnvelopeValue(
        display_id=display_id,
        revision=revision,
        idempotency_key=idempotency_key,
        title=title.strip() if isinstance(title, str) and title.strip() else None,
        durability=durability,
        description=description.strip(),
        representations=tuple(representations),
    )


def _payload_bytes(representation: DisplayRepresentationValue) -> bytes:
    if representation.encoding == "base64":
        return base64.b64decode(representation.data, validate=True)
    if representation.encoding == "json":
        return json.dumps(
            representation.data,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    return representation.data.encode("utf-8")


class DisplayService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        vault: SurfaceVault,
        events: SurfaceEventPublisherPort | None = None,
        clock=lambda: datetime.now(UTC),
        limits: DisplayEnvelopeLimits | None = None,
    ) -> None:
        self.db_path = str(db_path)
        self.vault = vault
        self.events = events
        self.clock = clock
        self.limits = limits or DisplayEnvelopeLimits()
        self.surfaces = SurfaceRepository(db_path)

    def _publish(
        self,
        descriptor: SurfaceDescriptor,
        *,
        event_type: str,
        context: DisplayExecutionContext,
    ) -> None:
        if self.events is None:
            return
        try:
            self.events.publish(
                descriptor,
                event_type=event_type,
                user_id=context.user_id,
                session_id=context.session_id,
            )
        except Exception:
            # The durable outbox remains the recovery source if process-local
            # fanout fails after the database transaction committed.
            logger.exception(
                "Workspace Surface display fanout failed",
                extra={
                    "workspace_id": context.workspace_id,
                    "surface_id": str(descriptor.surface_id),
                    "event_type": event_type,
                },
            )

    @staticmethod
    def _surface_id(context: DisplayExecutionContext, display_id: str) -> SurfaceId:
        identity = f"{context.workspace_id}:{context.task_id}:{display_id}"
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:40]
        return SurfaceId(f"display-{digest}")

    @staticmethod
    def _require_context(context: DisplayExecutionContext) -> None:
        if context.prompt is None:
            if not context.no_prompt:
                raise DisplayContractError("direct execution requires a no-prompt marker")
        elif context.no_prompt or not context.prompt.strip():
            raise DisplayContractError("agent generation requires the exact prompt")
        if context.script_revision < 1 or not context.script:
            raise DisplayContractError("exact script and positive revision are required")

    def _existing_by_idempotency(
        self, envelope: DisplayEnvelopeValue, context: DisplayExecutionContext
    ) -> SurfaceDescriptor | None:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                """SELECT artifact.*, surface.title AS surface_title,
                    surface.created_at AS surface_created_at
                FROM surface_display_artifacts AS artifact
                JOIN workspace_surfaces AS surface ON surface.surface_id=artifact.surface_id
                WHERE artifact.workspace_id=? AND artifact.producer_execution_id=?
                  AND artifact.idempotency_key=? AND surface.user_id=?
                  AND surface.session_id=?""",
                (
                    context.workspace_id,
                    context.execution_id,
                    envelope.idempotency_key,
                    context.user_id,
                    context.session_id,
                ),
            ).fetchone()
        if row is None:
            return None
        stored = json.loads(row["representations_json"])
        source = DisplaySurfaceSource(
            execution_id=row["producer_execution_id"],
            display_id=row["display_id"],
            artifact_revision=int(row["revision"]),
            durability=row["durability"],
            media_types=tuple(item["mediaType"] for item in stored),
        )
        return SurfaceDescriptor(
            schema_version=1,
            surface_id=SurfaceId(row["surface_id"]),
            workspace_id=row["workspace_id"],
            source=source,
            title=row["surface_title"],
            lifecycle=SurfaceLifecycle.READY,
            revision=SurfaceRevision(int(row["revision"])),
            created_at=datetime.fromisoformat(row["surface_created_at"]),
            updated_at=datetime.fromisoformat(row["created_at"]),
        )

    def ingest(
        self, value: dict[str, Any], *, context: DisplayExecutionContext
    ) -> DisplayIngestResult:
        self._require_context(context)
        envelope = validate_display_envelope(value, limits=self.limits)
        existing = self._existing_by_idempotency(envelope, context)
        if existing is not None:
            return DisplayIngestResult(existing, created=False)

        now = self.clock()
        surface_id = self._surface_id(context, envelope.display_id)
        stored_representations: list[dict[str, Any]] = []
        for representation in envelope.representations:
            payload = _payload_bytes(representation)
            digest = self.vault.put(
                workspace_id=context.workspace_id, payload=payload
            )
            stored_representations.append(
                {
                    "mediaType": representation.media_type,
                    "encoding": representation.encoding,
                    "vaultDigest": digest,
                    "byteLength": len(payload),
                    "contentHash": hashlib.sha256(payload).hexdigest(),
                    "metadata": representation.metadata,
                    "activeHtml": representation.active_html,
                    "fallbackRank": representation.fallback_rank,
                }
            )
        prompt_digest = (
            self.vault.put(
                workspace_id=context.workspace_id,
                payload=context.prompt.encode("utf-8"),
            )
            if context.prompt is not None
            else None
        )
        constraints_payload = json.dumps(
            context.effective_constraints,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        constraints_digest = self.vault.put(
            workspace_id=context.workspace_id, payload=constraints_payload
        )
        script_payload = context.script.encode("utf-8")
        script_digest = self.vault.put(
            workspace_id=context.workspace_id, payload=script_payload
        )
        artifact_id = str(uuid.uuid4())
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                workspace = connection.execute(
                    """SELECT 1 FROM engineering_workspaces
                    WHERE workspace_id=? AND session_id=?""",
                    (context.workspace_id, context.session_id),
                ).fetchone()
                if workspace is None:
                    raise KeyError(context.workspace_id)
                current = connection.execute(
                    """SELECT artifact.* FROM surface_display_artifacts AS artifact
                    JOIN workspace_surfaces AS surface
                      ON surface.surface_id=artifact.surface_id
                    WHERE artifact.workspace_id=?
                      AND artifact.producer_task_id=?
                      AND artifact.display_id=? AND artifact.current=1
                      AND surface.user_id=? AND surface.session_id=?""",
                    (
                        context.workspace_id,
                        context.task_id,
                        envelope.display_id,
                        context.user_id,
                        context.session_id,
                    ),
                ).fetchone()
                expected_revision = 1 if current is None else int(current["revision"]) + 1
                accepted_revision = envelope.revision
                if (
                    current is not None
                    and envelope.revision == 1
                    and current["producer_execution_id"] != context.execution_id
                ):
                    accepted_revision = expected_revision
                if accepted_revision != expected_revision:
                    raise DisplayRevisionConflict(
                        envelope.display_id,
                        expected=expected_revision,
                        received=envelope.revision,
                    )
                source = DisplaySurfaceSource(
                    execution_id=context.execution_id,
                    display_id=envelope.display_id,
                    artifact_revision=accepted_revision,
                    durability=envelope.durability,
                    media_types=tuple(
                        item.media_type for item in envelope.representations
                    ),
                )
                surface = connection.execute(
                    "SELECT * FROM workspace_surfaces WHERE surface_id=?",
                    (str(surface_id),),
                ).fetchone()
                title = envelope.title or envelope.display_id
                if surface is None:
                    surface_revision = 1
                    created_at = now
                    connection.execute(
                        """INSERT INTO workspace_surfaces (
                            surface_id, workspace_id, user_id, session_id,
                            schema_version, source_kind, source_id, source_version,
                            source_json, title, lifecycle, instance_json,
                            presentations_json, capabilities_json,
                            diagnostic_summary_json, generation_provenance_json,
                            revision, idempotency_key, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 1, 'display', ?, ?, ?, ?, 'ready',
                            NULL, '[]', '[]', NULL, NULL, ?, NULL, ?, ?)""",
                        (
                            str(surface_id),
                            context.workspace_id,
                            context.user_id,
                            context.session_id,
                            source.source_id,
                            source.source_version,
                            json.dumps(surface_source_to_dict(source), sort_keys=True),
                            title,
                            surface_revision,
                            now.isoformat(),
                            now.isoformat(),
                        ),
                    )
                else:
                    if (
                        surface["workspace_id"] != context.workspace_id
                        or surface["user_id"] != context.user_id
                        or surface["session_id"] != context.session_id
                    ):
                        raise KeyError(str(surface_id))
                    surface_revision = int(surface["revision"]) + 1
                    created_at = datetime.fromisoformat(surface["created_at"])
                    connection.execute(
                        """UPDATE workspace_surfaces SET source_version=?,
                            source_json=?, title=?, lifecycle='ready', revision=?,
                            updated_at=? WHERE surface_id=?""",
                        (
                            source.source_version,
                            json.dumps(surface_source_to_dict(source), sort_keys=True),
                            title,
                            surface_revision,
                            now.isoformat(),
                            str(surface_id),
                        ),
                    )
                    connection.execute(
                        """UPDATE surface_display_artifacts SET current=0
                        WHERE artifact_id=?""",
                        (current["artifact_id"],),
                    )
                connection.execute(
                    """INSERT INTO surface_display_artifacts (
                        artifact_id, surface_id, workspace_id, display_id, revision,
                        producer_execution_id, producer_task_id,
                        representations_json, title,
                        accessibility_description, dimensions_json, durability,
                        current, idempotency_key, supersedes_artifact_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, 1, ?, ?, ?)""",
                    (
                        artifact_id,
                        str(surface_id),
                        context.workspace_id,
                        envelope.display_id,
                        accepted_revision,
                        context.execution_id,
                        context.task_id,
                        json.dumps(stored_representations, sort_keys=True),
                        title,
                        envelope.description,
                        envelope.durability,
                        envelope.idempotency_key,
                        current["artifact_id"] if current is not None else None,
                        now.isoformat(),
                    ),
                )
                connection.execute(
                    """INSERT INTO surface_generation_provenance (
                        artifact_id, workspace_id, mode, prompt_vault_digest,
                        no_prompt, constraints_vault_digest, script_vault_digest,
                        script_content_hash, script_revision, task_id, execution_id,
                        trace_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        artifact_id,
                        context.workspace_id,
                        "agent_generated" if context.prompt is not None else "direct_execution",
                        prompt_digest,
                        int(context.no_prompt),
                        constraints_digest,
                        script_digest,
                        hashlib.sha256(script_payload).hexdigest(),
                        context.script_revision,
                        context.task_id,
                        context.execution_id,
                        context.trace_id,
                        now.isoformat(),
                    ),
                )
                connection.execute(
                    """INSERT INTO surface_outbox (
                        event_id, workspace_id, aggregate_id, aggregate_revision,
                        event_type, payload_json, trace_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        str(uuid.uuid4()),
                        context.workspace_id,
                        str(surface_id),
                        surface_revision,
                        "surface.display.created"
                        if surface_revision == 1
                        else "surface.display.updated",
                        json.dumps(
                            {
                                "surface_id": str(surface_id),
                                "display_id": envelope.display_id,
                                "artifact_revision": accepted_revision,
                            },
                            sort_keys=True,
                        ),
                        context.trace_id,
                        now.isoformat(),
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        descriptor = SurfaceDescriptor(
            schema_version=1,
            surface_id=surface_id,
            workspace_id=context.workspace_id,
            source=source,
            title=envelope.title or envelope.display_id,
            lifecycle=SurfaceLifecycle.READY,
            revision=SurfaceRevision(surface_revision),
            created_at=created_at,
            updated_at=now,
        )
        self._publish(
            descriptor,
            event_type=(
                "surface.display.created"
                if surface_revision == 1
                else "surface.display.updated"
            ),
            context=context,
        )
        return DisplayIngestResult(descriptor, created=True)

    def history(
        self, *, display_id: str, context: DisplayExecutionContext
    ) -> list[DisplayArtifactProjection]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                """SELECT artifact.* FROM surface_display_artifacts AS artifact
                JOIN workspace_surfaces AS surface ON surface.surface_id=artifact.surface_id
                WHERE artifact.workspace_id=? AND artifact.producer_task_id=?
                  AND artifact.display_id=? AND surface.user_id=?
                  AND surface.session_id=? ORDER BY artifact.revision""",
                (
                    context.workspace_id,
                    context.task_id,
                    display_id,
                    context.user_id,
                    context.session_id,
                ),
            ).fetchall()
        return [
            DisplayArtifactProjection(
                artifact_id=row["artifact_id"],
                revision=int(row["revision"]),
                current=bool(row["current"]),
                representations=tuple(json.loads(row["representations_json"])),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def read_representation(
        self,
        *,
        artifact_id: str,
        index: int,
        context: DisplayExecutionContext,
    ) -> bytes:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                """SELECT artifact.representations_json
                FROM surface_display_artifacts AS artifact
                JOIN workspace_surfaces AS surface ON surface.surface_id=artifact.surface_id
                WHERE artifact.artifact_id=? AND artifact.workspace_id=?
                  AND surface.user_id=? AND surface.session_id=?""",
                (
                    artifact_id,
                    context.workspace_id,
                    context.user_id,
                    context.session_id,
                ),
            ).fetchone()
        if row is None:
            raise KeyError(artifact_id)
        representations = json.loads(row["representations_json"])
        try:
            digest = representations[index]["vaultDigest"]
        except (IndexError, KeyError) as error:
            raise KeyError(f"{artifact_id}:{index}") from error
        return self.vault.get(workspace_id=context.workspace_id, digest=digest)

    def verify_artifact(
        self, *, surface_id: str, context: DisplayExecutionContext
    ) -> dict[str, Any]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                """SELECT provenance.*
                FROM surface_generation_provenance AS provenance
                JOIN surface_display_artifacts AS artifact
                  ON artifact.artifact_id=provenance.artifact_id
                JOIN workspace_surfaces AS surface ON surface.surface_id=artifact.surface_id
                WHERE artifact.surface_id=? AND artifact.current=1
                  AND artifact.workspace_id=? AND surface.user_id=?
                  AND surface.session_id=?""",
                (
                    surface_id,
                    context.workspace_id,
                    context.user_id,
                    context.session_id,
                ),
            ).fetchone()
        if row is None:
            raise KeyError(surface_id)
        prompt = (
            self.vault.get(
                workspace_id=context.workspace_id,
                digest=row["prompt_vault_digest"],
            ).decode("utf-8")
            if row["prompt_vault_digest"]
            else None
        )
        constraints = json.loads(
            self.vault.get(
                workspace_id=context.workspace_id,
                digest=row["constraints_vault_digest"],
            )
        )
        script = self.vault.get(
            workspace_id=context.workspace_id, digest=row["script_vault_digest"]
        ).decode("utf-8")
        return {
            "mode": row["mode"],
            "prompt": prompt,
            "no_prompt": bool(row["no_prompt"]),
            "effective_constraints": constraints,
            "script": script,
            "script_revision": int(row["script_revision"]),
            "task_id": row["task_id"],
            "execution_id": row["execution_id"],
            "trace_id": row["trace_id"],
        }

    def display_projection(
        self, *, surface_id: str, context: DisplayExecutionContext
    ) -> dict[str, Any]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            row = connection.execute(
                """SELECT artifact.* FROM surface_display_artifacts AS artifact
                JOIN workspace_surfaces AS surface ON surface.surface_id=artifact.surface_id
                WHERE artifact.surface_id=? AND artifact.current=1
                  AND artifact.workspace_id=? AND surface.user_id=?
                  AND surface.session_id=?""",
                (
                    surface_id,
                    context.workspace_id,
                    context.user_id,
                    context.session_id,
                ),
            ).fetchone()
        if row is None:
            raise KeyError(surface_id)
        representations = []
        for stored in json.loads(row["representations_json"]):
            payload = self.vault.get(
                workspace_id=context.workspace_id, digest=stored["vaultDigest"]
            )
            if stored["encoding"] == "base64":
                data: Any = base64.b64encode(payload).decode("ascii")
            elif stored["encoding"] == "json":
                data = json.loads(payload)
            else:
                data = payload.decode("utf-8")
            representations.append(
                {
                    "mediaType": stored["mediaType"],
                    "encoding": stored["encoding"],
                    "data": data,
                    "metadata": stored.get("metadata", {}),
                    "activeHtml": bool(stored.get("activeHtml", False)),
                    "fallbackRank": int(stored.get("fallbackRank", 0)),
                }
            )
        return {
            "artifactId": row["artifact_id"],
            "surfaceId": row["surface_id"],
            "displayId": row["display_id"],
            "revision": int(row["revision"]),
            "title": row["title"],
            "accessibilityDescription": row["accessibility_description"],
            "durability": row["durability"],
            "representations": representations,
        }

    def surface_history(
        self, *, surface_id: str, context: DisplayExecutionContext
    ) -> list[dict[str, Any]]:
        with connect_state_db(self.db_path, read_only=True, wal=False) as connection:
            rows = connection.execute(
                """SELECT artifact.artifact_id, artifact.revision,
                    artifact.current, artifact.created_at
                FROM surface_display_artifacts AS artifact
                JOIN workspace_surfaces AS surface ON surface.surface_id=artifact.surface_id
                WHERE artifact.surface_id=? AND artifact.workspace_id=?
                  AND surface.user_id=? AND surface.session_id=?
                ORDER BY artifact.revision""",
                (
                    surface_id,
                    context.workspace_id,
                    context.user_id,
                    context.session_id,
                ),
            ).fetchall()
        if not rows:
            raise KeyError(surface_id)
        return [
            {
                "artifactId": row["artifact_id"],
                "revision": int(row["revision"]),
                "current": bool(row["current"]),
                "createdAt": row["created_at"],
            }
            for row in rows
        ]

    @staticmethod
    def diagnostic_projection(descriptor: SurfaceDescriptor) -> dict[str, Any]:
        return {
            "surface_id": str(descriptor.surface_id),
            "source_id": descriptor.source.source_id,
            "source_version": descriptor.source.source_version,
            "revision": int(descriptor.revision),
            "lifecycle": descriptor.lifecycle.value,
        }

    def delete(
        self,
        *,
        surface_id: str,
        context: DisplayExecutionContext,
        retention_disclosure_confirmed: bool,
    ) -> DisplayDeletionResult:
        if not retention_disclosure_confirmed:
            raise DisplayDeletionNotConfirmed(
                "Confirm that deleting this durable output cannot be recovered."
            )
        descriptor = self.surfaces.get(
            SurfaceId(surface_id),
            workspace_id=context.workspace_id,
            user_id=context.user_id,
            session_id=context.session_id,
        )
        if descriptor is None or not isinstance(descriptor.source, DisplaySurfaceSource):
            raise KeyError(surface_id)
        with connect_state_db(self.db_path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                """DELETE FROM workspace_surfaces
                WHERE surface_id=? AND workspace_id=? AND user_id=?
                  AND session_id=? AND source_kind='display'""",
                (
                    surface_id,
                    context.workspace_id,
                    context.user_id,
                    context.session_id,
                ),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise KeyError(surface_id)
            connection.commit()
        self._publish(
            descriptor,
            event_type="surface.display.deleted",
            context=context,
        )
        return DisplayDeletionResult(
            deleted=True,
            recoverable=False,
            retention_status="payload_cleanup_scheduled",
        )
