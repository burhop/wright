from dataclasses import replace
import hashlib
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
from workspace_service.workspace_file_copy import (
    COPY_TOOL_NAME,
)
from packages.workspace_service.tests.test_workspace_document_gateway import _fixture


from workspace_service.workflow_results import file_result, Provenance


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
    tool = provider.tools(session)[2]
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
            return (tool,)

        def workspace_approvals_for_model_call(self, *a):
            return set()

        async def close_session(self, *a):
            pass

        async def call_tool(self, session_id, request_id, name, arguments, **kw):
            if self.mutate:
                self.mutate(arguments)
            if kw.get("before_dispatch"):
                kw["before_dispatch"](tool)
                assert events[-1][0] == "integration_file_copy_authorized"
            self.calls += 1
            value = await provider.call(
                self.session,
                tool,
                arguments,
                request_id=request_id,
                approval_context={},
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
        arguments={
            "sourcePath": "inputs/brief.md",
            "destinationPath": "outputs/current/working.kicad_pcb",
        },
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
        plan=plan,
    )


@pytest.mark.asyncio
async def test_input_copy_is_new_mutable_file_with_lineage_not_artifact(case):
    identity = await case.bind()
    value, _ = await case.runtime.call(
        case.step, case.step.arguments, on_event=case.emit
    )
    original = (case.root / "inputs/brief.md").read_bytes()
    copied = case.root / case.step.arguments["destinationPath"]
    assert copied.read_bytes() == original
    assert value["source"]["sha256"] == value["destination"]["sha256"] == sha(original)
    assert value["source"]["bytes"] == value["destination"]["bytes"] == len(original)
    assert value["source"]["provenance"]["kind"] == "enrolled_input"
    assert value["integration_policy_digest"] == identity
    assert (
        len(
            [
                item
                for item in case.events
                if item[0] == "integration_file_copy_authorized"
            ]
        )
        == 1
    )
    assert value["mutable_working_copy"] and not value["published_artifact"]
    assert "artifactId" not in value and "produced_files" not in value
    copied.write_bytes(b"subsequent native edit")
    assert (case.root / "inputs/brief.md").read_bytes() == original
    assert not list(copied.parent.glob("*.tmp"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        "manual",
        "no_context",
        "revoked",
        "definition",
        "input",
        "wrong_source",
        "wrong_destination",
        "schema",
        "agent_task",
        "arguments",
        "after_audit",
        "no_audit",
        "overwrite",
    ],
)
async def test_copy_authority_fails_closed(case, change):
    identity = (
        None
        if change == "no_context"
        else await case.bind(approval_mode="manual" if change == "manual" else "auto")
    )
    step, args = case.step, dict(case.step.arguments)
    if change == "revoked":
        case.policies.revoke(identity)
    if change == "definition":
        (case.root / "workflow.wflow").write_bytes(b"different")
    if change == "input":
        (case.root / "inputs/brief.md").write_bytes(b"changed")
    if change == "wrong_source":
        args["sourcePath"] = "outputs/current/measurement.json"
    if change == "wrong_destination":
        args["destinationPath"] = "outputs/current/other.kicad_pcb"
    if change == "schema":
        step = replace(step, schema_digest="f" * 64)
    if change == "agent_task":
        step = replace(step, agent_task=True)
    if change == "arguments":
        case.gateway.mutate = lambda args: args.update(
            destinationPath="outputs/current/other.kicad_pcb"
        )
    if change == "overwrite":
        (case.root / args["destinationPath"]).write_bytes(b"must remain")

    async def emit(kind, **data):
        await case.emit(kind, **data)
        if change == "after_audit":
            case.policies.revoke(identity)

    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        await case.runtime.call(
            step, args, on_event=None if change == "no_audit" else emit
        )
    target = case.root / args["destinationPath"]
    assert (
        target.read_bytes() == b"must remain"
        if change == "overwrite"
        else not target.exists()
    )


