import json
import subprocess

import pytest

from tool_registry import McpServer
from tool_registry.validation_executor import DockerCleanContainerExecutor
from tool_registry.validation_plan import build_validation_plan


@pytest.mark.asyncio
async def test_docker_executor_records_partial_when_gateway_probe_not_run():
    captured = {}

    def fake_runner(command, *, input, capture_output, text, timeout):
        captured["command"] = command
        captured["input"] = input
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "status": "passed",
                    "steps": [
                        {
                            "name": "docker.clean_container",
                            "status": "passed",
                            "output": "python=3.12",
                        }
                    ],
                    "protocol_probes": [
                        {
                            "name": "initialize",
                            "status": "passed",
                            "output": "{}",
                        },
                        {
                            "name": "tools/list",
                            "status": "passed",
                            "output": '{"tools":[]}',
                        },
                    ],
                    "gateway_proxy_probe": [],
                    "diagnostics": "Direct probes ran.",
                }
            ),
            stderr="",
        )

    plan = build_validation_plan(
        McpServer(
            server_id="clean-container-cad",
            name="Clean Container CAD",
            type="stdio",
            command=["python", "-m", "server"],
            is_active=False,
            status="inactive",
            created_at=1,
            updated_at=1,
        )
    )

    evidence = await DockerCleanContainerExecutor(
        "ubuntu-x64", runner=fake_runner
    ).execute(plan)

    assert captured["command"][:3] == ["docker", "run", "--rm"]
    assert "python3" in captured["command"]
    assert "initialize" in captured["input"]
    assert evidence.container_image == "wright-agent:latest"
    assert evidence.status == "partial"
    assert evidence.follow_up_required is True
    assert "gateway proxy probes were not executed" in evidence.diagnostics
