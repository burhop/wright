import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from agent_adapters.desktop_reasoning import DesktopWorkflowReasoner
from agent_adapters.workflow_instructions import load_default_workflow_instructions
from core.desktop_reasoning import (
    DesktopActionReply,
    DesktopHarnessBinding,
    DesktopReasoningResponse,
)
from data_vault.desktop_reasoning_repository import (
    DesktopHandoffConflict,
    DesktopReasoningRepository,
)
from workspace_service.workflow_instruction_settings import (
    materialize_new_workflow_instructions,
)
from workspace_service.workflow_model_routing import freeze_workflow_model_routing
from workspace_service.workflow_reasoning_dispatch import (
    WorkflowReasoningCallbacks,
    resolve_workflow_reasoning_callbacks,
)
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    task,
    source,
    service,
)


def reasoner(repo, **patch):
    return DesktopWorkflowReasoner(
        repo,
        workspace_id="workspace-1",
        session_id="session-1",
        run_id="run-1",
        binding=DesktopHarnessBinding(connection_id="connection-1", **patch),
        poll_interval=0.005,
    )


async def pending(repo, after=None, running=None):
    async def wait():
        while True:
            if running is not None and running.done():
                await running
                raise AssertionError("Execution completed without the expected handoff")
            tasks = [
                task
                for task in repo.pending("workspace-1", "session-1")
                if task.request_id != after
            ]
            if tasks:
                return tasks[0]
            await asyncio.sleep(0.005)

    return await asyncio.wait_for(wait(), 5)


def answer(repo, request, value):
    return repo.submit_response(
        "workspace-1",
        "session-1",
        DesktopReasoningResponse(
            request_id=request.request_id,
            request_digest=request.digest,
            binding_digest=request.binding.digest,
            response_id=str(uuid4()),
            received_at=datetime.now(timezone.utc).isoformat(),
            reply=json.dumps(
                {
                    "version": "wright.unattended-step/1",
                    "status": "completed",
                    "reason": None,
                    "response": value,
                }
            ),
        ),
    )


def test_existing_executor_accepts_scoped_reply_with_saved_instructions_and_frozen_binding(
    tmp_path, monkeypatch
):
    import httpx

    def no_model_service(*args, **kwargs):
        raise AssertionError("This callback must not use an HTTP model service")

    monkeypatch.setattr(httpx, "AsyncClient", no_model_service)
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    accepted = materialize_new_workflow_instructions(
        source(task(fmt="text")), load_default_workflow_instructions()
    )
    plan = compile_prompt_workflow(accepted)
    app = service(tmp_path)
    app.workflow_model_capabilities = desktop.capabilities

    def bind_run(**scope):
        assert scope["workspace_dir"] == str(tmp_path)
        assert scope["run_id"] == "run-1"
        assert scope["execution_context"]["model_routing"][
            "text"
        ] == desktop.resolution().model_dump(mode="json")
        return WorkflowReasoningCallbacks(
            desktop.generate_response, desktop.decide_action
        )

    app.workflow_reasoning_factory = bind_run

    async def forbidden_fallback(*args, **kwargs):
        raise AssertionError("Desktop work must not use a legacy model callback")

    events = []

    async def run():
        frozen, context = await freeze_workflow_model_routing(app, plan, {})

        async def emit(event):
            events.append(event)

        running = asyncio.create_task(
            execute_prompt_workflow(
                service=app,
                workspace_dir=str(tmp_path),
                plan=frozen,
                input_values={},
                response_generator=forbidden_fallback,
                execution_context=context,
                on_event=emit,
                run_id="run-1",
            )
        )
        request = await pending(repo)
        assert request.binding.reported_model is None
        assert (
            request.instruction_set_digest
            == load_default_workflow_instructions().digest
        )
        assert request.payload["messages"][0]["role"] == "system"
        assert request.payload["tools"] == []
        answer(repo, request, "A verified callback test result")
        return await asyncio.wait_for(running, 10)

    result = asyncio.run(run())
    assert result["outputs"][0]["output_path"] == "report.txt"
    assert (tmp_path / "report.txt").read_text() == "A verified callback test result"
    scopes = {
        e["invocation"]["capture_scope"]
        for e in events
        if e["kind"] == "model_invocation"
    }
    assert "desktop_handoff_request" in scopes
    assert "desktop_handoff_response_receipt" in scopes


