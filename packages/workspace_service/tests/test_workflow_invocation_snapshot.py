"""Actual submission and response events must not share mutable producer data."""

import json

import pytest

from workspace_service.workflow_run_record import record_workflow_run
from packages.workspace_service.tests.test_workflow_source_execution import service


@pytest.mark.asyncio
async def test_durable_invocation_events_are_snapshots_before_response_enrichment(
    tmp_path,
):
    app = service(tmp_path)
    received = []
    invocation = {
        "version": "wright.workflow-invocation/1",
        "capture_phase": "submission",
        "frozen_model_lock": {"model_reference": "prepared-model"},
        "request_fields": {"messages": [{"role": "user", "content": "Exact request"}]},
    }

    async def consumer(event):
        # Even a presentation observer cannot rewrite durable event snapshots.
        received.append(event)
        if event.get("kind") == "model_invocation":
            event["invocation"]["request_fields"]["messages"][0]["content"] = (
                "Presentation mutation"
            )

    async def execute(emit):
        await emit(
            {"kind": "model_invocation", "task_id": "report", "invocation": invocation}
        )
        invocation["capture_phase"] = "response"
        invocation["upstream_reported_model"] = "reported-version"
        await emit(
            {"kind": "model_invocation", "task_id": "report", "invocation": invocation}
        )
        return {
            "status": "completed",
            "run_id": "immutable-invocations",
            "steps": [],
            "outputs": [],
        }

    result = await record_workflow_run(
        service=app,
        workspace_dir=str(tmp_path),
        workspace_id="workspace",
        source_path="workflows/report.workflow.wflow",
        source_digest="a" * 64,
        run_id="immutable-invocations",
        execute=execute,
        on_event=consumer,
    )
    record = json.loads((tmp_path / result["run_log_path"]).read_text())
    submitted, responded = [
        event["invocation"]
        for event in record["events"]
        if event["kind"] == "model_invocation"
    ]
    assert submitted["capture_phase"] == "submission"
    assert "upstream_reported_model" not in submitted
    assert responded["capture_phase"] == "response"
    assert responded["upstream_reported_model"] == "reported-version"
    for item in (submitted, responded, invocation):
        assert item["request_fields"]["messages"][0]["content"] == "Exact request"
    assert received[-2]["invocation"]["capture_phase"] == "response"
