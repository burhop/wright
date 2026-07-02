import pytest

from tool_registry.models import McpServer
from tool_registry.validation_plan import build_validation_plan
from tool_registry.validation_runner import run_lightweight_validation


class FakeProbeClient:
    def __init__(self):
        self.calls = []

    async def initialize(self):
        self.calls.append("initialize")
        return {"serverInfo": {"name": "fake"}}

    async def initialized(self):
        self.calls.append("notifications/initialized")

    async def list_tools(self):
        self.calls.append("tools/list")
        return [{"name": "health_check"}]

    async def call_tool(self, name, arguments):
        self.calls.append(f"tools/call:{name}")
        return {"ok": True, "arguments": arguments}


def make_server():
    return McpServer(
        server_id="fake-server",
        name="Fake Server",
        type="stdio",
        command=["python", "-m", "fake"],
        is_active=False,
        status="inactive",
        created_at=1,
        updated_at=1,
    )


@pytest.mark.asyncio
async def test_lightweight_runner_exercises_mock_mcp_protocol_and_gateway():
    plan = build_validation_plan(
        make_server(),
        environment="local",
        requires_docker=False,
        safe_tool_name="health_check",
        safe_tool_arguments={"ping": True},
    )
    client = FakeProbeClient()
    gateway_client = FakeProbeClient()

    evidence = await run_lightweight_validation(
        plan, client, gateway_client=gateway_client
    )

    assert evidence.status == "passed"
    assert client.calls == [
        "initialize",
        "notifications/initialized",
        "tools/list",
        "tools/call:health_check",
    ]
    assert gateway_client.calls == [
        "tools/list",
        "tools/call:health_check",
    ]
    assert [step.name for step in evidence.steps] == [
        "initialize",
        "notifications/initialized",
        "tools/list",
        "safe_backend_probe",
        "wright_gateway.tools/list",
        "wright_gateway.safe_backend_probe",
    ]


@pytest.mark.asyncio
async def test_lightweight_runner_records_failed_required_probe():
    class FailingClient(FakeProbeClient):
        async def list_tools(self):
            raise RuntimeError("boom")

    plan = build_validation_plan(
        make_server(), environment="local", requires_docker=False
    )

    evidence = await run_lightweight_validation(plan, FailingClient())

    assert evidence.status == "failed"
    assert evidence.steps[-1].name == "tools/list"
    assert evidence.steps[-1].error == "boom"
