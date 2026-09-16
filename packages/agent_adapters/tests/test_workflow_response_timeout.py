import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

from agent_adapters import hermes_openai_bridge, report_generation


@pytest.mark.parametrize("configured, expected", [(None, 180), ("540", 540)])
def test_response_read_timeout_remains_distinct_from_model_configuration(
    monkeypatch, configured, expected
):
    if configured is None:
        monkeypatch.delenv("WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS", configured)

    class TimedOutClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"].read == expected
            assert kwargs["timeout"].connect == 10

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.ReadTimeout("private upstream diagnostic must not be exposed")

    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://127.0.0.1:8642", api_key=""),
    )
    monkeypatch.setattr(report_generation.httpx, "AsyncClient", TimedOutClient)
    with pytest.raises(TimeoutError, match=f"within {expected} seconds") as error:
        asyncio.run(
            report_generation.generate_workflow_response("Create a report", "markdown")
        )
    assert "private" not in str(error.value)
    assert "Model Setup" not in str(error.value)


@pytest.mark.parametrize(
    "configured, expected", [(None, 180), ("30", 30), ("540", 540), ("600", 600)]
)
def test_decision_adapter_receives_bounded_timeout(monkeypatch, configured, expected):
    if configured is None:
        monkeypatch.delenv("WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS", raising=False)
    else:
        monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS", configured)
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )
    message = {"role": "assistant", "content": "done"}

    class Bridge:
        def __init__(self, settings):
            assert settings.timeout_seconds == expected
            assert settings.workflow_task is True

        async def complete(self, payload):
            return {"choices": [{"message": message}]}

    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)
    observed = asyncio.run(report_generation.decide_workflow_tool_action([], []))
    assert observed == message
    assert observed.wright_usage["status"] == "unknown"


def test_decision_adapter_preserves_reported_model_usage(monkeypatch):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )

    class Bridge:
        def __init__(self, settings):
            pass

        async def complete(self, payload):
            return {
                "model": "gpt-5.6-sol",
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 9,
                    "total_tokens": 109,
                    "prompt_tokens_details": {"cached_tokens": 60},
                    "completion_tokens_details": {"reasoning_tokens": 2},
                },
                "choices": [{"message": {"role": "assistant", "content": "done"}}],
            }

    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)
    observed = asyncio.run(report_generation.decide_workflow_tool_action([], []))
    assert observed.wright_usage == {
        "status": "reported",
        "model": "gpt-5.6-sol",
        "input_tokens": 100,
        "cached_input_tokens": 60,
        "output_tokens": 9,
        "reasoning_output_tokens": 2,
        "total_tokens": 109,
        "duration_ms": 0,
    }


@pytest.mark.parametrize("failures", [1, 2])
def test_decision_adapter_retries_null_rstrip_failure_twice(monkeypatch, failures):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )
    message = {"role": "assistant", "content": "done"}

    class Bridge:
        calls = 0

        def __init__(self, settings):
            pass

        async def complete(self, payload):
            self.calls += 1
            if self.calls <= failures:
                raise AttributeError("'NoneType' object has no attribute 'rstrip'")
            return {"choices": [{"message": message}]}

    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)
    assert asyncio.run(report_generation.decide_workflow_tool_action([], [])) == message


def test_decision_adapter_stops_after_three_null_rstrip_failures(monkeypatch):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )

    class Bridge:
        calls = 0

        def __init__(self, settings):
            pass

        async def complete(self, payload):
            type(self).calls += 1
            raise AttributeError("'NoneType' object has no attribute 'rstrip'")

    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)
    with pytest.raises(AttributeError, match="NoneType"):
        asyncio.run(report_generation.decide_workflow_tool_action([], []))


def test_decision_adapter_blocks_post_tool_null_failure_without_replaying(monkeypatch):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )

    class Bridge:
        calls = []

        def __init__(self, settings):
            pass

        async def complete(self, payload):
            self.calls.append(payload)
            raise AttributeError("'NoneType' object has no attribute 'rstrip'")

    source = "SECRET_SOURCE_CODE()"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Export the part."},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,SECRET_IMAGE"},
                },
            ],
        },
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "tool_0",
                        "arguments": json.dumps({"code": source}),
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": json.dumps(
                {
                    "tool_call_number": 1,
                    "status": "succeeded",
                    "result": {"path": "part.stl"},
                    "text": "Exported part.stl.",
                }
            ),
        },
    ]
    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)

    message = asyncio.run(
        report_generation.decide_workflow_tool_action(messages, [{"type": "function"}])
    )
    envelope = json.loads(message["content"])
    assert len(Bridge.calls) == 3
    assert envelope["status"] == "blocked"
    assert envelope["evidence"] == [1]
    encoded = json.dumps(envelope)
    assert source not in encoded
    assert "SECRET_IMAGE" not in encoded


