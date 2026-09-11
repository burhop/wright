import asyncio
import json
from dataclasses import replace

import pytest

from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_ai_task import call, done, plan
from packages.workspace_service.tests.test_workflow_mcp_execution import TOOL, runtime
from workspace_service.workflow_mcp_execution import safe_recipe_parameter_correction


def safe_conflict():
    code = "solid_edge_recipe_variable_name_conflict"
    issue = {
        "code": code,
        "stage": "preflight_before_recipe_mutation_cleanup_confirmed",
        "retryable": False,
        "argument": "parameters",
    }
    return {
        "providerId": "solid_edge",
        "operationStatus": "failed",
        "isSuccess": False,
        "isSaved": False,
        "document": None,
        "outputPath": None,
        "createdReferences": [],
        "warnings": [],
        "error": issue,
        "issues": [dict(issue)],
    }


class BoundCad:
    def __init__(self):
        self.records = []
        self.observed = []

    def allows_tool(self, tool):
        return True

    def guard(self, tool, arguments):
        return arguments

    async def validate_creation(self, tool, arguments):
        pass

    def observe(self, tool, result):
        self.observed.append(result)


@pytest.mark.parametrize("mode", ["changed", "unchanged", "failed_evidence"])
def test_confirmed_clean_recipe_rejection_requires_changed_arguments_and_success_evidence(
    mode,
):
    gateway, runner = runtime()
    tool = replace(TOOL, tool_name="cad.create_sheet_metal_from_recipe")
    gateway.list_tools = lambda *_: (tool,)
    report = safe_conflict()
    gateway.result = GatewayToolResult(
        content=(), structured_content=report, is_error=True
    )
    cad = BoundCad()
    decisions, events = [], []

    async def decide(messages, *args, **kwargs):
        decisions.append(messages[:])
        if len(decisions) == 1:
            return call("BendAllowance")
        if len(decisions) == 2:
            assert json.loads(messages[-1]["content"])["status"] == "invalid_arguments"
            assert json.loads(messages[-1]["content"])["result"] == report
            gateway.result = GatewayToolResult(
                content=(), structured_content={"isSuccess": True}
            )
            return call(
                "BendAllowance" if mode == "unchanged" else "Design_BendAllowance"
            )
        return done("Created", (1,) if mode == "failed_evidence" else (2,))

    async def emit(kind, **payload):
        events.append({"kind": kind, **payload})

    execute = runner.run_task(plan().steps[0], "Create", decide, emit, cad=cad)
    if mode == "changed":
        result, records = asyncio.run(execute)
        assert result == "Created"
        assert [record["status"] for record in records] == [
            "invalid_arguments",
            "succeeded",
        ]
        assert cad.observed == [{"isSuccess": True}]
    else:
        with pytest.raises(
            WorkflowSourceExecutionError,
            match="same rejected recipe"
            if mode == "unchanged"
            else "valid execution evidence",
        ):
            asyncio.run(execute)
    assert len(gateway.calls) == (1 if mode == "unchanged" else 2)


@pytest.mark.parametrize(
    "field,value",
    [
        ("warnings", ["Cleanup uncertain"]),
        ("createdReferences", ["variable:width"]),
        ("document", {"id": "still-open"}),
        ("outputPath", "partial.psm"),
        ("isSuccess", True),
        ("isSaved", True),
        ("providerId", "other"),
        ("operationStatus", "partial"),
        ("issues", []),
        ("error", {}),
    ],
)
def test_adverse_or_incomplete_native_report_remains_fatal(field, value):
    gateway, runner = runtime()
    tool = replace(TOOL, tool_name="cad.create_sheet_metal_from_recipe")
    gateway.list_tools = lambda *_: (tool,)
    report = safe_conflict()
    report[field] = value
    gateway.result = GatewayToolResult(
        content=(), structured_content=report, is_error=True
    )

    async def decide(*args, **kwargs):
        assert not gateway.calls
        return call()

    async def emit(*args, **kwargs):
        pass

    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(
            runner.run_task(plan().steps[0], "Create", decide, emit, cad=BoundCad())
        )
    assert error.value.code == "MCP_CALL_FAILED"
    assert len(gateway.calls) == 1


def test_native_contract_requires_every_proof_field_and_exact_issue():
    tool = replace(TOOL, tool_name="cad.create_sheet_metal_from_recipe")
    assert safe_recipe_parameter_correction(tool, safe_conflict())
    assert not safe_recipe_parameter_correction(TOOL, safe_conflict())
    for field in safe_conflict():
        report = safe_conflict()
        del report[field]
        assert not safe_recipe_parameter_correction(tool, report), field
    for nested in ["error", "issue"]:
        for field in ["code", "stage", "retryable", "argument"]:
            report = safe_conflict()
            target = report["error"] if nested == "error" else report["issues"][0]
            target[field] = "preflight_cleanup_unconfirmed"
            assert not safe_recipe_parameter_correction(tool, report), (nested, field)


