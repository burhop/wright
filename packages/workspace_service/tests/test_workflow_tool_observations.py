"""Actual provider observations must not be replaced by model-authored claims."""

import asyncio
import hashlib
import json
from dataclasses import asdict

import pytest
from tool_registry.gateway_models import GatewayToolResult

from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workflow_tool_observations import response_from_observations
from .test_workflow_ai_task import call, done, source
from .test_workflow_source_execution import task
from .test_workflow_optional_research import run


def plan(**settings):
    values = dict(
        fmt="json",
        authoring_template="mcp-task",
        mcp_server="docs",
        mcp_response_source="tool_observations",
    )
    values.update(settings)
    return compile_prompt_workflow(source(task("inspect", **values)))


def test_actual_response_saved_instead_of_model_claim(tmp_path):
    workflow = plan()
    execution, gateway, _, _ = run(
        tmp_path,
        workflow,
        [call(), done('{"invented": "not provider evidence"}')],
        result=GatewayToolResult(
            content=(), structured_content={"documents": [{"title": "Found"}]}
        ),
    )
    result = asyncio.run(execution)
    record = result["steps"][0]
    saved = json.loads((tmp_path / result["output_path"]).read_text())
    observed = saved["observations"]
    assert observed["complete"] is True
    assert observed["value"][0]["result"] == {"documents": [{"title": "Found"}]}
    assert observed["value"][0]["call_number"] == 1
    assert (
        observed["value"][0]["schema_digest"]
        == record["tool_calls"][0]["schema_digest"]
    )
    assert "invented" not in json.dumps(saved)
    assert (
        record["model_summary"]["sha256"]
        == hashlib.sha256(b'{"invented": "not provider evidence"}').hexdigest()
    )
    assert len(gateway.calls) == 1
    assert asdict(workflow.steps[0])["mcp_response_source"] == "tool_observations"


@pytest.mark.parametrize(
    "settings",
    [
        {"fmt": "text"},
        {"mcp_response_source": "unknown"},
        {"mcp_response_source": {}},
        {"authoring_template": "ai-prompt", "mcp_server": ""},
        {"mcp_completion_policy": "supplied_inputs_or_tools"},
    ],
)
def test_incompatible_source_blocks_before_execution(settings):
    with pytest.raises(WorkflowSourceExecutionError):
        plan(**settings)


def test_redaction_and_truncation_are_explicit():
    value = json.loads(
        response_from_observations(
            "provider",
            [
                {
                    "tool": "inspect",
                    "arguments": {"api_key": "private-value"},
                    "result": {"ok": False},
                    "status": "completed",
                }
            ],
        )
    )
    projection = value["observations"]
    assert "private-value" not in json.dumps(value)
    assert projection["evidence_state"] == "redacted"
    assert projection["value"][0]["result"]["ok"] is False
    large = json.loads(
        response_from_observations(
            "provider", [{"result": {"message": "long result. " * 100000}}]
        )
    )["observations"]
    assert large["complete"] is False
    assert large["value"] is None
    assert large["evidence_state"] == "truncated"


def test_legacy_default_keeps_model_response(tmp_path):
    execution, _, _, _ = run(
        tmp_path, plan(mcp_response_source="model"), [call(), done('{"summary": true}')]
    )
    result = asyncio.run(execution)
    assert json.loads((tmp_path / result["output_path"]).read_text()) == {
        "summary": True
    }


def test_connected_consumer_receives_observations_not_model_summary(tmp_path):
    workflow = compile_prompt_workflow(
        source(
            task(
                "measure",
                fmt="json",
                authoring_template="mcp-task",
                mcp_server="docs",
                mcp_response_source="tool_observations",
            ),
            task(
                "diagnose",
                fmt="json",
                authoring_template="mcp-task",
                mcp_server="docs",
                prompt_source="connection",
                prompt_input="diagnose_prompt",
            ),
            links=[("measure", "diagnose")],
        )
    )
    execution, _, _, requests = run(
        tmp_path,
        workflow,
        [
            call(),
            done('{"invented": "discard this as tool evidence"}'),
            call(),
            done('{"diagnosis": "fixture only"}'),
        ],
    )
    asyncio.run(execution)
    consumer_request = json.dumps(requests[2][0])
    assert "wright.mcp-tool-observations/1" in consumer_request
    assert "Found" in consumer_request
    assert "discard this as tool evidence" not in consumer_request


@pytest.mark.parametrize("structured", [True, False])
def test_duplicate_json_text_cannot_bypass_redaction(structured):
    secret = {"api_key": "private-value", "ok": True}
    encoded = json.dumps(secret)
    result = secret if structured else {"content": [{"type": "text", "text": encoded}]}
    saved = response_from_observations(
        "provider", [{"result": result, "text": encoded}]
    )
    assert "private-value" not in saved
    assert "redacted" in saved


def test_opaque_text_is_not_claimed_as_retained_evidence():
    saved = json.loads(
        response_from_observations(
            "provider",
            [
                {
                    "result": {
                        "content": [{"type": "text", "text": "private opaque response"}]
                    }
                }
            ],
        )
    )
    assert "private opaque response" not in json.dumps(saved)
    assert saved["observations"]["complete"] is False
    assert saved["observations"]["value"] is None
    assert saved["observations"]["evidence_state"] == "not-retained"


def test_supplementary_warning_cannot_disappear_as_complete_success():
    saved = json.loads(
        response_from_observations(
            "provider",
            [{"result": {"ok": True}, "text": "Warning: incomplete support geometry"}],
        )
    )
    assert saved["observations"]["complete"] is False
    assert saved["observations"]["value"] is None
    assert saved["observations"]["evidence_state"] == "not-retained"
