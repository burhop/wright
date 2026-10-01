"""Restricted authoring is additive and never falls back to broad chat."""

import hashlib
from dataclasses import replace
from unittest.mock import AsyncMock

import pytest

from agent_adapters.base import (
    AgentChatMessage,
    AgentChatRequest,
    AgentInvocationCapabilities,
    AgentInvocationContext,
)
from agent_adapters.hermes import HermesAdapter, WRIGHT_SYSTEM_HINT
from agent_adapters.openclaw import OpenClawStubEngine
from agent_adapters.hermes_role import HermesRoleTransport


@pytest.fixture(autouse=True)
def no_live_role_discovery(monkeypatch):
    monkeypatch.setattr(HermesRoleTransport, "from_host", lambda: None)


def context():
    instructions = "Return a static Wright interface using the supplied contract."
    return AgentInvocationContext(
        role="process-ui-author",
        version="1",
        instructions_version="role-v1",
        instructions=instructions,
        instructions_digest=hashlib.sha256(instructions.encode()).hexdigest(),
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"role": "workspace-admin"},
        {"version": "2"},
        {"model_policy": "override"},
        {"instructions_version": ""},
        {"instructions_version": "a" * 129},
        {"instructions_version": None},
        {"instructions": None},
        {"instructions": ""},
        {"instructions": "x" * 131073},
        {"instructions_digest": "0" * 64},
        {"allowed_tools": ("terminal",)},
        {"allowed_tools": ("read-interface-contract",)},
        {"allowed_tools": []},
    ],
)
def test_context_rejects_unqualified_role_configuration(changes):
    with pytest.raises(ValueError):
        replace(context(), **changes)


def test_capability_availability_requires_complete_enforcement():
    with pytest.raises(ValueError):
        AgentInvocationCapabilities(adapter="test", available=True)
    with pytest.raises(ValueError):
        AgentInvocationCapabilities(adapter="test")
    assert AgentInvocationCapabilities(
        adapter="qualified-test",
        available=True,
        effective_instructions_every_turn=True,
        no_tools=True,
        inherited_default_model=True,
    ).available


@pytest.mark.parametrize("value", ["true", 1, None])
def test_capability_flags_do_not_coerce_unqualified_values(value):
    with pytest.raises(ValueError):
        AgentInvocationCapabilities(
            adapter="test", no_tools=value, reason="Unavailable"
        )


@pytest.mark.asyncio
async def test_existing_adapter_defaults_to_unavailable_scoped_role():
    capability = await OpenClawStubEngine().get_invocation_capabilities()
    assert not capability.available
    assert capability.reason


@pytest.mark.asyncio
async def test_hermes_role_rejection_precedes_history_or_network(monkeypatch):
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-secret")
    build = AsyncMock(side_effect=AssertionError("Broad native request attempted"))
    monkeypatch.setattr(adapter, "_build_messages", build)
    request = AgentChatRequest(
        "isolated", "Create the UI", invocation_context=context()
    )
    events = [event async for event in adapter.stream_chat(request)]
    assert [e.type for e in events] == ["error"]
    assert events[0].data["code"] == "SCOPED_INVOCATION_UNAVAILABLE"
    assert "test-secret" not in str(events)
    build.assert_not_awaited()
    assert adapter._active_clients == {}


@pytest.mark.asyncio
async def test_role_instructions_are_effective_on_every_turn_without_workspace_hints(
    monkeypatch,
):
    adapter = HermesAdapter("http://127.0.0.1:8642", "")
    history = [
        AgentChatMessage("s", "system", "Old workspace instructions", 0),
        AgentChatMessage("u", "user", "Earlier UI request", 0),
        AgentChatMessage("a", "assistant", "Earlier source", 0),
        AgentChatMessage("t", "tool", "Unrelated tool data", 0),
    ]
    monkeypatch.setattr(adapter, "get_chat_history", AsyncMock(return_value=history))
    workspace = AsyncMock(side_effect=AssertionError("Workspace context read"))
    monkeypatch.setattr(adapter, "get_session_workspace", workspace)
    role = context()
    for message in ("Create UI", "Repair the returned binding diagnostic"):
        request = AgentChatRequest(
            "isolated",
            message,
            active_rivet_slug="unrelated",
            invocation_context=role,
        )
        messages = await adapter._build_messages(request)
        assert messages == [
            {"role": "system", "content": role.instructions},
            {"role": "user", "content": "Earlier UI request"},
            {"role": "assistant", "content": "Earlier source"},
            {"role": "user", "content": message},
        ]
        assert WRIGHT_SYSTEM_HINT not in str(messages)
        assert "unrelated" not in str(messages)
    workspace.assert_not_awaited()