def test_report_contract_without_bound_cad_does_not_enable_correction():
    gateway, runner = runtime()
    gateway.list_tools = lambda *_: (
        replace(TOOL, tool_name="cad.create_sheet_metal_from_recipe"),
    )
    gateway.result = GatewayToolResult(
        content=(), structured_content=safe_conflict(), is_error=True
    )

    async def decide(*args, **kwargs):
        assert not gateway.calls
        return call()

    async def emit(*args, **kwargs):
        pass

    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(runner.run_task(plan().steps[0], "Create", decide, emit))
    assert len(gateway.calls) == 1


def failed_report():
    return {
        "isSuccess": False,
        "error": {"code": "native_failure", "message": "Creation stopped"},
        "outputPath": "manufacturing/owned-partial.psm",
        "warnings": ["Partial saved; owned document could not be closed"],
        "createdReferences": ["variable:DesignWidth"],
    }


@pytest.mark.parametrize("large", [False, True])
def test_failed_mutation_records_full_report_then_stops_without_another_decision(large):
    gateway, runner = runtime()
    report = failed_report()
    if large:
        report["diagnostic"] = "x" * 270_000
    gateway.result = GatewayToolResult(
        content=(), structured_content=report, is_error=True
    )
    events, decisions = [], []

    async def decide(*args, **kwargs):
        decisions.append(args)
        assert len(decisions) == 1
        return call()

    async def emit(kind, **payload):
        events.append({"kind": kind, **payload})

    with pytest.raises(WorkflowSourceExecutionError) as failure:
        asyncio.run(
            runner.run_task(
                plan().steps[0], "Create the requested output", decide, emit
            )
        )
    assert failure.value.code == "MCP_CALL_FAILED"
    completed = [event for event in events if event["kind"] == "tool_completed"]
    assert len(completed) == len(gateway.calls) == 1
    assert completed[0]["status"] == "failed"
    assert completed[0]["result"] == report
    assert completed[0]["schema_digest"]


def test_readonly_failure_reaches_next_decision_with_adverse_evidence_intact():
    gateway, runner = runtime()
    tool = replace(TOOL, annotations={"readOnlyHint": True})
    gateway.list_tools = lambda *_: (tool,)
    report = failed_report()
    gateway.result = GatewayToolResult(
        content=(), structured_content=report, is_error=True
    )
    seen = []

    async def decide(messages, *args, **kwargs):
        seen.append(messages[:])
        if len(seen) == 1:
            return call()
        envelope = json.loads(messages[-1]["content"])
        assert envelope["status"] == "failed"
        assert envelope["result"] == report
        return done("Claiming a failed call cannot pass", (1,))

    async def emit(*args, **kwargs):
        pass

    with pytest.raises(WorkflowSourceExecutionError, match="valid execution evidence"):
        asyncio.run(runner.run_task(plan().steps[0], "Inspect", decide, emit))
    assert len(gateway.calls) == 1
    assert len(seen) == 2


def test_nonstructured_tool_failure_retains_original_content_as_evidence():
    gateway, runner = runtime()
    content = ({"type": "text", "text": "Exact tool failure diagnostic"},)
    gateway.result = GatewayToolResult(content=content, is_error=True)
    events = []

    async def decide(*args, **kwargs):
        return call()

    async def emit(kind, **payload):
        events.append({"kind": kind, **payload})

    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(runner.run_task(plan().steps[0], "Inspect", decide, emit))
    assert events[-1]["kind"] == "tool_completed"
    assert events[-1]["result"] == {"content": list(content)}


def test_oversized_readonly_evidence_is_recorded_before_context_rejection():
    gateway, runner = runtime()
    gateway.list_tools = lambda *_: (replace(TOOL, annotations={"readOnlyHint": True}),)
    report = {"observations": "x" * 270_000}
    gateway.result = GatewayToolResult(content=(), structured_content=report)
    events = []

    async def decide(*args, **kwargs):
        return call()

    async def emit(kind, **payload):
        events.append({"kind": kind, **payload})

    with pytest.raises(WorkflowSourceExecutionError, match="context limit"):
        asyncio.run(runner.run_task(plan().steps[0], "Inspect", decide, emit))
    assert events[-1]["kind"] == "tool_completed"
    assert events[-1]["result"] == report
    assert len(gateway.calls) == 1
