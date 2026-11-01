"""Image handoff/file verification on the shared runner; providers are test doubles."""

import asyncio
import base64
import hashlib
import json

import pytest

from .test_workflow_source_execution import task, service
from .test_workflow_ai_task import call, done, source
from .test_workflow_mcp_execution import runtime, edge
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workflow_references import verify_task_files
from workspace_service.workflow_run_paths import bind_run_paths

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2ZQAAAABJRU5ErkJggg=="
)


def image_task(key="render", **changes):
    settings = dict(
        authoring_template="mcp-task",
        mcp_server="docs",
        save_output=False,
        expected_files=f"{key}.png",
        expected_file_ports={f"{key}_response": f"{key}.png"},
        image_output=json.dumps(
            {"format": "png", "path": f"{key}.png", "port": f"{key}_response"}
        ),
    )
    settings.update(changes)
    return task(
        key,
        fmt="text",
        prompt="Create a realistic rendering from the reference image.",
        **settings,
    ).replace(
        f'"key":"{key}_response","kind":"engineering_document"',
        f'"key":"{key}_response","kind":"workspace_file"',
    )


def test_actual_image_bytes_are_attached_and_the_final_deliverable_is_an_image(
    tmp_path,
):
    first = image_task("reference")
    second = image_task().replace(
        '"kind":"engineering_document","name":"Prompt"',
        '"kind":"workspace_file","name":"Reference image"',
    )
    plan = compile_prompt_workflow(
        source(first, second)
        + edge("reference.reference_response", "render.render_prompt")
    )
    assert not plan.steps[-1].save  # No synthetic .txt deliverable.
    gateway, runner = runtime()
    original = gateway.call_tool
    count = 0

    async def create(*args, **kwargs):
        nonlocal count
        path = "reference.png" if count == 0 else "render.png"
        count += 1
        (tmp_path / path).write_bytes(PNG)
        return await original(*args, **kwargs)

    gateway.call_tool = create
    replies = iter(
        [call(), done("Screenshot exported"), call(), done("Rendering completed")]
    )
    messages = []

    async def decide(history, tools, **kwargs):
        messages.append(history)
        return next(replies)

    async def generate(*args, **kwargs):
        pytest.fail(
            "Image tasks must use configured tools, not the text-only generator"
        )

    services = service(tmp_path)

    async def read_reference(workspace_dir, path):
        return (tmp_path / path).read_bytes()

    services.files.read_reference = read_reference
    result = asyncio.run(
        execute_prompt_workflow(
            service=services,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            action_generator=decide,
            tool_runtime=runner,
        )
    )
    image_results = [item for item in result["results"] if item["kind"] == "image"]
    assert len(image_results) == 2
    final = next(
        item for item in image_results if item["provenance"]["task_id"] == "render"
    )
    assert final["representations"][0]["sha256"] == hashlib.sha256(PNG).hexdigest()
    assert final["representations"][0]["location"] == "render.png"
    user = next(message for message in messages[2] if message["role"] == "user")
    assert any(
        part.get("type") == "image_url"
        and part["image_url"]["url"].startswith("data:image/png;base64,")
        for part in user["content"]
    )
    assert (
        result["steps"][-1]["references"][0]["sha256"]
        == hashlib.sha256(PNG).hexdigest()
    )
    assert not (tmp_path / "render.txt").exists()
    assert all(
        item["artifact_role"] == "verification"
        for item in result["results"]
        if item["kind"] == "text"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"mcp_server": ""},
        {"image_output": "malformed"},
        {
            "image_output": json.dumps(
                {"format": "jpeg", "path": "render.png", "port": "render_response"}
            )
        },
        {"expected_file_ports": {}},
        {
            "image_output": json.dumps(
                {"format": "png", "path": "different.png", "port": "render_response"}
            )
        },
    ],
)
def test_missing_provider_or_inconsistent_image_contract_fails_before_execution(
    changes,
):
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(source(image_task(**changes)))


@pytest.mark.parametrize(
    "content",
    [
        b"This is a textual description, not an image",
        b"",
        b"\xff\xd8\xffJPEG under a PNG name",
        b"\x89PNG\r\n\x1a\nnot a valid PNG header",
    ],
)
def test_tool_success_does_not_accept_missing_or_mislabeled_image_bytes(
    tmp_path, content
):
    (tmp_path / "render.png").write_bytes(content)
    with pytest.raises(WorkflowSourceExecutionError):
        verify_task_files(str(tmp_path), ("render.png",))


