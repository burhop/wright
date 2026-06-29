from tool_registry.mcp_validation import classify_server
from tool_registry.models import McpServer


def make_server(**updates):
    values = {
        "server_id": "server",
        "name": "Server",
        "type": "stdio",
        "is_active": False,
        "status": "inactive",
        "created_at": 1,
        "updated_at": 1,
    }
    values.update(updates)
    return McpServer(**values)


def test_blocked_server_is_not_validated():
    server = make_server(
        installability_tier="blocked",
        install_blocked_reason="URL missing",
    )

    result = classify_server(server, environment="ubuntu-linux-x64-container")

    assert result.status == "blocked"
    assert result.installability_tier == "blocked"
    assert "URL missing" in result.message


def test_missing_host_dependency_is_expected_limitation():
    server = make_server(
        installability_tier="might_work",
        host_software_required=["DefinitelyMissingCadHost"],
    )

    result = classify_server(server, environment="ubuntu-linux-x64-container")

    assert result.status == "dependency_missing"
    assert result.installability_tier == "might_work"
    assert result.missing_dependencies == ["DefinitelyMissingCadHost"]


def test_passed_seed_remains_tested():
    server = make_server(
        installability_tier="tested",
        validation_result={
            "status": "passed",
            "message": "Already validated",
            "missing_dependencies": [],
        },
    )

    result = classify_server(server, environment="ubuntu-linux-x64-container")

    assert result.status == "passed"
    assert result.installability_tier == "tested"