def _produced_case(case, *, run_id="run-1", evidence=True):
    # Simulate the canonical engine's verified results, never provider claims.
    raw = bytes(range(256)) * 32
    relative = "outputs/current/source.kicad_pcb"
    (case.root / relative).write_bytes(raw)
    producer = replace(
        case.step, id="native_board", arguments={}, expected_files=(relative,)
    )
    step = replace(case.step, arguments={**case.step.arguments, "sourcePath": relative})
    authority = case.runtime._integration_file_copy_authority
    authority.plan = replace(authority.plan, steps=(producer, step))
    case.runtime._verified_copy_sources = (
        (
            file_result(
                {"output_path": relative, "output_bytes": len(raw), "sha256": sha(raw)},
                Provenance(run_id, producer.id, "board"),
            ),
        )
        if evidence
        else ()
    )
    return step, raw


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [None, "missing_evidence", "cross_run", "drift", "size", "wrong_evidence_size"],
)
async def test_actual_binary_copy_needs_prior_verified_same_run_bytes(
    case, monkeypatch, change
):
    await case.bind()
    step, raw = _produced_case(
        case,
        run_id="other" if change == "cross_run" else "run-1",
        evidence=change != "missing_evidence",
    )
    if change == "drift":
        (case.root / step.arguments["sourcePath"]).write_bytes(raw + b"changed")
    if change == "size":
        monkeypatch.setattr("workspace_service.workspace_file_copy.MAX_COPY_BYTES", 100)
    if change == "wrong_evidence_size":
        result = case.runtime._verified_copy_sources[0]
        case.runtime._verified_copy_sources = (
            replace(
                result,
                representations=(replace(result.representations[0], size_bytes=1),),
            ),
        )
    if change:
        with pytest.raises((WorkflowSourceExecutionError, ValueError)):
            await case.runtime.call(step, step.arguments, on_event=case.emit)
        assert not (case.root / step.arguments["destinationPath"]).exists()
        assert not list((case.root / "outputs/current").glob("*.tmp"))
    else:
        value, _ = await case.runtime.call(step, step.arguments, on_event=case.emit)
        assert (case.root / step.arguments["destinationPath"]).read_bytes() == raw
        assert value["source"]["provenance"]["run_id"] == "run-1"
        assert value["source"]["provenance"]["kind"] == "verified_run_output"


@pytest.mark.asyncio
async def test_provider_rejects_forged_context_and_permit_is_single_use(case):
    arguments = case.step.arguments
    session = replace(case.session, principal_id="wright-native-workflow")
    with pytest.raises(GatewayError, match="authority"):
        await case.provider.call(
            session,
            case.tool,
            arguments,
            request_id="forged",
            approval_context={
                "workspace_approvals": ["workspace_write_approval"],
                "integration_policy_digest": "a" * 64,
            },
            progress_callback=None,
        )
    case.artifacts.file_copier.grant(
        request_id="once",
        session_id=session.session_id,
        workspace_id=session.workspace_id,
        workspace_path=session.workspace_path,
        arguments=arguments,
        expected_sha256=sha(b"Human engineering input"),
        expected_bytes=None,
        policy_digest="a" * 64,
        source_provenance={"kind": "enrolled_input"},
    )
    case.artifacts.file_copier.copy(session, arguments, "once")
    with pytest.raises(GatewayError, match="authority"):
        case.artifacts.file_copier.copy(session, arguments, "once")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "destination",
    ["../escape.kicad_pcb", "outputs/other/working.kicad_pcb", "inputs/copy.kicad_pcb"],
)
async def test_fixed_but_outside_granted_destination_rejected(case, destination):
    await case.bind()
    step = replace(
        case.step, arguments={**case.step.arguments, "destinationPath": destination}
    )
    authority = case.runtime._integration_file_copy_authority
    authority.plan = replace(authority.plan, steps=(step,))
    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        await case.runtime.call(step, step.arguments, on_event=case.emit)


@pytest.mark.asyncio
async def test_explicit_final_copy_is_left_to_ordinary_expected_file_verification(case):
    await case.bind()
    step = replace(case.step, expected_files=(case.step.arguments["destinationPath"],))
    authority = case.runtime._integration_file_copy_authority
    authority.plan = replace(authority.plan, steps=(step,))
    value, _ = await case.runtime.call(step, step.arguments, on_event=case.emit)
    assert value["published_artifact"] is False and "artifactId" not in value
    from workspace_service.workflow_references import verify_task_files

    files = verify_task_files(str(case.root), step.expected_files, {})
    assert files[0]["sha256"] == value["destination"]["sha256"]


