"""Recovery uses saved typed format even when the instruction wording changes."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from agent_adapters import hermes_openai_bridge, report_generation


def messages(instructions):
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": "Export the specified mesh."},
        {
            "role": "tool",
            "tool_call_id": "export-1",
            "content": json.dumps(
                {
                    "tool_call_number": 1,
                    "status": "succeeded",
                    "text": "Mesh exported; no final acceptance was measured.",
                }
            ),
        },
    ]


@pytest.mark.parametrize("output_format", ["text", "markdown", "html", "json"])
def test_instruction_edits_cannot_select_recovery_format(output_format):
    versions = [
        "Format response as html. Format response as json.",
        "Use the saved presentation contract for the final report.",
        "",
    ]
    observed = [
        report_generation._recorded_evidence_completion(
            messages(version), output_format=output_format
        )
        for version in versions
    ]
    assert observed[0] == observed[1] == observed[2]
    envelope = json.loads(observed[0]["content"])
    assert envelope["status"] == "blocked"
    assert envelope["evidence"] == [1]
    assert "tool_calls" not in observed[0]
    response = envelope["response"]
    if output_format == "html":
        assert response.startswith("<!doctype html>")
    elif output_format == "json":
        assert json.loads(response)["content_validated"] is False
    else:
        assert response.startswith("Wright retained successful tool-call evidence")


@pytest.mark.parametrize("invalid", ["image-png", "xml", "", None, ["json"]])
def test_invalid_recovery_format_rejected_before_model_dispatch(monkeypatch, invalid):
    def unexpected_settings():
        pytest.fail("An invalid format must be rejected before transport setup")

    monkeypatch.setattr(
        report_generation, "resolve_hermes_api_settings", unexpected_settings
    )
    with pytest.raises(ValueError, match="recovery output format"):
        asyncio.run(
            report_generation.decide_workflow_tool_action(
                messages("Format response as html."), [], output_format=invalid
            )
        )


def test_null_transport_recovery_uses_typed_format_and_keeps_blocked(monkeypatch):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )

    class NullBridge:
        calls = 0

        def __init__(self, settings):
            pass

        async def complete(self, payload):
            type(self).calls += 1
            raise AttributeError("'NoneType' object has no attribute 'rstrip'")

    monkeypatch.setattr(
        hermes_openai_bridge, "HermesOpenAICompatibilityBridge", NullBridge
    )
    decision = asyncio.run(
        report_generation.decide_workflow_tool_action(
            messages("Format response as html."), [], output_format="json"
        )
    )
    outcome = json.loads(decision["content"])
    assert NullBridge.calls == 3
    assert outcome["status"] == "blocked"
    assert json.loads(outcome["response"]) == {
        "status": "blocked_after_null_model_response",
        "successful_tool_call_numbers": [1],
        "content_validated": False,
    }
    assert outcome["evidence"] == [1]
