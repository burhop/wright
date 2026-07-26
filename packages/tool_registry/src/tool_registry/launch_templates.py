from __future__ import annotations

import os
import re
from collections.abc import Mapping, Sequence

WORKSPACE_PATH_PLACEHOLDER = "{workspace.path}"
_PLACEHOLDER = re.compile(r"\{[^{}]+\}")


class LaunchTemplateError(ValueError):
    category = "invalid_launch_template"

    def __init__(self, server_id: str, field: str, message: str) -> None:
        self.server_id = server_id
        self.field = field
        super().__init__(
            f"Invalid launch template for server '{server_id}' at {field}: {message}. "
            f"The only supported placeholder is {WORKSPACE_PATH_PLACEHOLDER}."
        )


def render_launch_configuration(
    command: str | Sequence[str],
    launch_env: Mapping[str, str],
    workspace_path: str | None,
    *,
    server_id: str,
) -> tuple[str | list[str], dict[str, str]]:
    """Render trusted launch data without invoking a shell or general formatter."""
    canonical_workspace = (
        os.path.realpath(os.path.abspath(workspace_path)) if workspace_path else None
    )
    rendered_environment = {
        str(key): _render_value(
            str(value),
            workspace_path=canonical_workspace,
            server_id=server_id,
            field=f"launch_env.{key}",
        )
        for key, value in launch_env.items()
    }

    if isinstance(command, str):
        _reject_unknown_placeholders(command, server_id=server_id, field="command")
        if WORKSPACE_PATH_PLACEHOLDER in command:
            raise LaunchTemplateError(
                server_id,
                "command",
                "workspace placeholders require a command array to preserve argument boundaries",
            )
        return command, rendered_environment

    rendered_command = [
        _render_value(
            str(value),
            workspace_path=canonical_workspace,
            server_id=server_id,
            field=f"command[{index}]",
        )
        for index, value in enumerate(command)
    ]
    return rendered_command, rendered_environment


def _render_value(
    value: str,
    *,
    workspace_path: str | None,
    server_id: str,
    field: str,
) -> str:
    _reject_unknown_placeholders(value, server_id=server_id, field=field)
    if WORKSPACE_PATH_PLACEHOLDER not in value:
        return value
    if workspace_path is None:
        raise LaunchTemplateError(
            server_id,
            field,
            "workspace placeholder requires an authenticated bound workspace",
        )
    return value.replace(WORKSPACE_PATH_PLACEHOLDER, workspace_path)


def _reject_unknown_placeholders(value: str, *, server_id: str, field: str) -> None:
    unknown = [
        token
        for token in _PLACEHOLDER.findall(value)
        if token != WORKSPACE_PATH_PLACEHOLDER
    ]
    if unknown:
        raise LaunchTemplateError(
            server_id,
            field,
            f"unsupported placeholder {unknown[0]}",
        )