def test_missing_desktop_dispatch_cannot_use_legacy_callback(tmp_path):
    desktop = reasoner(DesktopReasoningRepository(tmp_path / "wright.sqlite"))
    with pytest.raises(ValueError, match="no bound reasoning callback"):
        resolve_workflow_reasoning_callbacks(
            service(tmp_path),
            workspace_dir=str(tmp_path),
            run_id="run-1",
            execution_context={
                "model_routing": {"text": desktop.resolution().model_dump(mode="json")}
            },
            response=lambda *_: "A silent fallback",
            action=None,
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"requested_model": "different-selection"},
        {"image_input_profile": "inline-png-jpeg-engineering-v1"},
    ],
)
def test_frozen_binding_drift_blocks_before_another_request(tmp_path, patch):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    first = reasoner(repo)
    second = reasoner(repo, **patch)
    plan = compile_prompt_workflow(source(task(fmt="text")))
    app = service(tmp_path)

    async def run():
        app.workflow_model_capabilities = first.capabilities
        _, context = await freeze_workflow_model_routing(app, plan, {})
        app.workflow_model_capabilities = second.capabilities
        with pytest.raises(WorkflowSourceExecutionError) as changed:
            await freeze_workflow_model_routing(app, plan, {}, expected_context=context)
        assert changed.value.code == "WORKFLOW_MODEL_CHANGED"
        with pytest.raises(ValueError, match="frozen desktop binding changed"):
            await second.generate_response(
                "Task",
                "text",
                expected_resolution=first.resolution().model_dump(mode="json"),
            )

    asyncio.run(run())
    assert repo.pending("workspace-1", "session-1") == []


def test_invalid_json_fails_existing_validator_and_writes_no_output(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    plan = compile_prompt_workflow(source(task(fmt="json")))

    async def run():
        running = asyncio.create_task(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=desktop.generate_response,
                run_id="run-1",
            )
        )
        request = await pending(repo)
        answer(repo, request, "not a JSON document")
        with pytest.raises(WorkflowSourceExecutionError):
            await running

    asyncio.run(run())
    assert not (tmp_path / "report.json").exists()


@pytest.mark.parametrize("profile", ["unavailable", "inline-png-jpeg-engineering-v1"])
def test_cancellation_retains_receipt_and_denies_late_answer(tmp_path, profile):
    import base64
    from pathlib import Path

    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo, image_input_profile=profile)
    images = None
    if profile != "unavailable":
        root = Path(__file__).resolve().parents[3]
        data = (
            root
            / "artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/block-native-006/outputs/render_isometric.png"
        ).read_bytes()
        images = ["data:image/png;base64," + base64.b64encode(data).decode()]

    async def run():
        running = asyncio.create_task(
            desktop.generate_response("Task", "text", images=images)
        )
        request = await pending(repo)
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running
        assert (
            repo.get_request("workspace-1", "session-1", request.request_id) == request
        )
        with pytest.raises(DesktopHandoffConflict):
            answer(repo, request, "Late response")
        reopened = DesktopReasoningRepository(tmp_path / "wright.sqlite")
        assert (
            reopened.get_request("workspace-1", "session-1", request.request_id).digest
            == request.digest
        )
        assert reopened.pending("workspace-1", "session-1") == []
        with pytest.raises(DesktopHandoffConflict):
            answer(reopened, request, "Late response after reopen")

    asyncio.run(run())


