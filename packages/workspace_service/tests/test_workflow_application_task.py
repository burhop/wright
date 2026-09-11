"""Contract fixtures, not live cloud application verification."""

import asyncio
import json
from dataclasses import replace
import pytest
from tool_registry.gateway_models import GatewayTool, GatewayToolResult
from workspace_service.workflow_application_task import (
    ApplicationResourceTask,
    application_options,
    parse_application,
)
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
from workspace_service.workflow_source_execution import (
    PromptStep,
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway
from packages.workspace_service.tests.test_workflow_source_execution import (
    source,
    task,
    service,
)


PROFILE = dict(
    version=1,
    provider_id="cloud-fixture",
    name="Cloud contract fixture",
    kind="cad_model",
    list_tool="list",
    inspect_tool="inspect",
    create_tools=["create"],
    copy_tool="copy",
    export_tool="export",
    formats=["step"],
    export_policies=["indexed", "overwrite"],
    revision_argument="expected_revision",
)


class CloudGateway(Gateway):
    def __init__(self):
        self.calls = []
        self.resources = {
            "original": dict(
                resource_id="original",
                name="Bracket",
                revision="r1",
                url="https://example.invalid/models/original",
                durability="persistent",
            )
        }

    def list_tools(self, *args):
        properties = {
            k: {"type": "string"}
            for k in ("resource_id", "expected_revision", "name", "format", "policy")
        }
        return tuple(
            GatewayTool(
                name=name,
                server_id="cloud",
                tool_name=name,
                description=name,
                input_schema={
                    "type": "object",
                    "properties": properties if name not in {"list", "create"} else {},
                    "required": [] if name in {"list", "create"} else ["resource_id"],
                },
                annotations={"readOnlyHint": name in {"list", "inspect"}},
                upstream_meta={"wright/application": PROFILE},
            )
            for name in ("list", "inspect", "create", "copy", "modify", "export")
        )

    async def call_tool(self, session, request, name, args, **kw):
        self.calls.append((name, dict(args)))
        if name == "list":
            value = {"resources": list(self.resources.values())}
        elif name == "create":
            value = {
                **self.resources["original"],
                "resource_id": "created",
                "name": "Created bracket",
                "url": "https://example.invalid/models/created",
            }
            self.resources["created"] = value
        else:
            current = self.resources[args["resource_id"]]
            if name != "inspect":
                assert args["expected_revision"] == current["revision"], (
                    "Provider rejects stale mutations"
                )
            if name == "inspect":
                value = dict(current)
            elif name == "copy":
                value = {
                    **current,
                    "resource_id": "copy",
                    "url": "https://example.invalid/models/copy",
                }
                self.resources["copy"] = value
            elif name == "modify":
                value = {**current, "revision": current["revision"] + "+1"}
                self.resources[current["resource_id"]] = value
            elif name == "export":
                value = {
                    **current,
                    "resource_id": "export-" + current["resource_id"],
                    "name": args["name"],
                    "url": "https://example.invalid/exports/bracket.step",
                    "format": args["format"],
                }
        return GatewayToolResult(content=(), structured_content=value)


def runner(config=None, responses=None):
    gateway = CloudGateway()
    runtime = WorkflowMcpRuntime(
        gateway, workspace_id="workspace", session_id="session"
    )
    step = PromptStep(
        "edit",
        "Edit bracket",
        "Change thickness.",
        None,
        (),
        "text",
        "",
        False,
        "indexed",
        server_id="cloud",
        agent_task=True,
        application=config
        or dict(source="resource", resource_id="original", revision="r1", exports=[]),
        application_from="first.model",
    )

    async def emit(*args, **kwargs):
        pass

    return gateway, ApplicationResourceTask(runtime, step, responses or {}, emit)


def test_cloud_copy_modify_and_export_pin_resource_and_revision():
    gateway, run = runner(
        dict(
            source="resource",
            resource_id="original",
            revision="r1",
            edit_mode="copy",
            output_port="model",
            exports=[dict(format="step", name="bracket.step", port="step_export")],
        )
    )

    async def scenario():
        await run.start()
        tool = next(
            t for t in run.runtime.task_tools(run.step) if t.tool_name == "modify"
        )
        args = run.guard(tool, {})
        assert args == {"resource_id": "copy", "expected_revision": "r1"}
        value = await run.call("modify", args)
        run.observe(tool, value)
        result = await run.finish("run1")
        assert result.kind == "cad_model" and result.persistent
        assert result.representations[0].resource_id == "copy"
        assert result.provenance.input_revisions == (("original", "r1"),)
        assert result.exports[0].representations[0].format == "step"
        assert gateway.calls[-1][1]["expected_revision"] == "r1+1"
        assert gateway.calls[-1][1]["policy"] == "indexed"
        assert gateway.resources["original"]["revision"] == "r1"

    asyncio.run(scenario())


def test_stale_selection_fails_before_copy_or_mutation():
    gateway, run = runner()
    gateway.resources["original"]["revision"] = "r2"
    with pytest.raises(WorkflowSourceExecutionError, match="changed"):
        asyncio.run(run.start())
    assert [c[0] for c in gateway.calls] == ["inspect"]


def test_other_resource_cannot_be_targeted():
    _, run = runner()

    async def scenario():
        await run.start()
        tool = next(
            t for t in run.runtime.task_tools(run.step) if t.tool_name == "modify"
        )
        with pytest.raises(WorkflowSourceExecutionError, match="different"):
            run.guard(tool, {"resource_id": "other"})

    asyncio.run(scenario())


def test_upstream_cloud_resource_and_stale_revision():
    gateway, first = runner()

    async def scenario():
        await first.start()
        result = await first.finish("run1")
        second = ApplicationResourceTask(
            first.runtime,
            replace(first.step, application=dict(source="upstream", from_port="model")),
            {"first.model": result},
            first.emit,
        )
        await second.start()
        assert second.input_resource["resource_id"] == "original"
        gateway.resources["original"]["revision"] = "external-change"
        with pytest.raises(WorkflowSourceExecutionError, match="changed"):
            await second.start()
        wrong = replace(
            result,
            representations=(
                replace(result.representations[0], provider_id="another-provider"),
            ),
        )
        second.responses["first.model"] = wrong
        with pytest.raises(WorkflowSourceExecutionError, match="compatible"):
            await second.start()

    asyncio.run(scenario())


def test_application_options_only_list_with_explicit_resource_request():
    gateway, run = runner()

    async def scenario():
        assert (await application_options(run.runtime, run.step))["supported"]
        assert not gateway.calls
        options = await application_options(run.runtime, run.step, resources=True)
        assert options["resources"][0]["name"] == "Bracket"
        assert [c[0] for c in gateway.calls] == ["list"]

    asyncio.run(scenario())


@pytest.mark.parametrize("fail_after_result", [False, True])
def test_shared_executor_accepts_cloud_deliverable_without_local_file(
    tmp_path, fail_after_result
):
    config = dict(source="new", output_port="report_response", exports=[])
    plan = compile_prompt_workflow(
        source(
            task(
                fmt="text",
                authoring_template="mcp-task",
                mcp_server="cloud",
                application_resource=json.dumps(config),
            )
        )
    )
    if fail_after_result:
        next_step = compile_prompt_workflow(source(task("later", fmt="text"))).steps[0]
        plan = replace(plan, steps=(*plan.steps, next_step))
    assert not plan.steps[0].save
    gateway, run = runner(config)
    count = 0

    async def decide(messages, schemas, **kwargs):
        nonlocal count
        count += 1
        if count == 1:
            create = next(
                s["function"]["name"]
                for s in schemas
                if s["function"]["description"].startswith("create:")
            )
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "one",
                        "type": "function",
                        "function": {"name": create, "arguments": "{}"},
                    }
                ],
            }
        return {
            "role": "assistant",
            "content": json.dumps(
                dict(status="completed", response="Created the model.", evidence=[1])
            ),
        }

    events = []

    async def emit(event):
        events.append(event)

    async def fail(*args):
        raise ValueError("Later model unavailable")

    async def execute(on_event):
        return await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=fail,
            action_generator=decide,
            tool_runtime=run.runtime,
            on_event=on_event,
        )

    if fail_after_result:
        from workspace_service.workflow_run_record import record_workflow_run

        with pytest.raises(
            WorkflowSourceExecutionError, match="Later model unavailable"
        ):
            asyncio.run(
                record_workflow_run(
                    service=service(tmp_path),
                    workspace_dir=str(tmp_path),
                    source_path="workflows/cloud.workflow.wflow",
                    source_digest="a" * 64,
                    execute=execute,
                    on_event=emit,
                )
            )
        record = json.loads((tmp_path / events[0]["run_log_path"]).read_text())
        assert record["status"] == "failed" and "result" not in record
        saved = list(record["partial_results"].values())
        assert saved[0]["representations"][0]["resource_id"] == "created"
        assert [e["kind"] for e in events].index("result_ready") < next(
            i
            for i, e in enumerate(events)
            if e["kind"] == "step_started" and e["task_id"] == "later"
        )
        return
    result = asyncio.run(execute(emit))
    assert (
        result["output_path"] == ""
        and result["output_bytes"] == 0
        and result["outputs"] == []
    )
    assert result["results"][0]["representations"][0]["resource_id"] == "created"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "config",
    [
        dict(source="resource", resource_id=""),
        dict(source="resource", resource_id=2),
        dict(source="new", exports=[dict(format="step", name="bracket.step")]),
        dict(
            source="new",
            exports=[dict(format="step", name="bracket.step", port="resource")],
        ),
    ],
)
def test_invalid_resource_settings_rejected(config):
    with pytest.raises(WorkflowSourceExecutionError):
        parse_application(json.dumps(config))


