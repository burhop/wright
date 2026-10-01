"""Resolve normal or explicitly enrolled integration execution through one compiler."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .workflow_mcp_execution import WorkflowMcpRuntime
from .workflow_source_execution import (
    WorkflowSourceExecutionError,
    prepare_prompt_workflow,
)


@dataclass
class PreparedWorkflowRun:
    plan: object
    values: dict
    runtime: object | None
    execution_context: dict | None
    run_id: str


async def qualify_workflow_run_origin(
    *,
    service,
    workspace_dir,
    workspace_id,
    source_path,
    source_digest,
    integration_policy_digest=None,
):
    """Keep origin/grant gates ahead of source values and tool qualification."""
    grant = None
    if integration_policy_digest is not None:
        grant = service.workflow_integration_policies.get(integration_policy_digest)
        if (
            grant["workspace_id"] != workspace_id
            or grant["source_path"] != source_path
            or grant["source_digest"] != source_digest
        ):
            raise WorkflowSourceExecutionError(
                "WORKFLOW_INTEGRATION_POLICY_INVALID",
                "The enrolled grant does not match this workspace and source.",
                "Enroll the exact integration run through local campaign management.",
            )
    else:
        origin = await service.workflow_sources.read_template_origin(
            workspace_dir, source_path
        )
        if origin is not None:
            readiness = service.engineering_workflow_templates.readiness(
                str(origin.get("template_id", "")),
                str(origin.get("template_version", "")),
            )
            if readiness["state"] not in {"ready", "verified"}:
                reasons = readiness.get("blocking_reasons") or [
                    "Required engineering integrations are not ready."
                ]
                raise WorkflowSourceExecutionError(
                    "WORKFLOW_TEMPLATE_SETUP_REQUIRED",
                    "This engineering template needs setup or qualification before a live run.",
                    " ".join(str(reason) for reason in reasons),
                )

    return grant


async def prepare_authorized_workflow_run(
    *,
    service,
    workspace_dir: str,
    workspace_id: str,
    session_id: str,
    source_path: str,
    source_digest: str,
    gateway,
    integration_policy_digest: str | None = None,
    input_snapshot=None,
    run_id: str | None = None,
) -> PreparedWorkflowRun:
    """Public qualification and scoped integration readiness are separate gates.

    The request may reference a locally enrolled grant, but cannot supply its
    authority, tool set, actor or output boundary.
    """
    grant = await qualify_workflow_run_origin(
        service=service,
        workspace_dir=workspace_dir,
        workspace_id=workspace_id,
        source_path=source_path,
        source_digest=source_digest,
        integration_policy_digest=integration_policy_digest,
    )

    runtime = None

    def open_tools():
        nonlocal runtime
        if runtime is None:
            runtime = WorkflowMcpRuntime(
                gateway() if callable(gateway) else gateway,
                workspace_id=workspace_id,
                session_id=session_id,
            )
            if grant is not None:
                runtime.restrict_to(grant["allowed_tools"])
        return runtime

    try:
        plan, values = await prepare_prompt_workflow(
            service=service,
            workspace_dir=workspace_dir,
            path=source_path,
            expected_digest=source_digest,
            tool_runtime=open_tools,
            workspace_id=workspace_id,
            input_snapshot=input_snapshot,
        )
        context = None
        if grant is not None:
            context = await service.workflow_integration_policies.authorize(
                integration_policy_digest,
                workspace_id=workspace_id,
                workspace_dir=workspace_dir,
                source_path=source_path,
                source_digest=source_digest,
                plan=plan,
                tool_runtime=open_tools() if grant["allowed_tools"] else runtime,
                files=service.files,
            )
        if run_id is None:
            run_id = uuid4().hex
        else:
            from pydantic import TypeAdapter
            from core.process_validation import Identifier

            run_id = TypeAdapter(Identifier).validate_python(run_id)
        if context is not None and runtime is not None:
            from .workflow_integration_document_write import (
                bind_integration_document_writes,
            )

            bind_integration_document_writes(
                service=service,
                runtime=runtime,
                context=context,
                plan=plan,
                workspace_dir=workspace_dir,
                workspace_id=workspace_id,
                run_id=run_id,
            )
        return PreparedWorkflowRun(plan, values, runtime, context, run_id)
    except BaseException:
        if runtime is not None:
            await runtime.close()
        raise
