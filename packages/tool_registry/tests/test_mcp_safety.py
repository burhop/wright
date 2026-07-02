from tool_registry import EnvVarDefinition, McpServer
from tool_registry.safety import ApprovalContext, McpSafetyPolicy


def _server(**overrides):
    data = {
        "server_id": "server-1",
        "name": "Server One",
        "type": "stdio",
        "command": ["uvx", "server-one"],
        "is_active": False,
        "is_installed": False,
        "status": "inactive",
        "created_at": 1,
        "updated_at": 1,
    }
    data.update(overrides)
    return McpServer(**data)


def test_policy_blocks_catalog_blocked_install():
    decision = McpSafetyPolicy().can_install(
        _server(
            installability_tier="blocked",
            install_blocked_reason="URL missing.",
        )
    )

    assert decision.allowed is False
    assert decision.blocked_by_catalog is True
    assert decision.reason == "URL missing."


def test_policy_requires_approval_for_high_risk_server():
    server = _server(
        risk_level="high",
        approval_gates=["workspace_write_approval"],
    )

    denied = McpSafetyPolicy().can_start(server)
    allowed = McpSafetyPolicy().can_start(
        server,
        ApprovalContext(workspace_approvals={"workspace_write_approval"}),
    )

    assert denied.allowed is False
    assert denied.required_approvals == ["workspace_write_approval"]
    assert allowed.allowed is True


def test_policy_blocks_missing_credentials_for_start_and_call():
    server = _server(
        env_vars=[
            EnvVarDefinition(
                name="API_TOKEN",
                label="API token",
                required=True,
                secret=True,
            )
        ]
    )

    start = McpSafetyPolicy().can_start(
        server, credentials_configured={"API_TOKEN": False}
    )
    call = McpSafetyPolicy().can_call_tool(
        server,
        "dangerous_tool",
        credentials_configured={"API_TOKEN": False},
    )

    assert start.allowed is False
    assert start.missing_credentials == ["API_TOKEN"]
    assert call.allowed is False
    assert call.missing_credentials == ["API_TOKEN"]
    assert call.diagnostics["tool_name"] == "dangerous_tool"


def test_package_manager_use_alone_does_not_require_approval():
    decision = McpSafetyPolicy().can_install(_server(command=["uvx", "safe-mcp"]))

    assert decision.allowed is True
    assert decision.required_approvals == []
