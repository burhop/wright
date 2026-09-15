from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tool_registry.gateway_models import GatewayError, GatewayToolResult
from workspace_service.workflow_integration_document_write import (
    bind_integration_document_writes,
)
from workspace_service.workflow_integration_policy import (
    WorkflowIntegrationPolicyService,
)
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime, schema_digest
from workspace_service.workflow_source_execution import (
    PromptStep,
    PromptWorkflow,
    WorkflowSourceExecutionError,
)
from workspace_service.workspace_document_gateway import (
    WorkspaceDocumentGatewayProvider,
)
from workspace_service.workspace_file_inspection import (
    INSPECT_TOOL_NAME,
)
from packages.workspace_service.tests.test_workspace_document_gateway import _fixture


def sha(value):
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def case(tmp_path):
    database, root, artifacts, session = _fixture(tmp_path)
    (root / "inputs").mkdir()
    (root / "inputs/brief.md").write_bytes(b"Human engineering input")
    (root / "workflow.wflow").write_bytes(b"canonical immutable source")
    (root / "outputs/current").mkdir(parents=True)
    (root / "outputs/current/measurement.json").write_bytes(b'{"dimension_mm":12.5}')
    provider = WorkspaceDocumentGatewayProvider(artifacts)
    tool = provider.tools(session)[1]
    tools = provider.tools(session)[:2]
    events = []

    class Gateway:
        calls = 0
        mutate = None

        def open_session(self, **kw):
            self.session = replace(
                session, session_id=kw["session_id"], principal_id=kw["principal_id"]
            )

        def initialize_session(self, *a, **kw):
            pass

        def list_tools(self, *a):
            return tools

        def workspace_approvals_for_model_call(self, *a):
            return set()

        async def close_session(self, *a):
            pass

        async def call_tool(self, session_id, request_id, name, arguments, **kw):
            selected = next(item for item in tools if item.name == name)
            if self.mutate:
                self.mutate(arguments)
            if kw.get("before_dispatch"):
                kw["before_dispatch"](selected)
                expected_event = (
                    "integration_file_read_authorized"
                    if name == INSPECT_TOOL_NAME
                    else "integration_document_write_authorized"
                )
                assert events[-1][0] == expected_event
            self.calls += 1
            value = await provider.call(
                self.session,
                selected,
                arguments,
                request_id=request_id,
                approval_context={"workspace_approvals": kw.get("workspace_approvals")},
                progress_callback=None,
            )
            return GatewayToolResult(
                content=tuple(value["content"]),
                structured_content=value["structuredContent"],
            )

    gateway = Gateway()
    runtime = WorkflowMcpRuntime(gateway, workspace_id="w1", session_id="s1")
    runtime.restrict_to(runtime.available())
    policies = WorkflowIntegrationPolicyService(str(database), enabled=True)

    class Files:
        async def read_reference(self, workspace_dir, path):
            return (Path(workspace_dir) / path).read_bytes()

    service = SimpleNamespace(
        workflow_integration_policies=policies,
        files=Files(),
        workspace_document_artifacts=artifacts,
    )
    step = PromptStep(
        "observe",
        "Observe",
        "Read actual file",
        None,
        (),
        "json",
        "outputs/current/report.json",
        True,
        "indexed",
        tool_name=tool.name,
        server_id=tool.server_id,
        schema_digest=schema_digest(tool),
        agent_task=True,
        expected_files=("outputs/current/bracket-source.py",),
    )
    plan = PromptWorkflow(
        "Observe",
        (step,),
        {"brief": {"settings": {"workspace_file": "inputs/brief.md"}}},
        definition_digest=sha(b"canonical immutable source"),
    )

    async def bind(**changes):
        grant = dict(
            campaign_id="campaign",
            dataset_id="case-01",
            dataset_digest="a" * 64,
            workspace_id="w1",
            source_path="workflow.wflow",
            source_digest=plan.definition_digest,
            input_files={"inputs/brief.md": sha(b"Human engineering input")},
            output_root="outputs/current",
            allowed_tools=runtime.available(),
            approval_mode="auto",
        )
        identity = policies.enroll(**{**grant, **changes})
        context = await policies.authorize(
            identity,
            workspace_id="w1",
            workspace_dir=str(root),
            source_path="workflow.wflow",
            source_digest=plan.definition_digest,
            plan=plan,
            tool_runtime=runtime,
            files=service.files,
        )
        bind_integration_document_writes(
            service=service,
            runtime=runtime,
            context=context,
            plan=plan,
            workspace_dir=str(root),
            workspace_id="w1",
            run_id="run-1",
        )
        return identity

    async def emit(kind, **data):
        events.append((kind, data))

    return SimpleNamespace(
        root=root,
        artifacts=artifacts,
        session=session,
        provider=provider,
        tool=tool,
        runtime=runtime,
        gateway=gateway,
        step=step,
        policies=policies,
        bind=bind,
        emit=emit,
        events=events,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["auto", "manual"])
