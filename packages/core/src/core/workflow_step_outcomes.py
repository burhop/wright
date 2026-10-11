"""Tool-free AI completion policy; no interaction or execution authority."""

from typing import Annotated, Literal

from pydantic import Field, StrictStr, model_serializer, model_validator

from .process_validation import Contract
from .workflow_instructions import WorkflowAssumption


class InvalidStepOutcomeError(ValueError):
    """A model did not supply a usable execution disposition."""


class UnattendedStepOutcome(Contract):
    """Separate execution disposition from the requested engineering document."""

    version: Literal["wright.unattended-step/1"]
    status: Literal["completed", "blocked", "error"]
    response: Annotated[StrictStr, Field(min_length=1, max_length=16_777_216)]
    reason: (
        Literal["input_required", "capability_unavailable", "execution_failed"] | None
    )
    assumptions: Annotated[tuple[WorkflowAssumption, ...], Field(max_length=256)] = ()

    @model_serializer(mode="wrap")
    def omit_empty_assumptions(self, handler):
        data = handler(self)
        if not self.assumptions:
            data.pop("assumptions", None)
        return data

    @model_validator(mode="after")
    def valid_disposition(self):
        if not self.response.strip():
            raise ValueError("An outcome requires a nonempty response")
        if (self.status == "completed") != (self.reason is None):
            raise ValueError("Only completed outcomes may omit a failure reason")
        return self
