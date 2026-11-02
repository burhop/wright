"""Explicit response publication reuses file identity, validation and continuation."""

import asyncio
from dataclasses import replace
import hashlib
import json

import pytest

from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from workspace_service.workflow_run_paths import TOKEN, VERSION, bind_run_paths
from .test_workflow_mcp_execution import mcp, edge, runtime
from .test_workflow_source_execution import source, task
from .test_workflow_external_action_execution import service, source as approval_source
from .test_workflow_execution_continuation import authorize, order


def producer(**settings):
    return mcp(
        **{
            "mcp_arguments": json.dumps({"query": "Measure actual evidence"}),
            "mcp_argument_ports": "{}",
            "save_output": True,
            "output_filename": "response.json",
            "file_policy": "publish_indexed",
            "saved_response_file_port": "search_result",
            **settings,
        }
    ).replace('"kind":"structured_result"', '"kind":"workspace_file"')


def consumer():
    return task(
        "consume", fmt="text", prompt="Summarize the supplied exact evidence"
    ).replace('"kind":"engineering_document"', '"kind":"workspace_file"', 1)


def graph(*, pause=False, **settings):
    gate = approval_source()
    gate = gate[
        gate.index("task approve") : gate.index("connection package_to_approval")
    ]
    text = source(producer(**settings), gate if pause else "", consumer())
    text += edge("search.search_result", "consume.consume_prompt")
    if pause:
        text += order("pause", "search", "approve") + order(
            "resume", "approve", "consume"
        )
    return replace(compile_prompt_workflow(text), definition_digest="a" * 64)


@pytest.mark.parametrize(
    "patch",
    [
        {"saved_response_file_port": None},
        {"saved_response_file_port": []},
        {"saved_response_file_port": ""},
        {"saved_response_file_port": "search_text"},
        {"saved_response_file_port": "absent"},
        {"save_output": False},
        {"file_policy": "indexed"},
        {"file_policy": "overwrite"},
        {"file_policy": {}},
        {"file_policy": "publish_overwrite"},
        {"file_policy": "publish_overwrite", "run_path_template": VERSION},
        {"output_filename": "../response.json"},
        {"output_filename": "response.txt"},
        {
            "expected_files": "native.json",
            "expected_file_ports": {"search_result": "native.json"},
        },
        {"expected_files": "response.json"},
        {"revision_policy": "create_new_files"},
        {"run_path_template": "wright.run-path/2"},
    ],
)
def test_invalid_declarations_fail_before_execution(patch):
    with pytest.raises(WorkflowSourceExecutionError):
        graph(**patch)


def test_publication_policy_requires_explicit_port():
    with pytest.raises(WorkflowSourceExecutionError, match="saved response file port"):
        compile_prompt_workflow(source(mcp(file_policy="publish_indexed")))


@pytest.mark.parametrize(
    "path",
    ["response.json", "RESPONSE.json", "response-001.json", "response.json/child.json"],
)
def test_response_path_cannot_alias_another_declared_output(path):
    text = source(producer(), task("later", fmt="json", output_filename=path))
    text += order("next", "search", "later")
    with pytest.raises(WorkflowSourceExecutionError, match="collides"):
        compile_prompt_workflow(text)


def test_response_path_cannot_alias_another_indexed_writers_next_name():
    text = source(
        producer(output_filename="response-001.json"),
        task("later", fmt="json", output_filename="response.json"),
    )
    with pytest.raises(WorkflowSourceExecutionError, match="collides"):
        compile_prompt_workflow(text + order("next", "search", "later"))


