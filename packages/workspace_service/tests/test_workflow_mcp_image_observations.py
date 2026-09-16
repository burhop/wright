"""Actual image pixels reach model transport; durable evidence contains hashes."""

import asyncio
import base64
import hashlib
import json
import struct
import zlib

import pytest

from tool_registry.gateway_models import GatewayToolResult
from workspace_service.workflow_mcp_images import (
    image_observation,
    MAX_IMAGE_BASE64_BYTES,
)
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_mcp_execution import runtime
from packages.workspace_service.tests.test_workflow_ai_task import call, done, plan


def png(width=1, height=1, extra=b""):
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + chunk(b"IEND", b"")
        + extra
    )


def image(raw=None, mime="image/png"):
    return {
        "type": "image",
        "mimeType": mime,
        "data": base64.b64encode(raw or png()).decode(),
    }


@pytest.mark.parametrize(
    "structured", [None, {"source_pdf_sha256": "a" * 64, "page": 1}]
)
def test_image_and_metadata_reach_same_tool_observation_without_persisted_base64(
    structured,
):
    gateway, runner = runtime()
    # Above the old 256 KiB JSON context limit, still a bounded vision input.
    picture = image(png(extra=b"x" * 220_000))
    gateway.result = GatewayToolResult(
        content=({"type": "text", "text": "Actual PDF page 1 receipt"}, picture),
        structured_content=structured,
    )
    events, messages_seen = [], []
    replies = iter([call(), done("Inspected actual attached page")])

    async def decide(messages, tools, **kwargs):
        messages_seen.append(list(messages))
        return next(replies)

    async def emit(kind, **event):
        events.append({"kind": kind, **event})

    response, records = asyncio.run(
        runner.run_task(plan().steps[0], "Inspect the page", decide, emit)
    )
    observation = messages_seen[-1][-1]
    assert observation["role"] == "tool" and observation["tool_call_id"] == "call_1"
    assert observation["content"][0]["type"] == "text"
    assert observation["content"][1] == {
        "type": "image_url",
        "image_url": {
            "url": "data:image/png;base64," + picture["data"],
            "detail": "high",
        },
    }
    assert "Actual PDF page 1 receipt" in observation["content"][0]["text"]
    if structured:
        assert records[0]["result"] == structured
    assert (
        records[0]["image_observations"][0]["sha256"]
        == hashlib.sha256(base64.b64decode(picture["data"])).hexdigest()
    )
    assert records[0]["image_observations"][0]["width"] == 1
    assert picture["data"] not in json.dumps(records)
    assert picture["data"] not in json.dumps(events)
    assert "data:image/" not in json.dumps(events)
    assert response == "Inspected actual attached page"
    assert len(gateway.calls) == 1


@pytest.mark.parametrize(
    "part,reason",
    [
        (
            {"type": "image", "mimeType": "image/svg+xml", "data": "PHN2Zz4="},
            "unsupported_image_type",
        ),
        ({"type": "image", "mimeType": [], "data": "abc"}, "unsupported_image_type"),
        (
            {"type": "image", "mimeType": "image/png", "data": "not base64!"},
            "invalid_image_base64",
        ),
        (
            {
                "type": "image",
                "mimeType": "image/png",
                "data": "AAAA" * (MAX_IMAGE_BASE64_BYTES // 4 + 1),
            },
            "image_size_limit",
        ),
        (image(b"a different format"), "invalid_image_header"),
        (image(png(width=5000)), "image_dimension_limit"),
    ],
)
def test_unsupported_or_invalid_images_are_rejected_without_bytes_in_evidence(
    part, reason
):
    safe, parts, evidence, errors = image_observation([part])
    assert not parts and errors == [reason]
    assert evidence[0]["disposition"] == "rejected"
    assert "data" not in safe[0] and "data" not in evidence[0]


def test_jpeg_dimensions_and_per_result_image_count_are_bounded():
    # Minimal frame header is sufficient for transport dimension validation.
    jpeg = b"\xff\xd8\xff\xc0\x00\x0b\x08\x00\x02\x00\x03\x01\x01\x11\x00\xff\xd9"
    _, parts, evidence, errors = image_observation([image(jpeg, "image/jpeg")])
    assert not errors and len(parts) == 1
    assert evidence[0]["width"] == 3 and evidence[0]["height"] == 2
    _, parts, evidence, errors = image_observation([image()] * 5)
    assert len(parts) == 4 and errors == ["image_count_limit"]
    assert all("data" not in record for record in evidence)


def test_task_image_budget_failure_retains_actual_tool_evidence(monkeypatch):
    import workspace_service.workflow_mcp_images as limits

    monkeypatch.setattr(limits, "MAX_TASK_IMAGE_BYTES", 100)
    gateway, runner = runtime()
    picture = image()
    gateway.result = GatewayToolResult(
        content=(picture,), structured_content={"page": 1}
    )
    events = []

    async def decide(*args, **kwargs):
        assert not gateway.calls
        return call()

    async def emit(kind, **event):
        events.append({"kind": kind, **event})

    with pytest.raises(WorkflowSourceExecutionError, match="image observations exceed"):
        asyncio.run(runner.run_task(plan().steps[0], "Inspect", decide, emit))
    observed = next(event for event in events if event["kind"] == "tool_completed")
    assert observed["status"] == "succeeded" and observed["result"] == {"page": 1}
    assert picture["data"] not in json.dumps(events)
    assert len(gateway.calls) == 1


def test_failed_image_tool_keeps_failed_native_result_without_forwarding_pixels():
    gateway, runner = runtime()
    picture = image()
    gateway.result = GatewayToolResult(
        content=(picture,),
        structured_content={"error": "page_unavailable"},
        is_error=True,
    )
    observations = {}
    step = plan().steps[0]
    from dataclasses import replace
    from packages.workspace_service.tests.test_workflow_mcp_execution import TOOL
    from workspace_service.workflow_mcp_execution import (
        schema_digest,
        WorkflowMcpToolError,
    )

    step = replace(
        step, tool_name=TOOL.name, schema_digest=schema_digest(TOOL), agent_task=False
    )
    with pytest.raises(WorkflowMcpToolError) as caught:
        asyncio.run(
            runner.call(step, {"query": "page"}, image_observations=observations)
        )
    assert caught.value.tool_result == {"error": "page_unavailable"}
    assert "data" not in observations["evidence"][0]


def test_actual_durable_workflow_record_contains_only_image_metadata(tmp_path):
    from packages.workspace_service.tests.test_workflow_source_execution import service
    from workspace_service.workflow_source_execution import execute_prompt_workflow
    from workspace_service.workflow_run_record import record_workflow_run

    gateway, runner = runtime()
    picture = image()
    gateway.result = GatewayToolResult(
        content=({"type": "text", "text": "Source PDF receipt"}, picture)
    )
    replies = iter([call(), done("Page observed")])

    async def decide(*args, **kwargs):
        return next(replies)

    async def execute(emit):
        return await execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan(),
            input_values={},
            response_generator=None,
            action_generator=decide,
            tool_runtime=runner,
            on_event=emit,
        )

    asyncio.run(
        record_workflow_run(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            source_path="workflows/image.workflow.wflow",
            source_digest="b" * 64,
            execute=execute,
        )
    )
    raw = next((tmp_path / "runs/image").glob("*.json")).read_text()
    record = json.loads(raw)
    event = next(e for e in record["events"] if e["kind"] == "tool_completed")
    assert event["image_observations"][0]["sha256"] == hashlib.sha256(png()).hexdigest()
    assert event["status"] == "succeeded"
    assert picture["data"] not in raw and "data:image/" not in raw