def test_incompatible_transfer_preflight_prevents_producer_mutations(monkeypatch):
    from workspace_service.workflow_application_task import (
        validate_application_connection,
    )
    from workspace_service.workflow_source_execution import PromptWorkflow

    gateway, run = runner(
        {"source": "upstream", "from_port": "model", "kind": "cad_model", "exports": []}
    )
    producer = replace(
        run.step,
        id="first",
        server_id="another",
        application={
            "source": "new",
            "output_port": "model",
            "exports": [{"port": "step", "format": "step", "name": "model.step"}],
        },
    )
    plan = PromptWorkflow("Transfer", (producer, run.step), {})
    with pytest.raises(WorkflowSourceExecutionError, match="compatible"):
        validate_application_connection(run.runtime, run.step, plan)
    assert not gateway.calls


@pytest.mark.parametrize("location_kind", ["cloud_resource", "workspace_file"])
def test_declared_import_consumes_verified_export_and_pins_new_resource(
    tmp_path, monkeypatch, location_kind
):
    from workspace_service.workflow_results import (
        EngineeringResult,
        Representation,
        Provenance,
    )
    import hashlib

    monkeypatch.setitem(PROFILE, "import_tool", "import_file")
    monkeypatch.setitem(PROFILE, "import_formats", ["step"])
    monkeypatch.setitem(PROFILE, "import_kinds", ["file"])
    gateway = CloudGateway()
    old_tools = gateway.list_tools()
    importer = GatewayTool(
        name="import_file",
        server_id="cloud",
        tool_name="import_file",
        description="Import a verified STEP representation",
        input_schema={
            "type": "object",
            "properties": {"source": {"type": "object"}},
            "required": ["source"],
        },
        upstream_meta={"wright/application": PROFILE},
    )
    gateway.list_tools = lambda *args: (*old_tools, importer)
    old_call = gateway.call_tool

    async def call(session, request, name, args, **kwargs):
        if name == "import_file":
            gateway.calls.append((name, args))
            value = {
                **gateway.resources["original"],
                "resource_id": "imported",
                "name": "Imported bracket",
            }
            gateway.resources["imported"] = value
            return GatewayToolResult(content=(), structured_content=value)
        return await old_call(session, request, name, args, **kwargs)

    gateway.call_tool = call
    data = b"ISO-10303-21;\nEND-ISO-10303-21;"
    (tmp_path / "model.step").write_bytes(data)
    rep = Representation(
        location_kind,
        "model.step"
        if location_kind == "workspace_file"
        else "https://example.invalid/exports/model.step",
        "step",
        provider_id="other:cad",
        resource_id="export1",
        revision="r2",
        durability="persistent",
        sha256=hashlib.sha256(data).hexdigest(),
    )
    exported = EngineeringResult(
        "source:step",
        "file",
        "STEP export",
        (rep,),
        Provenance("run", "source", "step"),
    )
    runtime = WorkflowMcpRuntime(
        gateway, workspace_id="workspace", session_id="session"
    )
    step = PromptStep(
        "import",
        "Use exported model",
        "Inspect model.",
        None,
        (),
        "text",
        "",
        False,
        "indexed",
        server_id="cloud",
        agent_task=True,
        application={
            "source": "upstream",
            "from_port": "model",
            "kind": "cad_model",
            "exports": [],
        },
        application_from="source.step",
    )

    async def emit(*args, **kwargs):
        pass

    run = ApplicationResourceTask(
        runtime, step, {"source.step": exported}, emit, workspace_dir=str(tmp_path)
    )

    async def scenario():
        await run.start()
        assert run.resource["resource_id"] == "imported"
        assert not run.allows_tool(importer)
        result = await run.finish("run")
        assert result.provenance.input_revisions == (("export1", "r2"),)
        assert gateway.calls[0][1]["source"]["location"] == rep.location
        assert [name for name, _ in gateway.calls].count("import_file") == 1

    asyncio.run(scenario())
    if location_kind == "workspace_file":
        (tmp_path / "model.step").write_bytes(b"changed")
        gateway.calls.clear()
        with pytest.raises(WorkflowSourceExecutionError, match="changed"):
            asyncio.run(run.start())
        assert not gateway.calls
    run.responses["source.step"] = replace(
        exported, representations=(replace(rep, format="iges"),)
    )
    with pytest.raises(WorkflowSourceExecutionError, match="compatible"):
        asyncio.run(run.start())


