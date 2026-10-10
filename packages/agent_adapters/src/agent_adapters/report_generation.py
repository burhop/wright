"""Generate workflow responses through the configured Hermes model."""

from __future__ import annotations

import json
from copy import deepcopy
import inspect
import os
import time
import uuid
import httpx
from core.workflow_step_outcomes import (
    InvalidStepOutcomeError,
    UnattendedStepOutcome,
)
from .hermes_config import resolve_hermes_api_settings
from .workflow_model_routing import ModelRouteChangedError
from .workflow_instructions import (
    embedded_instruction_set,
    invocation_evidence,
    resolve_workflow_instructions,
    validate_workflow_assumptions,
    workflow_response_instructions,
)

# Wright's conservative workflow text policy, not a provider context guarantee.
# Native engineering observations can exceed 120 KB well below model capacity.
# The bridge still enforces complete evidence, per-part limits and retry reserves.
WORKFLOW_TRANSLATION_PROMPT_BYTES = 200_000


def _model_usage(result: dict, duration_ms: int) -> dict:
    usage = result.get("usage") if isinstance(result, dict) else None
    usage = usage if isinstance(usage, dict) else {}
    prompt_details = usage.get("prompt_tokens_details") or usage.get(
        "input_tokens_details"
    )
    completion_details = usage.get("completion_tokens_details") or usage.get(
        "output_tokens_details"
    )
    prompt_details = prompt_details if isinstance(prompt_details, dict) else {}
    completion_details = (
        completion_details if isinstance(completion_details, dict) else {}
    )

    def count(value):
        return value if type(value) is int and value >= 0 else None

    values = {
        "input_tokens": count(usage.get("prompt_tokens", usage.get("input_tokens"))),
        "cached_input_tokens": count(prompt_details.get("cached_tokens")),
        "output_tokens": count(
            usage.get("completion_tokens", usage.get("output_tokens"))
        ),
        "reasoning_output_tokens": count(completion_details.get("reasoning_tokens")),
        "total_tokens": count(usage.get("total_tokens")),
    }
    model = result.get("model") if isinstance(result, dict) else None
    return {
        "status": "reported"
        if any(value is not None for value in values.values())
        else "unknown",
        "model": model if isinstance(model, str) and model else None,
        **values,
        "duration_ms": duration_ms,
    }


class WorkflowGeneratedResponse(str):
    def __new__(
        cls,
        value: str,
        usage: dict,
        *,
        outcome: dict | None = None,
        image: dict | None = None,
        instructions: dict | None = None,
        invocations: list[dict] | None = None,
        assumptions: list[dict] | None = None,
    ):
        result = super().__new__(cls, value)
        result.wright_usage = usage
        result.wright_outcome = outcome
        result.wright_image = image  # Private bytes, never serialized into run text.
        result.wright_instructions = instructions
        result.wright_invocations = invocations or []
        result.wright_assumptions = assumptions or []
        return result


class WorkflowDecision(dict):
    """Model decision with private observer metadata outside its wire shape."""

    def __init__(self, value: dict, usage: dict, *, invocations=None):
        super().__init__(value)
        self.wright_usage = usage
        self.wright_invocations = invocations or []


