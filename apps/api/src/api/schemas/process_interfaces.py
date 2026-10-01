"""Transport envelopes; shared process contracts stay owned by core."""

from pydantic import Field
from typing import Literal

from core.process_interactions import (
    ArtifactRef,
    InputBinding,
    Locator,
    NavigationTarget,
    InlineJSON,
)
from core.process_validation import Contract, Digest, Identifier


class ProcessSourceRequest(Contract):
    session_id: Identifier
    path: Locator
    expected_storage_digest: Digest


class SetProcessInputsRequest(ProcessSourceRequest):
    bindings: tuple[InputBinding, ...] = Field(default=(), max_length=256)


class ProcessReadinessRequest(ProcessSourceRequest):
    input_snapshot_id: Identifier


class ProcessRunRequest(ProcessReadinessRequest):
    request_id: Identifier
    expected_input_digest: Digest
    integration_policy_digest: Digest | None = None


class ProcessCancelRequest(ProcessSourceRequest):
    request_id: Identifier


class ProcessInputResponseRequest(ProcessSourceRequest):
    subject_digest: Digest
    value: InlineJSON
    request_id: Identifier


class ProcessReviewDecisionRequest(ProcessSourceRequest):
    subject_digest: Digest
    decision: Literal["approved", "changes_requested"]
    reason: str = Field(default="", max_length=2000, strict=True)
    request_id: Identifier


class ProcessActionRequest(ProcessSourceRequest):
    subject_digest: Digest
    request_id: Identifier


class ProcessRepresentationRequest(ProcessSourceRequest):
    reference: ArtifactRef
    run_id: Identifier | None = None
    input_snapshot_id: Identifier | None = None


class ProcessNavigationRequest(ProcessSourceRequest):
    target: NavigationTarget


class ProcessUIAuthoringRequest(ProcessSourceRequest):
    request_id: Identifier
    instruction: str = Field(strict=True, min_length=1, max_length=16384)
    title: str = Field(
        default="Process interface", strict=True, min_length=1, max_length=512
    )
    ui_id: Identifier | None = None
    base_revision: Identifier | None = None


class ProcessUISaveRequest(ProcessSourceRequest):
    job_id: Identifier
    source_digest: Digest
    manifest_digest: Digest
    bundle_digest: Digest
    expected_active_revision: Identifier | None


class ProcessUIActivateRequest(ProcessSourceRequest):
    revision_id: Identifier
    expected_active_revision: Identifier | None


class ProcessUIPresentRequest(ProcessSourceRequest):
    request_id: Identifier
    revision_id: Identifier | None = None
    run_id: Identifier | None = None


class ProcessUIPreviewRequest(ProcessSourceRequest):
    request_id: Identifier
    run_id: Identifier | None = None


class ProcessUICloseRequest(ProcessSourceRequest):
    surface_id: Identifier
    presentation_id: Identifier