def test_unqualified_image_capability_is_explicit_and_creates_no_request(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    with pytest.raises(ValueError, match="not qualified"):
        asyncio.run(
            desktop.generate_response(
                "Task", "text", images=["data:image/png;base64,ignored"]
            )
        )
    assert repo.pending("workspace-1", "session-1") == []


@pytest.mark.parametrize(
    "part",
    [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,ignored"}},
        {
            "type": "image_url",
            "image_url": {"url": "https://example.invalid/image.png"},
        },
        {"type": "image", "mimeType": "image/png", "data": "ignored"},
        {"type": "input_image", "image_url": "data:image/png;base64,ignored"},
    ],
)
def test_unqualified_action_image_is_rejected_before_persistence_or_observation(
    tmp_path, part
):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    observations = []

    async def observe(evidence):
        observations.append(evidence)

    with pytest.raises(ValueError, match="image inputs are not qualified"):
        asyncio.run(
            asyncio.wait_for(
                desktop.decide_action(
                    [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Inspect the original sketch"},
                                part,
                            ],
                        }
                    ],
                    [],
                    invocation_observer=observe,
                ),
                timeout=1,
            )
        )
    assert desktop._ordinal == 0
    assert repo.pending("workspace-1", "session-1") == []
    assert observations == []


@pytest.mark.parametrize("error_code", ["timeout", "internal"])
def test_uncertain_provider_effect_stops_desktop_decision_loop_without_replay(
    tmp_path, error_code
):
    """Controlled effect boundary, not qualification of an installed provider."""
    from tool_registry.gateway_models import GatewayError, GatewayErrorCode
    from packages.workspace_service.tests.test_workflow_mcp_execution import runtime

    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    gateway, tools = runtime()
    marker = tmp_path / "private-effect-marker.txt"

    async def effect_then_lose_ack(*args, **kwargs):
        gateway.calls.append((args, kwargs))
        # Exclusive creation means an accidental replay cannot quietly pass.
        with marker.open("x") as stream:
            stream.write("One controlled digital effect happened")
        raise GatewayError(
            GatewayErrorCode(error_code), "Controlled lost acknowledgement"
        )

    gateway.call_tool = effect_then_lose_ack
    accepted = materialize_new_workflow_instructions(
        source(
            task(
                "research",
                fmt="text",
                prompt="Perform the controlled probe with the exact query controlled probe.",
                authoring_template="mcp-task",
                mcp_server="docs",
                max_tool_calls=2,
            )
        ),
        load_default_workflow_instructions(),
    )
    plan = compile_prompt_workflow(accepted)
    app = service(tmp_path)
    app.workflow_model_capabilities = desktop.capabilities
    app.workflow_reasoning_factory = lambda **_: WorkflowReasoningCallbacks(
        desktop.generate_response, desktop.decide_action
    )
    events = []

    async def run():
        frozen, context = await freeze_workflow_model_routing(app, plan, {})

        async def emit(event):
            events.append(event)

        running = asyncio.create_task(
            execute_prompt_workflow(
                service=app,
                workspace_dir=str(tmp_path),
                plan=frozen,
                input_values={},
                response_generator=None,
                action_generator=None,
                tool_runtime=tools,
                execution_context=context,
                run_id="run-1",
                on_event=emit,
            )
        )
        request = await pending(repo)
        assert request.kind == "action"
        assert (
            request.payload["tools"][0]["function"]["parameters"]["properties"][
                "schema_version"
            ]["const"]
            == "wright.workflow-action-intent/1"
        )
        proposal = {
            "schema_version": "wright.workflow-action-intent/1",
            "arguments": {"query": "controlled probe"},
            "assumptions": [],
            "unresolved_required_information": [],
        }
        repo.submit_response(
            "workspace-1",
            "session-1",
            DesktopReasoningResponse(
                request_id=request.request_id,
                request_digest=request.digest,
                binding_digest=request.binding.digest,
                response_id="uncertain-effect-answer",
                received_at=datetime.now(timezone.utc).isoformat(),
                reply=DesktopActionReply(
                    tool_calls=[
                        {
                            "id": "one-effect",
                            "type": "function",
                            "function": {
                                "name": "tool_0",
                                "arguments": json.dumps(proposal),
                            },
                        }
                    ]
                ),
            ),
        )
        with pytest.raises(WorkflowSourceExecutionError) as failed:
            await asyncio.wait_for(running, 10)
        assert failed.value.code == "MCP_CALL_FAILED"

    asyncio.run(run())
    assert marker.read_text() == "One controlled digital effect happened"
    assert len(gateway.calls) == 1
    assert repo.pending("workspace-1", "session-1") == []
    # No second handoff is created for retry or format repair after failure.
    assert (
        len(
            [
                event
                for event in events
                if event.get("kind") == "model_invocation"
                and event.get("invocation", {}).get("capture_scope")
                == "desktop_handoff_request"
            ]
        )
        == 1
    )
    assert not (tmp_path / "research.txt").exists()