def _tool_free_completion_recovery_payload(
    messages: list[dict],
    *,
    instruction_set=None,
    instruction_override=None,
) -> dict | None:
    """Build a bounded formatting-only request from successful call evidence."""
    evidence = []
    for message in messages:
        if message.get("role") != "tool":
            continue
        content = message.get("content")
        if isinstance(content, list):
            content = "\n".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        if not isinstance(content, str):
            continue
        try:
            record = json.loads(content)
        except (TypeError, ValueError):
            continue
        number = record.get("tool_call_number") if isinstance(record, dict) else None
        if (
            not isinstance(record, dict)
            or record.get("status") != "succeeded"
            or type(number) is not int
            or number < 1
        ):
            continue
        text = record.get("text", "")
        if isinstance(text, str):
            normalized = text.lstrip().lower()
            if normalized.startswith(
                (
                    "rejected by safe mode",
                    "error executing",
                    "communication error",
                    "traceback",
                )
            ):
                continue
        evidence.append(
            {
                "tool_call_number": number,
                "status": "succeeded",
                "text": text[:8192] if isinstance(text, str) else "",
            }
        )
    if not evidence:
        return None

    task_parts = []
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, str):
            task_parts.append(content)
        elif isinstance(content, list):
            task_parts.extend(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
    task = "\n".join(task_parts)
    if len(task) > 16_384:
        task = task[:8192] + "\n[task context shortened]\n" + task[-8192:]
    recovery = {"task": task, "successful_tool_evidence": evidence}
    return {
        "model": "wright-hermes",
        "messages": [
            {
                "role": "system",
                "content": resolve_workflow_instructions(
                    "protocol",
                    instruction_set=instruction_set,
                    instruction_override=instruction_override,
                ).text,
            },
            {"role": "user", "content": json.dumps(recovery, ensure_ascii=False)},
        ],
        "tools": [],
        "tool_choice": "none",
        "stream": False,
    }


def _validate_recovery_output_format(output_format: str) -> None:
    if not isinstance(output_format, str) or output_format not in {
        "text",
        "markdown",
        "html",
        "json",
    }:
        raise ValueError("Unsupported workflow recovery output format.")


def _recorded_evidence_completion(
    messages: list[dict],
    *,
    output_format: str,
    instruction_set=None,
    instruction_override=None,
) -> dict | None:
    """Return a blocked envelope after repeated null transport results.

    This is intentionally limited to evidence already marked successful by the
    workflow executor. A successful observation is not proof that the requested
    task reached its terminal operation, so this preserves evidence without
    synthesizing completion.
    """
    _validate_recovery_output_format(output_format)
    payload = _tool_free_completion_recovery_payload(
        messages,
        instruction_set=instruction_set,
        instruction_override=instruction_override,
    )
    if payload is None:
        return None
    recovery = json.loads(payload["messages"][1]["content"])
    numbers = [
        item["tool_call_number"] for item in recovery["successful_tool_evidence"]
    ]
    summary = {
        "status": "blocked_after_null_model_response",
        "successful_tool_call_numbers": numbers,
        "content_validated": False,
    }
    if output_format == "html":
        response = (
            "<!doctype html><html><head><title>Recorded tool evidence</title></head>"
            "<body><h1>Recorded tool evidence</h1><p>Wright retained successful "
            f"tool calls {', '.join(map(str, numbers))}, but the model did not "
            "return a terminal completion decision.</p>"
            "</body></html>"
        )
    elif output_format == "json":
        response = json.dumps(summary, separators=(",", ":"))
    else:
        response = (
            "Wright retained successful tool-call evidence "
            + ", ".join(map(str, numbers))
            + ", but the model did not return a terminal completion decision."
        )
    return {
        "role": "assistant",
        "content": json.dumps(
            {"status": "blocked", "response": response, "evidence": numbers},
            separators=(",", ":"),
        ),
    }


def workflow_model_timeout_seconds() -> int:
    """Resolve the bounded per-decision timeout; step execution has its own cap."""
    raw = os.environ.get("WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS", "180")
    if not raw.isascii() or not raw.isdecimal() or not 30 <= int(raw) <= 600:
        raise ValueError(
            "WRIGHT_WORKFLOW_MODEL_TIMEOUT_SECONDS must be an integer from 30 to 600."
        )
    return int(raw)


def response_instructions(
    output_format: str, *, instruction_set=None, instruction_override=None
) -> str:
    return workflow_response_instructions(
        output_format,
        instruction_set=instruction_set,
        instruction_override=instruction_override,
    ).text


async def generate_workflow_response(
    prompt: str,
    output_format: str,
    *,
    images: list[str] | None = None,
    expected_resolution: dict | None = None,
    instruction_set=None,
    instruction_override=None,
    invocation_observer=None,
) -> str:
    if output_format in {"image-png", "image-jpeg"}:
        return await generate_workflow_image(
            prompt,
            output_format[6:],
            images=images,
            expected_resolution=expected_resolution,
            instruction_set=instruction_set,
            instruction_override=instruction_override,
            invocation_observer=invocation_observer,
        )
    started = time.perf_counter()
    timeout_seconds = workflow_model_timeout_seconds()
    settings = resolve_hermes_api_settings()
    instructions = embedded_instruction_set(instruction_set)
    resolved = workflow_response_instructions(
        output_format,
        instruction_set=instructions,
        instruction_override=instruction_override,
    )
    payload = {
        "model": "hermes",
        "stream": False,
        "tools": [],
        "tool_choice": "none",
        "messages": [
            {"role": "system", "content": resolved.text},
            {
                "role": "user",
                "content": (
                    [
                        {"type": "text", "text": prompt},
                        *[
                            {"type": "image_url", "image_url": {"url": url}}
                            for url in images
                        ],
                    ]
                    if images
                    else prompt
                ),
            },
        ],
    }
    invocation = invocation_evidence(
        payload,
        operation="workflow-response",
        instruction_set=instructions,
        resolved=resolved,
    )
    headers = {"X-Hermes-Session-Id": f"wright-workflow-{uuid.uuid4()}"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds, connect=10)
        ) as client:
            if expected_resolution is not None:
                from .workflow_model_routing import lock_workflow_model

                invocation["frozen_model_lock"] = await lock_workflow_model(
                    client,
                    settings,
                    expected_resolution,
                    headers["X-Hermes-Session-Id"],
                )
            invocation["capture_phase"] = "submission"
            if invocation_observer is not None:
                await invocation_observer(deepcopy(invocation))
            response = await client.post(
                f"{settings.base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            message = result["choices"][0]["message"]
            value = message["content"]
    except httpx.ReadTimeout as error:
        raise TimeoutError(
            f"The model did not finish responding within {timeout_seconds} seconds."
        ) from error
    except ModelRouteChangedError:
        raise
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as error:
        raise ValueError(
            "The model did not return a response. Check Model Setup and run again."
        ) from error
    invocation["upstream_reported_model"] = result.get("model")
    invocation["capture_phase"] = "response"
    if invocation_observer is not None and expected_resolution is not None:
        await invocation_observer(deepcopy(invocation))
    if not isinstance(value, str):
        raise ValueError(
            "The model returned no text response. Run again with a clearer prompt."
        )
    # A prose question is not an engineering output. Require a separate closed
    # disposition before the executor validates/saves the requested document.
    # Invalid responses are not repaired here: no extra model call or effect replay.
    try:
        if message.get("tool_calls"):
            raise ValueError()
        outcome = UnattendedStepOutcome.model_validate_json(value)
        assumptions = validate_workflow_assumptions(
            [item.model_dump(mode="json") for item in outcome.assumptions],
            resolved.assumption_policy,
        )
    except (ValueError, TypeError):
        raise InvalidStepOutcomeError(
            "The model returned an invalid unattended-step outcome. "
            "Inspect the step instructions; no output or user interaction was accepted."
        ) from None
    return WorkflowGeneratedResponse(
        outcome.response,
        _model_usage(result, round((time.perf_counter() - started) * 1000)),
        outcome=outcome.model_dump(mode="json"),
        instructions=resolved.model_dump(mode="json"),
        invocations=[invocation],
        assumptions=assumptions,
    )


async def workflow_image_capabilities() -> dict:
    from .hermes_role import HermesRoleTransport

    transport = HermesRoleTransport.from_host()
    if transport is None:
        raise ValueError("The configured AI image connection is unavailable.")
    result = await transport.call({"operation": "probe-image"})
    if not result.get("available"):
        raise ValueError(
            result.get("reason") or "The configured AI connection cannot return images."
        )
    return result


async def generate_workflow_image(
    prompt,
    fmt,
    *,
    images=None,
    expected_resolution=None,
    instruction_set=None,
    instruction_override=None,
    invocation_observer=None,
):
    import base64
    from .hermes_role import HermesRoleTransport

    started = time.perf_counter()
    transport = HermesRoleTransport.from_host()
    if transport is None:
        raise ValueError("The configured AI image connection is unavailable.")
    resolution = (
        expected_resolution or (await workflow_image_capabilities())["resolution"]
    )
    instructions = embedded_instruction_set(instruction_set)
    resolved = resolve_workflow_instructions(
        "image-generation",
        instruction_set=instructions,
        instruction_override=instruction_override,
    )
    payload = {
        "operation": "generate-image",
        "expected_resolution": resolution,
        "output_format": fmt,
        "messages": [
            {"role": "system", "content": resolved.text},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    *[
                        {"type": "image_url", "image_url": {"url": url}}
                        for url in images or []
                    ],
                ],
            },
        ],
    }
    invocation = invocation_evidence(
        payload,
        operation="workflow-image",
        instruction_set=instructions,
        resolved=resolved,
    )
    if invocation_observer is not None:
        await invocation_observer(deepcopy(invocation))
    sdk_invocations = []

    async def observe_sdk(captured):
        evidence = {
            **captured,
            "instruction_set_digest": instructions.digest,
            "profile_id": instructions.profile_id,
            "resolved_instructions": resolved.model_dump(mode="json"),
        }
        sdk_invocations.append(evidence)
        if invocation_observer is not None:
            await invocation_observer(deepcopy(evidence))

    call_parameters = inspect.signature(transport.call).parameters
    observer_kwargs = (
        {"invocation_observer": observe_sdk}
        if "invocation_observer" in call_parameters
        or any(
            item.kind is inspect.Parameter.VAR_KEYWORD
            for item in call_parameters.values()
        )
        else {}
    )
    result = await transport.call(payload, **observer_kwargs)
    content = base64.b64decode(result["image_base64"], validate=True)
    usage = {
        "status": "reported",
        "model": result["response_model"],
        **result.get("usage", {}),
        "duration_ms": round((time.perf_counter() - started) * 1000),
    }
    response = "Image generated."
    return WorkflowGeneratedResponse(
        response,
        usage,
        outcome={
            "version": "wright.unattended-step/1",
            "status": "completed",
            "response": response,
            "reason": None,
        },
        image={
            "content": content,
            "format": result["output_format"],
            "provenance": {
                "resolution": result["resolution"],
                "tool": result["tool"],
                "image_call_id": result.get("image_call_id"),
            },
        },
        instructions=resolved.model_dump(mode="json"),
        invocations=[invocation, *sdk_invocations],
    )


