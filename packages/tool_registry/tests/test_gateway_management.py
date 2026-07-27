from tool_registry.gateway_management import GatewayManagementTools
from tool_registry.gateway_models import GatewaySessionContext


def test_management_tools_are_task_oriented_read_only_and_bound() -> None:
    management = GatewayManagementTools(
        server_status=lambda session: {
            "servers": [],
            "workspace_id": session.workspace_id,
        },
        catalog_status=lambda session: {"catalog": "ready"},
        workspace_status=lambda session: {"workspace_id": session.workspace_id},
    )
    tools = management.tools()
    assert [tool.name for tool in tools] == [
        "wright__server_status",
        "wright__catalog_status",
        "wright__workspace_status",
    ]
    assert all(tool.annotations["readOnlyHint"] is True for tool in tools)
    assert all(tool.provenance["source"] == "built-in" for tool in tools)
    bound = GatewaySessionContext("s1", "p1", "w1", "/w1", "stdio")
    assert management.call(bound, "wright__workspace_status") == {"workspace_id": "w1"}