def test_async_analysis_resource_uses_shared_task_monitor_before_completion(
    tmp_path, monkeypatch
):
    """Simulated analysis service: exercise task + async monitor + common result."""
    monkeypatch.setitem(PROFILE, "kind", "analysis")
    gateway, run = runner(dict(source="new", kind="analysis", exports=[]))
    base_tools = gateway.list_tools()
    operation = {"version": 1, "status_tool": "job_status", "poll_seconds": 0.05}
    tools = [
        replace(t, upstream_meta={**t.upstream_meta, "wright/operation": operation})
        if t.tool_name == "create"
        else t
        for t in base_tools
    ]
    tools.append(
        GatewayTool(
            name="job_status",
            server_id="cloud",
            tool_name="job_status",
            description="Read job status",
            input_schema={
                "type": "object",
                "properties": {"operation_id": {"type": "string"}},
                "required": ["operation_id"],
                "additionalProperties": False,
            },
            annotations={"readOnlyHint": True},
        )
    )
    gateway.list_tools = lambda *args: tuple(tools)
    original_call = gateway.call_tool
    polls = 0

    async def call(session, request, name, args, **kwargs):
        nonlocal polls
        if name == "create":
            gateway.calls.append((name, dict(args)))
            return GatewayToolResult(
                content=(), structured_content={"operation_id": "analysis-job"}
            )
        if name == "job_status":
            gateway.calls.append((name, dict(args)))
            polls += 1
            result = {
                **gateway.resources["original"],
                "resource_id": "analysis",
                "name": "Analysis result",
                "url": "https://example.invalid/analysis/1",
            }
            result["quantities"] = {"max_displacement": {"value": 0.25, "unit": "mm"}}
            gateway.resources["analysis"] = result
            return GatewayToolResult(
                content=(),
                structured_content={
                    "status": "working" if polls == 1 else "completed",
                    "result": result,
                },
            )
        return await original_call(session, request, name, args, **kwargs)

    gateway.call_tool = call
    config = dict(
        source="new", kind="analysis", output_port="report_response", exports=[]
    )
    plan = compile_prompt_workflow(
        source(
            task(
                fmt="text",
                authoring_template="mcp-task",
                mcp_server="cloud",
                application_resource=json.dumps(config),
            )
        )
    )
    decisions = 0
    events = []

    async def decide(messages, schemas, **kwargs):
        nonlocal decisions
        decisions += 1
        if decisions == 1:
            alias = next(
                s["function"]["name"]
                for s in schemas
                if s["function"]["description"].startswith("create:")
            )
            return {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "one",
                        "type": "function",
                        "function": {"name": alias, "arguments": "{}"},
                    }
                ],
            }
        assert polls == 2
        return {
            "role": "assistant",
            "content": json.dumps(
                dict(status="completed", response="Analysis completed.", evidence=[1])
            ),
        }

    async def emit(event):
        events.append(event)

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=None,
            action_generator=decide,
            tool_runtime=run.runtime,
            on_event=emit,
        )
    )
    assert result["results"][0]["kind"] == "analysis" and not result["outputs"]
    from workspace_service.workflow_campaign_oracles import (
        verify_engineering_assertions,
    )

    check = verify_engineering_assertions(
        result,
        [
            {
                "kind": "analysis_quantity",
                "task_id": "report",
                "tool": "inspect",
                "provider_id": "cloud:cloud-fixture",
                "path": ["quantities", "max_displacement"],
                "expected": 0.25,
                "unit": "mm",
                "tolerance": 0.001,
            }
        ],
    )
    assert check[0]["actual"] == 0.25
    assert [name for name, _ in gateway.calls].count("create") == 1
    assert [e["state"] for e in events if e["kind"] == "operation_progress"] == [
        "submitted",
        "working",
        "completed",
        "results_collected",
    ]