async def test_actual_input_and_native_output_observations_are_read_only_and_attributed(
    case, mode
):
    identity = await case.bind(approval_mode=mode)
    for relative in ("inputs/brief.md", "outputs/current/measurement.json"):
        original = (case.root / relative).read_bytes()
        result, _ = await case.runtime.call(
            case.step, {"relativePath": relative}, on_event=case.emit
        )
        assert result["text"] == original.decode()
        assert result["sha256"] == sha(original) and result["bytes"] == len(original)
        assert result["integration_policy_digest"] == identity
        assert (case.root / relative).read_bytes() == original
    assert case.events[0][1]["run_id"] == "run-1"
    assert "text" not in case.events[0][1]


@pytest.mark.asyncio
async def test_model_can_inspect_missing_output_then_write_and_observe_it(case):
    identity = await case.bind()
    relative = "outputs/current/bracket-source.py"
    content = "# Authored source is data in this test; it is never executed.\n"
    decisions = 0

    async def decide(messages, schemas, **_kwargs):
        nonlocal decisions
        decisions += 1
        if decisions > 1:
            observation = json.loads(messages[-1]["content"])
            if decisions == 2:
                assert observation["status"] == "failed"
                assert "MCP call failed (invalid_input)" in observation["text"]
                assert not (case.root / relative).exists()
            elif decisions == 3:
                assert observation["status"] == "succeeded"
                assert observation["result"]["sha256"] == sha(content.encode())
            else:
                assert observation["status"] == "succeeded"
                assert observation["result"]["text"] == content
                return {
                    "content": json.dumps(
                        {
                            "status": "completed",
                            "response": '{"source_created":true}',
                            "evidence": [2, 3],
                        }
                    )
                }
        write = decisions == 2
        selected = next(
            item["function"]
            for item in schemas
            if ("content" in item["function"]["parameters"]["properties"]) == write
        )
        arguments = {"relativePath": relative}
        if write:
            arguments.update(content=content, mediaType="text/plain")
        return {
            "tool_calls": [
                {
                    "id": str(decisions),
                    "type": "function",
                    "function": {
                        "name": selected["name"],
                        "arguments": json.dumps(arguments),
                    },
                }
            ]
        }

    response, records = await case.runtime.run_task(
        case.step,
        "Inspect, create and verify the declared source file.",
        decide,
        case.emit,
    )
    assert json.loads(response) == {"source_created": True}
    assert [record["status"] for record in records] == [
        "failed",
        "succeeded",
        "succeeded",
    ]
    assert (
        case.gateway.calls == 3
        and (case.root / relative).read_bytes() == content.encode()
    )
    authorizations = [
        data for kind, data in case.events if kind.endswith("_authorized")
    ]
    assert len(authorizations) == 3
    assert all(data["integration_policy_digest"] == identity for data in authorizations)
    assert len({data["request_id"] for data in authorizations}) == 3
    # Even failed reads consume their exact private permit; they cannot be replayed.
    with pytest.raises(GatewayError, match="authority"):
        case.artifacts.file_inspector.inspect(
            case.gateway.session,
            {"relativePath": relative},
            authorizations[0]["request_id"],
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "relative", ["outputs/previous/missing.py", "inputs/unlisted.py", "../missing.py"]
)
async def test_missing_file_does_not_weaken_scope_authority(case, relative):
    await case.bind()
    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        await case.runtime.call(
            case.step, {"relativePath": relative}, on_event=case.emit
        )
    assert case.gateway.calls == 0 and not case.events


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        "no_context",
        "revoked",
        "source",
        "input",
        "other_attempt",
        "unlisted_input",
        "escape",
        "schema",
        "no_audit",
        "arguments",
        "after_audit",
    ],
)
async def test_observation_authority_rejects_ungranted_or_changed_context(case, change):
    identity = await case.bind() if change != "no_context" else None
    args = {"relativePath": "outputs/current/measurement.json"}
    step = case.step
    if change == "revoked":
        case.policies.revoke(identity)
    if change == "source":
        (case.root / "workflow.wflow").write_bytes(b"changed")
    if change == "input":
        (case.root / "inputs/brief.md").write_bytes(b"changed")
    if change in {"other_attempt", "unlisted_input"}:
        args["relativePath"] = (
            "outputs/previous.json"
            if change == "other_attempt"
            else "inputs/unlisted.json"
        )
        (case.root / args["relativePath"]).write_bytes(b"private")
    if change == "escape":
        args["relativePath"] = "../outside.json"
    if change == "schema":
        step = replace(step, schema_digest="f" * 64)
    if change == "arguments":
        case.gateway.mutate = lambda args: args.update(includeText=False)

    async def emit(kind, **data):
        await case.emit(kind, **data)
        if change == "after_audit":
            case.policies.revoke(identity)

    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        await case.runtime.call(
            step, args, on_event=None if change == "no_audit" else emit
        )


