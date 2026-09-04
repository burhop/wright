"""Closed native transport envelopes; domain semantics use the shared schema."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NativeEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CreateNativeProcess(NativeEnvelope):
    definition: dict[str, Any]
    presentation: dict[str, Any]
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


class SaveNativeProcess(CreateNativeProcess):
    expected_token: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]+$")


class NativeBinding(NativeEnvelope):
    server_id: str = Field(min_length=1, max_length=200)
    tool_name: str = Field(min_length=1, max_length=200)
    input_schema_digest: str = Field(
        min_length=64, max_length=64, pattern=r"^[0-9a-f]+$"
    )
    output_schema_digest: str = Field(
        min_length=64, max_length=64, pattern=r"^[0-9a-f]+$"
    )


class CheckNativeProcess(NativeEnvelope):
    definition: dict[str, Any]
    bindings: dict[str, NativeBinding] = Field(default_factory=dict, max_length=100)


class StartNativeRun(NativeEnvelope):
    expected_token: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]+$")
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    bindings: dict[str, NativeBinding] = Field(default_factory=dict, max_length=100)
    derived_from_run_id: str | None = Field(default=None, min_length=1, max_length=80)
    timeout_seconds: int = Field(default=60, ge=1, le=300)


class EmptyNativeRequest(NativeEnvelope):
    pass
