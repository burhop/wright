"""Tool-free AI completion policy; no interaction or execution authority."""

from typing import Annotated, Literal

from pydantic import Field, StrictStr, model_validator

from .process_validation import Contract


UNATTENDED_STEP_POLICY = (
    "This is an unattended process step. Use the supplied requirements, explicit "
    "defaults and upstream evidence. Do not ask the user questions, invent a human "
    "interaction, or silently fill missing engineering requirements. A later "
    "declared human-input or review step is handled by Wright, not by this response. "
    "If completion requires an additional user choice, report status blocked with "
    "reason input_required; explain the missing dependency as a diagnostic. Do not "
    "perform unrelated operations or claim completion. This diagnostic does not "
    "authorize retrying completed operations."
)


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

    @model_validator(mode="after")
    def valid_disposition(self):
        if not self.response.strip():
            raise ValueError("An outcome requires a nonempty response")
        if (self.status == "completed") != (self.reason is None):
            raise ValueError("Only completed outcomes may omit a failure reason")
        return self
