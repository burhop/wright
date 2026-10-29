"""Qualify prepared inputs through the existing source-run preparation owner."""

from __future__ import annotations

from datetime import datetime

from core.process_interactions import NavigationTarget, Readiness

from ..workflow_mcp_execution import WorkflowMcpRuntime
from ..workflow_run_preparation import prepare_authorized_workflow_run
from ..workflow_source_execution import WorkflowSourceExecutionError
from .errors import ProcessInterfaceError
from .inputs import PreparedInputs, input_readiness, prepare_inputs, _sections


async def prepare_values(
    service, resolved, *, bindings=(), snapshot=None, gateway=None, session_id=""
):
    """Read configured choices only; never invoke a workflow's engineering stages."""
    runtime = None
    plan, _ = _sections(resolved.document.source)
    has_options = any(
        isinstance(
            metadata := fields.get("settings", {}).get("interaction_input"), dict
        )
        and metadata.get("option_source")
        for fields in plan.inputs.values()
    )
    try:
        if has_options and gateway is not None:
            runtime = WorkflowMcpRuntime(
                gateway() if callable(gateway) else gateway,
                workspace_id=resolved.process.workspace_id,
                session_id=session_id,
            )
        return await prepare_inputs(
            service=service.workspace,
            workspace_dir=resolved.workspace_dir,
            process=resolved.process,
            source=resolved.document.source,
            bindings=snapshot.bindings if snapshot else bindings,
            snapshot_id=snapshot.snapshot_id if snapshot else None,
            created_at=snapshot.created_at if snapshot else None,
            limits=service.limits,
            tool_runtime=runtime,
        )
    finally:
        if runtime is not None:
            await runtime.close()


async def qualify_inputs(
    service, resolved, prepared: PreparedInputs, *, gateway=None, session_id=""
) -> Readiness:
    readiness = input_readiness(prepared)
    if readiness.state != "ready":
        return readiness

    def available_gateway():
        if gateway is None:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "The configured process tools are unavailable.",
                "Connect the required MCP providers in this workspace before starting.",
            )
        return gateway() if callable(gateway) else gateway

    qualified = None
    try:
        qualified = await prepare_authorized_workflow_run(
            service=service.workspace,
            workspace_dir=resolved.workspace_dir,
            workspace_id=resolved.process.workspace_id,
            session_id=session_id,
            source_path=resolved.process.source_path,
            source_digest=resolved.process.source_digest,
            input_snapshot=prepared.snapshot,
            gateway=available_gateway,
        )
    except ProcessInterfaceError as error:
        reason = error.reason
    except WorkflowSourceExecutionError as error:
        code = (
            "SOURCE_CHANGED"
            if error.code == "WORKFLOW_SOURCE_CONFLICT"
            else "READINESS_UNSUPPORTED"
            if error.code
            in {
                "WORKFLOW_SOURCE_INVALID",
                "WORKFLOW_ACTION_INTENT_UPGRADE_REQUIRED",
                "WORKFLOW_ACTION_INTENT_SCHEMA_UNSUPPORTED",
                "WORKFLOW_ACTION_INTENT_INVALID",
            }
            else "CAPABILITY_UNAVAILABLE"
        )
        reason = ProcessInterfaceError(
            code,
            str(error),
            error.correction,
            navigation=NavigationTarget(kind="block", block_id=error.block_id)
            if error.block_id
            else None,
        ).reason
    else:
        expirations = [
            binding.stale_after
            for binding in prepared.snapshot.bindings
            if binding.kind == "option" and binding.stale_after
        ]
        return Readiness.model_validate(
            {
                **readiness.model_dump(),
                "expires_at": min(
                    expirations,
                    key=lambda timestamp: datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    ),
                )
                if expirations
                else None,
            }
        )
    finally:
        if qualified is not None and qualified.runtime is not None:
            await qualified.runtime.close()
    return Readiness.model_validate(
        {
            **readiness.model_dump(),
            "state": "unsupported"
            if reason.code == "READINESS_UNSUPPORTED"
            else "blocked",
            "reasons": (reason,),
        }
    )