@pytest.mark.asyncio
async def test_publication_racing_existing_file_is_never_overwritten(case, monkeypatch):
    import os
    import workspace_service.workspace_file_copy as copy_module

    await case.bind()
    link = os.link

    def competing_writer(source, destination, **kwargs):
        (case.root / case.step.arguments["destinationPath"]).write_bytes(
            b"other writer"
        )
        return link(source, destination, **kwargs)

    monkeypatch.setattr(copy_module.os, "link", competing_writer)
    with pytest.raises(WorkflowSourceExecutionError):
        await case.runtime.call(case.step, case.step.arguments, on_event=case.emit)
    assert (
        case.root / case.step.arguments["destinationPath"]
    ).read_bytes() == b"other writer"
    assert not list((case.root / "outputs/current").glob("*.tmp"))


@pytest.mark.asyncio
async def test_source_cannot_change_during_flush(case, monkeypatch):
    import os
    import workspace_service.workspace_file_copy as copy_module

    await case.bind()
    original = (case.root / case.step.arguments["sourcePath"]).read_bytes()
    fsync = os.fsync

    def concurrent_write(fd):
        fsync(fd)
        # Windows source handle denies writes; POSIX detects the changed source.
        (case.root / case.step.arguments["sourcePath"]).write_bytes(b"changed at flush")

    monkeypatch.setattr(copy_module.os, "fsync", concurrent_write)
    with pytest.raises(WorkflowSourceExecutionError):
        await case.runtime.call(case.step, case.step.arguments, on_event=case.emit)
    assert not (case.root / case.step.arguments["destinationPath"]).exists()
    assert not list((case.root / "outputs/current").glob("*.tmp"))
    if os.name == "nt":
        assert (case.root / case.step.arguments["sourcePath"]).read_bytes() == original


@pytest.mark.asyncio
async def test_existing_symlink_source_is_rejected(case, tmp_path):
    outside = tmp_path / "outside.kicad_pcb"
    outside.write_bytes(b"outside data")
    link = case.root / "outputs/current/link.kicad_pcb"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Host cannot create symlinks")
    await case.bind()
    step = replace(
        case.step,
        arguments={
            **case.step.arguments,
            "sourcePath": "outputs/current/link.kicad_pcb",
        },
    )
    authority = case.runtime._integration_file_copy_authority
    authority.plan = replace(authority.plan, steps=(step,))
    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        await case.runtime.call(step, step.arguments, on_event=case.emit)
    assert outside.read_bytes() == b"outside data"


@pytest.mark.asyncio
async def test_actual_gateway_dispatch_preserves_private_authority_and_audit(case):
    from tool_registry.gateway_service import GatewayService
    from tool_registry.gateway_notifications import GatewayNotificationHub
    from tool_registry.gateway_resources import GatewayResourceProvider
    from packages.tool_registry.tests.test_gateway_service import (
        Catalog,
        Lifecycle,
        Audit,
    )

    class Workspaces:
        def resolve_binding(self, *, session_id, principal_id, workspace_id):
            return {
                "session_id": session_id,
                "principal_id": principal_id,
                "workspace_id": workspace_id,
                "workspace_path": str(case.root),
            }

        def enabled_server_ids(self, session):
            return set()

    audit, lifecycle = Audit(), Lifecycle()
    gateway = GatewayService(
        workspaces=Workspaces(),
        catalog=Catalog(),
        lifecycle=lifecycle,
        audit=audit,
        notifier=GatewayNotificationHub(),
        resources=GatewayResourceProvider(),
        capability_providers=(case.provider,),
    )
    gateway.open_session(
        session_id=case.runtime.session_id,
        principal_id="wright-native-workflow",
        workspace_id="w1",
        transport="stdio",
        binding_session_id="s1",
    )
    gateway.initialize_session(
        case.runtime.session_id,
        protocol_version="2025-11-25",
        client_name="wright",
        client_version="test",
        client_capabilities={},
    )
    case.runtime.gateway = gateway
    await case.bind()
    value, _ = await case.runtime.call(
        case.step, case.step.arguments, on_event=case.emit
    )
    assert value["source"]["sha256"] == sha(b"Human engineering input")
    assert not lifecycle.calls
    assert any(
        event.get("target_name") == "copy_file" and event.get("allowed")
        for event in audit.events
    )
    with pytest.raises(GatewayError):
        await gateway.call_tool(
            case.runtime.session_id,
            "untrusted-request",
            COPY_TOOL_NAME,
            {
                **case.step.arguments,
                "destinationPath": "outputs/current/forged.kicad_pcb",
            },
            workspace_approvals={"workspace_write_approval"},
        )
    assert not (case.root / "outputs/current/forged.kicad_pcb").exists()
    await gateway.shutdown()