def test_opt_in_image_request_retains_exact_bytes_and_redacted_evidence(tmp_path):
    import base64
    from pathlib import Path

    data = (
        Path(__file__).resolve().parents[3]
        / "artifacts/stevecad-demonstrations/qualification/native/06-inspect-coupon-1.png"
    ).read_bytes()
    inline = "data:image/png;base64," + base64.b64encode(data).decode()
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo, image_input_profile="inline-png-jpeg-v1")
    assert desktop.resolution() != reasoner(repo).resolution()
    observed = []

    async def observe(value):
        observed.append(value)

    async def exercise():
        task = asyncio.create_task(
            desktop.generate_response(
                "Inspect this recorded image",
                "text",
                images=[inline],
                invocation_observer=observe,
            )
        )
        try:
            request = await pending(repo)
            assert request.binding.image_input_profile == "inline-png-jpeg-v1"
            assert request.payload["messages"][-1]["content"][1] == {
                "type": "image_url",
                "image_url": {"url": inline},
            }
            assert inline not in json.dumps(observed)
            answer(repo, request, "Synthetic response, not image perception evidence")
            assert (
                await asyncio.wait_for(task, 2)
                == "Synthetic response, not image perception evidence"
            )
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "image",
    [
        "https://example.invalid/image.png",
        "data:image/svg+xml;base64,PHN2Zz4=",
        "data:image/png;base64,***",
        "data:image/png;base64,YmFk",
    ],
)
def test_opt_in_image_rejects_noninline_unsupported_or_malformed_before_request(
    tmp_path, image
):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo, image_input_profile="inline-png-jpeg-v1")
    with pytest.raises(ValueError):
        asyncio.run(desktop.generate_response("Inspect", "text", images=[image]))
    assert repo.pending("workspace-1", "session-1") == []


def test_opt_in_image_does_not_relax_total_payload_bound(tmp_path):
    import base64

    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo, image_input_profile="inline-png-jpeg-v1")
    # Transport signature fixture; this is not a decoded-image qualification.
    inline = (
        "data:image/png;base64,"
        + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"x" * 100).decode()
    )
    with pytest.raises(ValueError, match="256 KiB"):
        asyncio.run(desktop.generate_response("x" * 262144, "text", images=[inline]))
    assert repo.pending("workspace-1", "session-1") == []


