"""Typed input preparation retains native SDK qualification in the same plan."""

import asyncio
import hashlib
import json
from types import SimpleNamespace

import pytest

from workspace_service.workflow_model_routing import freeze_workflow_model_routing
from workspace_service.workflow_source_execution import _parse, prepare_prompt_workflow
from packages.workspace_service.tests.test_process_input_readiness import source
from packages.workspace_service.tests.test_workflow_artifact_review import section
from packages.workspace_service.tests.test_workflow_source_execution import service


@pytest.mark.parametrize("frozen_input", [False, True])
def test_native_qualification_survives_recompiled_prepared_input_plan(
    tmp_path, frozen_input
):
    blocks = _parse(
        source(
            metadata={
                "version": 1,
                "value_schema": {"type": "string", "minLength": 1},
                "required": True,
                "default": "Render the supplied shape without changing it.",
            }
        )
    )
    first = next(b["fields"] for b in blocks if b["id"] == "first")
    first["outputs"][0]["kind"] = "workspace_file"
    first["settings"].update(
        authoring_template="ai-prompt",
        save_output=False,
        image_output=json.dumps(
            {"format": "png", "path": "render.png", "port": "first_out"}
        ),
        expected_files="render.png",
        expected_file_ports={"first_out": "render.png"},
    )
    text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
    app = service(tmp_path, text)
    source_digest = hashlib.sha256(text.encode()).hexdigest()

    async def read(*_):
        return SimpleNamespace(source=text, storage_digest=source_digest)

    app.workflow_sources.read = read
    public = {
        "provider": "openai-codex",
        "model_reference": "configured-image-model",
        "api_mode": "codex_responses",
        "endpoint_digest": "1" * 64,
        "sdk_digest": "2" * 64,
    }
    resolution = {
        **public,
        "configuration_digest": hashlib.sha256(
            json.dumps(public, sort_keys=True).encode()
        ).hexdigest(),
    }
    calls = []

    async def capability():
        calls.append("read-only-native-qualification")
        return {"available": True, "formats": ["png"], "resolution": resolution}

    app.workflow_image_capabilities = capability
    app.workflow_model_capabilities = (
        capability  # Image-only preparation never calls the text reader.
    )

    async def prepare():
        plan, values = await prepare_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            path="workflows/render.workflow.wflow",
            expected_digest=source_digest,
            workspace_id="ws",
            run_id="image-proof",
        )
        if frozen_input:
            plan, values = await prepare_prompt_workflow(
                service=app,
                workspace_dir=str(tmp_path),
                path="workflows/render.workflow.wflow",
                expected_digest=source_digest,
                workspace_id="ws",
                run_id="image-proof",
                input_snapshot=plan.input_snapshot,
            )
        bound, context = await freeze_workflow_model_routing(app, plan, None)
        return bound, values, context

    plan, values, context = asyncio.run(prepare())
    assert values["brief"] == "Render the supplied shape without changing it."
    assert plan.input_snapshot is not None
    assert plan.steps[0].native_image_resolution == resolution
    assert context["model_routing"]["images"] == {"first": resolution}
    assert context["model_routing"]["text"] is None
    assert calls == ["read-only-native-qualification"] * (2 if frozen_input else 1)
    assert not (tmp_path / "render.png").exists()
