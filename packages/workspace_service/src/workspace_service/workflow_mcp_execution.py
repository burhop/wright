"""Workspace-bound native workflow calls through Wright's existing MCP gateway."""

from __future__ import annotations

import hashlib
import asyncio
import inspect
from copy import copy, deepcopy
from html import escape
import json
import re
import time
import uuid
from agent_adapters.workflow_instructions import (
    embedded_instruction_set,
    invocation_evidence,
    resolve_workflow_instructions,
    validate_workflow_assumptions,
    workflow_action_intent_instructions,
    validate_workflow_helper_instructions,
)
from core.workflow_action_intent import (
    validate_workflow_action_intent,
    workflow_action_intent_schema,
)
from core.process_validation import canonical_digest
from core.workflow_instructions import ACTION_INTENT_VERSION
from agent_adapters.workflow_tool_schema import qualify_workflow_tool_schema_depth
from dataclasses import replace
from jsonschema import Draft202012Validator, SchemaError
from tool_registry.gateway_service import SUPPORTED_PROTOCOL_VERSION
from tool_registry.gateway_models import GatewayError, GatewayWorkspaceScopeError
from .workflow_source_execution import _invalid, _error, WorkflowSourceExecutionError
from .workspace_document_artifacts import (
    WORKSPACE_DOCUMENT_TOOL_NAME,
    WorkspaceDocumentArtifactError,
    validate_python_source,
)


def model_action_schema(tool):
    try:
        Draft202012Validator.check_schema(tool.input_schema)
        wrapped = workflow_action_intent_schema(dict(tool.input_schema))
    except (ValueError, TypeError, AttributeError, SchemaError) as error:
        raise _error(
            "WORKFLOW_ACTION_INTENT_SCHEMA_UNSUPPORTED",
            f"The selected tool ({tool.title or tool.tool_name}) has an input schema that cannot be safely wrapped by the saved action-intent contract.",
            "Select a provider with compatible local JSON pointer references, or update the shared action-intent schema support before running.",
        ) from error
    try:
        qualify_workflow_tool_schema_depth(
            wrapped, action_intent_contract=ACTION_INTENT_VERSION
        )
    except (ValueError, TypeError, AttributeError) as error:
        raise _error(
            "WORKFLOW_ACTION_INTENT_SCHEMA_UNSUPPORTED",
            f"The selected tool ({tool.title or tool.tool_name}) has an input schema that exceeds the supported nesting depth.",
            "Choose only the tools this task needs in its MCP tool selection. If this tool is required, use a compatible provider definition or qualify shared schema support before running.",
        ) from error
    return wrapped


def merged_task_assumptions(previous, proposed):
    merged = deepcopy(previous)
    for choice in proposed:
        prior = merged.get(choice["parameter"])
        if prior is not None:
            if canonical_digest(
                {"value": prior["value"], "units": prior["units"]}
            ) != canonical_digest({"value": choice["value"], "units": choice["units"]}):
                raise ValueError("conflicting_action_assumption")
            prior["affected_outputs"] = list(
                dict.fromkeys(
                    [
                        *prior["affected_outputs"],
                        *choice["affected_outputs"],
                    ]
                )
            )
            if len(prior["affected_outputs"]) > 64:
                raise ValueError("assumption_output_limit")
        else:
            merged[choice["parameter"]] = deepcopy(choice)
    if len(merged) > 64:
        raise ValueError("task_assumption_limit")
    return merged


class WorkflowMcpToolError(WorkflowSourceExecutionError):
    """A failed tool response retained for the run's evidence record."""

    def __init__(self, message, correction, result):
        super().__init__("MCP_CALL_FAILED", message, correction)
        self.tool_result = result


def response_format_repair_messages(
    outcome, output_format, *, instruction_set=None, instruction_override=None
):
    """Reformat a completed response without replay context or tool contracts."""
    return [
        {
            "role": "system",
            "content": resolve_workflow_instructions(
                "recovery",
                instruction_set=instruction_set,
                instruction_override=instruction_override,
                variables={"output_format": output_format},
            ).text,
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "status": outcome["status"],
                    "evidence": outcome["evidence"],
                    "response": outcome["response"],
                },
                ensure_ascii=False,
            ),
        },
    ]


def workflow_decision_kwargs(decide, step, instruction_set, invocation_observer=None):
    """Forward typed context without retrying incompatible legacy callbacks."""
    try:
        parameters = inspect.signature(decide).parameters
    except (TypeError, ValueError):
        parameters = {}
    accepts_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    optional = {
        "output_format": step.output_format,
        "instruction_set": instruction_set,
        "instruction_override": getattr(step, "instruction_override", None),
        "invocation_observer": invocation_observer,
        "expected_resolution": getattr(step, "model_resolution", None) or None,
    }
    context_budget = getattr(step, "mcp_context_budget_bytes", None)
    if context_budget is not None:
        if not accepts_kwargs and (
            "context_budget_bytes" not in parameters
            or parameters["context_budget_bytes"].kind
            is inspect.Parameter.POSITIONAL_ONLY
        ):
            raise _invalid(
                "The configured model adapter does not support this saved context budget."
            )
        optional["context_budget_bytes"] = context_budget
    return {
        name: value
        for name, value in optional.items()
        if accepts_kwargs
        or (
            name in parameters
            and parameters[name].kind is not inspect.Parameter.POSITIONAL_ONLY
        )
    }


def schema_digest(tool):
    material = {
        "server": tool.server_id,
        "name": tool.name,
        "input": dict(tool.input_schema),
        "output": tool.output_schema,
        "authority": tool.provenance.get("server_revision"),
        "approvals": sorted(tool.required_approvals),
    }
    if tool.upstream_meta.get("wright/operation"):
        material["operation_adapter"] = tool.upstream_meta["wright/operation"]
    if tool.upstream_meta.get("wright/approved-operation"):
        material["approved_operation_adapter"] = tool.upstream_meta[
            "wright/approved-operation"
        ]
    if tool.upstream_meta.get("wright/application"):
        material["application_adapter"] = tool.upstream_meta["wright/application"]
    if tool.upstream_meta.get("wright/terminalOperation"):
        material["terminal_operation"] = tool.upstream_meta["wright/terminalOperation"]
    return hashlib.sha256(
        json.dumps(
            material, sort_keys=True, separators=(",", ":"), default=dict
        ).encode()
    ).hexdigest()