@pytest.mark.parametrize("workflow", ["transport-fixture", "pi-primary-reference"])
def test_actual_mcp_image_producer_reaches_desktop_request_and_keeps_evidence_redacted(
    tmp_path,
    workflow,
):
    import base64
    import hashlib

    from tool_registry.gateway_models import GatewayToolResult
    from packages.workspace_service.tests.test_workflow_mcp_execution import runtime
    from packages.workspace_service.tests.test_workflow_mcp_image_observations import (
        image,
        png,
    )
    from packages.workspace_service.tests.test_workflow_ai_task import call, done, plan

    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo, image_input_profile="inline-png-jpeg-engineering-v1")
    gateway, runner = runtime()
    picture = image(png())
    gateway.result = GatewayToolResult(content=(picture,))
    step = plan().steps[0]
    proposal = call()
    if workflow == "pi-primary-reference":
        # Existing PDF/supplier-reference research stage, not CAD inspection.
        # Only provider responses are controlled; no campaign or engineering
        # acceptance is asserted by this image-transport regression.
        from pathlib import Path
        from types import SimpleNamespace
        from tool_registry.gateway_models import GatewayTool
        from packages.workspace_service.tests.test_pi_visual_preparer import (
            preparer,
            ROOT,
        )

        config = json.loads(preparer.BINDING.read_text())
        tool_catalog = [
            {
                "server_id": server,
                "tool_name": name,
                "name": f"{server}__{name}",
                "schema_digest": "a" * 64,
            }
            for server, names in config["allowed_tools"].items()
            for name in names
        ]
        prepared = preparer.prepare(
            SimpleNamespace(
                workspace_root=str(tmp_path / "workspace"),
                draft_root=str(tmp_path / "draft"),
                instance_source=None,
                attempt="image-contract",
                initialize_agentcad=False,
            ),
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure/01-riverstone-desktop-computer",
            tool_catalog,
        )
        draft = Path(prepared["draft"]).read_bytes()
        # As in normal creation, a fresh draft receives current versioned
        # instructions. This does not rewrite an accepted historical process.
        existing = compile_prompt_workflow(
            materialize_new_workflow_instructions(
                draft.decode(), load_default_workflow_instructions()
            )
        )
        step = next(s for s in existing.steps if "observe_pi_primary_page" in s.prompt)
        assert "Preserve manufacturer reference-only warning" in step.prompt
        assert "at most8image observations" in step.prompt
        tool = GatewayTool(
            name=step.server_id + "__observe_pi_primary_page",
            server_id=step.server_id,
            tool_name="observe_pi_primary_page",
            description="Controlled primary page observation contract",
            input_schema={
                "type": "object",
                "properties": {
                    "document_name": {"type": "string"},
                    "page_number": {"type": "integer"},
                    "view": {"type": "string"},
                },
                "required": ["document_name", "page_number", "view"],
                "additionalProperties": False,
            },
        )
        gateway.list_tools = lambda *args: (tool,)
        proposal["tool_calls"][0]["function"]["arguments"] = json.dumps(
            {
                "schema_version": "wright.workflow-action-intent/1",
                "arguments": {
                    "document_name": "manufacturer-drawing.pdf",
                    "page_number": 1,
                    "view": "full",
                },
                "assumptions": [],
                "unresolved_required_information": [],
            }
        )
        gateway.result = GatewayToolResult(
            content=(
                {
                    "type": "text",
                    "text": "Controlled page observation; not actual manufacturer dimensions",
                },
                picture,
            ),
            structured_content={
                "document": "manufacturer-drawing.pdf",
                "page": 1,
                "source_sha256": "c" * 64,
                "view": "full",
            },
        )
    events = []

    async def emit(kind, **event):
        events.append({"kind": kind, **event})

    def reply(request, message):
        repo.submit_response(
            "workspace-1",
            "session-1",
            DesktopReasoningResponse(
                request_id=request.request_id,
                request_digest=request.digest,
                binding_digest=request.binding.digest,
                response_id=str(uuid4()),
                received_at=datetime.now(timezone.utc).isoformat(),
                reply=DesktopActionReply.model_validate(message),
            ),
        )

    async def exercise():
        running = asyncio.create_task(
            runner.run_task(
                step,
                step.prompt,
                desktop.decide_action,
                emit,
            )
        )
        try:
            first = await pending(repo, running=running)
            assert step.prompt in json.dumps(first.payload, ensure_ascii=False)
            reply(first, proposal)
            request = await pending(repo, after=first.request_id, running=running)
            parts = request.payload["messages"][-1]["content"]
            image_part = next(part for part in parts if part["type"] == "image_url")
            assert image_part["image_url"] == {
                "url": "data:image/png;base64," + picture["data"],
                "detail": "high",
            }
            # Reading from SQLite revalidates the core request, not a hand-written mock.
            assert request.kind == "action"
            reply(
                request, done("Transport fixture inspected; not engineering acceptance")
            )
            response, records = await asyncio.wait_for(running, 5)
            assert response == "Transport fixture inspected; not engineering acceptance"
            assert (
                records[0]["image_observations"][0]["sha256"]
                == hashlib.sha256(base64.b64decode(picture["data"])).hexdigest()
            )
            assert "data:image/" not in json.dumps(records)
            assert picture["data"] not in json.dumps(events)
            assert len(gateway.calls) == 1
            if workflow == "pi-primary-reference":
                assert records[0]["result"]["source_sha256"] == "c" * 64
                assert Path(prepared["draft"]).read_bytes() == draft
        finally:
            if not running.done():
                running.cancel()
            await asyncio.gather(running, return_exceptions=True)

    asyncio.run(exercise())


