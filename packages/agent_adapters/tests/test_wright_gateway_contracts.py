from agent_adapters.gateway import (
    WRIGHT_GATEWAY_PROTOCOL,
    WrightGatewayProfile,
    build_wright_gateway_args,
)


def test_wright_gateway_profile_builds_mcp_server_config():
    profile = WrightGatewayProfile(
        provider_name="fake-agent",
        server_name="wright-gateway",
        command="uv",
        args=build_wright_gateway_args("/workspace"),
        terminal_cwd="/workspace",
    )

    assert profile.protocol == WRIGHT_GATEWAY_PROTOCOL
    assert profile.mcp_server_config() == {
        "command": "uv",
        "args": [
            "run",
            "--project",
            "/workspace",
            "python",
            "-m",
            "tool_registry.gateway",
        ],
    }
    assert profile.terminal_config() == {"cwd": "/workspace"}


def test_wright_gateway_profile_does_not_require_hermes_paths():
    profile = WrightGatewayProfile(
        provider_name="fake-agent",
        server_name="wright-gateway",
        command="uv",
        args=build_wright_gateway_args("/workspace"),
        terminal_cwd="/workspace",
    )

    values = [
        profile.provider_name,
        profile.server_name,
        profile.workspace_context_filename or "",
        *profile.args,
    ]
    assert not any("hermes" in value.lower() for value in values)
