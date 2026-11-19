"""Compile the fixed-call and declared-input subset of the native source grammar."""

import json
from dataclasses import dataclass

from .arguments import compile_arguments
from .bindings import PortableBinding
from .bundle import portable_path
from .human_input import compile_human_input
from .source import _invalid


@dataclass(frozen=True)
class FixedCall:
    id: str
    title: str
    server_id: str
    tool_name: str
    schema_digest: str
    portable: PortableBinding | None
    arguments: dict
    argument_sources: dict
    arguments_from: str | None
    file_dependencies: dict
    expected_files: tuple
    expected_file_ports: dict
    output_ports: dict
    output_format: str
    save_response: bool
    response_path: str
    file_policy: str
    timeout: int


@dataclass(frozen=True)
class InputBarrier:
    id: str
    declaration: object
    references: tuple


FIXED_SETTINGS = {
    "authoring_template",
    "mcp_server",
    "mcp_tool",
    "mcp_schema_digest",
    "mcp_binding",
    "mcp_arguments",
    "mcp_argument_ports",
    "mcp_arguments_source",
    "mcp_arguments_input",
    "mcp_file_dependencies",
    "expected_files",
    "expected_file_ports",
    "output_format",
    "save_output",
    "output_filename",
    "file_policy",
    "run_path_template",
    "timeout_seconds",
}


def compile_steps(graph, run_id):
    result = []
    for block_id in graph.ordered:
        section = graph.blocks[block_id]
        fields = section["fields"]
        settings = fields["settings"]
        if section["kind"] == "input":
            continue
        template = settings.get("authoring_template", fields.get("performed_by"))
        if template == "human-input":
            declaration, refs = compile_human_input(
                block_id, fields, graph.incoming, graph.blocks
            )
            result.append(InputBarrier(block_id, declaration, refs))
            continue
        if template != "mcp-tool" or set(settings) - FIXED_SETTINGS:
            raise _invalid(
                f"{fields['name']}: requires host support for {template} or its declared settings.",
                "Supply the qualified host capability before starting this workflow.",
                block_id=block_id,
            )
        result.append(compile_fixed_call(block_id, fields, graph, run_id))
    return result


def compile_fixed_call(block_id, fields, graph, run_id):
    from .run_paths import bind_template

    settings = bind_template(fields["settings"], run_id)
    title = fields["name"]

    def invalid(message):
        return _invalid(f"{title}: {message}", block_id=block_id)

    if (
        fields.get("performed_by") != "configured_tool"
        or fields.get("step_type") != "work"
        or fields.get("tool") is not None
        or fields.get("reusable_step") is not None
    ):
        raise invalid("the step must explicitly select a configured tool.")
    server, tool = settings.get("mcp_server"), settings.get("mcp_tool")
    if not all(isinstance(name, str) and name.strip() for name in (server, tool)):
        raise invalid("select an exact MCP server and tool.")
    references = []
    for port in fields["inputs"]:
        sources = graph.incoming.get(f"{block_id}.{port['key']}", [])
        if len(sources) > 1 or (port.get("required") and not sources):
            raise invalid(f"connect one output to {port['key']}.")
        references.extend((port["key"], source) for source in sources)
    arguments, argument_sources, arguments_from, file_dependencies = compile_arguments(
        block_id, title, settings, graph.incoming, graph.ports, references, is_mcp=True
    )
    raw_files = settings.get("expected_files", "")
    if not isinstance(raw_files, str):
        raise invalid("declare expected files one per line.")
    expected = tuple(
        portable_path(line.strip()) for line in raw_files.splitlines() if line.strip()
    )
    if len(expected) > 32 or len(set(p.casefold() for p in expected)) != len(expected):
        raise invalid("choose up to 32 distinct output files.")
    ports = {p["key"]: p["kind"] for p in fields["outputs"]}
    if not ports or any(p["quantity"] != "one" for p in fields["outputs"]):
        raise invalid("declare explicit single-value or file outputs.")
    files = {key for key, kind in ports.items() if kind == "workspace_file"}
    supported = {
        "workspace_file",
        "structured_result",
        "engineering_document",
        "text",
        "design_specification",
        "check_report",
    }
    if set(ports.values()) - supported:
        raise invalid("this output kind requires a qualified host handler.")
    mapping = settings.get("expected_file_ports", {})
    if isinstance(mapping, str):
        mapping = json.loads(mapping)
    if not mapping and len(expected) == len(files) == 1:
        mapping = {next(iter(files)): expected[0]}
    if (
        not isinstance(mapping, dict)
        or set(mapping) != files
        or set(mapping.values()) - set(expected)
    ):
        raise invalid("bind each file output port to its exact declared path.")
    fmt = settings.get("output_format", "json")
    extensions = {"text": ".txt", "json": ".json", "markdown": ".md", "html": ".html"}
    if fmt not in extensions or type(settings.get("save_output", False)) is not bool:
        raise invalid("choose a supported response format and explicit save policy.")
    policy = settings.get("file_policy", "indexed")
    if policy not in {"indexed", "overwrite", "publish_indexed", "publish_overwrite"}:
        raise invalid("choose a supported file policy.")
    save = settings.get("save_output", False) or (
        not graph.outgoing[block_id] and len(files) != len(ports)
    )
    filename = settings.get(
        "output_filename", block_id.replace("_", "-") + extensions[fmt]
    )
    if save and (
        not portable_path(filename).endswith(extensions[fmt]) or filename in expected
    ):
        raise invalid(
            "save the response to a distinct path with its response format extension."
        )
    timeout = settings.get("timeout_seconds", 300)
    if type(timeout) is not int or not 1 <= timeout <= 3600:
        raise invalid("choose a timeout from one to 3600 seconds.")
    portable = (
        PortableBinding.model_validate(settings["mcp_binding"])
        if "mcp_binding" in settings
        else None
    )
    return FixedCall(
        block_id,
        title,
        server,
        tool,
        settings.get("mcp_schema_digest", ""),
        portable,
        arguments,
        argument_sources,
        arguments_from,
        file_dependencies,
        expected,
        mapping,
        ports,
        fmt,
        save,
        filename,
        policy,
        timeout,
    )
