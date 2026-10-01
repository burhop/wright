"""Exact approved MCP operation configuration and subject preparation.

This is an adapter to the existing runtime and approval owner, not a process
executor. Provider semantics must be explicitly qualified in tool metadata;
neither a tool name nor a model's success prose supplies them.
"""

from dataclasses import replace
import asyncio
import hashlib
import json
import re

from core.process_validation import canonical_json


def _invalid(message):
    from .workflow_source_execution import _error

    return _error(
        "WORKFLOW_MCP_OPERATION_INVALID",
        message,
        "Configure an exact enabled tool, connected arguments, destination and finite operation policy before starting.",
    )


def _digest(value):
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _json_bytes(value):
    return canonical_json(value).encode("utf-8")


def _name(value):
    return isinstance(value, str) and 0 < len(value) <= 160 and value.strip() == value


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def operation_step(step):
    """Map declared submission inputs onto the existing MCP runtime's step."""
    action = step.external_action or {}
    binding, destination, settings = (
        action.get("binding"),
        action.get("destination"),
        action.get("settings"),
    )
    if (
        action.get("action_kind") != "mcp-operation"
        or action.get("action") != {"kind": "mcp-operation", "mode": "submit"}
        or not isinstance(binding, dict)
        or set(binding) != {"server", "tool", "schema"}
        or not _name(binding.get("server"))
        or not _name(binding.get("tool"))
        or not _sha(binding.get("schema"))
        or not isinstance(destination, dict)
        or set(destination) != {"kind", "id"}
        or not all(_name(destination.get(k)) for k in ("kind", "id"))
        or not isinstance(settings, dict)
        or set(settings)
        - {
            "arguments",
            "argument_sources",
            "destination_argument",
            "timeout_seconds",
            "operation_policy",
            "receipt_path",
        }
        or not isinstance(settings.get("arguments"), dict)
        or not isinstance(settings.get("argument_sources"), dict)
        or len(settings["arguments"]) + len(settings["argument_sources"]) > 128
        or not _name(settings.get("destination_argument"))
        or type(settings.get("timeout_seconds")) is not int
        or not 1 <= settings["timeout_seconds"] <= 3600
    ):
        raise _invalid(
            f"{step.title}: the approved MCP operation configuration is incomplete or unsupported."
        )
    policy = settings.get("operation_policy")
    if (
        not isinstance(policy, dict)
        or set(policy)
        - {"mode", "qualification_digest", "profile_digest", "tool_bindings"}
        or not {"mode", "qualification_digest", "profile_digest"}.issubset(policy)
        or policy.get("mode") not in {"receipt", "observe"}
        or not _sha(policy.get("qualification_digest"))
        or (policy["mode"] == "observe" and not _sha(policy.get("profile_digest")))
        or (policy["mode"] == "receipt" and policy.get("profile_digest") is not None)
        or (
            policy["mode"] == "observe"
            and not isinstance(policy.get("tool_bindings"), dict)
        )
        or (policy["mode"] == "receipt" and policy.get("tool_bindings"))
    ):
        raise _invalid(
            f"{step.title}: pin the qualified submission and observation policy."
        )
    refs = {source for _, source in step.references}
    mappings = settings["argument_sources"]
    if set(settings["arguments"]) & set(mappings) or any(
        not _name(name)
        or not isinstance(selector, dict)
        or set(selector) != {"source", "representation"}
        or selector.get("source") not in refs
        or selector.get("representation") not in {"json", "text", "workspace_file"}
        for name, selector in mappings.items()
    ):
        raise _invalid(
            f"{step.title}: each dynamic argument must name one connected source and representation."
        )
    if settings["destination_argument"] not in set(settings["arguments"]) | set(
        mappings
    ):
        raise _invalid(
            f"{step.title}: supply the destination argument before execution."
        )
    if settings["destination_argument"] in settings["arguments"] and (
        settings["arguments"][settings["destination_argument"]] != destination["id"]
    ):
        raise _invalid(
            f"{step.title}: the configured destination differs from its reviewed identity."
        )
    if "receipt_path" in settings:
        from .workflow_source_execution import _safe_path

        if not isinstance(settings["receipt_path"], str):
            raise _invalid(
                f"{step.title}: configure a workspace-relative receipt path."
            )
        _safe_path(settings["receipt_path"])
    from .workflow_external_actions import approval_subject_digest

    approval_subject_digest(
        {
            "definition_digest": "0" * 64,
            "input_digests": [],
            "artifact_digests": [],
            "binding": binding,
            "destination": destination,
            "settings": settings,
            "action": action["action"],
        }
    )
    return replace(
        step,
        tool_name=binding["tool"],
        server_id=binding["server"],
        schema_digest=binding["schema"],
        output_format="json",
        timeout_seconds=settings["timeout_seconds"],
        arguments=settings["arguments"],
        argument_sources={
            name: selector["source"] for name, selector in mappings.items()
        },
    )


