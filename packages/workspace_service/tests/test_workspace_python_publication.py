"""Syntax checks must happen before immutable source publication, not CAD."""

import asyncio
import hashlib
import json
from types import SimpleNamespace

import pytest

from tool_registry.gateway_models import GatewaySessionContext
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from workspace_service.workspace_document_artifacts import (
    MAX_DOCUMENT_BYTES,
    WorkspaceDocumentArtifactError,
    validate_python_source,
)
from workspace_service.workspace_document_gateway import (
    WorkspaceDocumentGatewayProvider,
)
from packages.workspace_service.tests.test_workspace_document_gateway import _fixture
from packages.workspace_service.tests.test_workflow_mcp_execution import Gateway
from packages.workspace_service.tests.test_workflow_source_execution import (
    task,
    source,
    service,
)
from packages.workspace_service.tests.test_workflow_ai_task import done


def native_session(session):
    return GatewaySessionContext(
        session.session_id,
        "wright-native-workflow",
        session.workspace_id,
        session.workspace_path,
        "legacy",
        binding_session_id="s1",
    )


def publish(artifacts, session, content, request_id):
    artifacts._grant_integration_source_write(
        request_id=request_id,
        session_id=session.session_id,
        workspace_id=session.workspace_id,
        relative_path="campaign/new/bracket-source.py",
        content_sha256=hashlib.sha256(content.encode()).hexdigest(),
        policy_digest="a" * 64,
        actor="integration-test",
    )
    return artifacts.publish(
        session=session,
        relative_path="campaign/new/bracket-source.py",
        content=content,
        media_type="text/plain",
        overwrite=False,
        request_id=request_id,
        correlation_id="syntax-test",
    )


@pytest.mark.parametrize(
    "content",
    [
        'segments = {"points": [[[0, 0, 0], [1, 0, 0]], [[0, 1, 0], [1, 1, 0]]}}\n',
        "return 1\n",
        "value = '\x00'\n",
    ],
)
def test_invalid_python_is_rejected_without_creating_file_or_directory(
    tmp_path, content
):
    _, workspace, artifacts, session = _fixture(tmp_path)
    with pytest.raises(WorkspaceDocumentArtifactError, match="Python.*syntax"):
        publish(artifacts, native_session(session), content, "invalid-source")
    assert list(workspace.iterdir()) == []


def test_corrected_source_can_be_published_once_after_syntax_rejection(tmp_path):
    _, workspace, artifacts, session = _fixture(tmp_path)
    session = native_session(session)
    with pytest.raises(WorkspaceDocumentArtifactError, match="Python.*syntax"):
        publish(artifacts, session, "values = [1, 2}\n", "invalid-source")
    content = "values = [1, 2]\n"
    record = publish(artifacts, session, content, "corrected-source")
    assert (workspace / record.relative_path).read_text() == content
    with pytest.raises(WorkspaceDocumentArtifactError, match="already exists"):
        publish(artifacts, session, "values = [3]\n", "overwrite-attempt")
    assert (workspace / record.relative_path).read_text() == content


def test_python_syntax_inspection_does_not_execute_source_or_import_native_tools(
    tmp_path,
):
    _, workspace, artifacts, session = _fixture(tmp_path)
    sentinel = workspace / "must-not-exist"
    content = f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\nimport unavailable_native_cad_package\n"
    record = publish(artifacts, native_session(session), content, "valid-source")
    assert not sentinel.exists()
    assert (workspace / record.relative_path).read_text() == content


def test_runtime_exposes_repairable_syntax_error_before_gateway_dispatch():
    tool = WorkspaceDocumentGatewayProvider._tool()
    gateway = Gateway()
    runtime = WorkflowMcpRuntime(gateway, workspace_id="w1", session_id="s1")
    step = SimpleNamespace(
        title="Author bracket", server_id=tool.server_id, tool_name=tool.name
    )
    arguments = {
        "relativePath": "bracket-source.py",
        "content": "a = [1}\n",
        "mediaType": "text/plain",
    }
    with pytest.raises(WorkflowSourceExecutionError, match="Python.*syntax.*line 1"):
        runtime.validate(step, arguments, tool.input_schema)
    # The existing bounded invalid-arguments path can ask for corrected content
    # before making any mutating call; it must not need overwrite authority.
    runtime.validate(step, {**arguments, "content": "a = [1]\n"}, tool.input_schema)
    runtime.validate(
        step, {**arguments, "relativePath": "notes.txt"}, tool.input_schema
    )
    assert gateway.calls == []


@pytest.mark.parametrize(
    "content",
    ["#" * (MAX_DOCUMENT_BYTES + 1), "\ud800"],
    ids=["oversize", "invalid-utf8"],
)
def test_source_validation_is_bounded_and_requires_utf8(content):
    with pytest.raises(WorkspaceDocumentArtifactError):
        validate_python_source(content)


@pytest.mark.parametrize("correct", [True, False])
def test_agent_loop_repairs_before_mutation_without_increasing_call_budget(
    tmp_path, correct
):
    tool = WorkspaceDocumentGatewayProvider._tool()
    gateway = Gateway()
    gateway.list_tools = lambda *_: (tool,)
    runner = WorkflowMcpRuntime(gateway, workspace_id="workspace", session_id="session")
    workflow = compile_prompt_workflow(
        source(
            task(
                "author",
                fmt="text",
                authoring_template="mcp-task",
                mcp_server=tool.server_id,
                max_tool_calls=2,
            )
        )
    )
    assert workflow.steps[0].max_tool_calls == 2
    decisions = []

    async def decide(messages, tools, **kwargs):
        decisions.append(messages[-1])
        index = len(decisions)
        if index == 3 and correct:
            return done("Source published", (2,))
        if index > 1:
            assert "Python source syntax" in messages[-1]["content"]
        arguments = {
            "relativePath": "source.py",
            "mediaType": "text/plain",
            "content": "values = [1]\n" if index == 2 and correct else "values = [1}\n",
        }
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": f"call_{index}",
                    "type": "function",
                    "function": {
                        "name": tools[0]["function"]["name"],
                        "arguments": json.dumps(arguments),
                    },
                }
            ],
        }

    run = execute_prompt_workflow(
        service=service(tmp_path),
        workspace_dir=str(tmp_path),
        plan=workflow,
        input_values={},
        response_generator=None,
        action_generator=decide,
        tool_runtime=runner,
    )
    if correct:
        result = asyncio.run(run)
        assert [call["status"] for call in result["steps"][0]["tool_calls"]] == [
            "invalid_arguments",
            "succeeded",
        ]
        assert len(gateway.calls) == 1
    else:
        with pytest.raises(WorkflowSourceExecutionError, match="tool-call limit"):
            asyncio.run(run)
        assert gateway.calls == []
    assert len(decisions) == 3
