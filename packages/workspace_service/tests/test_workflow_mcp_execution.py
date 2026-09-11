import asyncio
import json
import pytest
from tool_registry.gateway_models import (
    GatewayTool,
    GatewayToolResult,
    GatewayError,
    GatewayErrorCode,
    GatewayWorkspaceScopeError,
)
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    task,
    source,
    service,
    HTML,
)

TOOL = GatewayTool(
    name="docs__search",
    server_id="docs",
    tool_name="search",
    description="Search",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 2},
            "limit": {"type": "integer"},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
)


class Gateway:
    def __init__(self):
        self.calls = []
        self.enabled = True
        self.closed = False
        self.result = GatewayToolResult(
            content=({"type": "text", "text": "Tool evidence"},),
            structured_content={"documents": [{"title": "Found"}]},
        )

    def open_session(self, **kw):
        self.scope = kw

    def initialize_session(self, *a, **kw):
        pass

    async def close_session(self, *a):
        self.closed = True

    def list_tools(self, *a):
        return (TOOL,) if self.enabled else ()

    def workspace_approvals_for_model_call(self, *a):
        return {"workspace_enabled"}

    async def call_tool(self, *a, **kw):
        self.calls.append((a, kw))
        return self.result


def mcp(**patch):
    settings = {
        "authoring_template": "mcp-tool",
        "mcp_tool": TOOL.name,
        "mcp_server": "docs",
        "mcp_schema_digest": schema_digest(TOOL),
        "mcp_arguments": json.dumps({"limit": 3}),
        "mcp_argument_ports": json.dumps({"search_query": "query"}),
        "output_format": "json",
        **patch,
    }
    return (
        'task search\n name: "Search docs"\n step_type: work\n performed_by: configured_tool\n tool: null\n reusable_step: null\n inputs: [{"key":"search_query","name":"query","kind":"engineering_document"}]\n outputs: [{"key":"search_result","name":"Result","kind":"structured_result"},{"key":"search_text","name":"Text","kind":"text"}]\n settings: '
        + json.dumps(settings)
        + "\nend\n"
    )


def edge(a, b):
    return f'connection link_{a.replace(".", "_")}\n type: item\n from: "{a}"\n to: "{b}"\n when: null\nend\n'


def runtime():
    g = Gateway()
    return g, WorkflowMcpRuntime(g, workspace_id="workspace", session_id="session")


def test_prompt_tool_prompt_passes_exact_values_and_saves_terminal(tmp_path):
    plan = compile_prompt_workflow(
        source(
            task("query", fmt="text"),
            mcp(),
            task("report", prompt="Summarize the evidence."),
        )
        + edge("query.query_response", "search.search_query")
        + edge("search.search_text", "report.report_prompt")
    )
    g, r = runtime()
    r.preflight(plan.steps[1])
    prompts = []
    events = []

    async def generate(prompt, fmt):
        prompts.append(prompt)
        return "Fusion fillet workflow" if fmt == "text" else HTML

    async def emit(event):
        events.append(event)

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            tool_runtime=r,
            on_event=emit,
        )
    )
    assert (
        g.scope["workspace_id"] == "workspace"
        and g.scope["binding_session_id"] == "session"
    )
    assert g.calls[0][0][3] == {"query": "Fusion fillet workflow", "limit": 3}
    assert g.calls[0][1]["workspace_approvals"] == {"workspace_enabled"}
    assert "Tool evidence" in prompts[1]
    assert len(result["outputs"]) == 1 and result["output_path"] == "report.html"
    assert result["steps"][1]["execution_kind"] == "mcp"
    assert [e["execution_kind"] for e in events if e["kind"] == "step_started"] == [
        "ai",
        "mcp",
        "ai",
    ]
    assert not (tmp_path / "search.json").exists()


