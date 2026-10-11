"""Reuse the confined Hermes SDK for frozen workflow model decisions.

No tool executes here. The existing bridge/runtime validates model proposals.
"""

import hashlib
import json
import os

from core.process_validation import canonical_digest
from core.workflow_model_routing import WorkflowSdkTextResolution

from .hermes_role import HermesRoleTransport, HermesRoleInvocationError
from .workflow_model_routing import ModelRouteChangedError, _profile


def sdk_transport_selected():
    selected = os.getenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT", "hermes-http")
    if selected not in {"hermes-http", "hermes-model-sdk"}:
        raise ValueError("The configured workflow model transport is unsupported")
    return selected == "hermes-model-sdk"


def sdk_workflow_resolution(native):
    public = {
        **{
            key: value for key, value in native.items() if key != "configuration_digest"
        },
        "adapter": "hermes-model-sdk",
        "profile": _profile(),
    }
    return WorkflowSdkTextResolution.model_validate(
        {**public, "configuration_digest": canonical_digest(public)}
    ).model_dump(mode="json")


def native_sdk_resolution(frozen):
    route = WorkflowSdkTextResolution.model_validate(frozen)
    public = route.model_dump(
        mode="json", exclude={"adapter", "profile", "configuration_digest"}
    )
    return {
        **public,
        "configuration_digest": hashlib.sha256(
            json.dumps(public, sort_keys=True).encode()
        ).hexdigest(),
    }


async def workflow_sdk_capabilities():
    transport = HermesRoleTransport.from_host()
    if transport is None:
        raise ValueError("The configured Hermes SDK runtime is unavailable")
    native = await transport.probe()
    return {"available": True, "resolution": sdk_workflow_resolution(native)}


async def workflow_sdk_completion(
    payload, expected_resolution, *, invocation_observer=None, qualified_observer=None
):
    """Compare before submission and again inside the credential-owning worker."""
    expected = WorkflowSdkTextResolution.model_validate(expected_resolution)
    if not sdk_transport_selected() or expected.profile != _profile():
        raise ModelRouteChangedError(
            "The frozen workflow model transport/profile changed"
        )
    transport = HermesRoleTransport.from_host()
    if transport is None:
        raise ModelRouteChangedError("The frozen Hermes SDK runtime is unavailable")
    native = await transport.probe()
    if sdk_workflow_resolution(native) != expected.model_dump(mode="json"):
        raise ModelRouteChangedError(
            "The frozen workflow model/SDK configuration changed"
        )
    if qualified_observer is not None:
        await qualified_observer(
            {
                **expected.model_dump(mode="json"),
                "qualification": "sdk_configuration_verified",
            }
        )
    timeout_seconds = _workflow_timeout()
    try:
        result = await transport.call(
            {
                "operation": "generate-workflow",
                "expected_resolution": native_sdk_resolution(expected_resolution),
                "messages": payload["messages"],
                "timeout_seconds": timeout_seconds,
            },
            invocation_observer=invocation_observer,
            timeout_seconds=timeout_seconds,
        )
    except HermesRoleInvocationError as error:
        if error.code == "WORKFLOW_MODEL_CHANGED":
            raise ModelRouteChangedError(
                "The frozen model changed before SDK submission"
            ) from error
        if error.code == "SCOPED_MODEL_TIMEOUT":
            raise TimeoutError("The configured model SDK request timed out") from error
        raise
    return {
        "model": result.get("response_model"),
        "usage": result.get("usage"),
        "choices": [{"message": {"role": "assistant", "content": result["text"]}}],
    }


def _workflow_timeout():
    from .report_generation import workflow_model_timeout_seconds

    return workflow_model_timeout_seconds()