def qualify_operation(runtime, step, *, integration=False):
    """Read exact current capability and authority before obtaining consumption."""
    invocation = operation_step(step)
    runtime.preflight(invocation)
    tool = runtime.resolve(invocation)
    profile = tool.upstream_meta.get("wright/approved-operation")
    policy = step.external_action["settings"]["operation_policy"]
    if (
        not isinstance(profile, dict)
        or set(profile)
        != {
            "version",
            "effect",
            "destination_argument",
            "status_field",
            "accepted_values",
            "rejected_values",
            "reference_field",
            "file_arguments",
        }
        or type(profile.get("version")) is not int
        or profile["version"] != 1
        or profile.get("effect") not in {"digital", "physical", "supplier"}
        or profile.get("destination_argument")
        != step.external_action["settings"]["destination_argument"]
        or not _name(profile.get("status_field"))
        or not _name(profile.get("reference_field"))
        or not isinstance(profile.get("file_arguments"), list)
        or len(profile["file_arguments"]) > 32
        or not all(_name(name) for name in profile["file_arguments"])
        or len(set(profile["file_arguments"])) != len(profile["file_arguments"])
        or any(
            not isinstance(profile.get(key), list)
            or not 1 <= len(profile[key]) <= 16
            or not all(_name(v) for v in profile[key])
            or len(set(profile[key])) != len(profile[key])
            for key in ("accepted_values", "rejected_values")
        )
        or set(profile["accepted_values"]) & set(profile["rejected_values"])
        or _digest(profile) != policy["qualification_digest"]
    ):
        raise _invalid(
            f"{step.title}: the provider has no matching qualified submission semantics."
        )
    if integration and profile["effect"] != "digital":
        raise _invalid(
            f"{step.title}: integration test authority cannot authorize physical or supplier effects."
        )
    mappings = step.external_action["settings"]["argument_sources"]
    if any(
        mappings.get(name, {}).get("representation") != "workspace_file"
        for name in profile["file_arguments"]
    ):
        raise _invalid(
            f"{step.title}: connect exact artifact representations for every qualified file argument."
        )
    approvals = runtime.gateway.workspace_approvals_for_model_call(
        runtime.session_id, tool.name
    )
    if not set(tool.required_approvals).issubset(approvals):
        raise _invalid(
            f"{step.title}: configure the provider's required authority before submission."
        )
    operation = tool.upstream_meta.get("wright/operation")
    bindings = None
    if policy["mode"] == "observe":
        from .workflow_async_operations import validate_operation_profile

        if (
            not isinstance(operation, dict)
            or _digest(operation) != policy["profile_digest"]
        ):
            raise _invalid(
                f"{step.title}: the pinned observation policy changed or is unavailable."
            )
        if operation.get("id_field", "operation_id") != profile["reference_field"]:
            raise _invalid(
                f"{step.title}: observation must use the submission's exact provider reference."
            )
        names = tuple(
            operation[key]
            for key in ("status_tool", "result_tool", "cancel_tool")
            if operation.get(key)
        )
        # Reuse the existing finite monitor with only its declared provider tools.
        invocation = replace(invocation, task_tool_allowlist=names)
        bindings = validate_operation_profile(runtime, invocation, operation)
        expected_bindings = {
            name: {"name": identity[0], "schema": identity[1]}
            for name, identity in bindings.items()
        }
        if policy["tool_bindings"] != expected_bindings:
            raise _invalid(
                f"{step.title}: an observation or cancellation tool changed after qualification."
            )
    return invocation, profile, operation if bindings is not None else None, bindings


class OperationRejected(Exception):
    """Only an exact qualified provider rejection proves no submission effect."""

    def __init__(self, evidence):
        super().__init__("The qualified provider rejected the submission")
        self.evidence = evidence


def submission_receipt(value, profile, *, step, settings, integration=False):
    if not isinstance(value, dict) or len(_json_bytes(value)) > 256 * 1024:
        raise _invalid(
            f"{step.title}: the provider returned no bounded structured submission receipt."
        )
    status = value.get(profile["status_field"])
    if not isinstance(status, str):
        raise _invalid(
            f"{step.title}: the provider returned no qualified acceptance or rejection."
        )
    reference = value.get(profile["reference_field"])
    if status in profile["accepted_values"] and not _name(reference):
        raise _invalid(
            f"{step.title}: the provider accepted without an exact operation reference."
        )
    if status not in profile["accepted_values"] + profile["rejected_values"]:
        raise _invalid(f"{step.title}: its submission outcome needs reconciliation.")
    receipt = {
        "operation": "mcp-operation",
        "effect": profile["effect"],
        "submission": "accepted"
        if status in profile["accepted_values"]
        else "rejected",
        "provider_reference": reference if _name(reference) else None,
        "provider_receipt": {
            profile["status_field"]: status,
            profile["reference_field"]: reference if _name(reference) else None,
        },
        "response_digest": _digest(value),
        "argument_digest": settings["argument_digest"],
        "binding": step.external_action["binding"],
        "destination": step.external_action["destination"],
        "operation_policy": settings["operation_policy"],
        "integration_test": integration,
        "observed_outcome": None,
        "cancellation_requested": False,
        "cancellation_outcome": None,
        "delivery_completed": False,
        "replay_permitted": False,
    }
    if receipt["submission"] == "rejected":
        raise OperationRejected(receipt)
    return receipt