def test_desktop_saved_context_budget_is_rejected_during_route_preparation(tmp_path):
    from packages.workspace_service.tests.test_workflow_ai_task import plan

    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    app = service(tmp_path)
    app.workflow_model_capabilities = desktop.capabilities
    with pytest.raises(
        WorkflowSourceExecutionError, match="mcp_context_budget_bytes"
    ) as error:
        asyncio.run(
            freeze_workflow_model_routing(
                app, plan(mcp_context_budget_bytes=1048576), {}
            )
        )
    assert error.value.code == "WORKFLOW_NOT_READY"
    assert repo.pending("workspace-1", "session-1") == []
    frozen, _ = asyncio.run(freeze_workflow_model_routing(app, plan(), {}))
    assert frozen.steps[0].mcp_context_budget_bytes is None


@pytest.mark.asyncio
async def test_public_readiness_blocks_saved_budget_before_start_and_tool_effects(
    tmp_path,
):
    from packages.workspace_service.tests.test_process_preparation_service import (
        owner,
        process,
        scope,
        source as prepared_source,
        section,
    )
    from packages.workspace_service.tests.test_workflow_ai_task import (
        legacy_instruction_profile,
    )
    from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway
    from workspace_service.process_interfaces.errors import ProcessInterfaceError
    from workspace_service.workflow_source_execution import _parse

    blocks = _parse(prepared_source(default="Inspect the supplied engineering record"))
    blocks[0]["fields"]["instructions"] = legacy_instruction_profile()
    first = next(b["fields"] for b in blocks if b["id"] == "first")
    first["settings"].update(
        authoring_template="mcp-task",
        mcp_server="docs",
        mcp_context_budget_bytes=1048576,
    )
    text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
    app = owner(tmp_path, text)
    repo = DesktopReasoningRepository(tmp_path / "desktop.sqlite")
    app.workspace.workflow_model_capabilities = reasoner(repo).capabilities
    gateway = Gateway()
    try:
        prepared = await app.set_inputs(scope(), process(text))
        frozen = prepared.snapshot
        view = await app.check_readiness(
            scope(),
            process(text),
            frozen.snapshot_id,
            gateway=gateway,
            session_id="session",
        )
        assert view.state == "blocked"
        assert "mcp_context_budget_bytes" in view.reasons[0].message
        assert "Explicitly revise" in view.reasons[0].correction
        with pytest.raises(ProcessInterfaceError, match="mcp_context_budget_bytes"):
            await app.runs.start(
                scope(),
                process(text),
                frozen.snapshot_id,
                "unsupported-budget",
                expected_input_digest=frozen.digest,
                response_generator=None,
                gateway=gateway,
                session_id="session",
            )
        assert app.runs._owned == {}
        assert gateway.calls == []
        assert repo.pending("workspace-1", "session-1") == []
        assert not (tmp_path / "runs").exists()
        with pytest.raises(KeyError):
            app.inputs.start_receipt("user", process(text), "unsupported-budget")
    finally:
        await app.close()
