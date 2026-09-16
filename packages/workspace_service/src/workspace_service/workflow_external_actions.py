"""Exact-subject approval and one-shot dispatch authority for external actions."""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any, Mapping

from core.canonical_json import canonical_json_bytes
from data_vault import (
    WorkflowContinuationCheckpoint,
    WorkflowContinuationRepository,
    WorkflowContinuationStateConflict,
)


class WorkflowExternalActionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def approval_subject_digest(subject: Mapping[str, Any]) -> str:
    required = {
        "definition_digest",
        "input_digests",
        "artifact_digests",
        "binding",
        "destination",
        "settings",
        "action",
    }
    if set(subject) != required:
        raise WorkflowExternalActionError(
            "approval_subject_invalid",
            "Approval subject is incomplete or contains unknown fields",
        )
    forbidden = {"password", "secret", "token", "api_key", "card", "cvv", "credential"}

    def inspect(value, depth=0):
        if depth > 12:
            raise WorkflowExternalActionError(
                "approval_subject_invalid", "Approval subject is too deeply nested"
            )
        if isinstance(value, Mapping):
            for key, item in value.items():
                if not isinstance(key, str) or any(
                    marker in key.casefold().replace("-", "_") for marker in forbidden
                ):
                    raise WorkflowExternalActionError(
                        "approval_subject_sensitive",
                        "Approval subjects must not contain credentials or payment data",
                    )
                inspect(item, depth + 1)
        elif isinstance(value, (list, tuple)):
            for item in value:
                inspect(item, depth + 1)
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            raise WorkflowExternalActionError(
                "approval_subject_invalid",
                "Approval subject contains an unsupported value",
            )

    inspect(subject)
    encoded = canonical_json_bytes(dict(subject))
    if len(encoded) > 256 * 1024:
        raise WorkflowExternalActionError(
            "approval_subject_invalid", "Approval subject exceeds 256 KiB"
        )
    return hashlib.sha256(encoded).hexdigest()


