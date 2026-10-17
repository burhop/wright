"""Freeze/revalidate public model selection inside the existing prepared run."""

from dataclasses import replace

from core.workflow_model_routing import (
    WorkflowModelRouting,
    parse_workflow_text_resolution,
)

UNSET_CONTEXT = object()


def step_requires_model(step):
    """Classify model use identically for freezing, restoration and dispatch."""
    return step.agent_task or not (
        step.tool_name
        or step.human_interaction
        or step.human_review
        or step.external_action
        or step.validation
    )


def validate_frozen_model_plan(plan, context):
    """A restored plan must already carry the exact durable route qualification."""
    if context is not None and not isinstance(context, dict):
        raise ValueError("The durable execution context is invalid")
    if not context or "model_routing" not in context:
        return  # Historic checkpoints do not acquire invented frozen provenance.
    frozen = WorkflowModelRouting.model_validate(context["model_routing"])
    expected_text = frozen.text.model_dump(mode="json") if frozen.text else {}
    actual_images = {}
    for step in plan.steps:
        if not step_requires_model(step):
            continue
        if step.native_image_format:
            actual_images[step.id] = step.native_image_resolution
        elif not expected_text or step.model_resolution != expected_text:
            raise ValueError("The restored step has no matching frozen model route")
    if actual_images != frozen.images:
        raise ValueError("The restored native image SDK route changed")


async def freeze_workflow_model_routing(
    service, plan, context, expected_context=UNSET_CONTEXT
):
    from .workflow_source_execution import WorkflowSourceExecutionError

    def unavailable(message, continuing=False):
        return WorkflowSourceExecutionError(
            "WORKFLOW_MODEL_CHANGED" if continuing else "WORKFLOW_MODEL_UNAVAILABLE",
            message,
            "Restore this run's frozen model/adapter configuration, or explicitly revise and start a new run."
            if continuing
            else "Configure a model gateway with a qualified explicit provider/model before starting.",
        )

    continuing = expected_context is not UNSET_CONTEXT
    frozen_raw = (expected_context or {}).get("model_routing") if continuing else None
    # Old durable checkpoints and controlled legacy callbacks keep their original
    # context shape; absence is not retrospectively fabricated frozen provenance.
    if continuing and frozen_raw is None:
        return plan, context
    model_steps = [step for step in plan.steps if step_requires_model(step)]
    reader = getattr(service, "workflow_model_capabilities", None)
    if not model_steps or (reader is None and not continuing):
        return plan, context
    try:
        if reader is None:
            raise ValueError("The frozen adapter's capability reader is unavailable")
        text_steps = [step for step in model_steps if not step.native_image_format]
        text = None
        if text_steps:
            capability = await reader()
            if capability.get("available") is not True:
                raise ValueError(
                    "The model gateway could not qualify the selected model"
                )
            text = parse_workflow_text_resolution(capability["resolution"])
        current = WorkflowModelRouting(
            text=text,
            images={
                step.id: step.native_image_resolution
                for step in model_steps
                if step.native_image_format
            },
        )
        if continuing:
            frozen = WorkflowModelRouting.model_validate(frozen_raw)
            if current != frozen:
                raise ValueError(
                    "The provider, model, adapter/profile or native SDK identity changed during the wait"
                )
        else:
            frozen = current
        bound = replace(
            plan,
            steps=tuple(
                replace(step, model_resolution=frozen.text.model_dump(mode="json"))
                if step_requires_model(step) and not step.native_image_format and frozen.text
                else step
                for step in plan.steps
            ),
        )
        return bound, {
            **(context or {}),
            "model_routing": frozen.model_dump(mode="json"),
        }
    except (ValueError, OSError, KeyError, TypeError, TimeoutError) as exc:
        raise unavailable(
            "The saved model/adapter route cannot be revalidated."
            if continuing
            else "The configured model gateway cannot confirm its current provider/model.",
            continuing,
        ) from exc


def restore_review_model_routing(plan, context):
    """Inspect the recorded route without contacting or replacing its provider.

    This prepares only an inert review plan. Execution must still use the live
    freeze/revalidation above, including exact adapter and model equality.
    """
    from .workflow_source_execution import WorkflowSourceExecutionError

    try:
        if not plan.review_only:
            raise ValueError(
                "Only a review plan can restore a route without qualification"
            )
        if context is not None and not isinstance(context, dict):
            raise ValueError("Invalid frozen execution context")
        if not context or "model_routing" not in context:
            return plan  # Preserve historical absence of routing evidence.
        frozen = WorkflowModelRouting.model_validate(context["model_routing"])
        restored = replace(
            plan,
            steps=tuple(
                replace(step, native_image_resolution=frozen.images.get(step.id, {}))
                if step_requires_model(step) and step.native_image_format
                else replace(step, model_resolution=frozen.text.model_dump(mode="json"))
                if step_requires_model(step) and frozen.text
                else step
                for step in plan.steps
            ),
        )
        validate_frozen_model_plan(restored, context)
        return restored
    except (ValueError, TypeError, KeyError) as exc:
        raise WorkflowSourceExecutionError(
            "WORKFLOW_MODEL_CHANGED",
            "The recorded model/adapter route is invalid for this review.",
            "Inspect the saved run's routing evidence before recording a decision.",
        ) from exc
