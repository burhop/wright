from tool_registry.models import McpServer
from tool_registry.validation_plan import build_validation_plan


def make_server(**updates):
    values = {
        "server_id": "server",
        "name": "Server",
        "type": "stdio",
        "command": ["uvx", "server"],
        "is_active": False,
        "status": "inactive",
        "created_at": 1,
        "updated_at": 1,
    }
    values.update(updates)
    return McpServer(**values)


def test_blocked_metadata_preflight_produces_blocked_plan():
    server = make_server(
        installability_tier="blocked",
        install_blocked_reason="URL missing",
    )

    plan = build_validation_plan(
        server, environment="ubuntu-linux-x64-container", requires_docker=True
    )

    assert plan.preflight["status"] == "blocked"
    assert plan.requires_docker is True
    assert [probe.method for probe in plan.protocol_probes] == [
        "initialize",
        "notifications/initialized",
        "tools/list",
    ]
    assert plan.gateway_probe[0].name == "wright_gateway.tools/list"


def test_missing_host_dependency_stays_preflight_dependency_missing():
    server = make_server(host_software_required=["DefinitelyMissingCadHost"])

    plan = build_validation_plan(
        server, environment="ubuntu-linux-x64-container", requires_docker=False
    )

    assert plan.execution_mode == "local-mock"
    assert plan.preflight["status"] == "dependency_missing"
    assert plan.preflight["missing_dependencies"] == ["DefinitelyMissingCadHost"]


def test_plan_records_network_credentials_and_safe_probe_requirements():
    server = make_server(
        type="sse",
        command="https://example.com/mcp",
        credentials_required=["API_TOKEN"],
    )

    plan = build_validation_plan(
        server,
        environment="ubuntu-linux-x64-container",
        requires_docker=True,
        safe_tool_name="health_check",
    )

    assert plan.requires_network is True
    assert plan.requires_credentials is True
    assert plan.safe_backend_probe.method == "tools/call"
    assert plan.gateway_probe[-1].name == "wright_gateway.safe_backend_probe"