@pytest.mark.asyncio
async def test_canonical_engine_registers_verified_sources_and_does_not_seal_working_copy(
    case,
):
    from workspace_service.workflow_source_execution import execute_prompt_workflow
    from packages.workspace_service.tests.test_workflow_source_execution import service

    await case.bind()
    first = replace(
        case.step,
        id="preserve_source",
        output_path="outputs/current/first-copy.json",
        expected_files=(case.step.arguments["destinationPath"],),
    )
    second = replace(
        case.step,
        id="working_copy",
        output_path="outputs/current/second-copy.json",
        arguments={
            "sourcePath": first.arguments["destinationPath"],
            "destinationPath": "outputs/current/editable.kicad_pcb",
        },
    )
    authority = case.runtime._integration_file_copy_authority
    plan = replace(authority.plan, steps=(first, second))
    authority.plan = plan
    assert case.runtime._verified_copy_sources == ()

    async def no_model(*args, **kwargs):
        raise AssertionError("Fixed copy operations must not call a model")

    async def event_sink(event):
        await case.emit(
            event["kind"],
            **{key: value for key, value in event.items() if key != "kind"},
        )

    result = await execute_prompt_workflow(
        service=service(case.root),
        workspace_dir=str(case.root),
        plan=plan,
        input_values={"brief": "Human engineering input"},
        response_generator=no_model,
        on_event=event_sink,
        tool_runtime=case.runtime,
        run_id="run-1",
    )
    paths = {
        representation["location"]
        for output in result["results"]
        for representation in output["representations"]
        if representation["kind"] == "workspace_file"
    }
    assert first.arguments["destinationPath"] in paths
    assert second.arguments["destinationPath"] not in paths
    assert (
        case.root / second.arguments["destinationPath"]
    ).read_bytes() == b"Human engineering input"
    copy_events = [
        value
        for kind, value in case.events
        if kind == "integration_file_copy_authorized"
    ]
    assert len(copy_events) == 2
    assert copy_events[1]["source_provenance"]["kind"] == "verified_run_output"
    assert copy_events[1]["source_provenance"]["task_id"] == "preserve_source"


@pytest.mark.asyncio
async def test_input_growth_after_audit_uses_bounded_streaming_identity(
    case, monkeypatch
):
    await case.bind()

    async def emit(kind, **data):
        await case.emit(kind, **data)
        monkeypatch.setattr(
            "workspace_service.workspace_file_identity.MAX_IDENTITY_BYTES", 64
        )
        (case.root / "inputs/brief.md").write_bytes(b"x" * 65)

    with pytest.raises(ValueError, match="exceeds"):
        await case.runtime.call(case.step, case.step.arguments, on_event=emit)
    assert not (case.root / case.step.arguments["destinationPath"]).exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change", ["session", "workspace", "principal", "arguments", "expired"]
)
async def test_permit_is_bound_to_one_exact_private_session_call(
    case, monkeypatch, change
):
    import time

    session = replace(case.session, principal_id="wright-native-workflow")
    arguments = dict(case.step.arguments)
    case.artifacts.file_copier.grant(
        request_id="bound",
        session_id=session.session_id,
        workspace_id=session.workspace_id,
        workspace_path=session.workspace_path,
        arguments=arguments,
        expected_sha256=sha(b"Human engineering input"),
        expected_bytes=None,
        policy_digest="a" * 64,
        source_provenance={"kind": "enrolled_input"},
    )
    if change == "session":
        session = replace(session, session_id="different")
    if change == "workspace":
        session = replace(session, workspace_id="different")
    if change == "principal":
        session = replace(session, principal_id="public-caller")
    if change == "arguments":
        arguments["destinationPath"] = "outputs/current/other.kicad_pcb"
    if change == "expired":
        now = time.monotonic()
        monkeypatch.setattr(
            "workspace_service.workspace_file_copy.time.monotonic", lambda: now + 31
        )
    with pytest.raises(GatewayError, match="authority"):
        case.artifacts.file_copier.copy(session, arguments, "bound")
    assert not (case.root / arguments["destinationPath"]).exists()


