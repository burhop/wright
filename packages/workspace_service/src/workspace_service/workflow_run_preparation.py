"""Resolve normal or explicitly enrolled integration execution through one compiler."""

from __future__ import annotations

from dataclasses import dataclass
import re
from uuid import uuid4

from .workflow_mcp_execution import WorkflowMcpRuntime
from .workflow_source_execution import (
    WorkflowSourceExecutionError,
    prepare_prompt_workflow,
)
from .workflow_model_routing import UNSET_CONTEXT, freeze_workflow_model_routing


@dataclass
class PreparedWorkflowRun:
    plan: object
    values: dict
    runtime: object | None
    execution_context: dict | None
    run_id: str


def has_revised_template_source(origin, document):
    """Identify a locally revised starter; this grants no run qualification."""
    initial = origin.get("instantiated_source_digest") if origin else None
    return bool(
        isinstance(initial, str)
        and re.fullmatch(r"[a-f0-9]{64}", initial)
        and initial != document.storage_digest
        and document.definition_revision > 1
    )


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
            # Catalog readiness describes the shipped starter. A later accepted
            # source revision is qualified below against its actual inputs,
            # tools, model and authority; lineage is never a permanent setup lock.
            # Older origins without an exact initial identity remain fail-closed.
            initial = origin.get("instantiated_source_digest")
            if (
                isinstance(initial, str)
                and re.fullmatch(r"[a-f0-9]{64}", initial)
                and initial != source_digest
            ):
                current = await service.workflow_sources.read(
                    workspace_dir, source_path
                )
                if current.storage_digest != source_digest:
                    raise WorkflowSourceExecutionError(
                        "WORKFLOW_SOURCE_CONFLICT",
                        "The accepted process changed during setup.",
                        "Reopen the current process and check readiness again.",
                    )
                if has_revised_template_source(origin, current):
                    return None
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
    expected_execution_context=UNSET_CONTEXT,
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

    if run_id is None:
        run_id = uuid4().hex
    else:
        from pydantic import TypeAdapter
        from core.process_validation import Identifier

        run_id = TypeAdapter(Identifier).validate_python(run_id)
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
            run_id=run_id,
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
        from .workflow_approval_execution import qualify_workflow_action_dispatch

        qualify_workflow_action_dispatch(plan, context)
        plan, context = await freeze_workflow_model_routing(
            service, plan, context, expected_execution_context
        )
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
        if runtime is not None:
            for step in plan.steps:
                if step.tool_name or step.agent_task:
                    runtime.preflight_authority(step)
        return PreparedWorkflowRun(plan, values, runtime, context, run_id)
    except BaseException:
        if runtime is not None:
            await runtime.close()
        raise
