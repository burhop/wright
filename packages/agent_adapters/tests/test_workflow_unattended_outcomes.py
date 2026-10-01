"""The configured response adapter separates dispositions from documents."""

import json
from types import SimpleNamespace

import httpx
import pytest

from agent_adapters import report_generation
from core.workflow_step_outcomes import (
    UNATTENDED_STEP_POLICY,
    InvalidStepOutcomeError,
    UnattendedStepOutcome,
)


def outcome(response="A result", *, status="completed", reason=None):
    return {
        "version": "wright.unattended-step/1",
        "status": status,
        "response": response,
        "reason": reason,
    }


def model_transport(monkeypatch, replies):
    requests = []
    actual_client = httpx.AsyncClient

    def reply(request):
        requests.append(json.loads(request.content))
        message = replies[len(requests) - 1]
        return httpx.Response(
            200,
            json={
                "choices": [{"message": message}],
                "model": "controlled-default-model",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://model.test-only", api_key=""),
    )
    monkeypatch.setattr(
        report_generation.httpx,
        "AsyncClient",
        lambda **kwargs: actual_client(transport=httpx.MockTransport(reply), **kwargs),
    )
    return requests


@pytest.mark.asyncio
@pytest.mark.parametrize("fmt", ["text", "markdown", "html", "json"])
async def test_closed_disposition_keeps_document_format_and_separate_usage(
    monkeypatch, fmt
):
    documents = {
        "text": "Questions for a future review? The measured result is 4 mm.",
        "markdown": "# Result\nQuestions for a future review?",
        "html": "<!doctype html><html><body>Questions for a future review?</body></html>",
        "json": '{"status":"input_required","question":"This is document data?"}',
    }
    document = documents[fmt]
    requests = model_transport(
        monkeypatch, [{"content": json.dumps(outcome(document))}]
    )
    value = await report_generation.generate_workflow_response(
        "Write the engineering document", fmt, images=["data:image/png;base64,AAAA"]
    )
    assert value == document
    assert value.wright_outcome == outcome(document)
    assert value.wright_usage["model"] == "controlled-default-model"
    assert len(requests) == 1
    payload = requests[0]
    assert payload["tools"] == [] and payload["tool_choice"] == "none"
    assert UNATTENDED_STEP_POLICY in payload["messages"][0]["content"]
    assert "wright.unattended-step/1" in payload["messages"][0]["content"]
    assert payload["messages"][1]["content"][1]["type"] == "image_url"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["blocked", "error"])
async def test_missing_choice_is_a_diagnostic_disposition(monkeypatch, status):
    value = outcome(
        "Specify the allowable load", status=status, reason="input_required"
    )
    requests = model_transport(monkeypatch, [{"content": json.dumps(value)}])
    result = await report_generation.generate_workflow_response("Choose a size", "html")
    assert result.wright_outcome == value
    assert str(result) == "Specify the allowable load"
    assert len(requests) == 1  # No model repair, default, or question round trip.


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message",
    [
        {"content": "What material would you like?"},
        {"content": json.dumps({"status": "completed", "response": "bare document"})},
        {
            "content": json.dumps(
                outcome(status="waiting_human", reason="input_required")
            )
        },
        {"content": json.dumps(outcome(reason="input_required"))},
        {"content": json.dumps(outcome(status="blocked"))},
        {"content": json.dumps({**outcome(), "form": {"material": "PLA"}})},
        {
            "content": json.dumps(outcome()),
            "tool_calls": [{"function": {"name": "ask_user"}}],
        },
        {"content": json.dumps(outcome(" "))},
    ],
)
async def test_invalid_outcome_never_returns_a_document_or_retries(
    monkeypatch, message
):
    requests = model_transport(monkeypatch, [message])
    with pytest.raises(InvalidStepOutcomeError, match="no output or user interaction"):
        await report_generation.generate_workflow_response("Make the part", "text")
    assert len(requests) == 1


def test_closed_outcome_contract_rejects_invalid_disposition_and_authority():
    assert UnattendedStepOutcome.model_validate(outcome()).status == "completed"
    for value in (
        {**outcome(), "actor": "engineer"},
        outcome(status="blocked", reason="pick_default"),
        outcome(response=42),
        outcome(status="completed", reason="execution_failed"),
    ):
        with pytest.raises(ValueError):
            UnattendedStepOutcome.model_validate(value)
