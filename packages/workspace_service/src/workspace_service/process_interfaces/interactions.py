"""Declared input checkpoint evidence, using the existing continuation store.

The source executor and recorder own execution. This owner only retains a typed
answer and consumes its exact barrier. Public scope/transport orchestration must
validate current source/evidence before calling it; it never dispatches a tool.
"""

from __future__ import annotations

from datetime import datetime, timezone
import secrets
import time
import json

from pydantic import Field, field_validator

from core.process_interactions import (
    PAGE_ITEMS,
    InteractionResponse,
    checked_json,
    validate_response,
)
from core.process_validation import (
    Contract,
    Digest,
    Identifier,
    ResultIdentifier,
    canonical_digest,
    canonical_json,
)
from core.tracing import traced
from data_vault.process_input_repository import (
    ProcessInputRepository,
    ProcessRecordConflict,
)
from data_vault.workflow_continuation_repository import (
    WorkflowContinuationCheckpoint,
    WorkflowContinuationRepository,
    WorkflowContinuationStateConflict,
)

from ..workflow_human_input import HumanInputDeclaration
from .errors import ProcessInterfaceError


class InputCheckpointSubject(Contract):
    """Pins the declared question and actual connected upstream values."""

    definition_digest: Digest
    input_snapshot_id: Identifier
    input_digest: Digest
    input_digests: tuple[Digest, ...] = Field(max_length=PAGE_ITEMS)
    artifact_digests: tuple[Digest, ...] = Field(max_length=PAGE_ITEMS)
    step_id: Identifier
    declaration: HumanInputDeclaration
    upstream_digests: dict[ResultIdentifier, Digest] = Field(
        min_length=1, max_length=PAGE_ITEMS
    )

    @field_validator("input_digests", "artifact_digests")
    @classmethod
    def ordered_digests(cls, value):
        if value != tuple(sorted(value)):
            raise ValueError("Checkpoint digests must be ordered")
        return value


def input_subject(subject) -> InputCheckpointSubject:
    # Revalidate nested mutable JSON; frozen contracts do not freeze dictionaries.
    checked_json(subject)
    return InputCheckpointSubject.model_validate(subject)


def input_subject_digest(subject) -> str:
    return canonical_digest(input_subject(subject).model_dump(mode="json"))


def _unavailable(message, *, code="SUBJECT_STALE"):
    return ProcessInterfaceError(
        code,
        message,
        "Reopen the saved run and inspect the declared input and its evidence.",
    )