def terminal_operation_receipt(tool, arguments, result):
    """Project an explicitly contracted successful save/export receipt."""
    profile = tool.upstream_meta.get("wright/terminalOperation")
    if profile is None:
        return None
    if not isinstance(profile, dict) or profile.get("revision") != 1:
        raise _invalid("The terminal-operation adapter contract is invalid.")
    status_field = profile.get("status_field")
    success_values = profile.get("success_values")
    receipt_fields = profile.get("receipt_fields")
    if (
        not isinstance(status_field, str)
        or not status_field
        or not isinstance(success_values, list)
        or not success_values
        or any(not isinstance(value, str) or not value for value in success_values)
        or not isinstance(receipt_fields, list)
        or not 1 <= len(receipt_fields) <= 16
        or any(not isinstance(field, str) or not field for field in receipt_fields)
    ):
        raise _invalid("The terminal-operation adapter contract is invalid.")
    operation_field = profile.get("operation_field")
    operations = profile.get("operations")
    if operation_field is not None:
        if (
            not isinstance(operation_field, str)
            or not operation_field
            or not isinstance(operations, list)
            or not operations
            or any(not isinstance(value, str) or not value for value in operations)
        ):
            raise _invalid("The terminal-operation adapter contract is invalid.")
        if arguments.get(operation_field) not in operations:
            return None
    elif operations is not None:
        raise _invalid("The terminal-operation adapter contract is invalid.")
    if not isinstance(result, dict) or result.get(status_field) not in success_values:
        return None
    if any(
        field not in result or result[field] is None or result[field] == ""
        for field in receipt_fields
    ):
        return None
    return {
        status_field: result[status_field],
        **{field: result[field] for field in receipt_fields},
    }


