"""Desktop conversation handoff at Wright's existing decision callbacks.

This prototype never calls an LLM endpoint. Repository methods are injected;
connection authentication and run authority belong to the composition layer.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from core.desktop_reasoning import (
    DesktopHarnessBinding,
    DesktopReasoningRequest,
    decode_desktop_image as desktop_inline_image,
)
from core.process_validation import canonical_digest
from core.workflow_model_routing import WorkflowDesktopTextResolution
from core.workflow_step_outcomes import InvalidStepOutcomeError, UnattendedStepOutcome

from .workflow_instructions import (
    embedded_instruction_set,
    invocation_evidence,
    workflow_response_instructions,
    validate_workflow_assumptions,
)


class DesktopReasoningPort(Protocol):
    def put_request(self, request): ...
    def consume_response(self, workspace_id, session_id, request_id): ...
    def interrupt(self, workspace_id, session_id, request_id, *, outcome): ...


class DesktopTextReply(str):
    pass


class DesktopActionResult(dict):
    pass


async def _persist_request(repository, request):
    """Observe a started SQLite write before acknowledging cancellation."""
    worker = asyncio.create_task(asyncio.to_thread(repository.put_request, request))
    cancelled = False
    while not worker.done():
        try:
            await asyncio.shield(worker)
        except asyncio.CancelledError:
            cancelled = True
    result = worker.result()
    if cancelled:
        raise asyncio.CancelledError
    return result


class DesktopWorkflowReasoner:
    """One explicitly bound run; no automatic reconnect/restart replay."""

    def __init__(
        self,
        repository: DesktopReasoningPort,
        *,
        workspace_id,
        session_id,
        run_id,
        binding: DesktopHarnessBinding,
        poll_interval=0.1,
        initial_ordinal=0,
    ):
        self.repository = repository
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.run_id = run_id
        self.binding = DesktopHarnessBinding.model_validate_json(
            binding.model_dump_json()
        )
        self.poll_interval = poll_interval
        if type(initial_ordinal) is not int or not 0 <= initial_ordinal < 10000:
            raise ValueError(
                "Desktop continuation requires a qualified decision ordinal"
            )
        self._ordinal = initial_ordinal

    def resolution(self):
        public = {
            "adapter": "openai-desktop-harness",
            "binding": self.binding.model_dump(mode="json"),
        }
        return WorkflowDesktopTextResolution.model_validate(
            {**public, "configuration_digest": canonical_digest(public)}
        )

    async def capabilities(self):
        # Readiness of this callback is not evidence of an authenticated live
        # desktop connection. Its composition must establish that separately.
        return {
            "available": True,
            "resolution": self.resolution().model_dump(mode="json"),
        }

    async def _request(
        self,
        *,
        kind,
        output_format,
        payload,
        instructions,
        resolved=None,
        invocation_observer=None,
        expected_resolution=None,
    ):
        if expected_resolution is not None:
            expected = WorkflowDesktopTextResolution.model_validate(expected_resolution)
            if expected != self.resolution():
                raise ValueError(
                    "The frozen desktop binding changed; reconcile or restore it before continuing"
                )
        self._ordinal += 1
        request = DesktopReasoningRequest(
            request_id=str(uuid4()),
            workspace_id=self.workspace_id,
            session_id=self.session_id,
            run_id=self.run_id,
            ordinal=self._ordinal,
            created_at=datetime.now(timezone.utc).isoformat(),
            kind=kind,
            output_format=output_format,
            binding=self.binding,
            instruction_set_digest=instructions.digest,
            payload=payload,
        )
        evidence = invocation_evidence(
            payload,
            operation="desktop-workflow-" + kind,
            instruction_set=instructions,
            resolved=resolved,
        )
        evidence.update(
            {
                "capture_scope": "desktop_handoff_request",
                "desktop_request_id": request.request_id,
                "desktop_request_digest": request.digest,
                "binding_digest": request.binding.digest,
                "model_identity_source": request.binding.model_identity_source,
                "reported_model": request.binding.reported_model,
            }
        )
        try:
            await _persist_request(self.repository, request)
            if invocation_observer:
                await invocation_observer(evidence)
            while True:
                response = await asyncio.to_thread(
                    self.repository.consume_response,
                    self.workspace_id,
                    self.session_id,
                    request.request_id,
                )
                if response is not None:
                    if invocation_observer:
                        await invocation_observer(
                            {
                                **evidence,
                                "capture_scope": "desktop_handoff_response_receipt",
                                "response_id": response.response_id,
                                "response_digest": response.digest,
                                "outcome": "received",
                            }
                        )
                    return response.reply, evidence
                await asyncio.sleep(self.poll_interval)
        except BaseException:
            try:
                await asyncio.to_thread(
                    self.repository.interrupt,
                    self.workspace_id,
                    self.session_id,
                    request.request_id,
                    outcome="owner_interrupted",
                )
            except KeyError:
                # A rejected insert has no handoff receipt to interrupt.
                pass
            raise

    async def generate_response(
        self,
        prompt,
        output_format,
        *,
        images=None,
        instruction_set=None,
        instruction_override=None,
        invocation_observer=None,
        expected_resolution=None,
    ):
        if (
            images and self.binding.image_input_profile == "unavailable"
        ) or output_format not in {"text", "markdown", "html", "json"}:
            raise ValueError("Desktop image inputs and generation are not qualified")
        content = prompt
        if images:
            for image in images:
                desktop_inline_image(image, profile=self.binding.image_input_profile)
            content = [{"type": "text", "text": prompt}] + [
                {"type": "image_url", "image_url": {"url": image}} for image in images
            ]
        instructions = embedded_instruction_set(instruction_set)
        resolved = workflow_response_instructions(
            output_format,
            instruction_set=instructions,
            instruction_override=instruction_override,
        )
        payload = {
            "messages": [
                {"role": "system", "content": resolved.text},
                {"role": "user", "content": content},
            ],
            "tools": [],
            "tool_choice": "none",
        }
        reply, evidence = await self._request(
            kind="response",
            output_format=output_format,
            payload=payload,
            instructions=instructions,
            resolved=resolved,
            invocation_observer=invocation_observer,
            expected_resolution=expected_resolution,
        )
        try:
            outcome = UnattendedStepOutcome.model_validate_json(reply)
            assumptions = validate_workflow_assumptions(
                [item.model_dump(mode="json") for item in outcome.assumptions],
                resolved.assumption_policy,
            )
        except (ValueError, TypeError) as error:
            raise InvalidStepOutcomeError(
                "The desktop returned an invalid unattended-step disposition; no output was accepted"
            ) from error
        result = DesktopTextReply(outcome.response)
        result.wright_outcome = outcome.model_dump(mode="json")
        result.wright_assumptions = assumptions
        result.wright_instructions = resolved.model_dump(mode="json")
        result.wright_invocations = [evidence]
        return result

    async def decide_action(
        self,
        messages,
        tools,
        *,
        required=False,
        output_format="text",
        instruction_set=None,
        instruction_override=None,
        invocation_observer=None,
        expected_resolution=None,
    ):
        has_images = any(
            isinstance(message, dict)
            and isinstance(message.get("content"), list)
            and any(
                isinstance(part, dict)
                and part.get("type") in {"image_url", "image", "input_image"}
                for part in message["content"]
            )
            for message in messages
        )
        if has_images:
            if self.binding.image_input_profile == "unavailable":
                raise ValueError("Desktop image inputs are not qualified")
            for message in messages:
                if not isinstance(message, dict) or not isinstance(
                    message.get("content"), list
                ):
                    continue
                for part in message["content"]:
                    if isinstance(part, dict) and part.get("type") in {
                        "image_url",
                        "image",
                        "input_image",
                    }:
                        if (
                            set(part) != {"type", "image_url"}
                            or part["type"] != "image_url"
                            or not isinstance(part["image_url"], dict)
                            or set(part["image_url"]) != {"url"}
                        ):
                            raise ValueError(
                                "Desktop image parts require the exact inline image contract"
                            )
                        desktop_inline_image(
                            part["image_url"]["url"],
                            profile=self.binding.image_input_profile,
                        )
        instructions = embedded_instruction_set(instruction_set)
        # Existing runtime already resolves saved task/recovery instructions and
        # constructs the precise schema/context. Retain that request unchanged.
        reply, evidence = await self._request(
            kind="action",
            output_format=output_format,
            payload={
                "messages": messages,
                "tools": tools,
                "tool_choice": "required" if required else "auto",
            },
            instructions=instructions,
            invocation_observer=invocation_observer,
            expected_resolution=expected_resolution,
        )
        result = DesktopActionResult(reply.model_dump(mode="json"))
        result.wright_invocations = [evidence]
        return result
