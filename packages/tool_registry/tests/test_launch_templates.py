from __future__ import annotations

import os

import pytest

from tool_registry.launch_templates import (
    LaunchTemplateError,
    render_launch_configuration,
)


def test_renders_exact_canonical_workspace_in_command_and_environment(tmp_path):
    workspace = tmp_path / "nested" / ".." / "workspace with spaces & symbols"

    command, environment = render_launch_configuration(
        ["example-mcp", "--root={workspace.path}", "literal;$(unchanged)"],
        {"SERVER_ROOT": "{workspace.path}", "MODE": "literal"},
        str(workspace),
        server_id="example",
    )

    expected = os.path.realpath(os.path.abspath(workspace))
    assert command == ["example-mcp", f"--root={expected}", "literal;$(unchanged)"]
    assert environment == {"SERVER_ROOT": expected, "MODE": "literal"}


def test_two_differently_named_servers_render_identically(tmp_path):
    configured = (["server", "{workspace.path}"], {"ROOT": "{workspace.path}"})

    first = render_launch_configuration(*configured, str(tmp_path), server_id="alpha")
    second = render_launch_configuration(
        *configured, str(tmp_path), server_id="totally-different"
    )

    assert first == second


def test_unbound_configuration_is_unchanged_without_placeholders():
    command = ["server", "--mode", "normal"]
    environment = {"MODE": "normal"}

    rendered = render_launch_configuration(
        command, environment, None, server_id="unbound"
    )

    assert rendered == (command, environment)
    assert rendered[0] is not command
    assert rendered[1] is not environment


@pytest.mark.parametrize(
    ("command", "launch_env", "field"),
    [
        (["server", "{workspace.root}"], {}, "command[1]"),
        (["server"], {"ROOT": "{workspace.root}"}, "launch_env.ROOT"),
    ],
)
def test_unknown_placeholder_is_rejected(command, launch_env, field):
    with pytest.raises(LaunchTemplateError) as caught:
        render_launch_configuration(
            command, launch_env, "/workspace", server_id="example"
        )

    assert caught.value.category == "invalid_launch_template"
    assert caught.value.server_id == "example"
    assert caught.value.field == field
    assert "{workspace.path}" in str(caught.value)


def test_workspace_placeholder_requires_a_bound_workspace():
    with pytest.raises(LaunchTemplateError, match="bound workspace"):
        render_launch_configuration(
            ["server", "{workspace.path}"], {}, None, server_id="example"
        )


def test_string_command_workspace_placeholder_is_rejected():
    with pytest.raises(LaunchTemplateError, match="command array"):
        render_launch_configuration(
            "server --root {workspace.path}",
            {},
            "/workspace",
            server_id="example",
        )
