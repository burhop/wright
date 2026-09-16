"""Thin BaseTool adapters; gateway policy supplies the workspace authority."""

import asyncio
from threading import Event
from typing import Annotated, Literal

from pydantic import Field

from core.process_validation import (
    AssessmentReference,
    FindingPage,
    Contract,
    Identifier,
    ValidationReport,
    ValidationRequest,
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


class GetArguments(Contract):
    assessment_id: Identifier


class ExportArguments(GetArguments):
    format: Literal["json", "markdown", "csv"]


class ExportPayload(Contract):
    format: Literal["json", "markdown", "csv"]
    media_type: Identifier
    filename: Identifier
    content: Annotated[str, Field(max_length=16 * 1024 * 1024)]


class ProcessValidationTool(BaseTool):
    def __init__(
        self,
        application: ValidationApplication,
        operation="evaluate",
        *,
        cancelled=None,
    ):
        if operation not in {"evaluate", "read", "get", "export"}:
            raise ValueError("Unknown validation tool operation")
        self.application, self.operation = application, operation
        self.cancelled = cancelled or Event()

    @property
    def name(self):
        return "wright_validation__" + self.operation

    @property
    def description(self):
        return {
            "evaluate": "Inspect exact previous-step output using a pinned validation profile. Returns measured compliance and a saved assessment; never runs or repairs the producer.",
            "read": "List bounded findings from a workspace validation assessment. Historical passes may be superseded; use is_current and release_eligible.",
            "get": "Get a complete report envelope for a workspace validation assessment, including query-time currentness and requirements traceability.",
            "export": "Export one workspace validation assessment as JSON, readable Markdown or a requirements traceability CSV.",
        }[self.operation]

    @property
    def input_schema(self):
        return {
            "evaluate": EvaluateArguments,
            "read": ReadArguments,
            "get": GetArguments,
            "export": ExportArguments,
        }[self.operation].model_json_schema()

    @property
    def output_schema(self):
        return {
            "evaluate": AssessmentReference,
            "read": FindingPage,
            "get": ValidationReport,
            "export": ExportPayload,
        }[self.operation].model_json_schema()

    async def execute(self, arguments, *, context):
        if context.workspace_id != self.application.workspace_id:
            raise PermissionError("Tool context does not own this workspace")
        if self.operation == "read":
            args = ReadArguments.model_validate(arguments)
            return self.application.list_findings(
                args.assessment_id, cursor=args.cursor, limit=args.limit
            ).model_dump(mode="json")
        if self.operation == "get":
            args = GetArguments.model_validate(arguments)
            return self.application.get_result(args.assessment_id).model_dump(
                mode="json"
            )
        if self.operation == "export":
            args = ExportArguments.model_validate(arguments)
            exported = self.application.export_result(args.assessment_id, args.format)
            return ExportPayload(
                format=exported.format,
                media_type=exported.media_type,
                filename=exported.filename,
                content=exported.content.decode("utf-8"),
            ).model_dump(mode="json")
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
