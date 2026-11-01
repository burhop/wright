"""Closed presentation request models shared by fixed and workspace file modes."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class WorkspaceDocument(StrictModel):
    workspace_id: str = Field(min_length=1, max_length=100)
    session_id: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=4096)
    expected_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class FileInput(StrictModel):
    name: str = Field(min_length=1, max_length=255)
    resourceUri: str = Field(min_length=1, max_length=4096)


class Capabilities(StrictModel):
    files: bool
    resources: bool


class ProbeObservation(StrictModel):
    instance_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    stage: Literal[
        "opened",
        "rendered",
        "activated",
        "hidden",
        "teardown",
        "probe",
        "draft-changed",
    ]
    capabilities: Capabilities | None = None
    observed_source_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    editor_has_unsaved_changes: bool | None = None
    resume: WorkspaceDocument | None = None
