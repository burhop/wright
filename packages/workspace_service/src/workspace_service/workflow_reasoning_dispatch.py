"""Resolve run-scoped callbacks without moving execution out of Wright."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowReasoningCallbacks:
    response: object
    action: object = None


def resolve_workflow_reasoning_callbacks(
    service, *, workspace_dir, run_id, execution_context, response, action
):
    factory = getattr(service, "workflow_reasoning_factory", None)
    if factory is not None:
        callbacks = factory(
            workspace_dir=workspace_dir,
            run_id=run_id,
            execution_context=execution_context,
        )
        if (
            not isinstance(callbacks, WorkflowReasoningCallbacks)
            or not callable(callbacks.response)
            or (callbacks.action is not None and not callable(callbacks.action))
        ):
            raise ValueError("The configured workflow reasoning factory is unavailable")
        return callbacks
    # Explicitly injected adapter callbacks are supported for controlled probes.
    # A new frozen route must never fall through to the legacy model callbacks.
    route = (execution_context or {}).get("model_routing", {}).get("text") or {}
    if route.get("adapter") == "openai-desktop-harness":
        bound = getattr(response, "__self__", None)
        if (
            bound is None
            or not callable(getattr(bound, "resolution", None))
            or bound.resolution().model_dump(mode="json") != route
            or getattr(bound, "run_id", None) != run_id
        ):
            raise ValueError("The frozen desktop route has no bound reasoning callback")
    return WorkflowReasoningCallbacks(response, action)