def test_repeat_runs_resolve_separate_output_paths_without_changing_saved_bindings():
    path = "outputs/{{wright.run_id}}/render/render.png"
    plan = compile_prompt_workflow(
        source(
            image_task(
                expected_files=path,
                expected_file_ports={"render_response": path},
                run_path_template="wright.run-path/1",
            )
        )
    )
    first = bind_run_paths(plan, "first")
    second = bind_run_paths(plan, "second")
    assert first.steps[0].expected_files == ("outputs/first/render/render.png",)
    assert second.steps[0].expected_files == ("outputs/second/render/render.png",)
    assert plan.steps[0].expected_files == (path,)


def test_native_ai_image_is_saved_and_returned_without_mcp_or_text_file(tmp_path):
    from agent_adapters.report_generation import WorkflowGeneratedResponse

    plan = compile_prompt_workflow(
        source(image_task(authoring_template="ai-prompt", mcp_server=""))
    )
    assert plan.steps[0].native_image_format == "png" and not plan.steps[0].agent_task
    calls = []

    async def generate(prompt, fmt, **kwargs):
        calls.append((prompt, fmt, kwargs))
        return WorkflowGeneratedResponse(
            "Image generated.",
            {},
            image={
                "content": PNG,
                "format": "png",
                "provenance": {"tool": "image_generation"},
            },
        )

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
        )
    )
    assert calls[0][1] == "image-png"
    assert "Create these files" not in calls[0][0]
    assert (tmp_path / "render.png").read_bytes() == PNG and not (
        tmp_path / "render.txt"
    ).exists()
    assert result["steps"][0]["execution_kind"] == "ai"
    assert result["steps"][0]["image_generation"] == {"tool": "image_generation"}
    assert (
        next(r for r in result["results"] if r["kind"] == "image")["representations"][
            0
        ]["sha256"]
        == hashlib.sha256(PNG).hexdigest()
    )
    assert "image_base64" not in json.dumps(result)


@pytest.mark.parametrize(
    "content", [None, b"Not image bytes", b"\x89PNG\r\n\x1a\ninvalid header"]
)
def test_native_ai_text_or_invalid_image_is_rejected_before_publishing(
    tmp_path, content
):
    from agent_adapters.report_generation import WorkflowGeneratedResponse

    plan = compile_prompt_workflow(
        source(image_task(authoring_template="ai-prompt", mcp_server=""))
    )

    async def generate(*args, **kwargs):
        return WorkflowGeneratedResponse(
            "An image description.", {}, image={"format": "png", "content": content}
        )

    with pytest.raises(WorkflowSourceExecutionError):
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=generate,
            )
        )
    assert not (tmp_path / "render.png").exists()


@pytest.mark.parametrize("available", [False, True])
def test_native_image_readiness_checks_and_pins_the_configured_connection(
    tmp_path, available
):
    from workspace_service.workflow_source_execution import prepare_prompt_workflow

    services = service(
        tmp_path,
        source(image_task(authoring_template="ai-prompt", mcp_server=""))
        .replace(
            '  name: "Test workflow"\n',
            '  name: "Test workflow"\n  purpose: "Native image test"\n'
            '  discipline: "general"\n  reviewed_ai_suggestions: []\n',
            1,
        )
        .replace(
            "  step_type: work\n",
            '  purpose: "Render image"\n  group: null\n  step_type: work\n',
        ),
    )
    original_read = services.workflow_sources.read

    async def authoring_document(*args):
        document = await original_read(*args)
        lines = []
        for line in document.source.splitlines():
            if line.startswith(("  inputs: ", "  outputs: ")):
                prefix, value = line.split(": ", 1)
                ports = json.loads(value)
                for port in ports:
                    port.update(
                        item=None,
                        quantity="one",
                        description="Image readiness fixture",
                        required=port.get("required", False),
                    )
                line = prefix + ": " + json.dumps(ports)
            lines.append(line)
        document.source = "\n".join(lines) + "\n"
        return document

    services.workflow_sources.read = authoring_document
    resolution = {
        "model_reference": "configured-default",
        "configuration_digest": "a" * 64,
    }

    async def capabilities():
        return {"available": available, "formats": ["png"], "resolution": resolution}

    services.workflow_image_capabilities = capabilities
    if available:
        plan, _ = asyncio.run(
            prepare_prompt_workflow(
                service=services,
                workspace_dir=str(tmp_path),
                path="test.wflow",
                expected_digest="a" * 64,
            )
        )
        assert plan.steps[0].native_image_resolution == resolution
    else:
        with pytest.raises(WorkflowSourceExecutionError, match="AI image-output"):
            asyncio.run(
                prepare_prompt_workflow(
                    service=services,
                    workspace_dir=str(tmp_path),
                    path="test.wflow",
                    expected_digest="a" * 64,
                )
            )