class HumanInputCheckpointService:
    """Internal owner; actor and integration-test authority are supplied by Wright."""

    def __init__(
        self,
        repository: WorkflowContinuationRepository,
        inputs: ProcessInputRepository,
    ):
        if repository.db_path != inputs.db_path:
            raise ValueError(
                "Input responses and checkpoints must share one state store"
            )
        self.repository = repository
        self.inputs = inputs

    def _validate(self, checkpoint):
        try:
            subject = input_subject(checkpoint.subject)
            continuation = checkpoint.continuation
            if len(canonical_json(continuation).encode("utf-8")) > 20_971_520:
                raise ValueError("Input continuation exceeds 20 MiB")
            frozen = self.inputs.get_snapshot(
                checkpoint.workspace_id, subject.input_snapshot_id
            )
            if (
                checkpoint.action_kind != "human_input"
                or checkpoint.checkpoint_kind != "input"
                or type(continuation.get("schema_version")) is not int
                or continuation["schema_version"] != 3
                or checkpoint.subject_digest != input_subject_digest(checkpoint.subject)
                or checkpoint.step_id != subject.step_id
                or checkpoint.run_id != continuation.get("run_id")
                or checkpoint.external_action is not None
                or frozen.digest != subject.input_digest
                or frozen.process.source_digest != subject.definition_digest
                or frozen.process.source_path != checkpoint.workflow_id
                or continuation.get("definition_digest") != subject.definition_digest
                or continuation.get("input_snapshot_id") != subject.input_snapshot_id
                or continuation.get("input_digest") != subject.input_digest
                or bool(continuation.get("response_id"))
                != bool(continuation.get("response_digest"))
            ):
                raise ValueError(
                    "Input checkpoint identity does not match its evidence"
                )
        except (ValueError, TypeError, KeyError) as error:
            raise _unavailable(
                "The saved input checkpoint evidence is inconsistent."
            ) from error
        return subject

    @traced("process.interaction.input.request")
    def request(
        self,
        *,
        workspace_id: str,
        workflow_id: str,
        run_id: str,
        step_id: str,
        subject: dict,
        continuation: dict,
        expires_at: int | None = None,
    ) -> WorkflowContinuationCheckpoint:
        now = int(time.time())
        checkpoint = WorkflowContinuationCheckpoint(
            checkpoint_id=f"checkpoint-{secrets.token_hex(12)}",
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            run_id=run_id,
            step_id=step_id,
            action_kind="human_input",
            subject=input_subject(subject).model_dump(mode="json"),
            subject_digest=input_subject_digest(subject),
            state="pending",
            continuation=json.loads(canonical_json(continuation)),
            actor=None,
            reason=None,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            external_action=None,
        )
        self._validate(checkpoint)
        if continuation.get("response_id") is not None:
            raise _unavailable(
                "A new input checkpoint cannot contain a prior response."
            )
        return self.repository.create(checkpoint)

    @traced("process.interaction.input.read")
    def get(self, checkpoint_id, *, workspace_id, run_id):
        checkpoint = self.repository.get(checkpoint_id)
        if checkpoint is None or (
            checkpoint.workspace_id != workspace_id or checkpoint.run_id != run_id
        ):
            raise _unavailable(
                "The declared input is not available in this run.", code="SCOPE_DENIED"
            )
        self._validate(checkpoint)
        return checkpoint

    @traced("process.interaction.input.respond")
    def respond(
        self,
        checkpoint_id,
        *,
        workspace_id,
        run_id,
        expected_subject_digest,
        value,
        actor,
        reason,
        request_id,
        integration_test=False,
    ):
        checkpoint = self.get(checkpoint_id, workspace_id=workspace_id, run_id=run_id)
        if checkpoint.subject_digest != expected_subject_digest:
            raise _unavailable("The response belongs to an earlier input subject.")
        subject = self._validate(checkpoint)
        try:
            validate_response(subject.declaration.response_schema, value)
            response = InteractionResponse.create(
                response_id=f"response-{secrets.token_hex(12)}",
                workspace_id=workspace_id,
                run_id=run_id,
                checkpoint_id=checkpoint_id,
                subject_digest=checkpoint.subject_digest,
                schema_digest=canonical_digest(subject.declaration.response_schema),
                input_digest=subject.input_digest,
                value=value,
                actor=actor,
                reason=reason,
                request_id=request_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                integration_test=integration_test,
            )
        except (ValueError, TypeError) as error:
            raise _unavailable(
                "The response does not match the declared input schema.",
                code="RESPONSE_INVALID",
            ) from error
        try:
            return self.repository.attach_input_response(
                response, updated_at=int(time.time())
            )
        except (ProcessRecordConflict, WorkflowContinuationStateConflict) as error:
            raise _unavailable(
                "This checkpoint cannot accept a different or expired response.",
                code="REQUEST_CONFLICT",
            ) from error

    @traced("process.interaction.input.consume")
    def consume(self, checkpoint_id, *, workspace_id, run_id, response_id):
        checkpoint = self.get(checkpoint_id, workspace_id=workspace_id, run_id=run_id)
        response = self.response(checkpoint)
        if response.response_id != response_id:
            raise _unavailable("This response belongs to another continuation.")
        try:
            return self.repository.consume_input_response(
                checkpoint_id,
                workspace_id=workspace_id,
                run_id=run_id,
                subject_digest=checkpoint.subject_digest,
                response_id=response.response_id,
                response_digest=response.digest,
                updated_at=int(time.time()),
            )
        except WorkflowContinuationStateConflict as error:
            raise _unavailable(
                "The input continuation was already consumed or is no longer current.",
                code="REQUEST_CONFLICT",
            ) from error

    def response(self, checkpoint) -> InteractionResponse:
        """Only immutable, scoped schema-valid evidence can release an input step."""
        subject = self._validate(checkpoint)
        try:
            response = self.inputs.get_response(
                checkpoint.workspace_id, checkpoint.continuation["response_id"]
            )
            if (
                response.run_id != checkpoint.run_id
                or response.checkpoint_id != checkpoint.checkpoint_id
                or response.subject_digest != checkpoint.subject_digest
                or response.input_digest != subject.input_digest
                or response.schema_digest
                != canonical_digest(subject.declaration.response_schema)
                or response.digest != checkpoint.continuation.get("response_digest")
            ):
                raise ValueError("The immutable response does not match its checkpoint")
            validate_response(subject.declaration.response_schema, response.value)
        except (ValueError, TypeError, KeyError) as error:
            raise _unavailable(
                "There is no matching saved response for this input."
            ) from error
        return response
