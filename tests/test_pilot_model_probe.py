import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def probe(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts/qualify-pilot-model.py"
    spec = importlib.util.spec_from_file_location("pilot_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT", "hermes-model-sdk")
    monkeypatch.setenv("WRIGHT_HERMES_PROFILE", "isolated-pilot")
    state = SimpleNamespace(model="required-model", reasoning="high", calls=[])

    async def capability():
        return {
            "available": True,
            "resolution": {
                "adapter": "hermes-model-sdk",
                "profile": "isolated-pilot",
                "provider": "required-provider",
                "model_reference": state.model,
                "reasoning_effort": state.reasoning,
            },
        }

    class Reply(str):
        wright_usage = {"model": "required-model"}

    async def generate(prompt, fmt, **kwargs):
        state.calls.append(kwargs)
        await kwargs["invocation_observer"](
            {"capture_scope": "provider_sdk_request", "api_key": "not-for-evidence"}
        )
        return Reply("24 mm3")

    monkeypatch.setattr(module, "workflow_model_capabilities", capability)
    monkeypatch.setattr(module, "generate_workflow_response", generate)
    return module, state


@pytest.mark.asyncio
async def test_mismatch_never_makes_a_model_request(probe):
    module, state = probe
    state.model = "other-model"
    report = await module.qualify(
        provider="required-provider",
        model="required-model",
        prompt="probe",
        reasoning_effort="high",
    )
    assert report["status"] == "blocked"
    assert state.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("reasoning", [None, "low"])
async def test_missing_or_different_reasoning_blocks_pilot_probe(probe, reasoning):
    module, state = probe
    state.reasoning = reasoning
    report = await module.qualify(
        provider="required-provider",
        model="required-model",
        prompt="probe",
        reasoning_effort="high",
    )
    assert report["status"] == "blocked"
    assert state.calls == []


@pytest.mark.asyncio
async def test_records_actual_frozen_submission_without_credentials(probe):
    module, state = probe
    report = await module.qualify(
        provider="required-provider",
        model="required-model",
        prompt="probe",
        reasoning_effort="high",
    )
    assert report["status"] == "request_completed"
    assert report["requested_reasoning_effort"] == "high"
    assert state.calls[0]["expected_resolution"] == report["resolved_route"]
    assert report["invocations"][0]["api_key"] != "not-for-evidence"
    assert report["upstream_reported_model"] == "required-model"


@pytest.mark.asyncio
async def test_shared_profile_is_not_used(probe, monkeypatch):
    module, state = probe
    monkeypatch.setenv("WRIGHT_HERMES_PROFILE", "wright")
    report = await module.qualify(
        provider="required-provider", model="required-model", prompt="probe"
    )
    assert report["status"] == "blocked"
    assert state.calls == []
