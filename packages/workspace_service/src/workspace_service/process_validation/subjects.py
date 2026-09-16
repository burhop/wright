"""Exact, read-only subject snapshots from an already authorized workspace."""

from __future__ import annotations

import hashlib
from typing import Callable

from core.process_validation import SubjectBinding, ValidationRequest, canonical_json
from core.tracing import traced

from ..workflow_sources import WorkspaceWorkflowSourceStore, WorkflowSourceStorageError
from .readers.base import ReaderContext, SubjectSnapshot, ValidationIssue


class SubjectResolver:
    def __init__(
        self,
        workspace_id: str,
        workspace_root: str,
        *,
        verify_binding: Callable[[SubjectBinding], bool] | None = None,
        provider_readback: Callable[[SubjectBinding, ReaderContext], bytes]
        | None = None,
    ):
        self.workspace_id = workspace_id
        self.store = WorkspaceWorkflowSourceStore(workspace_root)
        self.verify_binding = verify_binding
        self.provider_readback = provider_readback

    @traced("workspace.process_validation.snapshot")
    def snapshot(
        self,
        request: ValidationRequest,
        subject: SubjectBinding,
        context: ReaderContext,
    ) -> SubjectSnapshot:
        context.checkpoint()
        byte_limit = min(
            context.budget.max_bytes, context.budget.memory_limit_mb * 1024 * 1024 // 8
        )
        if request.workspace_id != self.workspace_id or subject not in request.subjects:
            raise PermissionError(
                "Validation subject is outside the authorized request"
            )
        if request.run_id and (
            self.verify_binding is None or not self.verify_binding(subject)
        ):
            raise ValidationIssue(
                "subject.provenance",
                "Producer attempt/output binding is not verified by the runtime.",
                category="stale_subject",
                action="refresh_subject",
            )
        if subject.kind == "value":
            content = (
                subject.value.encode("utf-8")
                if subject.encoding == "raw-bytes"
                else canonical_json(subject.value).encode("utf-8")
            )
        elif subject.kind == "file":
            try:
                content = self.store.read_artifact_bytes(
                    subject.locator, max_bytes=byte_limit
                )
            except FileNotFoundError as exc:
                raise ValidationIssue(
                    "subject.missing",
                    "Bound output is not available in this workspace.",
                ) from exc
            except (ValueError, WorkflowSourceStorageError) as exc:
                raise ValidationIssue(
                    "subject.unreadable",
                    "Bound output cannot be read safely within the configured limits.",
                ) from exc
        else:
            if self.provider_readback is None:
                raise ValidationIssue(
                    "reader.provider_unavailable",
                    "Pinned native readback is unavailable.",
                    category="capability_unavailable",
                    action="restore_capability",
                )
            content = self.provider_readback(subject, context)
            if not isinstance(content, bytes):
                raise ValidationIssue(
                    "reader.provider_contract",
                    "Native reader returned an invalid snapshot.",
                    state="error",
                    category="validator_error",
                    action="retry_validation",
                )
        context.checkpoint()
        if len(content) > byte_limit:
            raise ValidationIssue(
                "subject.byte_limit",
                "Bound output exceeds the configured byte limit.",
                category="capability_unavailable",
                action="restore_capability",
            )
        if hashlib.sha256(content).hexdigest() != subject.sha256:
            raise ValidationIssue(
                "subject.changed",
                "Output content differs from the bound producer revision.",
                category="stale_subject",
                action="refresh_subject",
            )
        return SubjectSnapshot(subject, content)

    def assert_unchanged(self, request, snapshot, context):
        current = self.snapshot(request, snapshot.subject, context)
        if current.content != snapshot.content:
            raise ValidationIssue(
                "subject.changed",
                "Output changed during inspection.",
                category="stale_subject",
                action="refresh_subject",
            )