def test_completion_recovery_requires_successful_tool_evidence():
    assert (
        report_generation._tool_free_completion_recovery_payload(
            [
                {
                    "role": "tool",
                    "content": json.dumps(
                        {
                            "tool_call_number": 1,
                            "status": "failed",
                            "text": "No file.",
                        }
                    ),
                }
            ]
        )
        is None
    )


def test_completion_recovery_excludes_transport_success_with_safe_mode_rejection():
    assert (
        report_generation._tool_free_completion_recovery_payload(
            [
                {
                    "role": "tool",
                    "content": json.dumps(
                        {
                            "tool_call_number": 1,
                            "status": "succeeded",
                            "text": "Rejected by safe mode - line 2: invalid call",
                        }
                    ),
                }
            ]
        )
        is None
    )


@pytest.mark.parametrize(
    "text",
    [
        "Error executing code: Communication error with Blender",
        "Communication error with native application",
        "Traceback (most recent call last):",
    ],
)
def test_completion_recovery_excludes_success_status_with_error_text(text):
    assert (
        report_generation._tool_free_completion_recovery_payload(
            [
                {
                    "role": "tool",
                    "content": json.dumps(
                        {
                            "tool_call_number": 1,
                            "status": "succeeded",
                            "text": text,
                        }
                    ),
                }
            ]
        )
        is None
    )


def test_post_tool_completion_stops_after_bounded_exact_null_retries(monkeypatch):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )

    class Bridge:
        calls = []

        def __init__(self, settings):
            pass

        async def complete(self, payload):
            self.calls.append(payload)
            raise AttributeError("'NoneType' object has no attribute 'rstrip'")

    messages = [
        {"role": "user", "content": "Export."},
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": json.dumps(
                {
                    "tool_call_number": 1,
                    "status": "succeeded",
                    "text": "Exported part.stl.",
                }
            ),
        },
    ]
    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)

    observed = asyncio.run(
        report_generation.decide_workflow_tool_action(messages, [{}])
    )
    assert json.loads(observed["content"])["status"] == "blocked"
    assert len(Bridge.calls) == 3


def test_post_tool_completion_blocks_with_recorded_evidence_after_exact_nulls(
    monkeypatch,
):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )

    class Bridge:
        calls = 0

        def __init__(self, settings):
            pass

        async def complete(self, payload):
            type(self).calls += 1
            raise AttributeError("'NoneType' object has no attribute 'rstrip'")

    messages = [
        {
            "role": "system",
            "content": "Inside that envelope, format response as json.",
        },
        {"role": "user", "content": "Export the requested source mesh."},
        {
            "role": "tool",
            "tool_call_id": "call-1",
            "content": json.dumps(
                {
                    "tool_call_number": 1,
                    "status": "succeeded",
                    "text": "File exported successfully.",
                }
            ),
        },
    ]
    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)

    message = asyncio.run(report_generation.decide_workflow_tool_action(messages, [{}]))
    envelope = json.loads(message["content"])
    response = json.loads(envelope["response"])
    assert Bridge.calls == 3
    assert envelope["status"] == "blocked"
    assert envelope["evidence"] == [1]
    assert response == {
        "status": "blocked_after_null_model_response",
        "successful_tool_call_numbers": [1],
        "content_validated": False,
    }


def test_decision_adapter_does_not_retry_other_attribute_errors(monkeypatch):
    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://invalid.test", api_key=""),
    )

    class Bridge:
        calls = 0

        def __init__(self, settings):
            pass

        async def complete(self, payload):
            self.calls += 1
            raise AttributeError("unexpected adapter defect")

    monkeypatch.setattr(hermes_openai_bridge, "HermesOpenAICompatibilityBridge", Bridge)
    with pytest.raises(AttributeError, match="unexpected adapter defect"):
        asyncio.run(report_generation.decide_workflow_tool_action([], []))


@pytest.mark.parametrize(
    "configured", ["", "29", "601", "-1", "180.0", "nan", " 540", "540 ", "５４０"]
)
@pytest.mark.parametrize("adapter", ["response", "decision"])
def test_invalid_timeout_fails_before_model_configuration_or_dispatch(
    monkeypatch, configured, adapter
):
    monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS", configured)

    def forbidden():
        pytest.fail("Invalid timeout must fail before resolving model credentials")

    monkeypatch.setattr(report_generation, "resolve_hermes_api_settings", forbidden)
    operation = (
        report_generation.generate_workflow_response("test", "text")
        if adapter == "response"
        else report_generation.decide_workflow_tool_action([], [])
    )
    with pytest.raises(ValueError, match="must be an integer from 30 to 600"):
        asyncio.run(operation)
