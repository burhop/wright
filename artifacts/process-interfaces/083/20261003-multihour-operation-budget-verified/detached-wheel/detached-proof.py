from pathlib import Path
import asyncio
import hashlib
import json
import sys
from dataclasses import replace
from time import monotonic

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "wheel-root"))
from tool_registry.gateway_models import GatewayTool, GatewayToolResult
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import PromptStep
from workspace_service import workflow_async_operations, workflow_mcp_execution, workflow_mcp_operations

profile = {"version": 1, "status_tool": "status", "poll_seconds": 0.05,
           "observation_timeout_seconds": 7200}
submit = GatewayTool(name="proof__submit", server_id="proof", tool_name="submit",
    description="Controlled detached submission", input_schema={"type":"object"},
    upstream_meta={"wright/operation":profile})
status = GatewayTool(name="proof__status", server_id="proof", tool_name="status",
    description="Controlled detached observation", annotations={"readOnlyHint":True},
    input_schema={"type":"object", "properties":{"operation_id":{"type":"string"}},
                  "required":["operation_id"], "additionalProperties":False})

class Gateway:
    def __init__(self):
        self.calls, self.reads = [], 0
    def open_session(self, **kwargs):
        pass
    def initialize_session(self, *args, **kwargs):
        pass
    def list_tools(self, *args):
        return (submit, status)
    def workspace_approvals_for_model_call(self, *args):
        return ()
    async def call_tool(self, session, request, tool, arguments, **kwargs):
        self.calls.append({"tool":tool, "arguments":arguments, "timeout":kwargs["timeout"]})
        if tool == submit.name:
            value = {"operation_id":"detached-job-1"}
        else:
            assert arguments == {"operation_id":"detached-job-1"}
            self.reads += 1
            value = {"operation_id":"detached-job-1",
                     "status":"completed" if self.reads == 5 else "working",
                     "result":{"checked":"controlled-result"}}
        return GatewayToolResult(content=(), structured_content=value)

async def run():
    gateway = Gateway()
    runtime = WorkflowMcpRuntime(gateway, workspace_id="proof", session_id="proof")
    step = PromptStep("proof", "Detached observation", "", None, (), "json", "", False, "indexed",
        tool_name=submit.name, server_id="proof", schema_digest=schema_digest(submit),
        agent_task=True, timeout_seconds=0.1)
    runtime.preflight(step)
    events, decisions, deadlines = [], [], []
    real_timeout = asyncio.timeout
    def timeout(seconds):
        deadlines.append(seconds)
        return real_timeout(seconds)
    asyncio.timeout = timeout
    async def emit(kind, **data):
        events.append({"kind":kind, **data})
    async def decide(messages, schemas, **kwargs):
        decisions.append(messages[-1]["role"])
        if len(decisions) == 1:
            return {"role":"assistant", "tool_calls":[{"id":"once", "function":{
                "name":schemas[0]["function"]["name"], "arguments":"{}"}}]}
        assert any(event.get("state") == "completed" for event in events)
        return {"role":"assistant", "content":json.dumps({"status":"completed",
            "response":json.dumps({"checked":"controlled-result"}), "evidence":[1]})}
    start = monotonic()
    response, records = await runtime.run_task(step, "Controlled observation", decide, emit)
    elapsed = monotonic() - start
    assert elapsed > step.timeout_seconds
    assert json.loads(response) == {"checked":"controlled-result"}
    assert len(records) == 1 and decisions == ["user", "tool"]
    assert 7200 in deadlines
    assert len(gateway.calls) == 6 and all(call["timeout"] == 0.1 for call in gateway.calls)
    paths = {}
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] not in {"core","workspace_service","data_vault","tool_registry",
                                      "agent_adapter","model_registry","wright_engineering"}:
            continue
        path = getattr(module, "__file__", None)
        if path:
            resolved = Path(path).resolve()
            assert resolved.is_relative_to(root / "wheel-root"), (name, path)
            paths[name] = resolved.relative_to(root / "wheel-root").as_posix()
    assert paths
    report = {"status":"passed", "scope":"Detached wheel imports with controlled gateway/model responses",
        "live_model_provider_engineering_or_hardware":False,
        "observation_budget_seconds":7200, "call_and_decision_budget_seconds":0.1,
        "elapsed_seconds":elapsed, "deadlines":deadlines, "calls":gateway.calls,
        "decisions":decisions, "operation_states":[event["state"] for event in events if "state" in event],
        "loaded_project_modules":paths,
        "module_hashes":{Path(module.__file__).name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                         for module in (workflow_async_operations, workflow_mcp_execution, workflow_mcp_operations)}}
    (root / "detached-result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status":"passed", "elapsed_seconds":elapsed, "loaded_modules":len(paths)}))

asyncio.run(run())