@pytest.mark.asyncio
async def test_forged_gateway_context_and_consumed_permit_cannot_read(case):
    args = {"relativePath": "outputs/current/measurement.json"}
    with pytest.raises(GatewayError, match="authority"):
        await case.provider.call(
            case.session,
            case.tool,
            args,
            request_id="forged",
            approval_context={
                "integration_test": True,
                "workspace_approvals": ["workspace_write_approval"],
            },
            progress_callback=None,
        )
    await case.bind()
    await case.runtime.call(case.step, args, on_event=case.emit)
    with pytest.raises(GatewayError, match="authority"):
        case.artifacts.file_inspector.inspect(
            case.session, args, case.events[-1][1]["request_id"]
        )


@pytest.mark.asyncio
async def test_binary_metadata_text_paging_and_limits(case, monkeypatch):
    await case.bind()
    binary = case.root / "outputs/current/native.step"
    binary.write_bytes(b"ISO-10303-21;\x00\xffnative STEP evidence")
    value, _ = await case.runtime.call(
        case.step, {"relativePath": "outputs/current/native.step"}, on_event=case.emit
    )
    assert (
        value["sha256"] == sha(binary.read_bytes())
        and value["textIncluded"] is False
        and "text" not in value
    )
    text = case.root / "outputs/current/unicode.txt"
    text.write_bytes("abcéthenmore".encode())
    value, _ = await case.runtime.call(
        case.step,
        {"relativePath": "outputs/current/unicode.txt", "maxTextBytes": 4},
        on_event=case.emit,
    )
    assert (
        value["text"] == "abc" and value["nextOffsetBytes"] == 3 and value["truncated"]
    )
    value, _ = await case.runtime.call(
        case.step,
        {"relativePath": "outputs/current/unicode.txt", "offsetBytes": 3},
        on_event=case.emit,
    )
    assert value["text"] == "éthenmore" and not value["truncated"]
    # Exercise the production size guard without allocating a 256MiB fixture.
    import workspace_service.workspace_file_inspection as inspection

    monkeypatch.setattr(inspection, "MAX_FILE_BYTES", 128)
    with binary.open("wb") as stream:
        stream.truncate(129)
    with pytest.raises(WorkflowSourceExecutionError, match="invalid_input"):
        await case.runtime.call(
            case.step,
            {"relativePath": "outputs/current/native.step"},
            on_event=case.emit,
        )
    for name, data in (("private.env", b"private"), ("malformed.json", b"\xff\xfe")):
        (case.root / "outputs/current" / name).write_bytes(data)
        with pytest.raises(WorkflowSourceExecutionError):
            await case.runtime.call(
                case.step,
                {"relativePath": "outputs/current/" + name},
                on_event=case.emit,
            )


@pytest.mark.asyncio
async def test_symlink_outside_attempt_rejected(case, tmp_path):
    await case.bind()
    outside = tmp_path / "outside.json"
    outside.write_text("private")
    try:
        (case.root / "outputs/current/link.json").symlink_to(outside)
    except OSError:
        pytest.skip("Host cannot create symlinks")
    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        await case.runtime.call(
            case.step, {"relativePath": "outputs/current/link.json"}, on_event=case.emit
        )


def test_existing_write_tool_pin_is_unchanged_and_inspection_is_separate(case):
    write, read, _copy = case.provider.tools(case.session)
    assert write == case.provider._tool()
    assert (
        write.provenance["server_revision"]
        == "wright-workspace-document-v2-integration-source"
    )
    assert read.name == INSPECT_TOOL_NAME and not read.required_approvals


@pytest.mark.asyncio
@pytest.mark.parametrize("suffix", ["kicad_pcb", "kicad_pro", "kicad_sch"])
async def test_kicad_files_are_metadata_only_even_when_text_requested(case, suffix):
    await case.bind()
    relative = "outputs/current/design." + suffix
    data = b"(native cad data)\x00\xff"
    (case.root / relative).write_bytes(data)
    value, _ = await case.runtime.call(
        case.step, {"relativePath": relative, "includeText": True}, on_event=case.emit
    )
    assert value["sha256"] == sha(data) and value["bytes"] == len(data)
    assert value["textIncluded"] is False and "text" not in value
