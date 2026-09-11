"""Workspace-bound native workflow calls through Wright's existing MCP gateway."""
from __future__ import annotations

import hashlib
import asyncio
import json
import uuid
from dataclasses import replace
from jsonschema import Draft202012Validator
from tool_registry.gateway_service import SUPPORTED_PROTOCOL_VERSION
from tool_registry.gateway_models import GatewayError, GatewayWorkspaceScopeError
from .workflow_source_execution import _invalid, _error, WorkflowSourceExecutionError


class WorkflowMcpToolError(WorkflowSourceExecutionError):
    """A failed tool response retained for the run's evidence record."""

    def __init__(self, message, correction, result):
        super().__init__('MCP_CALL_FAILED', message, correction)
        self.tool_result = result


def schema_digest(tool):
    material = {"server": tool.server_id, "name": tool.name, "input": dict(tool.input_schema),
                "output": tool.output_schema, "authority": tool.provenance.get("server_revision"),
                "approvals": sorted(tool.required_approvals)}
    if tool.upstream_meta.get('wright/operation'):
        material['operation_adapter']=tool.upstream_meta['wright/operation']
    if tool.upstream_meta.get('wright/application'):
        material['application_adapter']=tool.upstream_meta['wright/application']
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), default=dict).encode()).hexdigest()


def repeatable_call(tool, arguments):
    if tool.annotations.get('readOnlyHint') is True or tool.annotations.get('idempotentHint') is True:
        return True
    # Microsoft's browser MCP labels navigation as an action because it changes
    # the selected page. Revisiting a page is normal task navigation, not replay
    # of a completed document mutation. Keep clicks, uploads and scripts guarded.
    source = tool.provenance.get('source_url', '').rstrip('/')
    if source != 'https://github.com/microsoft/playwright-mcp':
        return False
    return tool.tool_name in {'browser_navigate', 'browser_navigate_back'} or (
        tool.tool_name == 'browser_tabs' and arguments.get('action') in {'list', 'select'})


def safe_recipe_parameter_correction(tool, result):
    """Recognize only the native preflight contract that proves clean rejection."""
    if tool.tool_name != 'cad.create_sheet_metal_from_recipe' or not isinstance(result, dict):
        return False
    code = 'solid_edge_recipe_variable_name_conflict'
    stage = 'preflight_before_recipe_mutation_cleanup_confirmed'
    error = result.get('error')
    issues = result.get('issues')
    if not isinstance(error, dict) or not isinstance(issues, list) or len(issues) != 1:
        return False
    issue = issues[0]
    return (
        result.get('providerId') == 'solid_edge'
        and result.get('operationStatus') == 'failed'
        and result.get('isSuccess') is False and result.get('isSaved') is False
        and 'document' in result and result['document'] is None
        and 'outputPath' in result and result['outputPath'] is None
        and result.get('createdReferences') == [] and result.get('warnings') == []
        and isinstance(issue, dict)
        and all(item.get('code') == code and item.get('stage') == stage
                and item.get('retryable') is False and item.get('argument') == 'parameters'
                for item in (error, issue))
    )


