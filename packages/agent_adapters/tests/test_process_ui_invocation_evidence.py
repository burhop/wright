from unittest.mock import AsyncMock

import pytest

from agent_adapters.base import AgentChatRequest
from agent_adapters.hermes import HermesAdapter
from agent_adapters.hermes_role import HermesRoleTransport
from packages.agent_adapters.tests.test_process_ui_author_role import context


@pytest.mark.asyncio
@pytest.mark.parametrize("failed", [False, True])
@pytest.mark.parametrize("direct_observer", [False, True])
async def test_confined_role_forwards_sdk_request_evidence_on_success_and_failure(
    monkeypatch, failed, direct_observer
):
    evidence = {
        "schema_version": "wright.workflow-invocation/1",
        "capture_scope": "provider_sdk_request",
        "request_fields": {
            "model": "configured-default",
            "messages": [{"role": "system", "content": "Saved instructions"}],
        },
    }

    class Transport:
        async def probe(self):
            return {
                "model_reference": "configured-default",
                "configuration_digest": "a" * 64,
            }

        async def generate(self, role, message, actual, *, invocation_observer=None):
            await invocation_observer(evidence)
            if failed:
                raise TimeoutError("PRIVATE provider exception")
            return {
                "resolution": actual,
                "text": "Generated UI",
                "effective_instructions_digest": role.instructions_digest,
            }

    monkeypatch.setattr(HermesRoleTransport, "from_host", lambda: Transport())
    adapter = HermesAdapter("http://unused.invalid", "PRIVATE API credential")
    monkeypatch.setattr(
        adapter,
        "_build_messages",
        AsyncMock(side_effect=AssertionError("No general chat")),
    )
    captured = []

    async def observe(value):
        captured.append(value)

    events = [
        event
        async for event in adapter.stream_chat(
            AgentChatRequest(
                "job",
                "Generate",
                invocation_context=context(),
                invocation_observer=observe if direct_observer else None,
            )
        )
    ]
    if direct_observer:
        assert captured == [evidence]
        assert all("model_invocation" not in event.data for event in events)
    else:
        assert events[0].data == {"model_invocation": evidence}
    assert events[-1].type == ("error" if failed else "stream_end")
    assert "PRIVATE" not in str(events)
