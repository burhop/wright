from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from core.engineering_scenarios import AssertionState, EngineeringScenarioError
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from workspace_service.engineering_scenario_artifacts import normalize_artifact
from workspace_service.engineering_scenario_assertions import (
    EngineeringAssertionRegistry,
)
from workspace_service.engineering_scenario_catalog_service import (
    EngineeringScenarioCatalog,
)


FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "engineering_scenario_mcp.py"
)


def _parameters(profile: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=[
            str(FIXTURE),
            "--scenario",
            "structural-bracket",
            "--server",
            "fea",
            "--tool",
            "solve_static",
            "--run-id",
            "fixture-profile-run",
            "--profile",
            profile,
        ],
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "profile",
    ["malformed_artifact", "unit_mismatch", "domain_failure", "cleanup_residue"],
)
async def test_fault_profiles_use_the_real_mcp_protocol(profile) -> None:
    progress = []
    async with stdio_client(_parameters(profile)) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            listed = await session.list_tools()
            assert [tool.name for tool in listed.tools] == ["solve_static"]
            result = await session.call_tool(
                "solve_static",
                {"fixture": "structural-bracket"},
                progress_callback=lambda value, total, message: progress.append(
                    (value, total, message)
                ),
            )

    structured = result.structuredContent
    assert structured is not None
    artifact = structured["artifact"]
    if profile == "malformed_artifact":
        with pytest.raises(EngineeringScenarioError) as error:
            normalize_artifact(artifact)
        assert error.value.code == "artifact_schema_invalid"
    elif profile == "unit_mismatch":
        normalized = normalize_artifact(artifact)
        definition = next(
            value
            for value in EngineeringScenarioCatalog()
            .get("structural-bracket")
            .document["assertions"]
            if value["assertion_id"] == "stress-limit"
        )
        result = EngineeringAssertionRegistry().evaluate(
            definition, {normalized.artifact_id: normalized}
        )
        assert result.state == AssertionState.ERROR
        assert result.reason_code == "unit_dimension_mismatch"
    elif profile == "domain_failure":
        normalized = normalize_artifact(artifact)
        definition = next(
            value
            for value in EngineeringScenarioCatalog()
            .get("structural-bracket")
            .document["assertions"]
            if value["assertion_id"] == "fea-converged"
        )
        result = EngineeringAssertionRegistry().evaluate(
            definition, {normalized.artifact_id: normalized}
        )
        assert result.state == AssertionState.FAIL
        assert result.reason_code == "solver_not_converged"
    else:
        assert structured["cleanup"] == {
            "state": "residue",
            "kinds": ["temporary_file"],
            "recovery": "Inspect and remove the bounded disposable fixture residue.",
        }
    assert progress and progress[0][0] == 0.5


def test_delayed_fixture_acknowledges_protocol_cancellation() -> None:
    command = [
        sys.executable,
        str(FIXTURE),
        "--scenario",
        "structural-bracket",
        "--server",
        "fea",
        "--tool",
        "solve_static",
        "--run-id",
        "fixture-cancel-run",
        "--profile",
        "delay",
        "--delay-seconds",
        "30",
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    assert process.stdin is not None and process.stdout is not None
    try:
        process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1"},
                    },
                }
            )
            + "\n"
        )
        process.stdin.flush()
        assert json.loads(process.stdout.readline())["id"] == 1
        process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "solve_static",
                        "arguments": {"fixture": "structural-bracket"},
                    },
                }
            )
            + "\n"
        )
        process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/cancelled",
                    "params": {"requestId": 2, "reason": "test cancellation"},
                }
            )
            + "\n"
        )
        started = time.perf_counter()
        process.stdin.flush()
        response = json.loads(process.stdout.readline())
        assert time.perf_counter() - started < 1.0
        assert response == {
            "jsonrpc": "2.0",
            "id": 2,
            "error": {"code": -32800, "message": "Request cancelled"},
        }
    finally:
        process.terminate()
        process.wait(timeout=5)
