"""Process preparation composes existing qualification without executing work."""

from types import SimpleNamespace
from dataclasses import replace
from unittest.mock import AsyncMock
import json

import pytest

from core.process_interactions import ValueBinding
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import (
    ProcessInterfaceService,
    ProcessScope,
)
from packages.workspace_service.tests.test_process_input_readiness import (
    application,
    source,
    process,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section
from packages.workspace_service.tests.test_workflow_mcp_execution import TOOL, Gateway
from workspace_service.workflow_mcp_execution import schema_digest
from workspace_service.workflow_source_execution import _parse


def tool_source(**changes):
    blocks = _parse(source(**changes))
    first = next(block["fields"] for block in blocks if block["id"] == "first")
    first["performed_by"] = "configured_tool"
    first["settings"].update(
        authoring_template="mcp-tool",
        mcp_tool=TOOL.name,
        mcp_server=TOOL.server_id,
        mcp_schema_digest=schema_digest(TOOL),
        mcp_arguments=json.dumps({"limit": 3}),
        mcp_argument_ports=json.dumps({"first_in": "query"}),
        output_format="json",
        output_filename="first.json",
    )
    return "".join(
        section(block["kind"], block["id"], **block["fields"]) for block in blocks
    )


def owner(root, text):
    workspace = application(root, text)
    workspace.db_path = root / "state.db"
    workspace.repository = SimpleNamespace(
        get_by_id=lambda key: {"local_path": str(root)} if key == "workspace" else None
    )
    workspace.ensure_workspace_path_safe = lambda path: None
    workspace.workflow_sources.read_template_origin = AsyncMock(return_value=None)
    return ProcessInterfaceService(workspace)


def scope(*capabilities):
    return ProcessScope(
        "user",
        "workspace",
        frozenset(capabilities or ("process.read", "process.inputs", "process.start")),
    )


@pytest.mark.asyncio
async def test_set_inputs_persists_exact_values_without_source_edit_or_execution(
    tmp_path,
):
    text = source(default="Definition default", later=True)
    app = owner(tmp_path, text)
    prepared = await app.set_inputs(
        scope(),
        process(text),
        bindings=(ValueBinding(input_id="brief", value="Run requirements"),),
    )
    frozen = app.inputs.get_snapshot("workspace", prepared.snapshot.snapshot_id)
    assert frozen == prepared.snapshot
    assert frozen.bindings[0].value == "Run requirements"
    readiness = await app.check_readiness(scope(), process(text), frozen.snapshot_id)
    assert readiness.state == "ready"
    assert readiness.input_digest == frozen.digest
    assert {item.classification for item in readiness.dependencies} == {
        "supplied",
        "upstream_produced",
    }
    assert not (tmp_path / "first.txt").exists()
    assert not (tmp_path / "later.txt").exists()


@pytest.mark.asyncio
async def test_missing_later_choice_blocks_public_start_before_any_dispatch(tmp_path):
    text = source(later=True, late_root=True, required=False)
    app = owner(tmp_path, text)
    prepared = await app.set_inputs(scope(), process(text))
    readiness = await app.check_readiness(
        scope(), process(text), prepared.snapshot.snapshot_id
    )
    assert readiness.state == "blocked"
    assert readiness.dependencies[0].binding_id == "brief"
    assert readiness.dependencies[0].classification == "unresolved"
    calls = []

    async def must_not_execute(*args, **kwargs):
        calls.append("model")
        raise AssertionError("A missing later choice must block before any model work")

    def must_not_connect():
        calls.append("gateway")
        raise AssertionError("A missing later choice must block before any tool work")

    try:
        with pytest.raises(ProcessInterfaceError) as denied:
            await app.runs.start(
                scope(), process(text), prepared.snapshot.snapshot_id,
                "missing-later-choice", expected_input_digest=prepared.snapshot.digest,
                response_generator=must_not_execute, gateway=must_not_connect,
            )
        assert denied.value.reason.code == "INPUT_REQUIRED"
        assert calls == []
        assert app.runs._owned == {}
        with pytest.raises(KeyError):
            app.inputs.start_receipt("user", process(text), "missing-later-choice")
        assert not (tmp_path / "runs").exists()
        assert not (tmp_path / "first.txt").exists()
        assert not (tmp_path / "later.txt").exists()
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_read_only_default_view_and_missing_input_reasons(tmp_path):
    text = source(later=True)
    app = owner(tmp_path, text)
    snapshot = await app.get_snapshot(scope("process.read"), process(text))
    assert snapshot.context.run_id is None
    assert snapshot.context.input_snapshot_id is None
    assert snapshot.readiness.state == "blocked"
    assert snapshot.inputs[0].input_id == "brief"
    assert any(reason.code == "INPUT_REQUIRED" for reason in snapshot.readiness.reasons)
    assert not (tmp_path / "state.db").exists()


@pytest.mark.asyncio
async def test_stored_snapshot_is_used_in_preparation_projection(tmp_path):
    text = source(default="Definition default")
    app = owner(tmp_path, text)
    prepared = await app.set_inputs(
        scope(),
        process(text),
        bindings=(ValueBinding(input_id="brief", value="Frozen value"),),
    )
    snapshot = await app.get_snapshot(
        scope(), process(text), input_snapshot_id=prepared.snapshot.snapshot_id
    )
    assert snapshot.inputs[0].current_value.value == "Frozen value"
    assert snapshot.context.input_snapshot_id == prepared.snapshot.snapshot_id
    assert snapshot.readiness.state == "ready"
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_preparation_permissions_and_foreign_snapshot_are_rejected(tmp_path):
    text = source(default="Default")
    app = owner(tmp_path, text)
    with pytest.raises(ProcessInterfaceError) as denied:
        await app.set_inputs(scope("process.read"), process(text))
    assert denied.value.reason.code == "SCOPE_DENIED"
    prepared = await app.set_inputs(scope(), process(text))
    other = process(text).model_copy(update={"source_path": "workflows/other.wflow"})
    with pytest.raises(ProcessInterfaceError) as wrong:
        await app.check_readiness(scope(), other, prepared.snapshot.snapshot_id)
    assert wrong.value.reason.code == "SUBJECT_STALE"


@pytest.mark.asyncio
async def test_changed_template_qualification_blocks_the_same_inputs(tmp_path):
    text = source(default="Default")
    app = owner(tmp_path, text)
    prepared = await app.set_inputs(scope(), process(text))
    app.workspace.workflow_sources.read_template_origin.return_value = {
        "template_id": "engineering",
        "template_version": "1",
    }
    app.workspace.engineering_workflow_templates = SimpleNamespace(
        readiness=lambda *args: {
            "state": "setup_required",
            "blocking_reasons": ["Configure the required solver."],
        }
    )
    readiness = await app.check_readiness(
        scope(), process(text), prepared.snapshot.snapshot_id
    )
    assert readiness.state == "blocked"
    assert "setup" in readiness.reasons[0].message.lower()
    assert "solver" in readiness.reasons[0].correction
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_invalid_known_tool_value_blocks_readiness_without_effects(tmp_path):
    text = tool_source(default="x")
    app = owner(tmp_path, text)
    gateway = Gateway()
    prepared = await app.set_inputs(scope(), process(text))
    readiness = await app.check_readiness(
        scope(),
        process(text),
        prepared.snapshot.snapshot_id,
        gateway=gateway,
        session_id="session",
    )
    assert readiness.state == "blocked"
    assert "minLength" in readiness.reasons[0].message
    assert gateway.calls == []
    assert gateway.closed
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_text_file_tool_value_uses_contents_for_qualification(tmp_path):
    (tmp_path / "requirements.txt").write_text("Engineering requirements")
    text = tool_source(file="requirements.txt")
    app = owner(tmp_path, text)
    gateway = Gateway()
    prepared = await app.set_inputs(scope(), process(text))
    readiness = await app.check_readiness(
        scope(),
        process(text),
        prepared.snapshot.snapshot_id,
        gateway=gateway,
        session_id="session",
    )
    assert readiness.state == "ready"
    assert gateway.calls == []
    assert gateway.closed


@pytest.mark.asyncio
async def test_unavailable_tool_gateway_has_a_useful_blocking_reason(tmp_path):
    text = tool_source(default="Engineering requirements")
    app = owner(tmp_path, text)
    prepared = await app.set_inputs(scope(), process(text))
    readiness = await app.check_readiness(
        scope(), process(text), prepared.snapshot.snapshot_id
    )
    assert readiness.state == "blocked"
    assert readiness.reasons[0].code == "CAPABILITY_UNAVAILABLE"
    assert readiness.reasons[0].correction


@pytest.mark.asyncio
@pytest.mark.parametrize("agent_task", [False, True])
@pytest.mark.parametrize("granted", [False, True])
async def test_predictable_tool_authority_is_checked_before_execution(tmp_path, agent_task, granted):
    guarded = replace(TOOL, required_approvals=frozenset({"workspace_write_approval"}))
    blocks = _parse(tool_source(default="Engineering requirements"))
    first = next(block["fields"] for block in blocks if block["id"] == "first")
    first["settings"]["mcp_schema_digest"] = schema_digest(guarded)
    if agent_task:
        first["performed_by"] = "ai_assisted"
        first["settings"].update(authoring_template="mcp-task", mcp_task_tools=[guarded.tool_name],
                                 task_guidance="Use only the declared tool and exact supplied requirements.")
    text = "".join(section(block["kind"], block["id"], **block["fields"]) for block in blocks)
    app = owner(tmp_path, text)
    gateway = Gateway()
    gateway.list_tools = lambda *args: (guarded,)
    gateway.workspace_approvals_for_model_call = lambda *args: {"workspace_write_approval"} if granted else set()
    prepared = await app.set_inputs(scope(), process(text))
    readiness = await app.check_readiness(scope(), process(text), prepared.snapshot.snapshot_id,
                                          gateway=gateway, session_id="session")
    assert readiness.state == ("ready" if granted else "blocked")
    if not granted:
        assert readiness.reasons[0].code == "CAPABILITY_UNAVAILABLE"
        assert "authorization" in readiness.reasons[0].message.lower()
        assert readiness.reasons[0].correction
        async def must_not_execute(*args, **kwargs):
            raise AssertionError("A missing predictable grant must block before execution")

        with pytest.raises(ProcessInterfaceError) as denied:
            await app.runs.start(scope(), process(text), prepared.snapshot.snapshot_id,
                                 "missing-tool-grant", expected_input_digest=prepared.snapshot.digest,
                                 response_generator=must_not_execute, gateway=gateway, session_id="session")
        assert denied.value.reason.code == "CAPABILITY_UNAVAILABLE"
        assert app.runs._owned == {}
    assert gateway.calls == []
    assert gateway.closed
    assert not (tmp_path / "first.json").exists()