class WorkflowMcpRuntime:
    def __init__(self, gateway, *, workspace_id, session_id):
        self.gateway = gateway
        self.session_id = "native-workflow-" + uuid.uuid4().hex
        gateway.open_session(session_id=self.session_id, principal_id="wright-native-workflow",
            workspace_id=workspace_id, binding_session_id=session_id, transport="streamable_http")
        gateway.initialize_session(self.session_id, protocol_version=SUPPORTED_PROTOCOL_VERSION,
            client_name="wright-native-workflow", client_version="1", client_capabilities={})

    async def close(self):
        await self.gateway.close_session(self.session_id)

    def tools(self):
        # Native blocks use actual catalog MCP tools, not legacy workflow/management commands.
        return tuple(t for t in self.gateway.list_tools(self.session_id) if t.server_id not in {"wright", "rivet-workflows"})

    def available(self):
        return [{"name": t.name, "server_id": t.server_id, "tool_name": t.tool_name,
                 "title": t.title or t.tool_name.replace("_", " "), "description": t.description,
                 "input_schema": dict(t.input_schema), "output_schema": t.output_schema,
                 "schema_digest": schema_digest(t)} for t in self.tools()]

    def resolve(self, step):
        tool = next((t for t in self.tools() if t.name == step.tool_name and t.server_id == step.server_id), None)
        if tool is None:
            raise _invalid(f"{step.title}: the selected MCP tool is unavailable.", "Enable its server for this workspace in Tool Registry, then select the tool again.")
        if schema_digest(tool) != step.schema_digest:
            raise _invalid(f"{step.title}: the MCP tool definition has changed.", "Select the tool again to review its current inputs, then save and run.")
        return tool

    def preflight(self, step):
        if step.agent_task:
            self.task_tools(step)
            return
        tool = self.resolve(step)
        if step.output_format not in {"json", "text"}:
            raise _invalid(f"{step.title}: save MCP results as JSON or text.")
        if not step.arguments_from:
            required = set(tool.input_schema.get("required", []))
            supplied = set(step.arguments) | set(step.argument_sources)
            missing = required - supplied
            if missing:
                raise _invalid(f"{step.title}: provide {', '.join(sorted(missing))}.", "Enter the missing tool inputs or connect an upstream response.")
            # Validate known values now; connected values are checked again before invocation.
            schema = dict(tool.input_schema)
            schema['required'] = [key for key in required if key not in step.argument_sources]
            known = {key: value for key, value in step.arguments.items() if key not in step.argument_sources}
            self.validate(step, known, schema)

    def validate(self, step, arguments, schema):
        if not isinstance(arguments, dict):
            raise _invalid(f"{step.title}: tool arguments must be a JSON object.")
        errors = sorted(Draft202012Validator(schema).iter_errors(arguments), key=lambda e: str(e.path))
        if errors:
            error = errors[0]
            field = '.'.join(str(part) for part in error.absolute_path) or 'arguments'
            # Do not echo unbounded values, credentials, or upstream exception strings.
            raise _invalid(f"{step.title}: {field} does not match the tool's {error.validator} requirement.", "Correct this input or the upstream AI's JSON response, then run again.")

    def arguments(self, step, responses):
        tool = self.resolve(step)
        try:
            if step.arguments_from:
                arguments = json.loads(responses[step.arguments_from])
            else:
                arguments = dict(step.arguments)
                properties = tool.input_schema.get('properties', {})
                for name, source in step.argument_sources.items():
                    value = responses[source]
                    schema = properties.get(name, {})
                    variants = [schema, *schema.get('anyOf', []), *schema.get('oneOf', [])]
                    accepts_text = any(v.get('type') == 'string' or 'string' in (v.get('type') if isinstance(v.get('type'), list) else []) for v in variants)
                    arguments[name] = value if accepts_text else json.loads(value)
        except (ValueError, TypeError, KeyError):
            raise _invalid(f"{step.title}: the connected response is not valid JSON for this input.", "Set the upstream prompt to JSON and request the tool's required argument structure.") from None
        if not isinstance(arguments, dict):
            raise _invalid(f"{step.title}: tool arguments must be a JSON object.")
        self.validate(step, arguments, tool.input_schema)
        return arguments

    async def call(self, step, arguments, *, on_event=None, monitor=True):
        tool=self.resolve(step)
        if monitor and tool.upstream_meta.get('wright/operation'):
            from .workflow_async_operations import validate_operation_profile
            validate_operation_profile(self,step,tool.upstream_meta['wright/operation'])
        try:
            result = await self.gateway.call_tool(self.session_id, uuid.uuid4().hex, step.tool_name, arguments,
                workspace_approvals=self.gateway.workspace_approvals_for_model_call(self.session_id, step.tool_name),
                **({'timeout': min(120, step.timeout_seconds)} if step.cad else {}))
        except GatewayWorkspaceScopeError as error:
            # Only this locally constructed type carries trusted, static user
            # guidance. Generic gateway/child messages can contain private data.
            raise _error('MCP_WORKSPACE_SCOPE_MISMATCH',
                         f"{step.title}: {error.user_message}",
                         error.recovery_action) from error
        except GatewayError as error:
            raise _error('MCP_CALL_FAILED', f"{step.title}: MCP call failed ({error.code}).",
                         "Check the server in Tool Registry and the step's inputs, then retry.") from error
        if result.is_error:
            detail = ''
            if step.cad:
                # CAD validation errors are needed for a bounded correction.
                # Do not discard field names and suggested fixes, making the AI
                # guess repeatedly at a rejected recipe.
                messages = []
                def issues(value):
                    if isinstance(value, dict):
                        if isinstance(value.get('message'), str):
                            messages.append(' '.join(str(value.get(k, '')) for k in ('code', 'argument', 'message', 'suggestedFix')).strip())
                        for key in ('result', 'error', 'issues'):
                            if key in value:
                                issues(value[key])
                    elif isinstance(value, list):
                        for item in value[:16]:
                            issues(item)
                issues(result.structured_content)
                if not messages:
                    messages = [str(item.get('text', '')) for item in result.content if item.get('type') == 'text']
                detail = ' ' + ' | '.join(dict.fromkeys(messages))[:4000]
            value = result.structured_content if result.structured_content is not None else {'content': list(result.content)}
            raise WorkflowMcpToolError(f"{step.title}: the MCP tool reported an error.{detail}",
                         "Check the tool's inputs and its server log in Tool Registry, then retry.", value)
        text = '\n'.join(str(item.get('text', '')) for item in result.content if item.get('type') == 'text')
        value = result.structured_content if result.structured_content is not None else {'content': list(result.content)}
        if not text:
            text = json.dumps(value, ensure_ascii=False, default=dict)
        if monitor and tool.upstream_meta.get('wright/operation'):
            from .workflow_async_operations import monitor_operation
            return await monitor_operation(self,step,value,tool.upstream_meta['wright/operation'],on_event)
        return value, text

    def task_tools(self, step):
        tools = tuple(t for t in self.tools() if t.server_id == step.server_id)
        if not tools:
            raise _invalid(f"{step.title}: the selected server has no available tools.",
                           "Enable and connect this server in the workspace Tool Registry.")
        if len(tools) > 64:
            raise _invalid(f"{step.title}: this server exceeds the current 64-tool task limit.")
        return tools

    async def run_task(self, step, prompt, decide, emit, *, cad=None, images=None):
        """One isolated task, one server, bounded decisions, existing gateway calls."""
        from .workflow_source_execution import WorkflowSourceExecutionError
        alias_names = {}
        messages = [{"role": "system", "content": (
            "Complete the task using only the provided tools. Inspect their results before choosing "
            "another operation. Do not invent missing engineering requirements. The available tool "
            "contracts are refreshed for each decision. Before reporting "
            "that an inspection capability is unavailable, examine these contracts and use the relevant "
            "read-only inspection tool when one is provided. A creation response that omits measurements "
            "does not mean the separate measurement tools are unavailable. Do not repeat creation to "
            "obtain measurements of an existing result. Do not claim unperformed "
            "operations. Do not create files unless explicitly requested; Wright saves your final response. "
            "When finished, return a message whose content is a JSON object with status "
            "('completed' or 'blocked'), response (string), and evidence (array of successful tool-call "
            "numbers supporting the result). If requirements are missing or the task cannot be completed, "
            "return blocked and explain what must change; do not invent an answer or perform unrelated calls. "
            f"Inside that envelope, format response as {step.output_format}. For HTML use a complete standalone "
            "HTML document; for JSON use valid JSON text, without code fences. "
            f"You may use at most {step.max_tool_calls} tool calls.\nAdditional task guidance:\n{step.task_guidance}"
        )}, {"role": "user", "content": ([{"type": "text", "text": prompt},
            *[{"type": "image_url", "image_url": {"url": url}} for url in images]] if images else prompt)}]
        records, succeeded, rejected_recipes = [], set(), set()
        async def execute():
            for index in range(step.max_tool_calls + 1):
                # Lazy discovery can replace a cached catalog after a call.
                # Present the current contracts on each decision, with stable
                # aliases so previous tool results remain understandable.
                selected = self.task_tools(step)
                if step.design_check:
                    selected = tuple(t for t in selected if t.annotations.get('readOnlyHint') is True)
                if cad:
                    selected = tuple(t for t in selected if cad.allows_tool(t))
                aliases = {}
                for tool in selected:
                    alias = alias_names.setdefault(tool.name, f"tool_{len(alias_names)}")
                    aliases[alias] = tool
                schemas = [{"type": "function", "function": {"name": alias,
                    "description": f"{tool.title or tool.tool_name}: {tool.description}",
                    "parameters": dict(tool.input_schema)}} for alias, tool in aliases.items()]
                await emit("task_progress", task_id=step.id, task_title=step.title,
                           message="Reviewing tool results" if records else "Planning the task",
                           tool_calls=len(records),
                           available_tools=[{"alias": alias, "tool": tool.name,
                                             "schema_digest": schema_digest(tool)}
                                            for alias, tool in aliases.items()])
                message = await decide(messages, schemas, required=False)
                calls = message.get("tool_calls", [])
                if not calls:
                    try:
                        outcome = json.loads(message.get("content", ""))
                        if not isinstance(outcome, dict) or not isinstance(outcome.get("response"), str) or not outcome["response"].strip():
                            raise ValueError()
                    except (ValueError, TypeError):
                        raise _invalid(f"{step.title}: the task returned no verifiable completion evidence.") from None
                    if outcome.get("status") == "blocked":
                        raise _error("TASK_BLOCKED", f"{step.title}: {outcome['response']}", "Correct the task requirements or server setup before retrying.")
                    evidence = outcome.get("evidence")
                    if outcome.get("status") != "completed" or not isinstance(evidence, list) or not evidence or any(
                        type(number) is not int or not 1 <= number <= len(records) or records[number - 1]["status"] != "succeeded"
                        for number in evidence
                    ):
                        raise _invalid(f"{step.title}: the task returned no valid execution evidence.")
                    return outcome["response"], records
                if index == step.max_tool_calls:
                    raise _error("TASK_LIMIT_REACHED", f"{step.title}: the tool-call limit was reached.",
                                 "Inspect completed operations before increasing the limit or retrying.")
                if len(calls) != 1 or calls[0].get("function", {}).get("name") not in aliases:
                    raise _invalid(f"{step.title}: the model requested a tool outside this task.")
                call = calls[0]
                tool = aliases[call["function"]["name"]]
                invocation = replace(step, tool_name=tool.name, schema_digest=schema_digest(tool), agent_task=False)
                # Re-resolve on every call: removal or authority/schema change stops the run.
                current_tool = self.resolve(invocation)
                if step.design_check and current_tool.annotations.get('readOnlyHint') is not True:
                    raise _invalid('The design check cannot use a tool that changes the model.')
                try:
                    arguments = json.loads(call["function"]["arguments"])
                except (ValueError, KeyError, TypeError):
                    raise _invalid(f"{step.title}: the model returned invalid tool arguments.") from None
                if cad:
                    arguments = cad.guard(tool, arguments)
                signature = tool.name + json.dumps(arguments, sort_keys=True)
                if signature in rejected_recipes:
                    raise _invalid(f"{step.title}: the same rejected recipe was requested again.",
                                   "Correct the conflicting parameter names and their references before retrying.")
                if signature in succeeded and not repeatable_call(current_tool, arguments):
                    raise _invalid(f"{step.title}: a completed operation ({tool.title or tool.tool_name}) was requested again.",
                                   "Inspect the task log and clarify the remaining work before retrying.")
                await emit("tool_started", task_id=step.id, task_title=step.title,
                           tool=tool.title or tool.tool_name, arguments=arguments, tool_calls=index + 1)
                terminal_error = None
                try:
                    self.validate(invocation, arguments, tool.input_schema)
                    if cad:
                        await cad.validate_creation(tool, arguments)
                except WorkflowSourceExecutionError as error:
                    # No external operation has occurred; allow a bounded correction.
                    value, text, status = getattr(error, 'tool_result', {}), str(error), "invalid_arguments"
                else:
                    try:
                        value, text = await self.call(invocation, arguments, on_event=emit)
                        if cad:
                            cad.observe(tool, value)
                        succeeded.add(signature)
                        status = "succeeded"
                    except WorkflowSourceExecutionError as error:
                        value, text, status = getattr(error, 'tool_result', {}), str(error), "failed"
                        if cad and safe_recipe_parameter_correction(current_tool, value):
                            # The native server proved that its temporary document
                            # was closed and no recipe/output mutation remains.
                            # Permit a new decision, never replay these arguments.
                            rejected_recipes.add(signature)
                            status = "invalid_arguments"
                        elif not current_tool.annotations.get("readOnlyHint", False):
                            terminal_error = error
                record = {"tool": tool.name, "arguments": arguments, "status": status, "result": value, "text": text,
                          "schema_digest": schema_digest(tool)}
                records.append(record)
                if cad:
                    cad.records.append(record)
                await emit("tool_completed", task_id=step.id, task_title=step.title, **record)
                # A failed mutation still stops immediately. Keep its complete
                # report (including partial files and cleanup warnings) before
                # raising; it is evidence, never successful execution.
                if terminal_error is not None:
                    raise terminal_error
                result = json.dumps({"tool_call_number": index + 1, "status": status, "result": value, "text": text}, ensure_ascii=False, default=dict)
                if len(result.encode()) > 262_144:
                    raise _invalid(f"{step.title}: the tool result exceeds the task context limit.", "Request a smaller result.")
                messages.extend([message, {"role": "tool", "tool_call_id": call["id"], "content": result}])
            raise AssertionError("bounded task must return or fail")
        try:
            async with asyncio.timeout(step.timeout_seconds):
                return await execute()
        except TimeoutError as error:
            raise _error("TASK_TIMEOUT", f"{step.title}: the task exceeded its time limit.",
                         "Inspect the tool log and current files before retrying; completed operations remain.") from error