def terminal_operation_response(tool, number, receipt, output_format):
    payload = {
        "terminal_operation": tool.name,
        "tool_call_number": number,
        "receipt": receipt,
        "content_validated": False,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if output_format == "html":
        return (
            "<!doctype html><html><head><title>Terminal operation receipt</title>"
            "</head><body><h1>Terminal operation receipt</h1><pre>"
            + escape(encoded)
            + "</pre></body></html>"
        )
    return encoded


def repeatable_call(tool, arguments):
    if (
        tool.annotations.get("readOnlyHint") is True
        or tool.annotations.get("idempotentHint") is True
    ):
        return True
    # Microsoft's browser MCP labels navigation as an action because it changes
    # the selected page. Revisiting a page is normal task navigation, not replay
    # of a completed document mutation. Keep clicks, uploads and scripts guarded.
    source = tool.provenance.get("source_url")
    if not isinstance(source, str):
        return False
    source = source.rstrip("/")
    kicad_source = "https://github.com/blwfish/kicad-mcp"
    if source == kicad_source or source.startswith(kicad_source + "/tree/"):
        # The selected KiCad server exposes mixed read/write operations behind
        # one aggregate `pcb` tool. Standard MCP annotations can only describe
        # the tool as a whole, so repeated post-mutation inspection would be
        # mistaken for replay unless these repository-defined read operations
        # are classified here. Keep every file-changing operation guarded.
        operation = arguments.get("operation")
        if tool.tool_name == "pcb":
            return operation in {"get_constraints", "list_footprints"}
        if tool.tool_name == "audit":
            return operation in {
                "all",
                "placement",
                "footprint_overlaps",
                "pad_clearances",
                "validate_one",
                "keepouts",
                "pre_route_check",
                "constraints",
                "check_silkscreen_overlaps",
            }
        return False
    if source != "https://github.com/microsoft/playwright-mcp":
        return False
    return tool.tool_name in {"browser_navigate", "browser_navigate_back"} or (
        tool.tool_name == "browser_tabs"
        and arguments.get("action") in {"list", "select"}
    )


def safe_recipe_parameter_correction(tool, result):
    """Recognize only the native preflight contract that proves clean rejection."""
    if tool.tool_name != "cad.create_sheet_metal_from_recipe" or not isinstance(
        result, dict
    ):
        return False
    provider_id = result.get("providerId")
    if not isinstance(provider_id, str) or not re.fullmatch(
        r"[a-z][a-z0-9_]{0,63}", provider_id
    ):
        return False
    code = f"{provider_id}_recipe_variable_name_conflict"
    stage = "preflight_before_recipe_mutation_cleanup_confirmed"
    error = result.get("error")
    issues = result.get("issues")
    if not isinstance(error, dict) or not isinstance(issues, list) or len(issues) != 1:
        return False
    issue = issues[0]
    return (
        result.get("operationStatus") == "failed"
        and result.get("isSuccess") is False
        and result.get("isSaved") is False
        and "document" in result
        and result["document"] is None
        and "outputPath" in result
        and result["outputPath"] is None
        and result.get("createdReferences") == []
        and result.get("warnings") == []
        and isinstance(issue, dict)
        and all(
            item.get("code") == code
            and item.get("stage") == stage
            and item.get("retryable") is False
            and item.get("argument") == "parameters"
            for item in (error, issue)
        )
    )


class WorkflowMcpRuntime:
    def __init__(self, gateway, *, workspace_id, session_id):
        self.gateway = gateway
        self._allowed_tool_identities = None
        self._integration_document_write_authority = None
        self._integration_file_read_authority = None
        self._integration_file_copy_authority = None
        self._verified_copy_sources = ()
        self._preflight_catalog = None
        self._active_operations = {}
        self.session_id = "native-workflow-" + uuid.uuid4().hex
        gateway.open_session(
            session_id=self.session_id,
            principal_id="wright-native-workflow",
            workspace_id=workspace_id,
            binding_session_id=session_id,
            transport="streamable_http",
        )
        gateway.initialize_session(
            self.session_id,
            protocol_version=SUPPORTED_PROTOCOL_VERSION,
            client_name="wright-native-workflow",
            client_version="1",
            client_capabilities={},
        )

    async def close(self):
        await self.gateway.close_session(self.session_id)

    def restrict_to(self, allowed_tools):
        """Pin immutable integration authority for every subsequent discovery/call.

        A refreshed gateway catalog cannot introduce a tool, authority revision,
        or schema that was absent from the locally enrolled policy. Reusing a
        runtime for a different policy is forbidden; open another run session.
        """
        identities = set()
        try:
            for tool in allowed_tools:
                server, name, digest = (
                    tool[key] for key in ("server_id", "name", "schema_digest")
                )
                if (
                    not isinstance(server, str)
                    or not server
                    or not isinstance(name, str)
                    or not name
                    or not isinstance(digest, str)
                    or not re.fullmatch(r"[0-9a-f]{64}", digest)
                ):
                    raise ValueError()
                identities.add((server, name, digest))
        except (KeyError, TypeError, ValueError):
            raise _invalid(
                "Integration tools require exact server, name and schema identities."
            ) from None
        pinned = frozenset(identities)
        if (
            self._allowed_tool_identities is not None
            and pinned != self._allowed_tool_identities
        ):
            raise _invalid(
                "Integration tool authority cannot change within an active run."
            )
        self._allowed_tool_identities = pinned

    def tools(self):
        if self._preflight_catalog is not None:
            return self._preflight_catalog
        # Native blocks use actual catalog MCP tools, not legacy workflow/management commands.
        return tuple(
            t
            for t in self.gateway.list_tools(self.session_id)
            if t.server_id not in {"wright", "rivet-workflows"}
            and (
                self._allowed_tool_identities is None
                or (t.server_id, t.name, schema_digest(t))
                in self._allowed_tool_identities
            )
        )

    def preflight_many(self, steps, *, responses=None):
        """Qualify a synchronous batch with one authorized catalog observation.

        Use a disposable preparation copy: the execution runtime never retains
        this observation. No await or provider dispatch occurs in this batch;
        later batches and actual calls resolve current gateway authority again.
        """
        prepared = copy(self)
        prepared._preflight_catalog = self.tools()
        for step in steps:
            prepared.preflight(step)
            if responses is not None and step.tool_name:
                prepared.preflight_values(step, responses)

    def available(self):
        return [
            {
                "name": t.name,
                "server_id": t.server_id,
                "tool_name": t.tool_name,
                "title": t.title or t.tool_name.replace("_", " "),
                "description": t.description,
                "input_schema": dict(t.input_schema),
                "output_schema": t.output_schema,
                "schema_digest": schema_digest(t),
            }
            for t in self.tools()
        ]

    def resolve(self, step):
        tool = next(
            (
                t
                for t in self.tools()
                if t.name == step.tool_name and t.server_id == step.server_id
            ),
            None,
        )
        if tool is None:
            raise _invalid(
                f"{step.title}: the selected MCP tool is unavailable.",
                "Enable its server for this workspace in Tool Registry, then select the tool again.",
            )
        if schema_digest(tool) != step.schema_digest:
            raise _invalid(
                f"{step.title}: the MCP tool definition has changed.",
                "Select the tool again to review its current inputs, then save and run.",
            )
        return tool

    def preflight(self, step):
        selected = self.task_tools(step) if step.agent_task else (self.resolve(step),)
        from .workflow_async_operations import validate_operation_profile

        for tool in selected:
            if tool.upstream_meta.get("wright/operation"):
                validate_operation_profile(
                    self, step, tool.upstream_meta["wright/operation"]
                )
        if step.agent_task:
            self.task_instruction_contract(step, selected)
            return
        tool = selected[0]
        if step.output_format not in {"json", "text"}:
            raise _invalid(f"{step.title}: save MCP results as JSON or text.")
        if not step.arguments_from:
            required = set(tool.input_schema.get("required", []))
            supplied = set(step.arguments) | set(step.argument_sources)
            missing = required - supplied
            if missing:
                raise _invalid(
                    f"{step.title}: provide {', '.join(sorted(missing))}.",
                    "Enter the missing tool inputs or connect an upstream response.",
                )
            # Validate known values now; connected values are checked again before invocation.
            schema = dict(tool.input_schema)
            schema["required"] = [
                key for key in required if key not in step.argument_sources
            ]
            known = {
                key: value
                for key, value in step.arguments.items()
                if key not in step.argument_sources
            }
            self.validate(step, known, schema)

    def task_instruction_contract(self, step, tools):
        """Qualify saved action declarations before any model/provider request."""
        instruction_set = embedded_instruction_set(
            getattr(step, "instruction_set", None)
        )
        try:
            resolved = resolve_workflow_instructions(
                "mcp-task",
                instruction_set=instruction_set,
                instruction_override=getattr(step, "instruction_override", None),
                variables={
                    "output_format": step.output_format,
                    "max_tool_calls": str(step.max_tool_calls),
                    "task_guidance": step.task_guidance,
                },
            )
            action_instructions = workflow_action_intent_instructions(instruction_set)
            if (
                getattr(step, "mcp_completion_policy", "tool_evidence_required")
                == "supplied_inputs_or_tools"
            ):
                if getattr(step, "instruction_set", None) is None:
                    raise ValueError(
                        "Supplied-input completion requires saved instruction assets"
                    )
                supplemental = validate_workflow_helper_instructions(
                    instruction_set, "context.mcp-input-completion"
                )
                text = resolved.text + "\n\n" + supplemental.render({})
                resolved = type(resolved).model_validate(
                    {
                        **resolved.model_dump(),
                        "text": text,
                        "text_digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        "asset_ids": (
                            *resolved.asset_ids,
                            "context.mcp-input-completion",
                        ),
                        "origins": (*resolved.origins, supplemental.origin),
                    }
                )
        except ValueError as error:
            raise _invalid(
                f"{step.title}: saved task instructions are invalid: {error}"
            ) from None
        considered = [
            t
            for t in tools
            if not step.design_check or t.annotations.get("readOnlyHint") is True
        ]
        if getattr(
            step, "mcp_completion_policy", "tool_evidence_required"
        ) == "supplied_inputs_or_tools" and any(
            tool.annotations.get("readOnlyHint") is not True for tool in considered
        ):
            raise _invalid(
                f"{step.title}: supplied-input completion requires explicitly read-only tools.",
                "Select only tools with readOnlyHint=true, or keep mandatory tool evidence.",
            )
        if action_instructions:
            for tool in considered:
                model_action_schema(tool)
        if (
            resolved.assumption_policy == "require_specified"
            and action_instructions is None
            and any(t.annotations.get("readOnlyHint") is not True for t in considered)
        ):
            raise _error(
                "WORKFLOW_ACTION_INTENT_UPGRADE_REQUIRED",
                f"{step.title}: strict instructions lack the saved action-intent contract for potentially changing tools.",
                "Explicitly upgrade and save the workflow instructions to the action-intent profile, or restrict this step to known read-only tools.",
            )
        return instruction_set, resolved, action_instructions

    def preflight_authority(self, step):
        """Check known call gates after exact run authority has been resolved.

        This does not grant permission. Dispatch still rechecks current grants
        and any enrolled document write's exact arguments/source/output target.
        Declared human action steps are qualified by their separate review owner.
        """
        tools = self.task_tools(step) if step.agent_task else (self.resolve(step),)
        from .workspace_document_artifacts import WORKSPACE_WRITE_APPROVAL

        for tool in tools:
            approvals = set(
                self.gateway.workspace_approvals_for_model_call(
                    self.session_id, tool.name
                )
            )
            authority = self._integration_document_write_authority
            if (
                tool.name == WORKSPACE_DOCUMENT_TOOL_NAME
                and authority is not None
                and authority.context.get("approval_mode") == "auto"
                and {
                    "server_id": tool.server_id,
                    "name": tool.name,
                    "schema_digest": schema_digest(tool),
                }
                in authority.context["allowed_tools"]
            ):
                approvals.add(WORKSPACE_WRITE_APPROVAL)
            if tool.required_approvals - approvals:
                raise _error(
                    "WORKFLOW_TOOL_APPROVAL_REQUIRED",
                    f"{step.title}: the selected tool needs workspace authorization before this process can run.",
                    "Configure the required reviewed operation or choose an authorized provider before starting.",
                )

    def validate(self, step, arguments, schema):
        if not isinstance(arguments, dict):
            raise _invalid(f"{step.title}: tool arguments must be a JSON object.")
        errors = sorted(
            Draft202012Validator(schema).iter_errors(arguments),
            key=lambda e: str(e.path),
        )
        if errors:
            error = errors[0]
            field = ".".join(str(part) for part in error.absolute_path) or "arguments"
            # Do not echo unbounded values, credentials, or upstream exception strings.
            raise _invalid(
                f"{step.title}: {field} does not match the tool's {error.validator} requirement.",
                "Correct this input or the upstream AI's JSON response, then run again.",
            )
        # Agent tasks can correct invalid arguments within their existing budget
        # before any mutation. Rejecting only inside the writer would instead
        # terminate the task as a failed mutation, after consuming that call.
        if (
            step.tool_name == WORKSPACE_DOCUMENT_TOOL_NAME
            and isinstance(arguments.get("relativePath"), str)
            and arguments["relativePath"].lower().endswith(".py")
            and isinstance(arguments.get("content"), str)
        ):
            try:
                validate_python_source(arguments["content"])
            except WorkspaceDocumentArtifactError as error:
                raise _invalid(
                    f"{step.title}: {error}",
                    "Correct the Python content and submit it again within the existing task budget.",
                ) from error

    def preflight_values(self, step, responses):
        """Check available root values without demanding future upstream outputs."""
        if step.agent_task:
            self.task_instruction_contract(step, self.task_tools(step))
            return
        self.preflight(step)
        tool = self.resolve(step)
        if step.arguments_from:
            if step.arguments_from in responses:
                self.arguments(step, responses)
            return
        unknown = {
            name
            for name, source in step.argument_sources.items()
            if source not in responses
        }
        arguments = self._connected_arguments(step, responses, tool, partial=True)
        schema = dict(tool.input_schema)
        schema["required"] = [
            name for name in schema.get("required", []) if name not in unknown
        ]
        self.validate(step, arguments, schema)

    def _connected_arguments(self, step, responses, tool, *, partial=False):
        try:
            if step.arguments_from:
                value = responses[step.arguments_from]
                arguments = json.loads(value) if isinstance(value, str) else value
            else:
                arguments = {
                    name: value
                    for name, value in step.arguments.items()
                    if name not in step.argument_sources
                }
                properties = tool.input_schema.get("properties", {})
                for name, source in step.argument_sources.items():
                    if partial and source not in responses:
                        continue
                    value = responses[source]
                    schema = properties.get(name, {})
                    variants = [
                        schema,
                        *schema.get("anyOf", []),
                        *schema.get("oneOf", []),
                    ]
                    accepts_text = any(
                        v.get("type") == "string"
                        or "string"
                        in (v.get("type") if isinstance(v.get("type"), list) else [])
                        for v in variants
                    )
                    arguments[name] = (
                        json.loads(value)
                        if isinstance(value, str) and not accepts_text
                        else value
                    )
        except (ValueError, TypeError, KeyError):
            raise _invalid(
                f"{step.title}: the connected response is not valid JSON for this input.",
                "Set the upstream prompt to JSON and request the tool's required argument structure.",
            ) from None
        if not isinstance(arguments, dict):
            raise _invalid(f"{step.title}: tool arguments must be a JSON object.")
        return arguments

    def arguments(self, step, responses):
        tool = self.resolve(step)
        arguments = self._connected_arguments(step, responses, tool)
        self.validate(step, arguments, tool.input_schema)
        return arguments

    async def call(
        self,
        step,
        arguments,
        *,
        on_event=None,
        monitor=True,
        image_observations=None,
        before_dispatch=None,
        task_deadline=None,
    ):
        tool = self.resolve(step)
        request_id = uuid.uuid4().hex
        approvals = self.gateway.workspace_approvals_for_model_call(
            self.session_id, step.tool_name
        )
        exact_dispatch = None
        from .workspace_file_inspection import INSPECT_TOOL_NAME
        from .workspace_file_copy import COPY_TOOL_NAME

        if (
            tool.name == COPY_TOOL_NAME
            and self._integration_file_copy_authority is not None
        ):
            arguments = json.loads(
                json.dumps(arguments, ensure_ascii=False, allow_nan=False)
            )
            self.validate(step, arguments, tool.input_schema)
            if on_event is None:
                raise _invalid(
                    "Integration working copies require a durable run audit sink."
                )
            audit, exact_dispatch = await self._integration_file_copy_authority.prepare(
                step, tool, arguments, request_id=request_id
            )
            await on_event("integration_file_copy_authorized", **audit)
        from .workspace_document_artifacts import (
            WORKSPACE_DOCUMENT_TOOL_NAME,
            WORKSPACE_WRITE_APPROVAL,
        )

        if (
            tool.name == INSPECT_TOOL_NAME
            and self._integration_file_read_authority is not None
        ):
            arguments = json.loads(
                json.dumps(arguments, ensure_ascii=False, allow_nan=False)
            )
            self.validate(step, arguments, tool.input_schema)
            if on_event is None:
                raise _invalid(
                    "Integration file observations require a durable run audit sink."
                )
            audit, exact_dispatch = await self._integration_file_read_authority.prepare(
                step, tool, arguments, request_id=request_id
            )
            await on_event("integration_file_read_authorized", **audit)
        if (
            tool.name == WORKSPACE_DOCUMENT_TOOL_NAME
            and self._integration_document_write_authority is not None
        ):
            # Detach exact argument bytes from model-owned mutable dictionaries.
            arguments = json.loads(
                json.dumps(arguments, ensure_ascii=False, allow_nan=False)
            )
            self.validate(step, arguments, tool.input_schema)
            if on_event is None:
                raise _invalid(
                    "Integration document writes require a durable run audit sink."
                )
            (
                audit,
                exact_dispatch,
            ) = await self._integration_document_write_authority.prepare(
                step, tool, arguments, request_id=request_id
            )
            await on_event("integration_document_write_authorized", **audit)
            approvals = set(approvals) | {WORKSPACE_WRITE_APPROVAL}
        operation_profile = None
        operation_bindings = None
        if monitor and tool.upstream_meta.get("wright/operation"):
            from .workflow_async_operations import validate_operation_profile

            operation_profile = deepcopy(tool.upstream_meta["wright/operation"])
            operation_bindings = validate_operation_profile(
                self, step, operation_profile
            )
        if before_dispatch is not None:
            prior_dispatch = exact_dispatch

            def checked_dispatch(current_tool):
                before_dispatch(current_tool)
                if prior_dispatch is not None:
                    prior_dispatch(current_tool)

            exact_dispatch = checked_dispatch
        try:
            result = await self.gateway.call_tool(
                self.session_id,
                request_id,
                step.tool_name,
                arguments,
                workspace_approvals=approvals,
                **({"before_dispatch": exact_dispatch} if exact_dispatch else {}),
                # Honor the canonical operation budget for ordinary CAD/solver
                # tools too. Gateway's configured maximum and the enclosing
                # task deadline still bound this call.
                timeout=min(120, step.timeout_seconds)
                if step.cad
                else step.timeout_seconds,
            )
        except GatewayWorkspaceScopeError as error:
            # Only this locally constructed type carries trusted, static user
            # guidance. Generic gateway/child messages can contain private data.
            raise _error(
                "MCP_WORKSPACE_SCOPE_MISMATCH",
                f"{step.title}: {error.user_message}",
                error.recovery_action,
            ) from error
        except GatewayError as error:
            raise _error(
                "MCP_CALL_FAILED",
                f"{step.title}: MCP call failed ({error.code}).",
                "Check the server in Tool Registry and the step's inputs, then retry.",
            ) from error
        from .workflow_mcp_images import image_observation

        safe_content, image_parts, image_evidence, image_errors = image_observation(
            result.content
        )
        if image_observations is not None:
            image_observations.update(parts=image_parts, evidence=image_evidence)
        value = (
            result.structured_content
            if result.structured_content is not None
            else {"content": safe_content}
        )
        if on_event is not None:
            from core.process_validation import canonical_digest
            from .process_interfaces.errors import safe_diagnostic

            # Retain the provider's response before output verification or
            # interpretation can fail. A response is evidence, not completion.
            observed = {
                "structured_content": result.structured_content,
                "content": result.content,
                "is_error": result.is_error,
            }
            try:
                response_digest = canonical_digest(observed)
            except (ValueError, TypeError):
                response_digest = None
            await on_event(
                "tool_response_received",
                task_id=step.id,
                task_title=step.title,
                request_id=request_id,
                server=tool.server_id,
                tool=tool.name,
                schema_digest=schema_digest(tool),
                response_digest=response_digest,
                is_error=bool(result.is_error),
                diagnostic=safe_diagnostic(
                    {"structured_content": value, "content": safe_content}
                ),
            )
        if result.is_error:
            detail = ""
            if step.cad:
                # CAD validation errors are needed for a bounded correction.
                # Do not discard field names and suggested fixes, making the AI
                # guess repeatedly at a rejected recipe.
                messages = []

                def issues(value):
                    if isinstance(value, dict):
                        if isinstance(value.get("message"), str):
                            messages.append(
                                " ".join(
                                    str(value.get(k, ""))
                                    for k in (
                                        "code",
                                        "argument",
                                        "message",
                                        "suggestedFix",
                                    )
                                ).strip()
                            )
                        for key in ("result", "error", "issues"):
                            if key in value:
                                issues(value[key])
                    elif isinstance(value, list):
                        for item in value[:16]:
                            issues(item)

                issues(result.structured_content)
                if not messages:
                    messages = [
                        str(item.get("text", ""))
                        for item in result.content
                        if item.get("type") == "text"
                    ]
                detail = " " + " | ".join(dict.fromkeys(messages))[:4000]
            value = (
                result.structured_content
                if result.structured_content is not None
                else {"content": safe_content}
            )
            raise WorkflowMcpToolError(
                f"{step.title}: the MCP tool reported an error.{detail}",
                "Check the tool's inputs and its server log in Tool Registry, then retry.",
                value,
            )
        text = "\n".join(
            str(item.get("text", ""))
            for item in result.content
            if item.get("type") == "text"
        )
        if not text:
            text = json.dumps(value, ensure_ascii=False, default=dict)
        if image_evidence:
            text += "\nWright image observation metadata: " + json.dumps(image_evidence)
        if image_errors:
            raise WorkflowMcpToolError(
                f"{step.title}: image observation rejected ({', '.join(dict.fromkeys(image_errors))}).",
                "Request at most four PNG/JPEG images per result, each at most 4 MiB base64 and 4096 pixels per edge.",
                value,
            )
        if operation_profile is not None:
            from .workflow_async_operations import (
                delegated_observation_budget,
                monitor_operation,
            )

            async with delegated_observation_budget(operation_profile, task_deadline):
                return await monitor_operation(
                    self,
                    step,
                    value,
                    operation_profile,
                    on_event,
                    pinned_tools=operation_bindings,
                )
        return value, text

    def task_tools(self, step):
        allowed = set(step.task_tool_allowlist)
        tools = tuple(
            t
            for t in self.tools()
            if t.server_id == step.server_id and (not allowed or t.tool_name in allowed)
        )
        if not tools:
            raise _invalid(
                f"{step.title}: the selected server has no available tools.",
                "Enable and connect this server in the workspace Tool Registry.",
            )
        if allowed != {tool.tool_name for tool in tools} and allowed:
            raise _invalid(
                f"{step.title}: a required MCP task tool is unavailable.",
                "Enable the configured tools for this server in the workspace Tool Registry, then check readiness again.",
            )
        if len(tools) > 64:
            raise _invalid(
                f"{step.title}: this server exceeds the current 64-tool task limit."
            )
        return tools

    async def run_task(
        self, step, prompt, decide, emit, *, cad=None, images=None, captured_images=None
    ):
        """One isolated task, one server, bounded decisions, existing gateway calls."""
        from .workflow_source_execution import WorkflowSourceExecutionError

        instruction_set, resolved, action_instructions = self.task_instruction_contract(
            step, self.task_tools(step)
        )
        instruction_override = getattr(step, "instruction_override", None)
        await emit(
            "instructions_resolved",
            task_id=step.id,
            task_title=step.title,
            instructions=resolved.model_dump(mode="json"),
        )

        async def observe_invocation(invocation):
            await emit(
                "model_invocation",
                task_id=step.id,
                task_title=step.title,
                invocation=invocation,
            )

        decision_kwargs = workflow_decision_kwargs(
            decide, step, instruction_set, observe_invocation
        )
        # Accepted execution identities are request data, never editable policy.
        # A model must see the same exact output IDs enforced on its assumptions.
        request_context = {
            "schema_version": "wright.workflow-step-context/1",
            "step_id": step.id,
            "declared_outputs": [
                {"output_id": key, "kind": kind}
                for key, kind in getattr(step, "output_ports", ())
            ],
            "protected_requirement_identifiers": list(
                instruction_set.policy.protected_requirements
            ),
        }
        supplied_input_completion = (
            getattr(step, "mcp_completion_policy", "tool_evidence_required")
            == "supplied_inputs_or_tools"
        )
        if supplied_input_completion:
            request_context["completion_evidence_policy"] = "supplied_inputs_or_tools"
        input_digest = (
            canonical_digest({"prompt": prompt, "images": images or []})
            if supplied_input_completion
            else None
        )
        contextual_prompt = (
            prompt
            + "\n\n"
            + json.dumps({"wright_step_context": request_context}, ensure_ascii=False)
        )
        alias_names = {}
        messages = [
            {"role": "system", "content": resolved.text},
            *(
                [{"role": "system", "content": action_instructions}]
                if action_instructions
                else []
            ),
            {
                "role": "user",
                "content": (
                    [
                        {"type": "text", "text": contextual_prompt},
                        *[
                            {"type": "image_url", "image_url": {"url": url}}
                            for url in images
                        ],
                    ]
                    if images
                    else contextual_prompt
                ),
            },
        ]
        records, succeeded, rejected_recipes = [], set(), set()
        from .workflow_mcp_reconciliation import ReconciliationTracker

        reconciliation = ReconciliationTracker(
            getattr(step, "mcp_reconciliation_contracts", {})
        )
        action_assumptions = {}
        from .workflow_mcp_images import MAX_IMAGES_PER_TASK, MAX_TASK_IMAGE_BYTES

        image_count = len(images or [])
        image_bytes = sum(len(url) for url in images or [])

        async def execute():
            nonlocal image_count, image_bytes
            for index in range(step.max_tool_calls + 1):
                # Lazy discovery can replace a cached catalog after a call.
                # Present the current contracts on each decision, with stable
                # aliases so previous tool results remain understandable.
                selected = self.task_tools(step)
                if step.design_check:
                    selected = tuple(
                        t for t in selected if t.annotations.get("readOnlyHint") is True
                    )
                if cad:
                    selected = tuple(t for t in selected if cad.allows_tool(t))
                aliases = {}
                for tool in selected:
                    alias = alias_names.setdefault(
                        tool.name, f"tool_{len(alias_names)}"
                    )
                    aliases[alias] = tool
                schemas = [
                    {
                        "type": "function",
                        "function": {
                            "name": alias,
                            "description": f"{tool.title or tool.tool_name}: {tool.description}",
                            "parameters": model_action_schema(tool)
                            if action_instructions
                            else dict(tool.input_schema),
                        },
                    }
                    for alias, tool in aliases.items()
                ]
                await emit(
                    "task_progress",
                    task_id=step.id,
                    task_title=step.title,
                    message="Reviewing tool results"
                    if records
                    else "Planning the task",
                    tool_calls=len(records),
                    available_tools=[
                        {
                            "alias": alias,
                            "tool": tool.name,
                            "schema_digest": schema_digest(tool),
                            "provider_input_schema": dict(tool.input_schema),
                            "model_input_schema_digest": canonical_digest(
                                model_action_schema(tool)
                                if action_instructions
                                else dict(tool.input_schema)
                            ),
                            "action_intent_contract": instruction_set.action_intent_contract,
                        }
                        for alias, tool in aliases.items()
                    ],
                )
                prepared_invocation = invocation_evidence(
                    {"messages": messages, "tools": schemas},
                    operation="mcp-task",
                    instruction_set=instruction_set,
                    resolved=resolved,
                    attempt=index + 1,
                )
                prepared_invocation["capture_scope"] = "runtime_decision_input"
                if getattr(step, "mcp_context_budget_bytes", None) is not None:
                    prepared_invocation["context_budget_bytes"] = (
                        step.mcp_context_budget_bytes
                    )
                await emit(
                    "model_invocation",
                    task_id=step.id,
                    task_title=step.title,
                    invocation=prepared_invocation,
                )
                message = await decide(
                    messages, schemas, required=False, **decision_kwargs
                )
                if getattr(message, "wright_invocations", None):
                    await emit(
                        "model_invocation_result",
                        task_id=step.id,
                        task_title=step.title,
                        invocations=message.wright_invocations,
                    )
                decision_usage = getattr(message, "wright_usage", None)
                if isinstance(decision_usage, dict):
                    await emit(
                        "model_usage",
                        task_id=step.id,
                        task_title=step.title,
                        usage=decision_usage,
                    )
                calls = message.get("tool_calls", [])
                from .workflow_source_execution import require_unattended_completion

                # A mixed question/tool decision cannot dispatch its accompanying
                # operations. Only an explicit structured disposition is checked;
                # ordinary documents may legitimately contain questions.
                if calls and message.get("content"):
                    try:
                        disposition = json.loads(message["content"])
                    except (ValueError, TypeError):
                        disposition = None
                    if isinstance(disposition, dict):
                        await require_unattended_completion(step, disposition, emit)
                if not calls:
                    try:
                        outcome = json.loads(message.get("content", ""))
                        if (
                            not isinstance(outcome, dict)
                            or not isinstance(outcome.get("response"), str)
                            or not outcome["response"].strip()
                        ):
                            raise ValueError()
                    except (ValueError, TypeError):
                        raise _invalid(
                            f"{step.title}: the task returned no verifiable completion evidence."
                        ) from None
                    await require_unattended_completion(step, outcome, emit)
                    try:
                        assumptions = validate_workflow_assumptions(
                            outcome.get("assumptions", []), resolved.assumption_policy
                        )
                        if action_instructions:
                            validate_workflow_action_intent(
                                {
                                    "schema_version": instruction_set.action_intent_contract,
                                    "arguments": {},
                                    "assumptions": assumptions,
                                    "unresolved_required_information": [],
                                },
                                assumption_policy=resolved.assumption_policy,
                                protected_requirements=instruction_set.policy.protected_requirements,
                                output_ids=[
                                    key for key, _ in getattr(step, "output_ports", ())
                                ],
                            )
                        assumptions = list(
                            merged_task_assumptions(
                                action_assumptions, assumptions
                            ).values()
                        )
                    except ValueError:
                        raise _error(
                            "WORKFLOW_ASSUMPTION_INVALID",
                            f"{step.title}: invalid declared assumptions.",
                            "Inspect the declared choices and accepted output/requirement identities before starting a new run.",
                        ) from None
                    evidence = outcome.get("evidence")
                    from_supplied_inputs = (
                        supplied_input_completion
                        and not records
                        and evidence == []
                        and outcome.get("completion_basis") == "supplied_inputs"
                    )
                    if (
                        outcome.get("status") != "completed"
                        or not isinstance(evidence, list)
                        or (not evidence and not from_supplied_inputs)
                        or (
                            outcome.get("completion_basis") == "supplied_inputs"
                            and not from_supplied_inputs
                        )
                        or any(
                            type(number) is not int
                            or not 1 <= number <= len(records)
                            or records[number - 1]["status"] != "succeeded"
                            for number in evidence
                        )
                    ):
                        raise _invalid(
                            f"{step.title}: the task returned no valid execution evidence."
                        )
                    from .workflow_source_execution import validate_response

                    try:
                        response = validate_response(
                            outcome["response"], step.output_format
                        )
                    except WorkflowSourceExecutionError:
                        # A formatting mistake after successful engineering
                        # calls does not justify replaying those operations.
                        # One tool-free correction stays inside this task's
                        # existing deadline and preserves its evidence claims.
                        await emit(
                            "task_response_format_repair",
                            task_id=step.id,
                            task_title=step.title,
                            output_format=step.output_format,
                            evidence=evidence,
                            original_response=outcome["response"],
                        )
                        repair = {}
                        repair_usage_recorded = False
                        repair_started = time.perf_counter()
                        failure_reason = "model_request_failed"
                        try:
                            repair_messages = response_format_repair_messages(
                                outcome,
                                step.output_format,
                                instruction_set=instruction_set,
                                instruction_override=instruction_override,
                            )
                            repair_instructions = resolve_workflow_instructions(
                                "recovery",
                                instruction_set=instruction_set,
                                instruction_override=instruction_override,
                                variables={"output_format": step.output_format},
                            )
                            await emit(
                                "model_invocation",
                                task_id=step.id,
                                task_title=step.title,
                                invocation=invocation_evidence(
                                    {"messages": repair_messages, "tools": []},
                                    operation="mcp-format-repair",
                                    instruction_set=instruction_set,
                                    resolved=repair_instructions,
                                ),
                            )
                            repair = await decide(
                                repair_messages,
                                [],
                                required=False,
                                **decision_kwargs,
                            )
                            if getattr(repair, "wright_invocations", None):
                                await emit(
                                    "model_invocation_result",
                                    task_id=step.id,
                                    task_title=step.title,
                                    invocations=repair.wright_invocations,
                                )
                            repair_usage = getattr(repair, "wright_usage", None)
                            if not isinstance(repair_usage, dict):
                                repair_usage = {
                                    "status": "unknown",
                                    "model": None,
                                    "input_tokens": None,
                                    "cached_input_tokens": None,
                                    "output_tokens": None,
                                    "reasoning_output_tokens": None,
                                    "total_tokens": None,
                                    "duration_ms": round(
                                        (time.perf_counter() - repair_started) * 1000
                                    ),
                                }
                            await emit(
                                "model_usage",
                                task_id=step.id,
                                task_title=step.title,
                                usage=repair_usage,
                            )
                            repair_usage_recorded = True
                            failure_reason = "invalid_completion_envelope"
                            corrected = json.loads(repair.get("content", ""))
                            if repair.get("tool_calls"):
                                failure_reason = "tool_call_requested"
                                raise ValueError()
                            if not isinstance(corrected, dict):
                                raise ValueError()
                            # A formatting repair has no authority to ask for
                            # input or change the engineering disposition.
                            if corrected.get("reason") == "input_required":
                                await require_unattended_completion(
                                    step, corrected, emit
                                )
                            failure_reason = "execution_evidence_changed"
                            if (
                                corrected.get("status") != outcome["status"]
                                or corrected.get("evidence") != evidence
                                or any(
                                    type(number) is not int
                                    for number in corrected["evidence"]
                                )
                            ):
                                raise ValueError()
                            failure_reason = "invalid_response_format"
                            response = validate_response(
                                corrected.get("response"), step.output_format
                            )
                        except (
                            ValueError,
                            TypeError,
                            WorkflowSourceExecutionError,
                        ) as error:
                            if (
                                isinstance(error, WorkflowSourceExecutionError)
                                and error.code == "INTERACTION_NOT_DECLARED"
                            ):
                                raise
                            content = (
                                repair.get("content", "")
                                if isinstance(repair, dict)
                                else ""
                            )
                            if not repair_usage_recorded:
                                await emit(
                                    "model_usage",
                                    task_id=step.id,
                                    task_title=step.title,
                                    usage={
                                        "status": "unknown",
                                        "model": None,
                                        "input_tokens": None,
                                        "cached_input_tokens": None,
                                        "output_tokens": None,
                                        "reasoning_output_tokens": None,
                                        "total_tokens": None,
                                        "duration_ms": round(
                                            (time.perf_counter() - repair_started)
                                            * 1000
                                        ),
                                    },
                                )
                            content = content if isinstance(content, str) else ""
                            await emit(
                                "task_response_format_repair_failed",
                                task_id=step.id,
                                task_title=step.title,
                                output_format=step.output_format,
                                evidence=evidence,
                                reason=failure_reason,
                                correction_sha256=hashlib.sha256(
                                    content.encode()
                                ).hexdigest(),
                                correction_preview=content[:2048],
                                correction_truncated=len(content) > 2048,
                            )
                            raise _invalid(
                                f"{step.title}: final response formatting could not be corrected without changing execution evidence."
                            ) from None
                    if assumptions:
                        await emit(
                            "assumptions_recorded",
                            task_id=step.id,
                            task_title=step.title,
                            assumptions=assumptions,
                        )
                    if supplied_input_completion:
                        await emit(
                            "task_completion_evidence",
                            task_id=step.id,
                            task_title=step.title,
                            completion_policy=step.mcp_completion_policy,
                            basis="supplied_inputs"
                            if from_supplied_inputs
                            else "tool_calls",
                            tool_call_numbers=evidence,
                            input_digest=input_digest,
                            capture_scope="runtime_task_input",
                        )
                    return response, records
                if index == step.max_tool_calls:
                    raise _error(
                        "TASK_LIMIT_REACHED",
                        f"{step.title}: the tool-call limit was reached.",
                        "Inspect completed operations before increasing the limit or retrying.",
                    )
                if (
                    len(calls) != 1
                    or calls[0].get("function", {}).get("name") not in aliases
                ):
                    raise _invalid(
                        f"{step.title}: the model requested a tool outside this task."
                    )
                call = calls[0]
                tool = aliases[call["function"]["name"]]
                invocation = replace(
                    step,
                    tool_name=tool.name,
                    schema_digest=schema_digest(tool),
                    agent_task=False,
                )
                # Re-resolve on every call: removal or authority/schema change stops the run.
                current_tool = self.resolve(invocation)
                if (
                    supplied_input_completion
                    and current_tool.annotations.get("readOnlyHint") is not True
                ):
                    raise _invalid(
                        "Read-only research cannot dispatch a changing or unclassified tool."
                    )
                if (
                    step.design_check
                    and current_tool.annotations.get("readOnlyHint") is not True
                ):
                    raise _invalid(
                        "The design check cannot use a tool that changes the model."
                    )
                try:

                    def reject_nonfinite(value):
                        raise ValueError("nonfinite_argument")

                    arguments = json.loads(
                        call["function"]["arguments"], parse_constant=reject_nonfinite
                    )
                except (ValueError, KeyError, TypeError):
                    raise _invalid(
                        f"{step.title}: the model returned invalid tool arguments."
                    ) from None
                proposed_assumptions = []
                if action_instructions:
                    try:
                        intent = validate_workflow_action_intent(
                            arguments,
                            assumption_policy=resolved.assumption_policy,
                            protected_requirements=instruction_set.policy.protected_requirements,
                            output_ids=[
                                key for key, _ in getattr(step, "output_ports", ())
                            ],
                        )
                        proposed_assumptions = [
                            a.model_dump(mode="json") for a in intent.assumptions
                        ]
                        proposed_accumulated = merged_task_assumptions(
                            action_assumptions, proposed_assumptions
                        )
                    except ValueError as error:
                        from .process_interfaces.errors import safe_diagnostic

                        # Never expose Pydantic's raw value-bearing exception string.
                        reason = (
                            str(error)
                            if type(error) is ValueError
                            else "invalid_action_intent_envelope"
                        )
                        await emit(
                            "action_intent_rejected",
                            task_id=step.id,
                            task_title=step.title,
                            tool=current_tool.name,
                            schema_digest=schema_digest(current_tool),
                            proposal_digest=canonical_digest(arguments),
                            reason=reason,
                            diagnostic=safe_diagnostic(arguments),
                        )
                        raise _error(
                            "WORKFLOW_ACTION_INTENT_INVALID",
                            f"{step.title}: the proposed tool action failed its declared information/assumption contract ({reason}).",
                            "Review the recorded proposal and supply required information or explicitly revise permitted assumptions before starting a new run.",
                        ) from None
                    await emit(
                        "action_intent_validated",
                        task_id=step.id,
                        task_title=step.title,
                        tool=current_tool.name,
                        schema_digest=schema_digest(current_tool),
                        proposal_digest=canonical_digest(arguments),
                        action_intent_contract=intent.schema_version,
                        assumptions=proposed_assumptions,
                        declared_outputs=[
                            key for key, _ in getattr(step, "output_ports", ())
                        ],
                        protected_requirement_identifiers=list(
                            instruction_set.policy.protected_requirements
                        ),
                    )
                    arguments = intent.arguments
                if cad:
                    arguments = cad.guard(tool, arguments)
                signature = tool.name + json.dumps(arguments, sort_keys=True)
                if signature in rejected_recipes:
                    raise _invalid(
                        f"{step.title}: the same rejected recipe was requested again.",
                        "Correct the conflicting parameter names and their references before retrying.",
                    )
                repeat_allowed = (
                    reconciliation.permit_repeat(signature, current_tool.tool_name)
                    if signature in succeeded
                    and current_tool.tool_name in reconciliation.contracts
                    else repeatable_call(current_tool, arguments)
                )
                if signature in succeeded and not repeat_allowed:
                    raise _invalid(
                        f"{step.title}: a completed operation ({tool.title or tool.tool_name}) was requested again.",
                        "Inspect the task log and clarify the remaining work before retrying.",
                    )
                await emit(
                    "tool_started",
                    task_id=step.id,
                    task_title=step.title,
                    tool=tool.title or tool.tool_name,
                    arguments=arguments,
                    tool_calls=index + 1,
                )
                terminal_error = None
                observation = {}
                try:
                    self.validate(invocation, arguments, tool.input_schema)
                    if cad:
                        await cad.validate_creation(tool, arguments)
                except WorkflowSourceExecutionError as error:
                    # No external operation has occurred; allow a bounded correction.
                    value, text, status = (
                        getattr(error, "tool_result", {}),
                        str(error),
                        "invalid_arguments",
                    )
                else:
                    try:
                        value, text = await self.call(
                            invocation,
                            arguments,
                            on_event=emit,
                            image_observations=observation,
                            task_deadline=task_deadline,
                        )
                        succeeded.add(signature)
                        receipt = reconciliation.observe(
                            signature, current_tool.tool_name, arguments, value
                        )
                        if receipt is not None:
                            await emit(
                                "operation_reconciled",
                                task_id=step.id,
                                tool=current_tool.name,
                                request_signature_digest=canonical_digest(signature),
                                **receipt,
                            )
                        if action_instructions:
                            action_assumptions.clear()
                            action_assumptions.update(proposed_accumulated)
                        if proposed_assumptions:
                            # Preserve choices for successful operations even if
                            # a later decision fails before task completion.
                            await emit(
                                "assumptions_recorded",
                                task_id=step.id,
                                task_title=step.title,
                                assumptions=list(action_assumptions.values()),
                            )
                        if cad:
                            cad.observe(tool, value)
                        status = "succeeded"
                    except WorkflowSourceExecutionError as error:
                        value, text, status = (
                            getattr(error, "tool_result", {}),
                            str(error),
                            "failed",
                        )
                        if cad and safe_recipe_parameter_correction(
                            current_tool, value
                        ):
                            # The native server proved that its temporary document
                            # was closed and no recipe/output mutation remains.
                            # Permit a new decision, never replay these arguments.
                            rejected_recipes.add(signature)
                            status = "invalid_arguments"
                        elif not current_tool.annotations.get("readOnlyHint", False):
                            terminal_error = error
                terminal_receipt = (
                    terminal_operation_receipt(current_tool, arguments, value)
                    if status == "succeeded"
                    else None
                )
                record = {
                    "tool": tool.name,
                    "arguments": arguments,
                    "status": status,
                    "result": value,
                    "text": text,
                    "schema_digest": schema_digest(tool),
                }
                if isinstance(decision_usage, dict):
                    record["model_usage"] = decision_usage
                if terminal_receipt is not None:
                    record["terminal_receipt"] = terminal_receipt
                if observation.get("evidence"):
                    record["image_observations"] = observation["evidence"]
                records.append(record)
                if (
                    captured_images is not None
                    and status == "succeeded"
                    and observation.get("parts")
                ):
                    captured_images.append(
                        {
                            "tool": tool.name,
                            "tool_name": tool.tool_name,
                            "arguments": arguments,
                            "tool_call_number": len(records),
                            "parts": observation["parts"],
                            "evidence": observation["evidence"],
                        }
                    )
                if cad:
                    cad.records.append(record)
                await emit(
                    "tool_completed", task_id=step.id, task_title=step.title, **record
                )
                # A failed mutation still stops immediately. Keep its complete
                # report (including partial files and cleanup warnings) before
                # raising; it is evidence, never successful execution.
                if terminal_error is not None:
                    raise terminal_error
                if terminal_receipt is not None:
                    from .workflow_source_execution import validate_response

                    response = validate_response(
                        terminal_operation_response(
                            current_tool,
                            index + 1,
                            terminal_receipt,
                            step.output_format,
                        ),
                        step.output_format,
                    )
                    await emit(
                        "task_terminal_operation",
                        task_id=step.id,
                        task_title=step.title,
                        tool=current_tool.name,
                        tool_call_number=index + 1,
                        receipt=terminal_receipt,
                    )
                    return response, records
                result = json.dumps(
                    {
                        "tool_call_number": index + 1,
                        "status": status,
                        "result": value,
                        "text": text,
                    },
                    ensure_ascii=False,
                    default=dict,
                )
                if len(result.encode()) > max(
                    262_144, getattr(step, "mcp_context_budget_bytes", None) or 0
                ):
                    raise _invalid(
                        f"{step.title}: the tool result exceeds the task context limit.",
                        "Request a smaller result.",
                    )
                image_parts = (
                    observation.get("parts", []) if status == "succeeded" else []
                )
                image_count += len(image_parts)
                image_bytes += sum(
                    len(part["image_url"]["url"]) for part in image_parts
                )
                if (
                    image_count > MAX_IMAGES_PER_TASK
                    or image_bytes > MAX_TASK_IMAGE_BYTES
                ):
                    raise _invalid(
                        f"{step.title}: image observations exceed the task context limit.",
                        "Split the visual inspection into tasks with at most eight images and 8 MiB of image data.",
                    )
                content = (
                    [{"type": "text", "text": result}, *image_parts]
                    if image_parts
                    else result
                )
                messages.extend(
                    [
                        message,
                        {
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "content": content,
                        },
                    ]
                )
            raise AssertionError("bounded task must return or fail")

        try:
            async with asyncio.timeout(step.timeout_seconds) as task_deadline:
                return await execute()
        except TimeoutError as error:
            raise _error(
                "TASK_TIMEOUT",
                f"{step.title}: the task exceeded its time limit.",
                "Inspect the tool log and current files before retrying; completed operations remain.",
            ) from error