def test_ordinary_chat_request_remains_backward_compatible():
    assert AgentChatRequest("old-session", "Hello").invocation_context is None


@pytest.mark.parametrize(
    "changes",
    [
        {"expected_model_reference": "configured-default"},
        {"expected_configuration_digest": "a" * 64},
        {"expected_model_reference": "", "expected_configuration_digest": "a" * 64},
        {
            "expected_model_reference": "configured-default",
            "expected_configuration_digest": "bad",
        },
        {
            "expected_model_reference": "configured-default",
            "expected_configuration_digest": "A" * 64,
        },
    ],
)
def test_expected_model_and_configuration_are_a_validated_pair(changes):
    with pytest.raises(ValueError):
        replace(context(), **changes)


@pytest.mark.parametrize(
    "changes",
    [
        {"model_reference": "x" * 161},
        {"model_reference": 7},
        {"configuration_digest": "invalid"},
        {"provider_reference": ""},
        {"transport": False},
    ],
)
def test_invocation_provenance_uses_bounded_public_metadata(changes):
    with pytest.raises(ValueError):
        AgentInvocationCapabilities(
            adapter="controlled", reason="Unavailable", **changes
        )


@pytest.mark.asyncio
async def test_qualified_sdk_role_applies_prepared_instructions_each_turn_and_avoids_native_chat(
    monkeypatch,
):
    resolution = {
        "provider": "configured-provider",
        "model_reference": "configured-default",
        "configuration_digest": "a" * 64,
    }
    calls = []

    class Transport:
        async def probe(self):
            return resolution

        async def generate(self, role, message, actual):
            calls.append((role, message, actual))
            return {
                "resolution": actual,
                "text": '{"source":"synthetic"}',
                "effective_instructions_digest": role.instructions_digest,
            }

    monkeypatch.setattr(HermesRoleTransport, "from_host", lambda: Transport())
    adapter = HermesAdapter("http://127.0.0.1:8642", "never-used-api-secret")
    build = AsyncMock(side_effect=AssertionError("Native chat attempted"))
    monkeypatch.setattr(adapter, "_build_messages", build)
    capability = await adapter.get_invocation_capabilities()
    assert capability.available and capability.transport == "hermes-model-sdk"
    assert capability.model_reference == "configured-default"
    role = replace(
        context(),
        expected_model_reference=capability.model_reference,
        expected_configuration_digest=capability.configuration_digest,
    )
    for message in ("Generate", "Repair the exact supplied diagnostic"):
        events = [
            e
            async for e in adapter.stream_chat(
                AgentChatRequest("role-job", message, invocation_context=role)
            )
        ]
        assert [e.type for e in events] == ["progress", "token", "stream_end"]
        assert (
            events[0].data["effective_instructions_digest"] == role.instructions_digest
        )
        assert events[0].data["resolution"] == resolution
        assert "never-used-api-secret" not in str(events)
    assert calls == [
        (role, message, resolution)
        for message in ("Generate", "Repair the exact supplied diagnostic")
    ]
    build.assert_not_awaited()


@pytest.mark.asyncio
async def test_changed_default_model_is_rejected_before_generation(monkeypatch):
    class Transport:
        generate = AsyncMock(side_effect=AssertionError("Unexpected model invoked"))

        async def probe(self):
            return {"model_reference": "new-default", "configuration_digest": "b" * 64}

    transport = Transport()
    monkeypatch.setattr(HermesRoleTransport, "from_host", lambda: transport)
    role = replace(
        context(),
        expected_model_reference="old-default",
        expected_configuration_digest="a" * 64,
    )
    events = [
        e
        async for e in HermesAdapter("http://unused.invalid", "").stream_chat(
            AgentChatRequest("role-job", "Generate", invocation_context=role)
        )
    ]
    assert events[0].type == "error"
    transport.generate.assert_not_awaited()
