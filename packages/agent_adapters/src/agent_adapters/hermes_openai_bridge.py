"""A bounded OpenAI Chat Completions compatibility surface over Hermes.

Rivet speaks the OpenAI tool-call protocol. Hermes remains the sole agent and
credential owner; this adapter translates Rivet's single-tool decision contract
without exposing the Hermes API key or accepting provider authority from Rivet.
"""

from __future__ import annotations

from copy import deepcopy

import hashlib
import json
import re
import time
import uuid
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, replace
from typing import Any

import httpx
import structlog
from jsonschema import Draft202012Validator, SchemaError, ValidationError
from core.redaction import redact_mapping, redact_text

from .workflow_observation_projection import (
    TOOL_CONTENT_ENCODING,
    decode_tool_message,
    observation_reference_guide,
    project_tool_message,
    tool_content_encoding_guide,
)
from .workflow_instructions import (
    embedded_asset,
    embedded_instruction_set,
    invocation_evidence,
    validate_workflow_instruction_dependencies,
)


_MODEL_ALIAS = "wright-hermes"
_TOOL_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")
_ROLES = {"system", "developer", "user", "assistant", "tool"}
_AUTHORITY_FIELDS = {
    "api_key",
    "apiKey",
    "base_url",
    "baseUrl",
    "endpoint",
    "provider",
    "session_id",
}
_TRANSLATION_MESSAGE_BYTES = 12_000
# Hermes API normalization caps each string/text part at this character count.
# The workflow's total byte budget is larger, so one text part is not sufficient.
_HERMES_TEXT_PART_CHARACTERS = 65_536
_TRANSLATION_TRUNCATION_MARKER = (
    "\n[Wright omitted older bounded content; inspect again if details are needed.]\n"
)

logger = structlog.get_logger(__name__)


def _workflow_observation_requires_retention(content: object) -> bool:
    """Keep unsuccessful/unknown envelopes and structured adverse evidence.

    Transport success is not engineering acceptance. Conservatively retain any
    native verification report, without duplicating the design-check verdict
    evaluator. Raw observed geometry may legitimately be not_evaluated.
    """
    try:
        envelope = json.loads(content) if isinstance(content, str) else None
    except (ValueError, TypeError):
        return True
    if not isinstance(envelope, dict) or envelope.get("status") != "succeeded":
        return True
    pending = [envelope.get("result")]
    while pending:
        value = pending.pop()
        if isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, dict):
            if (
                value.get("evidenceKind") == "inspection"
                or any(
                    key in value
                    for key in (
                        "inspection",
                        "requirementEvaluations",
                        "allCriticalRequirementsPass",
                        "overall",
                        "verdict",
                    )
                )
                or any(
                    key in value and value[key] is not True
                    for key in ("isValid", "isSuccess", "isSatisfied")
                )
                or value.get("isError") is True
                or value.get("status")
                in (
                    "failed",
                    "error",
                    "blocked",
                    "unverified",
                    "needs_input",
                    "rejected",
                    "cancelled",
                    "canceled",
                    "timeout",
                )
            ):
                return True
            if "evidenceStatus" in value:
                evidence = value["evidenceStatus"]
                if (
                    not isinstance(evidence, dict)
                    or evidence.get("provenance") != "observed"
                    or evidence.get("disposition") not in ("pass", "not_evaluated")
                ):
                    return True
            pending.extend(value.values())
    return False


@dataclass(frozen=True, slots=True)
class HermesOpenAIBridgeSettings:
    base_url: str
    api_key: str
    timeout_seconds: float = 300.0
    maximum_messages: int = 128
    maximum_tools: int = 32
    maximum_text_bytes: int = 1024 * 1024
    maximum_output_bytes: int = 1024 * 1024
    maximum_translation_prompt_bytes: int = 60_000
    translation_context: str = ""
    maximum_translation_context_bytes: int = 32_000
    workflow_task: bool = False
    expected_resolution: dict | None = None

    def __post_init__(self) -> None:
        if self.expected_resolution is not None:
            from core.workflow_model_routing import parse_workflow_text_resolution

            parse_workflow_text_resolution(self.expected_resolution)
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError("Hermes base URL must be HTTP(S)")
        if not 1 <= self.timeout_seconds <= 600:
            raise ValueError("Hermes bridge timeout must be between 1 and 600 seconds")
        if (
            min(
                self.maximum_messages,
                self.maximum_tools,
                self.maximum_text_bytes,
                self.maximum_output_bytes,
                self.maximum_translation_prompt_bytes,
                self.maximum_translation_context_bytes,
            )
            < 1
        ):
            raise ValueError("Hermes bridge limits must be positive")
        if (
            len(self.translation_context.encode("utf-8"))
            > self.maximum_translation_context_bytes
        ):
            raise ValueError("Hermes bridge translation context exceeds its safe limit")


class HermesBridgeError(RuntimeError):
    """Stable, browser-safe bridge error."""

    def __init__(self, code: str, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code

    def envelope(self) -> dict[str, object]:
        return {
            "error": {
                "message": str(self),
                "type": "wright_rivet_bridge_error",
                "code": self.code,
            }
        }


@dataclass(frozen=True, slots=True)
class _Tool:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True, slots=True)
class _ValidatedRequest:
    messages: list[dict[str, Any]]
    tools: tuple[_Tool, ...]
    tool_choice: str | dict[str, Any]
    stream: bool
    instruction_set: Any = None


class HermesBridgeCompletion(dict):
    """Private evidence attributes do not change the public compatibility wire."""

    def __init__(self, value, invocations, upstream_model):
        super().__init__(value)
        self.wright_invocations = invocations
        self.wright_upstream_model = upstream_model