@pytest.mark.parametrize("policy", ["publish_indexed", "publish_overwrite"])
def test_actual_response_publishes_once_before_downstream(policy, tmp_path):
    settings = {"file_policy": policy}
    if policy == "publish_overwrite":
        settings.update(
            run_path_template=VERSION, output_filename=f"outputs/{TOKEN}/response.json"
        )
    plan = bind_run_paths(graph(**settings), "saved-response-proof")
    gateway, runner = runtime()
    services, calls, events, prompts = service(tmp_path), [], [], []
    write = services.files.write_generated

    async def save(root, path, content, selected_policy):
        calls.append((path, selected_policy))
        return await write(root, path, content, selected_policy)

    services.files.write_generated = save

    async def generate(prompt, fmt):
        prompts.append(prompt)
        assert len(calls) == 1
        return "Actual document evidence summarized"

    async def emit(event):
        events.append(event)

    result = asyncio.run(
        execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            tool_runtime=runner,
            on_event=emit,
            run_id="saved-response-proof",
        )
    )
    assert len(gateway.calls) == 1 and len(prompts) == 1
    output = next(
        item for item in result["outputs"] if item.get("output_port") == "search_result"
    )
    raw = (tmp_path / output["output_path"]).read_bytes()
    assert (
        raw
        == json.dumps(
            gateway.result.structured_content, ensure_ascii=False, indent=2
        ).encode()
    )
    assert output["sha256"] == hashlib.sha256(raw).hexdigest()
    assert calls[0][1] == policy.removeprefix("publish_")
    assert sum(path == output["output_path"] for path, _ in calls) == 1
    assert '"Found"' in prompts[0]
    published = [
        e
        for e in events
        if e["kind"] == "output_saved" and e.get("output_port") == "search_result"
    ]
    assert len(published) == 1
    assert events.index(published[0]) < next(
        i
        for i, e in enumerate(events)
        if e["kind"] == "step_started" and e["task_id"] == "consume"
    )
    receipt = next(
        r
        for r in result["results"]
        if r["provenance"]["output_port"] == "search_result"
    )
    assert receipt["provenance"]["task_id"] == "search"
    assert receipt["provenance"]["run_id"] == result["run_id"]
    assert receipt["representations"][0]["sha256"] == output["sha256"]


@pytest.mark.parametrize(
    "failure", ["tool_error", "missing_file", "stale_file", "invalid_response"]
)
def test_failed_tool_or_missing_expected_output_never_publishes_receipt(
    tmp_path, failure
):
    settings = (
        {"expected_files": "native.bin"}
        if failure in {"missing_file", "stale_file"}
        else {}
    )
    plan = graph(**settings)
    gateway, runner = runtime()
    if failure == "tool_error":
        gateway.result = replace(gateway.result, is_error=True)
    if failure == "invalid_response":
        gateway.result = replace(gateway.result, structured_content={"x": float("nan")})
    if failure == "stale_file":
        (tmp_path / "native.bin").write_bytes(b"old output")
    events, prompts = [], []

    async def generate(prompt, fmt):
        prompts.append(prompt)
        return "Must not run"

    async def emit(event):
        events.append(event)

    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
                tool_runtime=runner,
                on_event=emit,
            )
        )
    assert not prompts and not (tmp_path / "response.json").exists()
    assert not any(e["kind"] == "output_saved" for e in events)
    assert any(e["kind"] == "tool_response_received" for e in events)


@pytest.mark.parametrize("tamper", [None, "changed", "missing", "source"])
def test_indexed_receipt_survives_restart_without_rewrite_or_replay(tmp_path, tamper):
    plan = graph(pause=True)
    (tmp_path / "response.json").write_text("Earlier run retained")
    gateway, runner = runtime()
    writes, prompts = [], []

    async def generate(prompt, fmt):
        prompts.append(prompt)
        return "Reviewed actual document evidence"

    async def execute(**kwargs):
        services = service(tmp_path)
        write = services.files.write_generated

        async def save(root, path, content, policy):
            writes.append(path)
            return await write(root, path, content, policy)

        services.files.write_generated = save
        return await execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            tool_runtime=runner,
            **kwargs,
        )

    first = asyncio.run(execute())
    assert not prompts and len(gateway.calls) == 1
    checkpoint = authorize(service(tmp_path), first)
    snapshot = json.loads(json.dumps(checkpoint["continuation"]))
    value = snapshot["responses"]["search.search_result"]
    assert value["type"] == "engineering_result"
    assert value["value"]["representations"][0]["location"] == "response-001.json"
    retained = (tmp_path / "response-001.json").read_bytes()
    if tamper == "changed":
        (tmp_path / "response-001.json").write_text("Replacement")
    elif tamper == "missing":
        (tmp_path / "response-001.json").unlink()
    elif tamper == "source":
        plan = replace(plan, definition_digest="b" * 64)
    if tamper:
        with pytest.raises(WorkflowSourceExecutionError) as caught:
            asyncio.run(execute(continuation=snapshot, completed_checkpoint=checkpoint))
        assert caught.value.code == "WORKFLOW_CONTINUATION_STALE"
        assert not prompts
    else:
        final = asyncio.run(
            execute(continuation=snapshot, completed_checkpoint=checkpoint)
        )
        assert final["run_id"] == first["run_id"]
        assert '"Found"' in prompts[0]
        assert (tmp_path / "response-001.json").read_bytes() == retained
    assert len(gateway.calls) == 1 and writes.count("response.json") == 1
    assert (tmp_path / "response.json").read_text() == "Earlier run retained"
    assert not (tmp_path / "response-002.json").exists()