async def submit_operation(
    runtime,
    invocation,
    step,
    settings,
    profile,
    *,
    integration=False,
    before_dispatch=None,
):
    """One finite submission; no retry and no completion claim from acceptance."""
    from .workflow_mcp_execution import WorkflowMcpToolError

    arguments = json.loads(_json_bytes(settings["resolved_arguments"]))
    tool = runtime.resolve(invocation)
    runtime.validate(invocation, arguments, tool.input_schema)
    try:
        async with asyncio.timeout(invocation.timeout_seconds):
            value, _ = await runtime.call(
                invocation, arguments, monitor=False, before_dispatch=before_dispatch
            )
    except WorkflowMcpToolError as error:
        # MCP isError alone does not establish rejection before side effects.
        # Only the pinned structured rejection semantics can prove it.
        submission_receipt(
            error.tool_result,
            profile,
            step=step,
            settings=settings,
            integration=integration,
        )
        raise
    receipt = submission_receipt(
        value, profile, step=step, settings=settings, integration=integration
    )
    return value, receipt


async def resolved_operation_settings(
    step,
    responses,
    *,
    service,
    workspace_dir,
    artifacts_by_output=None,
    engineering_results=(),
):
    """Freeze exact argument values and producer identities without executing tools."""
    from .workflow_execution_continuation import encode_value
    from .workflow_references import WorkflowReference, reference_from_result
    from .workflow_results import EngineeringResult

    operation_step(step)
    configured = step.external_action["settings"]
    arguments = json.loads(json.dumps(configured["arguments"], allow_nan=False))
    upstream = {}
    for name, selector in configured["argument_sources"].items():
        source = selector["source"]
        if source not in responses:
            raise _invalid(
                f"{step.title}: a declared argument producer has not supplied its result."
            )
        value = responses[source]
        upstream[source] = _digest(encode_value(value))
        representation = selector["representation"]
        if representation == "workspace_file":
            if not isinstance(value, (WorkflowReference, EngineeringResult)):
                producer, port = source.split(".", 1)
                matches = [
                    result
                    for result in engineering_results
                    if result.provenance.task_id == producer
                    and result.provenance.output_port == port
                    and any(
                        rep.kind == "workspace_file" for rep in result.representations
                    )
                ]
                if len(matches) == 1:
                    value = matches[0]
            if isinstance(value, WorkflowReference):
                path, expected = value.path, value.sha256
            elif isinstance(value, EngineeringResult):
                files = [
                    rep for rep in value.representations if rep.kind == "workspace_file"
                ]
                if len(files) != 1:
                    raise _invalid(
                        f"{step.title}: select one exact file representation."
                    )
                path, expected = files[0].location, files[0].sha256
            else:
                artifacts = (artifacts_by_output or {}).get(source, [])
                if len(artifacts) != 1 or not isinstance(artifacts[0], dict):
                    raise _invalid(
                        f"{step.title}: its file argument has no exact upstream artifact identity."
                    )
                path, expected = (
                    artifacts[0].get("output_path"),
                    artifacts[0].get("sha256"),
                )
            from .workspace_path import WorkspacePath

            WorkspacePath(workspace_dir).resolve(path, must_exist=True)
            if await service.files.hash_reference(workspace_dir, path) != expected:
                raise _invalid(
                    f"{step.title}: its connected file changed before approval."
                )
            arguments[name] = path
            continue
        if isinstance(value, EngineeringResult):
            value = await reference_from_result(
                value,
                service=service,
                workspace_dir=workspace_dir,
                task_title=step.title,
            )
        if isinstance(value, WorkflowReference):
            if value.image_url or value.file_only:
                raise _invalid(
                    f"{step.title}: this argument requires a readable text or JSON representation."
                )
            value = value.text
        if representation == "text":
            if not isinstance(value, str):
                raise _invalid(
                    f"{step.title}: its text argument is not a text representation."
                )
        elif isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError as error:
                raise _invalid(
                    f"{step.title}: its JSON argument is invalid."
                ) from error
        arguments[name] = value
    if (
        arguments.get(configured["destination_argument"])
        != step.external_action["destination"]["id"]
    ):
        raise _invalid(
            f"{step.title}: the resolved destination differs from its declared reviewed identity."
        )
    # Detached canonical bytes reject NaN, unsupported values and oversized data
    # through the existing approval subject validator before checkpoint creation.
    arguments = json.loads(_json_bytes(arguments))
    return {
        **configured,
        "resolved_arguments": arguments,
        "argument_digest": _digest(arguments),
        "upstream_digests": upstream,
    }