def test_whole_json_arguments_and_final_result_file(tmp_path):
    plan = compile_prompt_workflow(
        source(
            task("query", fmt="json"),
            mcp(mcp_arguments_source="connection", mcp_arguments_input="search_query"),
        )
        + edge("query.query_response", "search.search_query")
    )
    g, r = runtime()
    r.preflight(plan.steps[1])

    async def generate(*a):
        return '{"query":"Fusion fillet", "limit":2}'

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            tool_runtime=r,
        )
    )
    assert g.calls[0][0][3] == {"query": "Fusion fillet", "limit": 2}
    assert json.loads((tmp_path / "search.json").read_text()) == {
        "documents": [{"title": "Found"}]
    }
    assert result["output_path"] == "search.json"


@pytest.mark.parametrize(
    "patch",
    [
        {},
        {"mcp_schema_digest": "changed"},
        {"mcp_arguments": '{"query":"ok","limit":"bad"}'},
    ],
)
def test_missing_input_stale_binding_or_bad_literal_fails_preflight(patch):
    plan = compile_prompt_workflow(source(mcp(**patch)))
    g, r = runtime()
    with pytest.raises(WorkflowSourceExecutionError):
        r.preflight(plan.steps[0])
    assert not g.calls


def test_invalid_generated_arguments_fail_before_call(tmp_path):
    plan = compile_prompt_workflow(
        source(
            task("query", fmt="json"),
            mcp(mcp_arguments_source="connection", mcp_arguments_input="search_query"),
        )
        + edge("query.query_response", "search.search_query")
    )
    g, r = runtime()

    async def generate(*a):
        return '{"query":42}'

    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
                tool_runtime=r,
            )
        )
    assert not g.calls and not list(tmp_path.iterdir())


def test_disabled_server_and_tool_error_fail_without_success(tmp_path):
    plan = compile_prompt_workflow(
        source(mcp(mcp_arguments='{"query":"Fusion fillet"}'))
    )
    g, r = runtime()
    g.enabled = False
    with pytest.raises(WorkflowSourceExecutionError):
        r.preflight(plan.steps[0])
    g.enabled = True
    g.result = GatewayToolResult(content=(), is_error=True)
    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=None,
                tool_runtime=r,
            )
        )
    assert not list(tmp_path.iterdir())


def test_cached_browser_workspace_failure_preserves_safe_recovery(tmp_path):
    plan = compile_prompt_workflow(
        source(mcp(mcp_arguments='{"query":"Fusion fillet"}'))
    )
    g, r = runtime()

    async def reject_scope(*args, **kwargs):
        raise GatewayWorkspaceScopeError()

    g.call_tool = reject_scope
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=None,
                tool_runtime=r,
            )
        )
    assert error.value.code == "MCP_WORKSPACE_SCOPE_MISMATCH"
    assert "different or unspecified workspace" in str(error.value)
    assert error.value.correction == GatewayWorkspaceScopeError.recovery_action
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "code", [GatewayErrorCode.INVALID_BINDING, GatewayErrorCode.CHILD_UNAVAILABLE]
)
def test_generic_gateway_failure_does_not_expose_raw_message(code):
    plan = compile_prompt_workflow(
        source(mcp(mcp_arguments='{"query":"Fusion fillet"}'))
    )
    g, r = runtime()
    # A matching phrase in an ordinary upstream error must not gain the trusted
    # treatment reserved for the locally constructed typed workspace error.
    private_message = (
        GatewayWorkspaceScopeError.user_message
        + " private-token=example-secret /private/customer-file"
    )

    async def reject(*args, **kwargs):
        raise GatewayError(code, private_message)

    g.call_tool = reject
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(r.call(plan.steps[0], {"query": "Fusion fillet"}))
    assert error.value.code == "MCP_CALL_FAILED"
    assert "private-token" not in str(error.value) + error.value.correction
    assert "customer-file" not in str(error.value) + error.value.correction
    assert (
        error.value.correction
        == "Check the server in Tool Registry and the step's inputs, then retry."
    )