def test_native_file_and_response_file_keep_distinct_validator_subjects(tmp_path):
    from .test_workflow_process_validation import validator, runtime_service
    from workspace_service.process_validation.application import ValidationApplication
    from workspace_service.process_validation.process import output_id

    block = producer(
        expected_files="native.bin", expected_file_ports={"native": "native.bin"}
    )
    block = block.replace(
        "outputs: [",
        'outputs: [{"key":"native","name":"Native output","kind":"workspace_file"},',
    )
    check = validator().replace(
        '"kind":"engineering_document"', '"kind":"workspace_file"', 1
    )
    plan = compile_prompt_workflow(
        source(block, check) + edge("search.search_result", "inspect.inspect_subject")
    )
    gateway, runner = runtime()
    gateway.result = replace(
        gateway.result, structured_content={"length_mm": 100, "part_id": "demo-plate"}
    )
    call = gateway.call_tool

    async def create(*args, **kwargs):
        (tmp_path / "native.bin").write_bytes(b"Separate provider-created bytes")
        return await call(*args, **kwargs)

    gateway.call_tool = create
    services = runtime_service(tmp_path)
    result = asyncio.run(
        execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=None,
            tool_runtime=runner,
        )
    )
    app = ValidationApplication(
        str(tmp_path / "validation.db"), "workspace", str(tmp_path)
    )
    subjects = {
        port: app.repository.output(
            "workspace", output_id(result["run_id"], "search", 1, port)
        )
        for port in ("search_result", "native")
    }
    assert subjects["search_result"].locator == "response.json"
    assert subjects["native"].locator == "native.bin"
    assert subjects["search_result"].sha256 != subjects["native"].sha256
    assert result["steps"][-1]["response"]


@pytest.mark.parametrize("mismatch", [False, True])
def test_exact_mcp_consumer_requires_published_path_hash_and_port(tmp_path, mismatch):
    downstream = (
        mcp(
            mcp_arguments=json.dumps({"query": "Use the exact saved response"}),
            mcp_argument_ports="{}",
            mcp_file_dependencies={
                "consume_query": "wrong.json"
                if mismatch
                else {"source": "connected_output"}
            },
        )
        .replace("task search\n", "task consume\n")
        .replace("search_query", "consume_query")
        .replace('"kind":"engineering_document"', '"kind":"workspace_file"', 1)
    )
    plan = compile_prompt_workflow(
        source(producer(), downstream)
        + edge("search.search_result", "consume.consume_query")
    )
    (tmp_path / "response.json").write_text("Earlier result")
    gateway, runner = runtime()

    async def execute():
        return await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=None,
            tool_runtime=runner,
        )

    if mismatch:
        with pytest.raises(
            WorkflowSourceExecutionError, match="differs from the declared input"
        ):
            asyncio.run(execute())
        assert len(gateway.calls) == 1
    else:
        result = asyncio.run(execute())
        assert len(gateway.calls) == 2
        reference = result["steps"][1]["references"][0]
        assert reference["path"] == "response-001.json"
        assert reference["source_port"] == "search.search_result"
        assert (
            reference["sha256"]
            == hashlib.sha256((tmp_path / "response-001.json").read_bytes()).hexdigest()
        )


def test_storage_failure_prevents_publication_and_dependents(tmp_path):
    gateway, runner = runtime()
    services, events = service(tmp_path), []

    async def fail(*args):
        raise OSError("Controlled unavailable output storage")

    async def emit(event):
        events.append(event)

    services.files.write_generated = fail
    with pytest.raises(OSError, match="unavailable output storage"):
        asyncio.run(
            execute_prompt_workflow(
                service=services,
                workspace_dir=str(tmp_path),
                plan=graph(),
                input_values={},
                response_generator=None,
                tool_runtime=runner,
                on_event=emit,
            )
        )
    assert len(gateway.calls) == 1
    assert not any(e["kind"] == "output_saved" for e in events)
    assert not any(
        e["kind"] == "step_started" and e["task_id"] == "consume" for e in events
    )