async def generate_html_report(prompt: str) -> str:
    """Compatibility entry point; workflow execution validates the response."""
    return await generate_workflow_response(prompt, "html")


async def decide_workflow_tool_action(
    messages: list[dict],
    tools: list[dict],
    *,
    required: bool = False,
    output_format: str = "text",
    instruction_set=None,
    instruction_override=None,
    invocation_observer=None,
    expected_resolution=None,
) -> dict:
    """Reuse Hermes' validated single-action protocol adapter for native tasks."""
    from .hermes_openai_bridge import (
        HermesOpenAICompatibilityBridge,
        HermesOpenAIBridgeSettings,
        HermesBridgeError,
    )

    _validate_recovery_output_format(output_format)
    timeout_seconds = workflow_model_timeout_seconds()
    settings = resolve_hermes_api_settings()
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url=settings.base_url,
            api_key=settings.api_key,
            workflow_task=True,
            timeout_seconds=timeout_seconds,
            maximum_tools=64,
            maximum_translation_prompt_bytes=WORKFLOW_TRANSLATION_PROMPT_BYTES,
            # Includes base64 workspace image attachments, which remain separate
            # from the bounded 200,000-byte textual decision transcript.
            maximum_text_bytes=16 * 1024 * 1024,
            expected_resolution=expected_resolution,
        )
    )
    instructions = embedded_instruction_set(instruction_set)
    payload = {
        "model": "wright-hermes",
        "messages": messages,
        "tools": tools,
        "tool_choice": "required" if required else "auto",
        "stream": False,
        "wright_instruction_set": instructions.model_dump(mode="json"),
    }
    invocations = []
    duration_seconds = 0.0
    try:
        for attempt in range(3):
            invocations.append(
                invocation_evidence(
                    payload,
                    operation="workflow-tool-decision",
                    instruction_set=instructions,
                    attempt=attempt + 1,
                )
            )
            if invocation_observer is not None:
                await invocation_observer(deepcopy(invocations[-1]))
            started = time.perf_counter()
            try:
                complete_parameters = inspect.signature(bridge.complete).parameters
                callback_kwargs = (
                    {"invocation_observer": invocation_observer}
                    if invocation_observer is not None
                    and (
                        "invocation_observer" in complete_parameters
                        or any(
                            item.kind is inspect.Parameter.VAR_KEYWORD
                            for item in complete_parameters.values()
                        )
                    )
                    else {}
                )
                result = await bridge.complete(payload, **callback_kwargs)
                invocations.extend(getattr(result, "wright_invocations", []))
                duration_seconds += time.perf_counter() - started
                break
            except AttributeError as error:
                duration_seconds += time.perf_counter() - started
                # Hermes can intermittently return a null final text value after a
                # multimodal tool transcript and then call rstrip() on it. A model
                # decision has no external side effect; retry that decision twice
                # while completed MCP operations remain recorded in ``messages``.
                exact_null_failure = (
                    str(error) == "'NoneType' object has no attribute 'rstrip'"
                )
                if not exact_null_failure:
                    raise
                if attempt == 2:
                    completion = _recorded_evidence_completion(
                        messages,
                        output_format=output_format,
                        instruction_set=instruction_set,
                        instruction_override=instruction_override,
                    )
                    if completion is None:
                        raise
                    result = {"choices": [{"message": completion}]}
                    break
        else:  # pragma: no cover - the bounded loop returns or raises
            result = await bridge.complete(payload)
        usage_result = dict(result)
        if getattr(result, "wright_upstream_model", None):
            usage_result["model"] = result.wright_upstream_model
        return WorkflowDecision(
            result["choices"][0]["message"],
            _model_usage(usage_result, round(duration_seconds * 1000)),
            invocations=invocations,
        )
    except HermesBridgeError as error:
        # Bridge errors are deliberately browser-safe. Preserve the actionable
        # contract failure rather than misreporting every error as Model Setup.
        raise ValueError(
            f"The model task could not continue ({error.code}): {error}"
        ) from error
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(
            "The model could not choose a valid task action. Check Model Setup or clarify the task."
        ) from error
