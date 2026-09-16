from dataclasses import replace
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from tool_registry.gateway_models import GatewayToolResult, GatewayError
from workspace_service.workflow_integration_document_write import (
    bind_integration_document_writes,
)
from workspace_service.workflow_integration_policy import (
    WorkflowIntegrationPolicyService,
    WorkflowIntegrationPolicyError,
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
from packages.workspace_service.tests.test_workspace_document_gateway import _fixture


def sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def case(tmp_path):
    database, root, artifacts, session = _fixture(tmp_path)
    (root / "inputs").mkdir()
    (root / "inputs/brief.md").write_bytes(b"Create declared engineering source")
    (root / "workflow.wflow").write_bytes(b"immutable canonical source")
    provider = WorkspaceDocumentGatewayProvider(artifacts)
    tool = provider.tools(session)[0]
    events = []

    class Gateway:
        calls = []
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
                assert events[-1][0] == "integration_document_write_authorized"
            self.calls.append(kw)
            value = await provider.call(
                self.session,
                tool,
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
        "author",
        "Author source",
        "write source",
        None,
        (),
        "json",
        "outputs/run/report.json",
        True,
        "indexed",
        tool_name=tool.name,
        server_id=tool.server_id,
        schema_digest=schema_digest(tool),
        expected_files=("outputs/run/jig.py",),
        agent_task=True,
    )
    plan = PromptWorkflow(
        "Source",
        (step,),
        {"brief": {"settings": {"workspace_file": "inputs/brief.md"}}},
        definition_digest=sha(b"immutable canonical source"),
    )
    grant = dict(
        campaign_id="campaign",
        dataset_id="jig-01",
        dataset_digest="a" * 64,
        workspace_id="w1",
        source_path="workflow.wflow",
        source_digest=plan.definition_digest,
        input_files={"inputs/brief.md": sha(b"Create declared engineering source")},
        output_root="outputs/run",
        allowed_tools=runtime.available(),
        approval_mode="auto",
    )

    async def bind(**changes):
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

    arguments = {
        "relativePath": "outputs/run/jig.py",
        "content": "# generated source; no execution here\nraise RuntimeError('source is data')\n",
        "mediaType": "text/plain",
    }
    return SimpleNamespace(
        root=root,
        runtime=runtime,
        step=step,
        plan=plan,
        arguments=arguments,
        bind=bind,
        events=events,
        emit=emit,
        policies=policies,
        gateway=gateway,
        provider=provider,
        tool=tool,
        artifacts=artifacts,
    )


@pytest.mark.asyncio
async def test_declared_python_source_is_written_once_with_exact_attributed_call(case):
    identity = await case.bind()
    value, _ = await case.runtime.call(case.step, case.arguments, on_event=case.emit)
    assert (case.root / "outputs/run/jig.py").read_text() == case.arguments["content"]
    audit = case.events[0][1]
    assert (
        audit["actor"] == "integration_test:campaign"
        and audit["integration_policy_digest"] == identity
    )
    assert audit["content_sha256"] == value["sha256"] and audit["run_id"] == "run-1"
    assert "content" not in audit
    assert case.gateway.calls[0]["workspace_approvals"] == {"workspace_write_approval"}
    with pytest.raises(WorkflowIntegrationPolicyError, match="existing output"):
        await case.runtime.call(case.step, case.arguments, on_event=case.emit)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        "manual",
        "revoked",
        "source",
        "input",
        "unexpected_path",
        "escape",
        "overwrite",
        "no_audit",
        "schema",
    ],
)
async def test_integration_document_authority_is_narrow_and_live(case, change):
    identity = await case.bind(
        **({"approval_mode": "manual"} if change == "manual" else {})
    )
    step = case.step
    if change == "revoked":
        case.policies.revoke(identity)
    elif change == "source":
        (case.root / "workflow.wflow").write_bytes(b"changed")
    elif change == "input":
        (case.root / "inputs/brief.md").write_bytes(b"changed")
    elif change == "unexpected_path":
        case.arguments["relativePath"] = "outputs/run/unexpected.py"
    elif change == "escape":
        case.arguments["relativePath"] = "../outside.py"
    elif change == "overwrite":
        case.arguments["overwrite"] = True
    elif change == "schema":
        step = replace(step, schema_digest="f" * 64)
    with pytest.raises(WorkflowSourceExecutionError):
        await case.runtime.call(
            step, case.arguments, on_event=None if change == "no_audit" else case.emit
        )
    assert not (case.root / "outputs/run/jig.py").exists()


@pytest.mark.asyncio
async def test_normal_runtime_cannot_invent_document_approval(case):
    with pytest.raises(WorkflowSourceExecutionError):
        await case.runtime.call(case.step, case.arguments, on_event=case.emit)
    assert case.gateway.calls[-1]["workspace_approvals"] == set()
    assert case.events == []


@pytest.mark.asyncio
async def test_forged_provider_context_does_not_enable_python_source(case):
    with pytest.raises(GatewayError, match="reviewed text extension"):
        await case.provider.call(
            case.gateway.session,
            case.tool,
            case.arguments,
            request_id="forged-request",
            approval_context={
                "workspace_approvals": ["workspace_write_approval"],
                "integration_test": True,
                "actor": "integration_test:campaign",
                "integration_policy_digest": "a" * 64,
            },
            progress_callback=None,
        )
    assert not (case.root / "outputs/run/jig.py").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change", ["arguments", "revoke_after_audit", "source_after_audit"]
)
async def test_final_dispatch_rechecks_exact_bytes_and_revocation(case, change):
    identity = await case.bind()
    if change == "arguments":
        case.gateway.mutate = lambda args: args.update(content="different content")

    async def emit(kind, **data):
        await case.emit(kind, **data)
        if change == "revoke_after_audit":
            case.policies.revoke(identity)
        if change == "source_after_audit":
            (case.root / "workflow.wflow").write_bytes(b"changed after authorization")

    with pytest.raises(WorkflowIntegrationPolicyError):
        await case.runtime.call(case.step, case.arguments, on_event=emit)
    assert not (case.root / "outputs/run/jig.py").exists()


@pytest.mark.asyncio
async def test_declared_path_cannot_follow_symlink_outside_attempt(case, tmp_path):
    await case.bind()
    outside = tmp_path / "external"
    outside.mkdir()
    (case.root / "outputs").mkdir()
    try:
        (case.root / "outputs/run").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Host does not permit creation of a test symlink")
    with pytest.raises((WorkflowSourceExecutionError, ValueError)):
        await case.runtime.call(case.step, case.arguments, on_event=case.emit)
    assert not (outside / "jig.py").exists()


def test_new_scoped_source_authority_changes_pinned_tool_revision(case):
    old = replace(
        case.tool,
        provenance={
            **case.tool.provenance,
            "server_revision": "wright-workspace-document-v1",
        },
    )
    assert schema_digest(old) != schema_digest(case.tool)
