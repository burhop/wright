"""Monitor provider-declared operations inside one application task block.

The wright/operation tool metadata is a Wright adapter contract, not a claim
that every MCP server implements MCP Tasks. No job semantics are inferred from
AI prose. Submission happens once; only identified status reads are polled.
"""

import asyncio
import math
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field as dataclass_field, replace
from core.redaction import redact_text
from .workflow_source_execution import _error, _invalid


_PROVIDER_STATES = {"working", "completed", "failed", "cancelled", "input_required"}


@dataclass
class OperationCancellation:
    """One live monitor's control barrier; durable request ownership is upstream."""

    operation_id: str
    step_id: str
    provider_binding: str
    qualify: object
    active: bool = True
    reserved: bool = False
    requested: bool = False
    outcome: str | None = None
    decision: asyncio.Event = dataclass_field(default_factory=asyncio.Event)
    changed: asyncio.Event = dataclass_field(default_factory=asyncio.Event)
    publication_failed: bool = False

    def reserve(self):
        if not self.active or self.reserved or not self.qualify():
            return False
        self.reserved = True
        self.decision = asyncio.Event()
        self.changed.set()
        return True

    def activate(self):
        self.requested = True
        self.decision.set()

    def publication_unknown(self):
        self.publication_failed = True
        self.outcome = "unknown"
        self.decision.set()


def operation_cancellation(runtime, *, reserve=False):
    operations = tuple(getattr(runtime, "_active_operations", {}).values())
    if len(operations) != 1:
        return None
    target = operations[0]
    if reserve:
        return target if target.reserve() else None
    return (
        target if target.active and not target.reserved and target.qualify() else None
    )


def _finite_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _bounded_seconds(profile, field, default, minimum, maximum):
    value = profile.get(field, default)
    if (
        type(value) not in (int, float)
        or not minimum <= value <= maximum
        or not _finite_number(value)
    ):
        raise _invalid(f"The operation {field} is invalid.")
    return float(value)


def _observation_options(profile):
    for field in (
        "id_field",
        "id_argument",
        "status_field",
        "progress_field",
        "remaining_seconds_field",
    ):
        value = profile.get(field)
        if value is not None and (
            not isinstance(value, str) or not value.strip() or len(value) > 160
        ):
            raise _invalid("The operation observation selector is invalid.")
    metrics = profile.get("metrics_fields", {})
    if (
        not isinstance(metrics, dict)
        or len(metrics) > 16
        or any(
            not isinstance(value, str) or not value.strip() or len(value) > 160
            for pair in metrics.items()
            for value in pair
        )
    ):
        raise _invalid("The operation metric selectors are invalid.")
    states = profile.get("states")
    if states is not None and (
        not isinstance(states, dict)
        or not states
        or len(states) > 32
        or any(
            not isinstance(k, str)
            or not k
            or len(k) > 160
            or not isinstance(v, str)
            or v not in _PROVIDER_STATES
            for k, v in states.items()
        )
    ):
        raise _invalid("The operation state mapping is invalid.")
    _bounded_seconds(profile, "poll_seconds", 1, 0.05, 30)
    _bounded_seconds(profile, "freshness_seconds", 30, 0.05, 300)
    _bounded_seconds(profile, "cancel_confirm_seconds", 1, 0, 10)


def _observation(profile, value=None, *, source):
    """Only explicit provider selectors supply metrics; absence remains null."""
    value = value or {}
    now = datetime.now(timezone.utc)
    limitations = []

    def number(selector, maximum=None):
        raw = value.get(selector) if selector else None
        if raw is None:
            return None
        if (
            not _finite_number(raw)
            or raw < 0
            or (maximum is not None and raw > maximum)
        ):
            limitations.append(
                "A configured provider metric is invalid and unavailable."
            )
            return None
        return raw

    metrics = {}
    for name, selector in profile.get("metrics_fields", {}).items():
        raw = value.get(selector)
        if raw is None or type(raw) in (bool, int, float, str):
            if (
                type(raw) in (int, float)
                and not _finite_number(raw)
                or isinstance(raw, str)
                and len(raw) > 1000
            ):
                limitations.append(
                    "A configured provider metric is invalid and unavailable."
                )
                continue
            metrics[name] = redact_text(raw) if isinstance(raw, str) else raw
        else:
            limitations.append(
                "A configured provider metric is invalid and unavailable."
            )
    return {
        "observed_at": now.isoformat(),
        "stale_after": (
            now + timedelta(seconds=float(profile.get("freshness_seconds", 30)))
        ).isoformat(),
        "observation_source": source,
        "progress_percent": number(profile.get("progress_field"), 100),
        "estimated_remaining_seconds": number(profile.get("remaining_seconds_field")),
        "metrics": metrics,
        "limitations": tuple(dict.fromkeys(limitations)),
    }


