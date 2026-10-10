import pytest

from agent_adapters.base import AgentStreamEvent
from packages.workspace_service.tests.test_process_ui_authoring import (
    Engine,
    prepared,
    authorized,
    fake_build,
)


@pytest.fixture(autouse=True)
def controlled_build(monkeypatch):
    from workspace_service.process_interfaces import authoring

    monkeypatch.setattr(authoring, "build_interface", fake_build)


@pytest.mark.asyncio
@pytest.mark.parametrize("failed", [False, True])
@pytest.mark.parametrize("direct_observer", [False, True])
async def test_authoring_actual_sdk_request_is_retained_even_if_no_response(
    tmp_path, failed, direct_observer
):
    class CaptureEngine(Engine):
        async def stream_chat(self, request):
            invocation = {
                "schema_version": "wright.workflow-invocation/1",
                "capture_scope": "provider_sdk_request",
                "request_fields": {
                    "model": "configured-default",
                    "authorization": "private-credential",
                    "messages": [{"role": "user", "content": request.message}],
                },
            }
            if direct_observer:
                await request.invocation_observer(invocation)
            else:
                yield AgentStreamEvent("progress", {"model_invocation": invocation})
            if failed:
                yield AgentStreamEvent("error", {"code": "SCOPED_MODEL_TIMEOUT"})
            else:
                async for event in super().stream_chat(request):
                    yield event

    service, reference = prepared(tmp_path, CaptureEngine())
    job = await service.submit(authorized(), reference, "captured", "Inspect outputs")
    final = await service.wait(authorized(), reference, job.job_id)
    assert final.state == ("failed" if failed else "preview_ready")
    retained = service.repository.get_authoring_record(
        "workspace", job.job_id, "attempt-0-invocation-1"
    )
    fields = retained["invocation"]["request_fields"]
    assert fields["model"] == "configured-default"
    assert "Inspect outputs" in fields["messages"][0]["content"]
    assert "private-credential" not in str(retained)
    reopened, _ = prepared(tmp_path)
    assert (
        reopened.repository.get_authoring_record(
            "workspace", job.job_id, "attempt-0-invocation-1"
        )
        == retained
    )
