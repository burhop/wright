"""Compile native tool arguments and resolve connected values against the upstream schema."""

import json

from .source import _error, _invalid


def _safe_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise _error(
            "WORKFLOW_OUTPUT_INVALID",
            "A file name is required.",
            "Enter a workspace-relative filename.",
        )
    parts = value.split("/")
    if (
        "\\" in value
        or ":" in value
        or "%" in value
        or any(
            not part or part.startswith(".") or part.rstrip(" .") != part
            for part in parts
        )
    ):
        raise _error(
            "WORKFLOW_OUTPUT_INVALID",
            "The file path must stay inside the workspace.",
            "Use a filename such as report.html or reports/report.html.",
        )
    return value


def compile_arguments(
    block_id, title, settings, incoming, ports, references, *, is_mcp, agent_task=False
):
    arguments, argument_sources, arguments_from = {}, {}, None
    file_dependencies = {}
    raw_dependencies = settings.get("mcp_file_dependencies", {})
    if not isinstance(raw_dependencies, dict) or any(
        not isinstance(port, str)
        or not (isinstance(path, str) or path == {"source": "connected_output"})
        for port, path in raw_dependencies.items()
    ):
        raise _invalid(
            f"{title}: file dependencies must map input ports to workspace files or an explicit connected-output binding."
        )
    if raw_dependencies and not (is_mcp or agent_task):
        raise _invalid(
            f"{title}: file dependencies require a configured tool or AI MCP task."
        )
    for port, path in raw_dependencies.items():
        endpoint = f"{block_id}.{port}"
        connected = incoming.get(endpoint, [])
        if (
            endpoint not in ports
            or ports[endpoint][1] != "inputs"
            or ports[endpoint][2].get("kind") != "workspace_file"
            or len(connected) != 1
            or ports[connected[0]][2].get("kind") != "workspace_file"
        ):
            raise _invalid(f"{title}: connect one named workspace file to {port}.")
        file_dependencies[connected[0]] = (
            dict(path) if isinstance(path, dict) else _safe_path(path)
        )
    if is_mcp:
        try:
            arguments = json.loads(settings.get("mcp_arguments", "{}"))
            argument_ports = json.loads(settings.get("mcp_argument_ports", "{}"))
            if not isinstance(arguments, dict) or not isinstance(argument_ports, dict):
                raise ValueError()
        except (ValueError, TypeError):
            raise _invalid(f"{title}: tool arguments must be a JSON object.") from None
        if settings.get("mcp_arguments_source", "fields") == "connection":
            connected = incoming.get(
                f"{block_id}.{settings.get('mcp_arguments_input', '')}", []
            )
            if len(connected) != 1:
                raise _invalid(f"{title}: connect one JSON response as tool arguments.")
            arguments_from = connected[0]
        elif settings.get("mcp_arguments_source", "fields") != "fields":
            raise _invalid(f"{title}: choose named inputs or connected JSON arguments.")
        else:
            for key, name in argument_ports.items():
                endpoint = f"{block_id}.{key}"
                if (
                    endpoint not in ports
                    or ports[endpoint][1] != "inputs"
                    or not isinstance(name, str)
                ):
                    raise _invalid(f"{title}: a tool input mapping is invalid.")
                connected = incoming.get(endpoint, [])
                if len(connected) > 1:
                    raise _invalid(f"{title}: connect one response to {name}.")
                if connected:
                    argument_sources[name] = connected[0]
        handled = (
            set(argument_sources.values())
            | set(file_dependencies)
            | ({arguments_from} if arguments_from else set())
        )
        if any(source not in handled for _, source in references):
            raise _invalid(
                f"{title}: a connected input is not assigned to a tool argument."
            )
    return arguments, argument_sources, arguments_from, file_dependencies


def connected_arguments(step, responses, tool, *, partial=False):
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