def validate_operation_profile(runtime, step, profile):
    from .workflow_mcp_execution import schema_digest

    if (
        not isinstance(profile, dict)
        or type(profile.get("version")) is not int
        or profile["version"] != 1
    ):
        raise _invalid("The application operation adapter is unsupported.")
    _observation_options(profile)
    tools = {t.tool_name: t for t in runtime.task_tools(step)}
    pinned = {}
    for role in ("status_tool", "result_tool", "cancel_tool"):
        name = profile.get(role)
        if not name and role != "status_tool":
            continue
        tool = tools.get(name)
        if tool is None or (
            role != "cancel_tool" and tool.annotations.get("readOnlyHint") is not True
        ):
            raise _invalid(f"The application operation adapter needs a valid {role}.")
        if role != "cancel_tool" and not set(tool.required_approvals).issubset(
            runtime.gateway.workspace_approvals_for_model_call(
                runtime.session_id, tool.name
            )
        ):
            raise _invalid(
                "The operation observation capability needs authority configured before submission."
            )
        argument = profile.get("id_argument", "operation_id")
        properties = tool.input_schema.get("properties", {})
        if argument not in properties or set(tool.input_schema.get("required", [])) - {
            argument
        }:
            raise _invalid(
                f"The application {role} must accept the pinned operation identity without additional required inputs."
            )
        pinned[name] = (tool.name, schema_digest(tool))
    return pinned