def _compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _workflow_user_text_parts(message: dict[str, Any]) -> dict[str, Any]:
    """Represent long user text as ordered text parts without losing a character.

    This changes transport representation only. Roles, images, tool observations
    and the original recorded request remain intact; no content is summarized.
    Bound the JSON encoding too, since quotes/control characters expand on wire.
    """
    if (
        message.get("role") != "user"
        or len(_compact(message)) <= _HERMES_TEXT_PART_CHARACTERS
    ):
        return message
    content = message.get("content")
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    if not isinstance(content, list):
        return message
    parts = []
    for part in content:
        if (
            not isinstance(part, dict)
            or part.get("type") != "text"
            or not isinstance(part.get("text"), str)
            or set(part) != {"type", "text"}
        ):
            parts.append(part)
            continue
        remaining = part["text"]
        while (
            len(_compact({**part, "text": remaining}))
            > _HERMES_TEXT_PART_CHARACTERS // 2
        ):
            low, high = 1, min(len(remaining), _HERMES_TEXT_PART_CHARACTERS // 2)
            while low < high:
                middle = (low + high + 1) // 2
                if (
                    len(_compact({**part, "text": remaining[:middle]}))
                    <= _HERMES_TEXT_PART_CHARACTERS // 2
                ):
                    low = middle
                else:
                    high = middle - 1
            parts.append({**part, "text": remaining[:low]})
            remaining = remaining[low:]
        parts.append({**part, "text": remaining})
    return {**message, "content": parts}


class HermesOpenAICompatibilityBridge:
    def __init__(
        self,
        settings: HermesOpenAIBridgeSettings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._transport = transport

    @property
    def available(self) -> bool:
        return bool(self.settings.api_key.strip())

    def _validate(self, payload: Mapping[str, Any]) -> _ValidatedRequest:
        authority = sorted(_AUTHORITY_FIELDS.intersection(payload))
        if authority:
            raise HermesBridgeError(
                "invalid_request",
                "Provider authority fields are not accepted by the Wright AI bridge.",
            )
        if payload.get("model") != _MODEL_ALIAS:
            raise HermesBridgeError(
                "invalid_request", "The requested model alias is not supported."
            )
        instruction_set = None
        if "wright_instruction_set" in payload:
            if not self.settings.workflow_task:
                raise HermesBridgeError(
                    "invalid_request",
                    "Workflow instruction context is not accepted on this surface.",
                )
            try:
                if payload["wright_instruction_set"] is None:
                    raise ValueError("Captured workflow instructions cannot be null")
                instruction_set = embedded_instruction_set(
                    payload["wright_instruction_set"]
                )
                validate_workflow_instruction_dependencies(instruction_set, "mcp-task")
            except (ValueError, TypeError) as error:
                raise HermesBridgeError(
                    "invalid_request", "Saved workflow instruction context is invalid."
                ) from error
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            raise HermesBridgeError(
                "invalid_request", "Messages must be a bounded non-empty array."
            )
        normalized_messages: list[dict[str, Any]] = []
        text_bytes = 0
        for message in messages:
            if not isinstance(message, dict) or message.get("role") not in _ROLES:
                raise HermesBridgeError(
                    "invalid_request", "A chat message has an invalid role or shape."
                )
            content = message.get("content")
            if content is not None and not isinstance(content, (str, list)):
                raise HermesBridgeError(
                    "invalid_request", "A chat message has invalid content."
                )
            text_bytes += len(_compact(content).encode("utf-8"))
            normalized_messages.append(
                {
                    key: value
                    for key, value in message.items()
                    if key in {"role", "content", "name", "tool_call_id", "tool_calls"}
                }
            )
        if text_bytes > self.settings.maximum_text_bytes:
            raise HermesBridgeError(
                "invalid_request", "Chat message content exceeds the bridge limit."
            )

        raw_tools = payload.get("tools") or []
        if (
            not isinstance(raw_tools, list)
            or len(raw_tools) > self.settings.maximum_tools
        ):
            raise HermesBridgeError(
                "unsupported_tool_contract", "Tools must be a bounded array."
            )
        tools: list[_Tool] = []
        names: set[str] = set()
        for item in raw_tools:
            if (
                not isinstance(item, dict)
                or item.get("type") != "function"
                or not isinstance(item.get("function"), dict)
            ):
                raise HermesBridgeError(
                    "unsupported_tool_contract", "Only function tools are supported."
                )
            function = item["function"]
            name = function.get("name")
            parameters = function.get("parameters", {"type": "object"})
            if (
                not isinstance(name, str)
                or not _TOOL_NAME.fullmatch(name)
                or name in names
            ):
                raise HermesBridgeError(
                    "unsupported_tool_contract",
                    "Tool names must be unique safe identifiers.",
                )
            from .workflow_tool_schema import qualify_workflow_tool_schema_depth

            try:
                qualify_workflow_tool_schema_depth(
                    parameters,
                    action_intent_contract=instruction_set.action_intent_contract
                    if instruction_set
                    else None,
                )
            except (ValueError, TypeError, AttributeError) as error:
                raise HermesBridgeError(
                    "unsupported_tool_contract",
                    "Tool schema is invalid or too deeply nested.",
                ) from error
            try:
                Draft202012Validator.check_schema(parameters)
            except SchemaError as error:
                raise HermesBridgeError(
                    "unsupported_tool_contract", "Tool schema is invalid."
                ) from error
            names.add(name)
            tools.append(
                _Tool(name, str(function.get("description") or "")[:4096], parameters)
            )

        choice = payload.get("tool_choice", "auto")
        if isinstance(choice, str):
            if choice not in {"auto", "none", "required"}:
                raise HermesBridgeError(
                    "unsupported_tool_contract", "Tool choice is not supported."
                )
        elif isinstance(choice, dict):
            named = (
                choice.get("function", {}).get("name")
                if choice.get("type") == "function"
                else None
            )
            if named not in names:
                raise HermesBridgeError(
                    "unsupported_tool_contract",
                    "Named tool choice is not in the tool list.",
                )
        else:
            raise HermesBridgeError(
                "unsupported_tool_contract", "Tool choice is not supported."
            )
        if payload.get("parallel_tool_calls") is True:
            raise HermesBridgeError(
                "unsupported_tool_contract",
                "Parallel tool calls are not supported by the Rivet compatibility bridge.",
            )
        if len(normalized_messages) > self.settings.maximum_messages:
            if not tools:
                raise HermesBridgeError(
                    "invalid_request", "Messages must be a bounded non-empty array."
                )
            if self.settings.workflow_task:
                if choice == "none":
                    raise HermesBridgeError(
                        "invalid_request", "Messages must be a bounded non-empty array."
                    )
                # Bound complete exchanges with the rendered schemas below. The
                # legacy message-count compactor can separate a call from its result.
            else:
                normalized_messages = self._compact_tool_transcript(
                    normalized_messages,
                    maximum_messages=self.settings.maximum_messages,
                )
        return _ValidatedRequest(
            normalized_messages,
            tuple(tools),
            choice,
            payload.get("stream") is True,
            instruction_set,
        )

    @staticmethod
    def _compact_tool_transcript(
        messages: list[dict[str, Any]], *, maximum_messages: int
    ) -> list[dict[str, Any]]:
        """Bound Rivet's amplified transcript without losing its active objective.

        Legacy Graph Builder repeats the same authority and task objective before
        every one-tool turn. Keep the first copy of those stable messages, then
        retain the newest unique action history. The translated conversation is
        JSON data rather than an upstream native tool transcript, so retaining an
        assistant/tool pair boundary is not required for protocol validity.
        """

        stable: list[dict[str, Any]] = []
        history: list[dict[str, Any]] = []
        seen_stable: set[str] = set()
        for message in messages:
            role = message.get("role")
            if role in {"system", "developer", "user"}:
                identity = _compact(
                    {
                        "role": role,
                        "content": message.get("content"),
                        "name": message.get("name"),
                    }
                )
                if identity in seen_stable:
                    continue
                seen_stable.add(identity)
                stable.append(message)
                continue
            history.append(message)

        if len(stable) >= maximum_messages:
            return stable[:maximum_messages]
        remaining = maximum_messages - len(stable)
        return [*stable, *history[-remaining:]]

    def _headers(self, request_id: str) -> dict[str, str]:
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "X-Hermes-Session-Id": f"rivet-{request_id}",
        }
        if self.settings.api_key:
            headers["Authorization"] = f"Bearer {self.settings.api_key}"
        return headers

    def _translation_prompt(
        self, request: _ValidatedRequest, *, repair: dict[str, Any] | None = None
    ) -> str:
        choice = request.tool_choice
        optional = choice == "auto"
        instructions = embedded_instruction_set(request.instruction_set)
        family = "workflow" if self.settings.workflow_task else "graph"
        notice = (
            embedded_asset(
                instructions,
                f"bridge.{'optional' if optional else 'required'}-{family}",
            ).body
            + " "
        )
        preamble = (
            embedded_asset(instructions, f"bridge.{family}-translation").render(
                {"optional_notice": notice}
            )
            + "\n"
        )
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in request.tools
        ]
        workspace_context: object = {}
        if self.settings.translation_context:
            try:
                workspace_context = json.loads(self.settings.translation_context)
            except json.JSONDecodeError as error:
                raise HermesBridgeError(
                    "unsupported_tool_contract",
                    "Wright's workspace tool context is invalid.",
                ) from error

        def render(
            messages: list[dict[str, Any]],
            omissions: list[dict[str, Any]] | None = None,
            reference_calls: list[str] | None = None,
            decoded_calls: list[str] | None = None,
        ) -> str:
            transcript = {
                "conversation": messages,
                "tools": tools,
                "tool_choice": choice,
                "wright_workspace_context": workspace_context,
            }
            if repair is not None:
                transcript["translation_repair"] = repair
            if omissions:
                transcript["wright_transcript_omissions"] = {
                    "notice": embedded_asset(
                        instructions, "bridge.transcript-omissions"
                    ).body,
                    "exchanges": omissions,
                }
            if reference_calls:
                transcript["wright_observation_references"] = (
                    observation_reference_guide(
                        reference_calls,
                        meaning=embedded_asset(
                            instructions, "bridge.observation-reference-guide"
                        ).body,
                    )
                )
            if decoded_calls:
                transcript[TOOL_CONTENT_ENCODING] = tool_content_encoding_guide(
                    decoded_calls,
                    meaning=embedded_asset(
                        instructions, "bridge.tool-content-guide"
                    ).body,
                )
            return preamble + _compact(transcript)

        if self.settings.workflow_task:
            return self._workflow_translation_prompt(
                request.messages,
                render,
                system_prompt=embedded_asset(
                    instructions, "bridge.translation-system"
                ).body,
            )

        messages: list[dict[str, Any]] = []
        seen_authority_messages: set[str] = set()
        for message in request.messages:
            compacted_message = self._compact_translation_message(message)
            if compacted_message.get("role") in {"system", "developer"}:
                identity = _compact(
                    {
                        "role": compacted_message.get("role"),
                        "content": compacted_message.get("content"),
                    }
                )
                if identity in seen_authority_messages:
                    continue
                seen_authority_messages.add(identity)
            messages.append(compacted_message)
        prompt = render(messages)
        if (
            len(prompt.encode("utf-8"))
            <= self.settings.maximum_translation_prompt_bytes
        ):
            return prompt

        pinned: set[int] = set()
        for index, message in enumerate(messages):
            if message.get("role") in {"system", "developer"}:
                pinned.add(index)
        for index, message in enumerate(messages):
            if message.get("role") == "user":
                pinned.add(index)
                next_index = index + 1
                while (
                    next_index < len(messages)
                    and messages[next_index].get("role") == "user"
                ):
                    pinned.add(next_index)
                    next_index += 1
                break

        selected = set(pinned)
        for index in range(len(messages) - 1, -1, -1):
            if index in selected:
                continue
            candidate_indexes = sorted({*selected, index})
            candidate = render([messages[item] for item in candidate_indexes])
            if (
                len(candidate.encode("utf-8"))
                <= self.settings.maximum_translation_prompt_bytes
            ):
                selected.add(index)

        compacted = render([messages[index] for index in sorted(selected)])
        if (
            len(compacted.encode("utf-8"))
            > self.settings.maximum_translation_prompt_bytes
        ):
            raise HermesBridgeError(
                "unsupported_tool_contract",
                "The tool contract leaves insufficient room for a bounded current transcript.",
            )
        return compacted

    def _workflow_translation_prompt(
        self,
        messages: list[dict[str, Any]],
        render: Callable[..., str],
        *,
        system_prompt: str,
    ) -> str:
        """Retain whole observations, task instructions and current tool schemas.

        Content inside a CAD observation is evidence, not expendable chat history.
        Keep a complete observation for every distinct tool, not just the newest
        tool. Older same-tool exchanges are not assumed semantically superseded;
        their omitted identities and arguments remain explicit task metadata.
        """
        groups: list[list[dict[str, Any]]] = []
        for message in messages:
            if (
                message.get("role") == "tool"
                and groups
                and groups[-1][0].get("role") == "assistant"
                and groups[-1][0].get("tool_calls")
            ):
                groups[-1].append(message)
            else:
                groups.append([message])

        pinned = {
            index
            for index, group in enumerate(groups)
            if group[0].get("role") in {"system", "developer", "user"}
        }
        if groups:
            pinned.add(len(groups) - 1)
        latest_by_tool: dict[str, int] = {}
        exchange_metadata: dict[int, list[dict[str, Any]]] = {}
        for index, group in enumerate(groups):
            calls = group[0].get("tool_calls", [])
            results = {
                message.get("tool_call_id"): message
                for message in group
                if message.get("role") == "tool"
            }
            if not calls:
                if results:
                    pinned.add(index)
                continue
            if len(results) != len(calls):
                pinned.add(index)
            metadata = []
            for call in calls:
                function = call.get("function", {})
                name = function.get("name")
                result = results.get(call.get("id"))
                if not isinstance(name, str) or result is None:
                    pinned.add(index)
                    continue
                latest_by_tool[name] = index
                content = result.get("content")
                if _workflow_observation_requires_retention(content):
                    pinned.add(index)
                try:
                    envelope = json.loads(content) if isinstance(content, str) else {}
                except (ValueError, TypeError):
                    envelope = {}
                envelope = envelope if isinstance(envelope, dict) else {}
                metadata.append(
                    {
                        "tool_call_id": call.get("id"),
                        "tool": name,
                        "tool_call_number": envelope.get("tool_call_number"),
                        "status": envelope.get("status", "unknown"),
                        "arguments": function.get("arguments"),
                    }
                )
            if metadata:
                exchange_metadata[index] = metadata
        pinned.update(latest_by_tool.values())

        projected: dict[int, tuple[dict[str, Any], bool]] | None = None
        decoded: dict[int, tuple[dict[str, Any], bool]] | None = None

        def within_text_budget(prompt: str) -> bool:
            try:
                # Count separator whitespace too: Hermes joins text-only parts with
                # newlines while preserving multimodal parts separately.
                transport_bytes = len(
                    "\n".join(self._workflow_transport_text_parts(prompt)).encode(
                        "utf-8"
                    )
                )
                transport_bytes += len(system_prompt.encode("utf-8"))
            except HermesBridgeError:
                return False
            return transport_bytes <= self.settings.maximum_translation_prompt_bytes

        def candidate(indexes: set[int]) -> tuple[str, bool]:
            retained = [
                message for index in sorted(indexes) for message in groups[index]
            ]
            omitted = [
                item
                for index, metadata in exchange_metadata.items()
                if index not in indexes
                for item in metadata
            ]
            prompt = render(retained, omitted)
            text_fits = within_text_budget(prompt)
            if not text_fits and projected is not None:
                reference_calls = [
                    message["tool_call_id"]
                    for message in retained
                    if projected[id(message)][1]
                ]
                prompt = render(
                    [projected[id(message)][0] for message in retained],
                    omitted,
                    reference_calls,
                )
                text_fits = within_text_budget(prompt)
                if not text_fits and decoded is not None:
                    decoded_calls = [
                        message["tool_call_id"]
                        for message in retained
                        if decoded[id(message)][1]
                    ]
                    prompt = render(
                        [decoded[id(message)][0] for message in retained],
                        omitted,
                        reference_calls,
                        decoded_calls,
                    )
                    text_fits = within_text_budget(prompt)
            return prompt, text_fits and len(retained) <= self.settings.maximum_messages

        selected = set(range(len(groups)))
        prompt, fits = candidate(selected)
        if fits:
            return prompt
        # Try a reversible representation before removing any complete exchange.
        # Retention decisions above still use the untouched native observations.
        projected = {id(message): project_tool_message(message) for message in messages}
        prompt, fits = candidate(selected)
        if fits:
            return prompt
        # Avoid double-escaping valid native JSON before considering omissions.
        # This is an encoding change inside the text transcript, never a change
        # to source messages, retention semantics or the downstream text budget.
        decoded = {
            id(message): decode_tool_message(projected[id(message)][0])
            for message in messages
        }
        prompt, fits = candidate(selected)
        if fits:
            return prompt
        # If eviction is still necessary and the old representation already
        # accommodates mandatory evidence, preserve that existing behavior.
        # Use decoded envelopes during eviction only to rescue a mandatory
        # floor that otherwise cannot fit at all.
        all_decoded = decoded
        decoded = None
        _, required_fits = candidate(pinned)
        if not required_fits:
            decoded = all_decoded
            _, required_fits = candidate(pinned)
        if not required_fits:
            raise HermesBridgeError(
                "workflow_context_limit",
                "The task instructions, available tool schemas, latest observation per tool, "
                "retained failure evidence and omission metadata "
                "exceed the workflow context limit or Hermes' per-item text limit. Narrow the task or request a smaller, "
                "focused tool observation; no model request was sent and no evidence was truncated.",
            )

        # Repeated-tool exchanges are the first eviction candidates. Sole/latest
        # sources and known adverse/unknown observations are pinned above.
        eviction_order = sorted(
            range(len(groups)),
            key=lambda index: (index not in exchange_metadata, index),
        )
        for index in eviction_order:
            if fits:
                break
            if index in pinned:
                continue
            selected.remove(index)
            prompt, fits = candidate(selected)
        if len(selected) < len(groups):
            logger.info(
                "workflow_transcript_compacted",
                omitted_messages=sum(
                    len(group)
                    for index, group in enumerate(groups)
                    if index not in selected
                ),
                prompt_bytes=len(prompt.encode("utf-8")),
            )
        return prompt

    @staticmethod
    def _workflow_transport_text_parts(prompt: str) -> list[str]:
        """Split between complete JSON values, never inside JSON strings.

        Concatenation preserves the original transcript exactly; newline joining
        also remains valid JSON with identical values. This supports both Hermes'
        text-only normalization and its image-preserving content-part path.
        """
        if len(prompt) <= _HERMES_TEXT_PART_CHARACTERS:
            return [prompt]
        preamble, serialized = prompt.split("\n", 1)
        transcript = json.loads(serialized)
        units = [preamble + "\n{"]

        def structural_units(value):
            # Hermes joins text parts with whitespace. JSON container boundaries
            # can carry that whitespace without changing any value or discarding
            # evidence. Scalar strings/numbers remain indivisible; never split
            # source text or a numeric token inside its JSON representation.
            if isinstance(value, dict):
                yield "{"
                for index, (key, child) in enumerate(sorted(value.items())):
                    yield ("," if index else "") + _compact(key) + ":"
                    yield from structural_units(child)
                yield "}"
            elif isinstance(value, list):
                yield "["
                for index, child in enumerate(value):
                    if index:
                        yield ","
                    yield from structural_units(child)
                yield "]"
            else:
                yield _compact(value)

        for index, (key, value) in enumerate(sorted(transcript.items())):
            units.append(("," if index else "") + _compact(key) + ":")
            if key in {"conversation", "tools"} and isinstance(value, list):
                units.append("[")
                for item_index, item in enumerate(value):
                    prefix = "," if item_index else ""
                    # A user message can contain many intact text/image parts.
                    # Keep it one message while placing transport boundaries
                    # between those parts. Tool/schema atomicity stays unchanged.
                    if (
                        key == "conversation"
                        and item.get("role") == "user"
                        and isinstance(item.get("content"), list)
                        and len(prefix + _compact(item)) > _HERMES_TEXT_PART_CHARACTERS
                    ):
                        units.append(prefix + "{")
                        for field_index, (field, field_value) in enumerate(
                            sorted(item.items())
                        ):
                            units.append(
                                ("," if field_index else "") + _compact(field) + ":"
                            )
                            if field == "content":
                                units.append("[")
                                units.extend(
                                    ("," if part_index else "") + _compact(part)
                                    for part_index, part in enumerate(field_value)
                                )
                                units.append("]")
                            else:
                                units.append(_compact(field_value))
                        units.append("}")
                    elif len(prefix + _compact(item)) > _HERMES_TEXT_PART_CHARACTERS:
                        if prefix:
                            units.append(prefix)
                        units.extend(structural_units(item))
                    else:
                        units.append(prefix + _compact(item))
                units.append("]")
            else:
                units.append(_compact(value))
        units.append("}")
        parts: list[str] = []
        current = ""
        for unit in units:
            if len(unit) > _HERMES_TEXT_PART_CHARACTERS:
                raise HermesBridgeError(
                    "workflow_context_limit",
                    "A complete task message, tool observation, schema or context item exceeds Hermes' "
                    "per-item text limit. Request a smaller item; no model request was sent and no evidence was truncated.",
                )
            if current and len(current) + len(unit) > _HERMES_TEXT_PART_CHARACTERS:
                parts.append(current)
                current = ""
            current += unit
        if current:
            parts.append(current)
        return parts

    @staticmethod
    def _compact_translation_message(message: Mapping[str, Any]) -> dict[str, Any]:
        compacted = dict(message)
        content = compacted.get("content")
        if isinstance(content, list):
            content = _compact(content)
        if isinstance(content, str):
            encoded = content.encode("utf-8")
            if len(encoded) > _TRANSLATION_MESSAGE_BYTES:
                marker = _TRANSLATION_TRUNCATION_MARKER.encode("utf-8")
                available = _TRANSLATION_MESSAGE_BYTES - len(marker)
                head_bytes = (available * 4) // 5
                tail_bytes = available - head_bytes
                head = encoded[:head_bytes].decode("utf-8", errors="ignore")
                tail = encoded[-tail_bytes:].decode("utf-8", errors="ignore")
                compacted["content"] = head + _TRANSLATION_TRUNCATION_MARKER + tail
        return compacted

    def _upstream_payload(
        self,
        request: _ValidatedRequest,
        *,
        translate: bool,
        stream: bool,
        repair: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        messages = request.messages
        if translate:
            # Engineering reference images must remain multimodal attachments.
            # Serializing them into the decision transcript would both hide the
            # pixels from the model and truncate their base64 as ordinary text.
            images: list[dict[str, Any]] = []
            translated_messages = []
            for message in request.messages:
                content = message.get("content")
                if (
                    self.settings.workflow_task
                    and message.get("role") in {"user", "tool"}
                    and isinstance(content, list)
                ):
                    parts = []
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "image_url":
                            image = part.get("image_url")
                            if (
                                not isinstance(image, dict)
                                or not isinstance(image.get("url"), str)
                                or not image["url"].startswith("data:image/")
                            ):
                                raise HermesBridgeError(
                                    "invalid_request",
                                    "Workflow image references must contain workspace image data.",
                                )
                            images.append(part)
                            instructions = embedded_instruction_set(
                                request.instruction_set
                            )
                            label = (
                                embedded_asset(
                                    instructions, "bridge.image-tool-label"
                                ).render(
                                    {
                                        "image_index": str(len(images)),
                                        "tool_call_id": str(
                                            message.get("tool_call_id")
                                        ),
                                    }
                                )
                                if message.get("role") == "tool"
                                else embedded_asset(
                                    instructions, "bridge.image-reference-label"
                                ).render({"image_index": str(len(images))})
                            )
                            parts.append(
                                {
                                    "type": "text",
                                    "text": f"[{label}]",
                                }
                            )
                        else:
                            parts.append(part)
                    message = {**message, "content": parts}
                translated_messages.append(
                    _workflow_user_text_parts(message)
                    if self.settings.workflow_task
                    else message
                )
            prompt = self._translation_prompt(
                replace(request, messages=translated_messages), repair=repair
            )
            text_parts = (
                self._workflow_transport_text_parts(prompt)
                if self.settings.workflow_task
                else [prompt]
            )
            content = (
                [{"type": "text", "text": part} for part in text_parts] + images
                if images or len(text_parts) > 1
                else prompt
            )
            messages = [
                {
                    "role": "system",
                    "content": embedded_asset(
                        embedded_instruction_set(request.instruction_set),
                        "bridge.translation-system",
                    ).body,
                },
                {"role": "user", "content": content},
            ]
        return {"model": "hermes", "messages": messages, "stream": stream}

    def _translation_repair_payload(
        self,
        request: _ValidatedRequest,
        upstream: Mapping[str, Any],
        error: HermesBridgeError,
    ) -> dict[str, Any]:
        try:
            previous = self._content(upstream)[:8192]
        except HermesBridgeError:
            previous = ""
        # An explicit Hermes session replaces incoming prior turns with stored
        # history. Our fresh model-locked session has none. Keep the task, tool
        # schemas, images and repair together in the current user message.
        # The existing renderer counts the whole repair in its context budget;
        # it cannot discard the correction or split it from required evidence.
        return self._upstream_payload(
            request,
            translate=True,
            stream=False,
            repair={
                "previous_decision": previous,
                "instructions": embedded_asset(
                    embedded_instruction_set(request.instruction_set),
                    "bridge.translation-repair",
                ).render({"error": str(error)}),
            },
        )

    def _map_http_error(self, response: httpx.Response) -> HermesBridgeError:
        if response.status_code in {401, 403}:
            return HermesBridgeError(
                "hermes_auth_failed",
                "Hermes rejected its configured credentials.",
                status_code=502,
            )
        if response.status_code == 429:
            return HermesBridgeError(
                "hermes_unavailable",
                "Hermes is temporarily rate limited.",
                status_code=503,
            )
        return HermesBridgeError(
            "hermes_unavailable",
            "Hermes did not complete the AI request.",
            status_code=502,
        )

    async def _post_json(
        self,
        payload: dict[str, Any],
        request_id: str,
        *,
        pre_send_observer=None,
        sdk_observer=None,
    ) -> dict[str, Any]:
        if (self.settings.expected_resolution or {}).get(
            "adapter"
        ) == "hermes-model-sdk":
            from .workflow_sdk import workflow_sdk_completion

            return await workflow_sdk_completion(
                payload,
                self.settings.expected_resolution,
                invocation_observer=sdk_observer,
                qualified_observer=pre_send_observer,
            )
        if not self.available:
            raise HermesBridgeError(
                "hermes_unavailable", "Hermes AI is not configured.", status_code=503
            )
        try:
            async with httpx.AsyncClient(
                transport=self._transport,
                timeout=self.settings.timeout_seconds,
            ) as client:
                if self.settings.expected_resolution is not None:
                    from .hermes_config import HermesApiSettings
                    from .workflow_model_routing import lock_workflow_model

                    frozen_headers = self._headers(request_id)
                    frozen_headers["X-Hermes-Session-Id"] = (
                        "wright-workflow-bridge-" + uuid.uuid4().hex
                    )
                    model_lock = await lock_workflow_model(
                        client,
                        HermesApiSettings(
                            self.settings.base_url,
                            self.settings.api_key,
                            "workflow-bridge",
                        ),
                        self.settings.expected_resolution,
                        frozen_headers["X-Hermes-Session-Id"],
                    )
                    if pre_send_observer is not None:
                        await pre_send_observer(model_lock)
                response = await client.post(
                    f"{self.settings.base_url.rstrip('/')}/v1/chat/completions",
                    json=payload,
                    headers=frozen_headers
                    if self.settings.expected_resolution is not None
                    else self._headers(request_id),
                )
        except httpx.TimeoutException as error:
            raise HermesBridgeError(
                "upstream_timeout", "Hermes AI request timed out.", status_code=504
            ) from error
        except httpx.HTTPError as error:
            raise HermesBridgeError(
                "hermes_unavailable", "Hermes AI is unavailable.", status_code=503
            ) from error
        if response.status_code >= 400:
            raise self._map_http_error(response)
        try:
            value = response.json()
        except ValueError as error:
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned an invalid response.",
                status_code=502,
            ) from error
        if not isinstance(value, dict):
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned an invalid response.",
                status_code=502,
            )
        return value

    @staticmethod
    def _content(upstream: Mapping[str, Any]) -> str:
        try:
            content = upstream["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned no translatable decision.",
                status_code=502,
            ) from error
        if not isinstance(content, str):
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned no translatable decision.",
                status_code=502,
            )
        return content

    def _translate_decision(
        self, upstream: Mapping[str, Any], request: _ValidatedRequest
    ) -> dict[str, Any]:
        content = self._content(upstream)
        try:
            decision = json.loads(content)
        except json.JSONDecodeError as error:
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned malformed tool-decision JSON.",
                status_code=502,
            ) from error
        if not isinstance(decision, dict) or set(decision) - {
            "kind",
            "name",
            "arguments",
            "content",
        }:
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned an invalid tool decision.",
                status_code=502,
            )
        request_id = uuid.uuid4().hex
        if decision.get("kind") == "message":
            if request.tool_choice != "auto" or not isinstance(
                decision.get("content"), str
            ):
                raise HermesBridgeError(
                    "translation_invalid",
                    "Hermes returned a message when a tool call was required.",
                    status_code=502,
                )
            return self._completion(
                request_id, str(decision["content"]), finish_reason="stop"
            )
        if decision.get("kind") != "tool_call":
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned an invalid tool call: kind must be tool_call.",
                status_code=502,
            )
        if not isinstance(decision.get("arguments"), dict):
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned an invalid tool call: arguments must be an object.",
                status_code=502,
            )
        named_choice = (
            request.tool_choice.get("function", {}).get("name")
            if isinstance(request.tool_choice, dict)
            else None
        )
        name = decision.get("name")
        tools = {tool.name: tool for tool in request.tools}
        if (
            not isinstance(name, str)
            or name not in tools
            or (named_choice and name != named_choice)
        ):
            suffix = " named tool." if named_choice else " allowed tool."
            raise HermesBridgeError(
                "translation_invalid",
                f"Hermes did not select the requested{suffix}",
                status_code=502,
            )
        try:
            Draft202012Validator(tools[name].parameters).validate(decision["arguments"])
        except ValidationError as error:
            detail = ""
            if self.settings.workflow_task:
                # ValidationError.message can include the full submitted instance.
                # Report locations/constraints, never argument values or credentials.
                issues = []
                for issue in [error, *error.context[:3]]:
                    summary: dict[str, Any] = {
                        "path": [str(part)[:80] for part in issue.absolute_path],
                        "schema_path": [
                            str(part)[:80] for part in issue.absolute_schema_path
                        ],
                        "constraint": issue.validator,
                    }
                    if issue.validator == "required" and isinstance(
                        issue.instance, dict
                    ):
                        summary["missing"] = [
                            key[:80]
                            for key in issue.validator_value
                            if key not in issue.instance
                        ][:10]
                    if issue.validator == "type":
                        summary["expected_type"] = issue.validator_value
                    issues.append(summary)
                logger.info(
                    "workflow_tool_arguments_rejected", tool=name, issues=issues
                )
                detail = f" Tool {name}; validation: {_compact(issues)}"
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes returned arguments that do not match the tool schema." + detail,
                status_code=502,
            ) from error
        return self._tool_completion(request_id, name, decision["arguments"])

    def _decision_response_evidence(
        self, upstream: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Record protocol structure and bounded redacted final-message context.

        A failed final repair has no subsequent request in which to retain its
        response. Keep a bounded structural receipt at the same invocation owner,
        before translation can raise. The hash identifies the original text; this
        is not a claim to retain its full content or provider-internal behavior.
        """
        try:
            content = self._content(upstream)
        except HermesBridgeError:
            return {"content_available": False}
        encoded = content.encode("utf-8")
        evidence: dict[str, Any] = {
            "content_available": True,
            "sha256": hashlib.sha256(encoded).hexdigest(),
            "size_bytes": len(encoded),
        }
        try:
            decision = json.loads(content)
        except json.JSONDecodeError as error:
            return {
                **evidence,
                "json_valid": False,
                "error_line": error.lineno,
                "error_column": error.colno,
                "error_offset": error.pos,
            }
        evidence.update(json_valid=True, root_type=type(decision).__name__)
        if isinstance(decision, dict):
            allowed = {"kind", "name", "arguments", "content"}
            kind = decision.get("kind")
            evidence.update(
                present_fields=sorted(allowed.intersection(decision)),
                unknown_field_count=len(set(decision) - allowed),
                kind=kind
                if isinstance(kind, str) and kind in {"tool_call", "message"}
                else "invalid",
                arguments_type=type(decision.get("arguments")).__name__,
                name_type=type(decision.get("name")).__name__,
                content_type=type(decision.get("content")).__name__,
            )
            if kind == "message" and isinstance(decision.get("content"), str):
                # A message can explain why no tool was selected. Preserve that
                # diagnostic at the existing private invocation owner, without
                # retaining tool argument values or unbounded response bodies.
                text = decision["content"]
                try:
                    text = _compact(
                        redact_mapping({"content": json.loads(text)})["content"]
                    )
                except (ValueError, TypeError):
                    pass
                redacted = redact_text(text, [self.settings.api_key])
                evidence["message_excerpt"] = redacted[:4096]
                evidence["message_excerpt_truncated"] = len(redacted) > 4096
        return evidence

    @staticmethod
    def _completion(
        completion_id: str, content: str, *, finish_reason: str
    ) -> dict[str, Any]:
        return {
            "id": f"chatcmpl-{completion_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": _MODEL_ALIAS,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": finish_reason,
                }
            ],
        }

    @classmethod
    def _tool_completion(
        cls, completion_id: str, name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        result = cls._completion(completion_id, "", finish_reason="tool_calls")
        result["choices"][0]["message"] = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": f"call_{uuid.uuid4().hex}",
                    "type": "function",
                    "function": {"name": name, "arguments": _compact(arguments)},
                }
            ],
        }
        return result

    async def complete(
        self,
        payload: Mapping[str, Any],
        *,
        request_id: str | None = None,
        invocation_observer=None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        request = self._validate(payload)
        validated = time.perf_counter()
        correlation = request_id or uuid.uuid4().hex
        translate = bool(request.tools) and request.tool_choice != "none"
        upstream_started = time.perf_counter()
        invocations = []
        sdk_invocations = []

        async def retain_sdk(record):
            sdk_invocations.append(record)
            if invocation_observer is not None:
                await invocation_observer(deepcopy(record))

        async def submit(actual_payload, operation):
            capture = invocation_evidence(
                actual_payload,
                operation=operation,
                instruction_set=request.instruction_set,
                attempt=len(invocations) + 1,
            )
            capture["capture_scope"] = "hermes_bridge_upstream_request"
            invocations.append(capture)
            if self.settings.expected_resolution is not None:

                async def before_send(model_lock):
                    capture["capture_phase"] = "submission"
                    capture[
                        "frozen_model_resolution"
                        if (self.settings.expected_resolution or {}).get("adapter")
                        == "hermes-model-sdk"
                        else "frozen_model_lock"
                    ] = model_lock
                    if invocation_observer is not None:
                        await invocation_observer(deepcopy(capture))

                observed = await self._post_json(
                    actual_payload,
                    correlation,
                    pre_send_observer=before_send,
                    sdk_observer=retain_sdk,
                )
            else:
                if invocation_observer is not None:
                    await invocation_observer(deepcopy(capture))
                observed = await self._post_json(actual_payload, correlation)
            capture["upstream_reported_model"] = observed.get("model")
            capture["upstream_usage"] = observed.get("usage")
            capture["capture_phase"] = "response"
            if translate:
                capture["decision_response"] = self._decision_response_evidence(
                    observed
                )
            if self.settings.expected_resolution is not None:
                capture["frozen_model_resolution"] = self.settings.expected_resolution
            if invocation_observer is not None:
                await invocation_observer(deepcopy(capture))
            return observed

        upstream = await submit(
            self._upstream_payload(request, translate=translate, stream=False),
            "hermes-bridge-translation" if translate else "hermes-bridge-completion",
        )
        upstream_completed = time.perf_counter()
        repair_attempted = False
        if translate:
            try:
                result = self._translate_decision(upstream, request)
            except HermesBridgeError as error:
                if error.code != "translation_invalid":
                    raise
                repair_attempted = True
                upstream = await submit(
                    self._translation_repair_payload(request, upstream, error),
                    "hermes-bridge-translation-repair",
                )
                result = self._translate_decision(upstream, request)
        else:
            result = dict(upstream)
        translated = time.perf_counter()
        result["model"] = _MODEL_ALIAS
        if len(_compact(result).encode("utf-8")) > self.settings.maximum_output_bytes:
            raise HermesBridgeError(
                "translation_invalid",
                "Hermes output exceeded the bridge limit.",
                status_code=502,
            )
        logger.info(
            "rivet_ai_bridge_completed",
            request_id=correlation,
            tool_count=len(request.tools),
            translated=translate,
            repair_attempted=repair_attempted,
            validation_ms=round((validated - started) * 1000, 3),
            upstream_ms=round((upstream_completed - upstream_started) * 1000, 3),
            translation_ms=round((translated - upstream_completed) * 1000, 3),
            total_ms=round((translated - started) * 1000, 3),
        )
        if (
            request.instruction_set is not None
            or invocation_observer is not None
            or self.settings.expected_resolution is not None
        ):
            if upstream.get("usage") is not None:
                result["usage"] = upstream["usage"]
            return HermesBridgeCompletion(
                result, [*invocations, *sdk_invocations], upstream.get("model")
            )
        return result

    @staticmethod
    def _sse_translation(result: Mapping[str, Any]) -> tuple[str, ...]:
        completion_id = result["id"]
        choice = result["choices"][0]
        message = choice["message"]
        first = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": result["created"],
            "model": _MODEL_ALIAS,
            "choices": [
                {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
            ],
        }
        if message.get("tool_calls"):
            delta = {"tool_calls": [{"index": 0, **message["tool_calls"][0]}]}
        else:
            delta = {"content": message.get("content", "")}
        second = {
            **first,
            "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        }
        final = {
            **first,
            "choices": [
                {"index": 0, "delta": {}, "finish_reason": choice["finish_reason"]}
            ],
        }
        return tuple(
            f"data: {_compact(item)}\n\n" for item in (first, second, final)
        ) + ("data: [DONE]\n\n",)

    async def stream(
        self, payload: Mapping[str, Any], *, request_id: str | None = None
    ) -> AsyncIterator[str]:
        request = self._validate(payload)
        correlation = request_id or uuid.uuid4().hex
        translate = bool(request.tools) and request.tool_choice != "none"
        if translate:
            upstream = await self._post_json(
                self._upstream_payload(request, translate=True, stream=False),
                correlation,
            )
            try:
                result = self._translate_decision(upstream, request)
            except HermesBridgeError as error:
                if error.code != "translation_invalid":
                    raise
                upstream = await self._post_json(
                    self._translation_repair_payload(request, upstream, error),
                    correlation,
                )
                result = self._translate_decision(upstream, request)
            for chunk in self._sse_translation(result):
                yield chunk
            return

        if not self.available:
            raise HermesBridgeError(
                "hermes_unavailable", "Hermes AI is not configured.", status_code=503
            )
        try:
            async with httpx.AsyncClient(
                transport=self._transport, timeout=self.settings.timeout_seconds
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self.settings.base_url.rstrip('/')}/v1/chat/completions",
                    json=self._upstream_payload(request, translate=False, stream=True),
                    headers=self._headers(correlation),
                ) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        raise self._map_http_error(response)
                    async for line in response.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            yield "data: [DONE]\n\n"
                            return
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(chunk, dict):
                            chunk["model"] = _MODEL_ALIAS
                            yield f"data: {_compact(chunk)}\n\n"
        except HermesBridgeError:
            raise
        except httpx.TimeoutException as error:
            raise HermesBridgeError(
                "upstream_timeout", "Hermes AI request timed out.", status_code=504
            ) from error
        except httpx.HTTPError as error:
            raise HermesBridgeError(
                "hermes_unavailable", "Hermes AI is unavailable.", status_code=503
            ) from error
