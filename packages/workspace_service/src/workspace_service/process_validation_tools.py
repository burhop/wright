"""Thin BaseTool adapters; gateway policy supplies the workspace authority."""

import asyncio
from threading import Event
from typing import Annotated

from pydantic import Field

from core.process_validation import (
    AssessmentReference,
    FindingPage,
    Contract,
    Identifier,
    ValidationRequest,
    canonical_json,
)
from core.tools import BaseTool
from .process_validation.application import ValidationApplication, assessment_reference
from .process_validation.configuration import ProfileLocation


class EvaluateArguments(Contract):
    request: ValidationRequest
    profile: ProfileLocation


class ReadArguments(Contract):
    assessment_id: Identifier
    cursor: Annotated[int, Field(strict=True, ge=0)] = 0
    limit: Annotated[int, Field(strict=True, ge=1, le=20)] = 20


class ProcessValidationTool(BaseTool):
    def __init__(
        self,
        application: ValidationApplication,
        operation="evaluate",
        *,
        cancelled=None,
    ):
        if operation not in {"evaluate", "read"}:
            raise ValueError("Unknown validation tool operation")
        self.application, self.operation = application, operation
        self.cancelled = cancelled or Event()

    @property
    def name(self):
        return "wright_validation__" + self.operation

    @property
    def description(self):
        return (
            "Inspect exact previous-step output using a pinned validation profile. Returns measured compliance and a saved assessment; never runs or repairs the producer."
            if self.operation == "evaluate"
            else "Read a workspace validation assessment and bounded findings. Historical passes may be superseded; use is_current and release_eligible."
        )

    @property
    def input_schema(self):
        return (
            EvaluateArguments if self.operation == "evaluate" else ReadArguments
        ).model_json_schema()

    @property
    def output_schema(self):
        return (
            AssessmentReference if self.operation == "evaluate" else FindingPage
        ).model_json_schema()

    async def execute(self, arguments, *, context):
        if context.workspace_id != self.application.workspace_id:
            raise PermissionError("Tool context does not own this workspace")
        if self.operation == "read":
            args = ReadArguments.model_validate(arguments)
            assessment, current = self.application.read(args.assessment_id)
            result = assessment_reference(assessment, current)
            items = []
            for finding in assessment.findings[args.cursor : args.cursor + args.limit]:
                candidate = finding.model_dump(mode="json")
                if len(canonical_json([*items, candidate]).encode()) > 64 * 1024:
                    if not items:
                        raise ValueError(
                            "Finding exceeds inline capacity; use the authorized JSON export"
                        )
                    break
                items.append(candidate)
            end = args.cursor + len(items)
            result.update(
                findings=items,
                next_cursor=end if end < len(assessment.findings) else None,
            )
            return result
        args = EvaluateArguments.model_validate(arguments)
        request = args.request
        if request.workspace_id != context.workspace_id or request.run_id is not None:
            # An external caller can inspect outputs but cannot replace the
            # canonical runner's gate stream or supply its execution authority.
            raise PermissionError(
                "External validation cannot claim a canonical gate invocation"
            )
        for subject in request.subjects:
            owner = subject.producer
            imported = (
                owner.step_id == "import"
                and owner.run_id == request.invocation_id
                and owner.attempt == 1
            )
            if not imported and not self.application.repository.output_is_current(
                context.workspace_id, subject
            ):
                raise PermissionError(
                    "Producer identity is not a registered current output; use an explicit standalone import"
                )
        work = asyncio.create_task(
            asyncio.to_thread(
                self.application.evaluate,
                request,
                args.profile,
                cancelled=self.cancelled,
            )
        )
        try:
            outcome = await asyncio.shield(work)
        except asyncio.CancelledError:
            self.cancelled.set()
            await asyncio.shield(work)
            raise
        if outcome.assessment is None:
            raise ValueError("Validation attempt has no terminal assessment")
        return assessment_reference(outcome.assessment, outcome.is_current)