@pytest.mark.parametrize(
    "kind,filename,data,result_kind",
    [
        (
            "workspace_file",
            "model.psm",
            b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1\x00native-fixture",
            "file",
        ),
        (
            "reference_images",
            "reference.png",
            b"\x89PNG\r\n\x1a\nimage-fixture",
            "image",
        ),
    ],
)
def test_workspace_file_and_image_inputs_reach_declared_importer(
    tmp_path, monkeypatch, kind, filename, data, result_kind
):
    from workspace_service.workflow_source_execution import prepare_prompt_workflow
    from workspace_service.workflow_campaign import sha

    monkeypatch.setitem(PROFILE, "import_tool", "import_file")
    monkeypatch.setitem(PROFILE, "import_formats", [filename.split(".")[-1]])
    monkeypatch.setitem(PROFILE, "import_kinds", [result_kind])
    gateway = CloudGateway()
    old_tools = gateway.list_tools()
    old_call = gateway.call_tool
    importer = GatewayTool(
        name="import_file",
        server_id="cloud",
        tool_name="import_file",
        description="Import supported input",
        input_schema={
            "type": "object",
            "properties": {"source": {"type": "object"}},
            "required": ["source"],
        },
        upstream_meta={"wright/application": PROFILE},
    )
    gateway.list_tools = lambda *args: (*old_tools, importer)

    async def call(session, request, name, args, **kwargs):
        if name == "import_file":
            gateway.calls.append((name, args))
            value = {
                **gateway.resources["original"],
                "resource_id": "imported",
                "name": "Imported model",
            }
            gateway.resources["imported"] = value
            return GatewayToolResult(content=(), structured_content=value)
        return await old_call(session, request, name, args, **kwargs)

    gateway.call_tool = call

    def section(kind, key, fields):
        return (
            f"{kind} {key}\n"
            + "".join(f"  {k}: {json.dumps(v)}\n" for k, v in fields.items())
            + "end\n"
        )

    def port(key):
        return dict(
            key=key,
            name=key,
            kind=kind,
            item=None,
            required=False,
            quantity="optional",
            description="Test input",
        )

    common = dict(
        purpose="Import the selected workspace input.",
        step_type="work",
        group=None,
        tool=None,
        reusable_step=None,
    )
    text = section(
        "workflow",
        "input_import",
        dict(
            name="Input import",
            purpose="Contract fixture",
            discipline="engineering",
            reviewed_ai_suggestions=True,
        ),
    )
    text += section(
        "input",
        "file",
        dict(
            **common,
            name="Workspace input",
            provided_by="engineer",
            instructions="",
            inputs=[],
            outputs=[port("source")],
            settings={"input_mode": "workspace-file", "workspace_file": filename},
        ),
    )
    config = dict(
        source="upstream",
        from_port="input",
        kind="cad_model",
        output_port="model",
        exports=[],
    )
    text += section(
        "task",
        "use",
        dict(
            **common,
            name="Use input",
            performed_by="ai_assisted",
            prompt="Inspect the imported model.",
            inputs=[port("input")],
            outputs=[{**port("model"), "kind": "cad_model"}],
            settings={
                "authoring_template": "mcp-task",
                "mcp_server": "cloud",
                "output_format": "text",
                "save_output": False,
                "application_resource": json.dumps(config),
            },
        ),
    )
    text += section(
        "connection",
        "input_connection",
        dict(
            type="item",
            **{"from": "file.source", "to": "use.input"},
            label="Input",
            when=None,
        ),
    )
    (tmp_path / filename).write_bytes(data)
    svc = service(tmp_path, text)

    async def read_reference(root, path):
        return (tmp_path / path).read_bytes()

    svc.files.read_reference = read_reference
    runtime = WorkflowMcpRuntime(
        gateway, workspace_id="workspace", session_id="session"
    )
    invalid_actor = service(tmp_path, text.replace('"engineer"', '"human"'))
    with pytest.raises(WorkflowSourceExecutionError, match="unknown performer"):
        asyncio.run(
            prepare_prompt_workflow(
                service=invalid_actor,
                workspace_dir=str(tmp_path),
                path="workflows/test.wflow",
                expected_digest="a" * 64,
                tool_runtime=runtime,
            )
        )
    assert not gateway.calls
    prepared, values = asyncio.run(
        prepare_prompt_workflow(
            service=svc,
            workspace_dir=str(tmp_path),
            path="workflows/test.wflow",
            expected_digest="a" * 64,
            tool_runtime=runtime,
        )
    )
    if result_kind == "file":
        assert values["file"].file_only
    decisions = 0

    async def decide(messages, tools, **kwargs):
        nonlocal decisions
        decisions += 1
        if decisions == 1:
            alias = next(
                t["function"]["name"]
                for t in tools
                if t["function"]["description"].startswith("inspect:")
            )
            return {
                "tool_calls": [
                    {
                        "id": "inspection",
                        "type": "function",
                        "function": {
                            "name": alias,
                            "arguments": '{"resource_id":"imported"}',
                        },
                    }
                ]
            }
        return {
            "content": json.dumps(
                {
                    "status": "completed",
                    "response": "Inspected the imported model.",
                    "evidence": [1],
                }
            )
        }

    result = asyncio.run(
        execute_prompt_workflow(
            service=svc,
            workspace_dir=str(tmp_path),
            plan=prepared,
            input_values=values,
            response_generator=None,
            action_generator=decide,
            tool_runtime=runtime,
        )
    )
    imported = next(
        args["source"] for name, args in gateway.calls if name == "import_file"
    )
    assert (
        imported["location"] == filename
        and imported["sha256"] == sha(data)
        and imported["size_bytes"] == len(data)
    )
    assert result["results"][0]["kind"] == "cad_model"
    assert (
        result["steps"][0]["input_resource"]["representation"]["location"] == filename
    )
    monkeypatch.setitem(PROFILE, "import_formats", ["unsupported"])
    gateway.calls.clear()
    with pytest.raises(WorkflowSourceExecutionError, match="cannot import"):
        asyncio.run(
            prepare_prompt_workflow(
                service=svc,
                workspace_dir=str(tmp_path),
                path="workflows/test.wflow",
                expected_digest="a" * 64,
                tool_runtime=runtime,
            )
        )
    assert not gateway.calls