@pytest.mark.asyncio
async def test_parent_replacement_at_publication_fails_closed(case, monkeypatch):
    import os
    import workspace_service.workspace_file_copy as copy_module

    await case.bind()
    fsync = os.fsync
    parent = case.root / "outputs/current"
    moved = case.root / "outputs/moved"

    def concurrent_move(fd):
        fsync(fd)
        # Windows denies ancestor rename. POSIX checks the pinned parent identity.
        parent.rename(moved)
        parent.mkdir()

    monkeypatch.setattr(copy_module.os, "fsync", concurrent_move)
    with pytest.raises(WorkflowSourceExecutionError):
        await case.runtime.call(case.step, case.step.arguments, on_event=case.emit)
    assert not (parent / "working.kicad_pcb").exists()
    assert not (moved / "working.kicad_pcb").exists()
    assert not list((case.root / "outputs").rglob("*.tmp"))


@pytest.mark.asyncio
@pytest.mark.parametrize("through_descriptor", [False, True])
async def test_actual_temporary_bytes_must_match_source_before_receipt(
    case, monkeypatch, through_descriptor
):
    import os
    import workspace_service.workspace_file_copy as copy_module

    await case.bind()
    original = (case.root / case.step.arguments["sourcePath"]).read_bytes()
    fsync = os.fsync

    def corrupt_temporary(fd):
        fsync(fd)
        if through_descriptor:
            # Fault injection through our own descriptor exercises actual output
            # hashing even on Windows where independent writes are denied.
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, b"X" * len(original))
        else:
            temporary = next(
                (case.root / "outputs/current").glob("*.wright-copy-*.tmp")
            )
            with temporary.open("r+b") as stream:
                stream.write(b"X" * len(original))

    monkeypatch.setattr(copy_module.os, "fsync", corrupt_temporary)

    def forbidden_publication(*args, **kwargs):
        raise AssertionError("Corrupted copied bytes must never reach publication")

    monkeypatch.setattr(copy_module.os, "link", forbidden_publication)
    with pytest.raises(WorkflowSourceExecutionError):
        await case.runtime.call(case.step, case.step.arguments, on_event=case.emit)
    assert (case.root / case.step.arguments["sourcePath"]).read_bytes() == original
    assert not (case.root / case.step.arguments["destinationPath"]).exists()
    assert not list((case.root / "outputs/current").glob("*.tmp"))


@pytest.mark.asyncio
async def test_windows_case_alias_cannot_collide_with_saved_receipt(case):
    import os

    if os.name != "nt":
        pytest.skip("Windows case-insensitive filesystem contract")
    await case.bind()
    step = replace(
        case.step,
        output_path="outputs/current/report.json",
        arguments={
            **case.step.arguments,
            "destinationPath": "outputs/current/REPORT.json",
        },
    )
    authority = case.runtime._integration_file_copy_authority
    authority.plan = replace(authority.plan, steps=(step,))
    with pytest.raises(WorkflowSourceExecutionError, match="receipt"):
        await case.runtime.call(step, step.arguments, on_event=case.emit)
    assert not (case.root / "outputs/current/report.json").exists()