async def monitor_operation(
    runtime, step, submitted, profile, emit, *, pinned_tools=None
):
    from .workflow_mcp_execution import schema_digest

    if (
        not isinstance(profile, dict)
        or type(profile.get("version")) is not int
        or profile["version"] != 1
    ):
        raise _invalid("The application operation adapter is unsupported.")
    _observation_options(profile)
    id_field = profile.get("id_field", "operation_id")
    if (
        not isinstance(submitted, dict)
        or not isinstance(submitted.get(id_field), str)
        or not submitted[id_field]
        or submitted[id_field].strip() != submitted[id_field]
        or len(submitted[id_field]) > 160
    ):
        if emit:
            await emit(
                "operation_progress",
                task_id=step.id,
                task_title=step.title,
                provider_binding=step.server_id,
                provider_schema_digest=step.schema_digest,
                state="reconciliation_required",
                operation_id=None,
                message="The provider returned a submission response without a verifiable operation identity.",
                **_observation(profile, source="unknown"),
            )
        raise _error(
            "APPLICATION_OUTCOME_UNKNOWN",
            "The application did not return a stable operation identity.",
            "Reconcile the submission before another attempt; do not submit it again automatically.",
        )
    operation_id = submitted[id_field]
    argument = profile.get("id_argument", "operation_id")
    pinned = (
        pinned_tools
        if pinned_tools is not None
        else validate_operation_profile(runtime, step, profile)
    )
    last_observation = _observation(profile, source="submission_receipt")
    last_provider_state = None

    def qualified_cancel():
        name = profile.get("cancel_tool")
        try:
            tool = next(
                (t for t in runtime.task_tools(step) if t.tool_name == name), None
            )
            if tool is None or pinned.get(name) != (tool.name, schema_digest(tool)):
                return False
            approvals = runtime.gateway.workspace_approvals_for_model_call(
                runtime.session_id, tool.name
            )
            return set(tool.required_approvals).issubset(approvals)
        except Exception:
            return False

    cancellation = OperationCancellation(
        operation_id, step.id, step.server_id, qualified_cancel
    )
    runtime._active_operations[step.id] = cancellation

    async def event(state, **extra):
        if emit:
            await emit(
                "operation_progress",
                task_id=step.id,
                task_title=step.title,
                operation_id=operation_id,
                provider_binding=step.server_id,
                provider_schema_digest=step.schema_digest,
                state=state,
                **last_observation,
                **extra,
            )

    async def invoke(role, readonly=False):
        name = profile.get(role)
        tool = next((t for t in runtime.task_tools(step) if t.tool_name == name), None)
        if tool is None or (
            readonly and tool.annotations.get("readOnlyHint") is not True
        ):
            raise _invalid(
                f"The application needs an available {'read-only ' if readonly else ''}{role} operation."
            )
        if pinned.get(name) != (tool.name, schema_digest(tool)):
            raise _invalid(
                "The application operation binding has changed; reconcile its identity before retrying."
            )
        invocation = replace(
            step,
            tool_name=tool.name,
            schema_digest=schema_digest(tool),
            agent_task=False,
        )
        args = {argument: operation_id}
        runtime.validate(invocation, args, tool.input_schema)
        return await runtime.call(invocation, args, monitor=False)

    interval = float(profile.get("poll_seconds", 1))
    states = profile.get(
        "states",
        {
            "working": "working",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
            "input_required": "input_required",
        },
    )

    async def read_status():
        nonlocal last_observation, last_provider_state
        value, _ = await invoke("status_tool", readonly=True)
        if not isinstance(value, dict):
            raise _invalid("The application returned an invalid job status.")
        if id_field in value and value[id_field] != operation_id:
            last_observation = _observation(profile, source="unknown")
            await event(
                "reconciliation_required",
                message="The provider status belongs to another operation identity.",
            )
            raise _invalid(
                "The application returned another operation identity; reconcile the identified job."
            )
        raw_state = value.get(profile.get("status_field", "status"))
        state = states.get(raw_state) if isinstance(raw_state, str) else None
        if state not in _PROVIDER_STATES:
            last_observation = _observation(profile, source="unknown")
            await event(
                "reconciliation_required",
                message="The provider's operation state is not recognized.",
            )
            raise _invalid(
                "The application returned an unknown job state; inspect the operation before retrying."
            )
        last_observation = _observation(profile, value, source="provider_status")
        last_provider_state = state
        await event(state, message=redact_text(str(value.get("message", state)))[:1000])
        return state, value

    async def cancel_and_observe():
        nonlocal last_observation
        if not qualified_cancel():
            last_observation = _observation(profile, source="unknown")
            await event(
                "cancellation_unavailable",
                message="This operation has no currently authorized cancellation capability; reconcile its outcome.",
            )
            return "unknown"
        try:
            async with asyncio.timeout(10):
                await invoke("cancel_tool")
            last_observation = _observation(profile, source="local_request")
            await event(
                "cancellation_requested",
                message="Cancellation requested; waiting for the provider's actual outcome.",
            )
            confirmation = float(profile.get("cancel_confirm_seconds", 1))
            if confirmation:
                async with asyncio.timeout(confirmation):
                    while True:
                        state, _ = await read_status()
                        if state in {"completed", "failed", "cancelled"}:
                            return state
                        await asyncio.sleep(interval)
        except Exception:
            pass
        last_observation = _observation(profile, source="unknown")
        await event(
            "cancellation_unconfirmed",
            message="The provider operation may still be working. Reconcile it before another submission.",
        )
        return "unknown"

    async def cancellation_barrier():
        if not cancellation.reserved:
            return
        try:
            async with asyncio.timeout(6):
                await cancellation.decision.wait()
        except TimeoutError:
            raise _error(
                "APPLICATION_OUTCOME_UNKNOWN",
                "Cancellation request publication could not be confirmed.",
                "Reconcile the retained operation before another action.",
            ) from None
        if cancellation.publication_failed:
            raise _error(
                "APPLICATION_OUTCOME_UNKNOWN",
                "Cancellation request publication could not be confirmed.",
                "Reconcile the retained operation before another action.",
            )
        if cancellation.requested:
            cancellation.outcome = (
                last_provider_state
                if last_provider_state in {"completed", "failed", "cancelled"}
                else await cancel_and_observe()
            )
            raise asyncio.CancelledError()

    try:
        await event(
            "submitted",
            message="Application job submitted; waiting for verified completion.",
        )
        async with asyncio.timeout(step.timeout_seconds):
            while True:
                await cancellation_barrier()
                state, value = await read_status()
                await cancellation_barrier()
                if state == "completed":
                    if profile.get("result_tool"):
                        result = await invoke("result_tool", readonly=True)
                    else:
                        if "result" not in value:
                            raise _invalid(
                                "The application completed without returning its result."
                            )
                        import json

                        result = (
                            value["result"],
                            json.dumps(value["result"], ensure_ascii=False),
                        )
                    await event("results_collected")
                    await cancellation_barrier()
                    return result
                if state in {"failed", "cancelled", "input_required"}:
                    raise _error(
                        "APPLICATION_" + state.upper(),
                        f"{step.title}: application job {state.replace('_', ' ')}.",
                        str(
                            value.get(
                                "message",
                                "Inspect the identified operation before starting another run.",
                            )
                        )[:1000],
                    )
                try:
                    await asyncio.wait_for(
                        cancellation.changed.wait(), timeout=interval
                    )
                except TimeoutError:
                    pass
    except asyncio.CancelledError:
        # Interrupting a monitor has no provider mutation authority. The explicit
        # cancellation use case must retain its separate request/actual outcome.
        if not cancellation.requested or cancellation.outcome is None:
            last_observation = _observation(profile, source="unknown")
            await event(
                "monitor_interrupted",
                message="Observation stopped; the provider operation may still be working.",
            )
        raise
    except TimeoutError:
        # A cancellation request is not proof that a remote mutation stopped.
        await cancel_and_observe()
        raise
    except Exception:
        if (
            last_provider_state
            not in {"completed", "failed", "cancelled", "input_required"}
            or last_observation["observation_source"] == "unknown"
        ):
            last_observation = _observation(profile, source="unknown")
            await event(
                "reconciliation_required",
                message="The provider operation outcome could not be verified; inspect it before submitting another operation.",
            )
        raise
    finally:
        cancellation.active = False
        if runtime._active_operations.get(step.id) is cancellation:
            del runtime._active_operations[step.id]