class WorkflowExternalActionService:
    def __init__(self, repository: WorkflowContinuationRepository) -> None:
        self._repository = repository

    def request(
        self,
        *,
        workspace_id: str,
        workflow_id: str,
        run_id: str,
        step_id: str,
        action_kind: str,
        subject: Mapping[str, Any],
        continuation: Mapping[str, Any],
        expires_at: int | None = None,
    ) -> WorkflowContinuationCheckpoint:
        if action_kind not in {
            "printer_transfer",
            "supplier_upload_preview",
            "cart_quote_handoff",
            "local_review",
        }:
            raise WorkflowExternalActionError(
                "external_action_unsupported", "External action is unsupported"
            )
        now = int(time.time())
        return self._repository.create(
            WorkflowContinuationCheckpoint(
                checkpoint_id=f"checkpoint-{secrets.token_hex(12)}",
                workspace_id=workspace_id,
                workflow_id=workflow_id,
                run_id=run_id,
                step_id=step_id,
                action_kind=action_kind,
                subject=dict(subject),
                subject_digest=approval_subject_digest(subject),
                state="pending",
                continuation=dict(continuation),
                actor=None,
                reason=None,
                created_at=now,
                updated_at=now,
                expires_at=expires_at,
                external_action=None,
            )
        )

    def decide(
        self,
        checkpoint_id: str,
        *,
        workspace_id: str,
        expected_subject_digest: str,
        actor: str,
        approved: bool,
        reason: str | None = None,
    ) -> WorkflowContinuationCheckpoint:
        checkpoint = self._required(checkpoint_id, workspace_id)
        self._validate_current(checkpoint, expected_subject_digest)
        target = "approved" if approved else "changes_requested"
        if (
            checkpoint.state == target
            and checkpoint.actor == actor
            and checkpoint.reason == reason
        ):
            return checkpoint
        try:
            return self._repository.transition(
                checkpoint_id,
                expected_state="pending",
                state=target,
                updated_at=int(time.time()),
                actor=actor,
                reason=reason,
            )
        except WorkflowContinuationStateConflict as error:
            raise WorkflowExternalActionError(
                "approval_state_conflict", str(error)
            ) from error

    def lookup(self, checkpoint_id: str) -> WorkflowContinuationCheckpoint:
        checkpoint = self._repository.get(checkpoint_id)
        if checkpoint is None:
            raise WorkflowExternalActionError(
                "approval_not_found", "Approval checkpoint was not found"
            )
        return checkpoint

    def get(
        self, checkpoint_id: str, *, workspace_id: str, run_id: str
    ) -> WorkflowContinuationCheckpoint:
        checkpoint = self._required(checkpoint_id, workspace_id)
        if checkpoint.run_id != run_id:
            raise WorkflowExternalActionError(
                "approval_not_found", "Approval checkpoint was not found"
            )
        if (
            checkpoint.expires_at is not None
            and checkpoint.expires_at <= int(time.time())
            and checkpoint.state in {"pending", "approved"}
        ):
            try:
                checkpoint = self._repository.transition(
                    checkpoint_id,
                    expected_state=checkpoint.state,
                    state="expired",
                    updated_at=int(time.time()),
                )
            except WorkflowContinuationStateConflict:
                checkpoint = self._required(checkpoint_id, workspace_id)
        return checkpoint

    def reconcile(
        self,
        checkpoint_id: str,
        *,
        workspace_id: str,
        run_id: str,
        expected_subject_digest: str,
        outcome: str,
        evidence: Mapping[str, Any],
    ) -> WorkflowContinuationCheckpoint:
        if outcome not in {"dispatched", "not_dispatched", "outcome_unknown"}:
            raise WorkflowExternalActionError(
                "external_action_outcome_invalid", "External action outcome is invalid"
            )
        checkpoint = self.get(checkpoint_id, workspace_id=workspace_id, run_id=run_id)
        if checkpoint.subject_digest != expected_subject_digest:
            raise WorkflowExternalActionError(
                "approval_stale", "Approval subject changed"
            )
        if checkpoint.state != "consumed" or checkpoint.external_action is None:
            raise WorkflowExternalActionError(
                "external_action_not_started",
                "No consumed dispatch authority exists for reconciliation",
            )
        external_action = {
            **checkpoint.external_action,
            "outcome": outcome,
            "reconciled_at": int(time.time()),
            "evidence": dict(evidence),
        }
        try:
            return self._repository.transition(
                checkpoint_id,
                expected_state="consumed",
                state="consumed",
                updated_at=int(time.time()),
                external_action=external_action,
            )
        except WorkflowContinuationStateConflict as error:
            raise WorkflowExternalActionError(
                "external_action_state_conflict", str(error)
            ) from error

    def consume_for_dispatch(
        self,
        checkpoint_id: str,
        *,
        workspace_id: str,
        current_subject: Mapping[str, Any],
        action_id: str,
    ) -> WorkflowContinuationCheckpoint:
        checkpoint = self._required(checkpoint_id, workspace_id)
        current_digest = approval_subject_digest(current_subject)
        if current_digest != checkpoint.subject_digest:
            if checkpoint.state == "approved":
                try:
                    self._repository.transition(
                        checkpoint_id,
                        expected_state="approved",
                        state="stale",
                        updated_at=int(time.time()),
                    )
                except WorkflowContinuationStateConflict:
                    pass
            raise WorkflowExternalActionError(
                "approval_stale", "Approval subject changed before dispatch"
            )
        self._validate_current(checkpoint, current_digest)
        if (
            checkpoint.state == "consumed"
            and checkpoint.external_action
            and checkpoint.external_action.get("action_id") == action_id
            and checkpoint.external_action.get("subject_digest") == current_digest
        ):
            return checkpoint
        if checkpoint.state != "approved":
            raise WorkflowExternalActionError(
                "approval_required", "A current approval is required before dispatch"
            )
        action = {
            "action_id": action_id,
            "subject_digest": current_digest,
            "outcome": "not_dispatched",
            "dispatch_authorized_at": int(time.time()),
        }
        try:
            return self._repository.transition(
                checkpoint_id,
                expected_state="approved",
                state="consumed",
                updated_at=int(time.time()),
                external_action=action,
            )
        except WorkflowContinuationStateConflict as error:
            raise WorkflowExternalActionError(
                "approval_consumed", "Approval was already consumed"
            ) from error

    def _required(
        self, checkpoint_id: str, workspace_id: str
    ) -> WorkflowContinuationCheckpoint:
        checkpoint = self._repository.get(checkpoint_id)
        if checkpoint is None or checkpoint.workspace_id != workspace_id:
            raise WorkflowExternalActionError(
                "approval_not_found", "Approval checkpoint was not found"
            )
        return checkpoint

    def _validate_current(
        self, checkpoint: WorkflowContinuationCheckpoint, expected_digest: str
    ) -> None:
        if expected_digest != checkpoint.subject_digest:
            raise WorkflowExternalActionError(
                "approval_stale", "Approval subject changed"
            )
        if checkpoint.expires_at is not None and checkpoint.expires_at <= int(
            time.time()
        ):
            if checkpoint.state in {"pending", "approved"}:
                try:
                    self._repository.transition(
                        checkpoint.checkpoint_id,
                        expected_state=checkpoint.state,
                        state="expired",
                        updated_at=int(time.time()),
                    )
                except WorkflowContinuationStateConflict:
                    pass
            raise WorkflowExternalActionError(
                "approval_expired", "Approval checkpoint expired"
            )
