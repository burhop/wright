from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from core.workflow_instructions import checked_instruction_text

from data_vault import WorkspaceRepository


def public_git_remote(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) > 2048 or any(ord(char) < 33 for char in value):
        raise ValueError("Use a repository URL without credentials or spaces")
    if re.fullmatch(r"[A-Za-z0-9._-]+@[A-Za-z0-9.-]+:[A-Za-z0-9_./-]+", value):
        return value
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"https", "ssh"}
        or not parsed.hostname
        or parsed.password
        or parsed.query
        or parsed.fragment
        or (parsed.scheme == "https" and parsed.username)
    ):
        raise ValueError(
            "Use HTTPS or SSH without passwords, tokens, query or fragment"
        )
    return value


class WorkspaceConfigurationChanges(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    git_remote_url: str | None = Field(default=None, max_length=2048)
    git_username: str | None = Field(default=None, max_length=256)
    workspace_prompt: str | None = Field(default=None, max_length=131072)
    git_large_file_threshold: int | None = Field(
        default=None, ge=1, le=9007199254740991
    )

    @field_validator("git_remote_url")
    @classmethod
    def repository_url(cls, value):
        return public_git_remote(value)

    @field_validator("git_username")
    @classmethod
    def username(cls, value):
        if value is not None and any(ord(char) < 32 for char in value):
            raise ValueError("Use a public Git username without control characters")
        return value

    @field_validator("workspace_prompt")
    @classmethod
    def prompt(cls, value):
        return (
            checked_instruction_text(value, empty=True) if value is not None else None
        )

    @model_validator(mode="after")
    def nonempty_changes(self):
        if not self.model_fields_set:
            raise ValueError("Choose a setting to update")
        return self


def configuration_view(value: dict[str, Any]) -> dict[str, Any]:
    """Keep legacy/private remote URLs out of the desktop transport."""
    try:
        remote = public_git_remote(value["git_remote_url"])
        hidden = False
    except ValueError:
        remote, hidden = None, True
    return {**value, "git_remote_url": remote, "remote_hidden": hidden}


class WorkspaceContextUseCases:
    def __init__(self, repository: WorkspaceRepository) -> None:
        self.repository = repository

    def config(self, local_path: str) -> dict[str, Any] | None:
        workspace = self.repository.get_by_path(local_path)
        if workspace:
            workspace = {
                **workspace,
                "has_token": self.repository.has_git_token(workspace["workspace_id"]),
            }
        return workspace

    def configuration(self, workspace_id: str) -> dict[str, Any]:
        return configuration_view(self.repository.configuration(workspace_id))

    def patch_configuration(
        self,
        workspace_id: str,
        *,
        expected_revision: str,
        changes: WorkspaceConfigurationChanges,
    ) -> dict[str, Any]:
        return configuration_view(
            self.repository.patch_configuration(
                workspace_id,
                expected_revision=expected_revision,
                changes=changes.model_dump(exclude_unset=True),
            )
        )

    def save(self, workspace_id: str, context_data: Any) -> None:
        self.repository.save_context(workspace_id, json.dumps(context_data))

    def load(self, workspace_id: str) -> dict[str, Any] | None:
        row = self.repository.load_context(workspace_id)
        if not row:
            return None
        try:
            context_data = json.loads(row["context_data"])
        except (TypeError, json.JSONDecodeError):
            context_data = row["context_data"]
        return {
            "workspace_id": workspace_id,
            "context_data": context_data,
            "updated_at": row.get("updated_at"),
        }
