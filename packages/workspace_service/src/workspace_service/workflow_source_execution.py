"""Native execution for the first workspace-owned workflow source capability.

The source file is authoritative: clients provide only its workspace path and
the digest they read. This module reads and validates the stored source before
executing connected AI prompts and saving their declared response files.
"""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from datetime import datetime, timezone

from .workflow_sources import WorkflowSourceStorageError
from .workflow_references import WorkflowReference


class WorkflowSourceExecutionError(RuntimeError):
    """A correction-oriented error returned for a source-run request."""

    def __init__(self, code: str, message: str, correction: str) -> None:
        super().__init__(message)
        self.code = code
        self.correction = correction


_SECTION = re.compile(r"(workflow|item|input|task|group|connection) ([a-z][a-z0-9_]*)$")
_FIELD = re.compile(r"([a-z][a-z0-9_]*):\s*(.+)$")
_STABLE_NAME = re.compile(r"[a-z][a-z0-9_]*$")


def _error(code: str, message: str, correction: str) -> WorkflowSourceExecutionError:
    return WorkflowSourceExecutionError(code, message, correction)


def _parse(source: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    seen: set[tuple[str, str]] = set()
    for line_number, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if current is None:
            match = _SECTION.fullmatch(line)
            if match is None or match.groups() in seen:
                raise _error(
                    "WORKFLOW_SOURCE_INVALID",
                    f"The source declaration at line {line_number} is invalid or duplicated.",
                    "Correct the source declaration and save the workflow before running it.",
                )
            seen.add(match.groups())
            current = {"kind": match.group(1), "id": match.group(2), "fields": {}}
            continue
        if line == "end":
            sections.append(current)
            current = None
            continue
        match = _FIELD.fullmatch(line)
        fields = current["fields"]
        assert isinstance(fields, dict)
        if not raw.startswith((" ", "\t")) or match is None or match.group(1) in fields:
            raise _error(
                "WORKFLOW_SOURCE_INVALID",
                f"The source field at line {line_number} is invalid or duplicated.",
                "Correct the source field and save the workflow before running it.",
            )
        value = match.group(2)
        try:
            parsed: object = json.loads(value)
        except ValueError:
            if _STABLE_NAME.fullmatch(value) is None:
                raise _error(
                    "WORKFLOW_SOURCE_INVALID",
                    f"The source value at line {line_number} is invalid.",
                    "Use a JSON value or a stable name, then save the workflow.",
                ) from None
            parsed = value
        fields[match.group(1)] = parsed
    if current is not None:
        raise _error(
            "WORKFLOW_SOURCE_INVALID",
            "The saved workflow source is incomplete.",
            "Close the unfinished source section and save the workflow before running it.",
        )
    return sections


FORMATS = {"text": ".txt", "markdown": ".md", "html": ".html", "json": ".json"}
TEXT_KINDS = {
    "text",
    "workspace_file",
    "engineering_document",
    "design_specification",
    "check_report",
    "structured_result",
}


@dataclass(frozen=True)
class PromptStep:
    id: str
    title: str
    prompt: str
    prompt_from: str | None
    references: tuple[tuple[str, str], ...]
    output_format: str
    output_path: str
    save: bool
    file_policy: str
    output_ports: tuple[tuple[str, str], ...] = ()
    tool_name: str = ""
    server_id: str = ""
    schema_digest: str = ""
    arguments: dict = field(default_factory=dict)
    argument_sources: dict = field(default_factory=dict)
    arguments_from: str | None = None
    agent_task: bool = False
    task_guidance: str = ""
    max_tool_calls: int = 8
    timeout_seconds: int = 300
    expected_files: tuple[str, ...] = ()
    cad: dict | None = None
    cad_from: str | None = None
    application: dict | None = None
    application_from: str | None = None
    design_check: bool = False
    max_revisions: int = 0
    human_review: bool = False


@dataclass(frozen=True)
class PromptWorkflow:
    title: str
    steps: tuple[PromptStep, ...]
    inputs: dict[str, dict]
    revisions: dict[str, str] = field(default_factory=dict)
    review_context: dict = field(default_factory=dict)


def _invalid(
    message: str,
    correction: str = "Correct the highlighted workflow settings and save before running.",
):
    return _error("WORKFLOW_NOT_READY", message, correction)


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


def _require_connected_process(sections, blocks, ports):
    """Reject independent processes before resolving tools or executing any task.

    Connectivity ignores direction: several inputs may converge and a task may
    produce several deliverables. Visual groups do not establish dependencies.
    Source storage/authoring deliberately does not impose this run constraint.
    """
    neighbors = {key: set() for key in blocks}
    for section in sections:
        if section["kind"] != "connection":
            continue
        fields = section["fields"]
        source, target = fields.get("from"), fields.get("to")
        if not isinstance(source, str) or not isinstance(target, str):
            continue  # The compiler reports malformed connections separately.
        if fields.get("type") == "item":
            if source not in ports or target not in ports:
                continue
            source, target = ports[source][0], ports[target][0]
        elif fields.get("type") not in {"order", "approval", "revision"}:
            continue
        if source in neighbors and target in neighbors:
            neighbors[source].add(target)
            neighbors[target].add(source)
    visited, groups = set(), []
    for block_id in blocks:
        if block_id in visited:
            continue
        group, pending = [], [block_id]
        visited.add(block_id)
        while pending:
            current = pending.pop()
            group.append(current)
            for neighbor in neighbors[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        groups.append(group)
    if len(groups) > 1:
        examples = "; ".join(
            f"“{blocks[group[0]]['fields']['name']}” ({len(group)} {'block' if len(group) == 1 else 'blocks'})"
            for group in groups[:4]
        )
        raise _error(
            "WORKFLOW_DISCONNECTED_PROCESS",
            f"This workflow contains {len(groups)} disconnected groups of blocks. Run is blocked; one workflow must describe one connected process.",
            f"Connect the groups into one process, or move each independent process to its own workflow. Groups: {examples}{'; …' if len(groups) > 4 else ''}.",
        )


def compile_prompt_workflow(source: str) -> PromptWorkflow:
    sections = _parse(source)
    workflows = [s for s in sections if s["kind"] == "workflow"]
    tasks = [s for s in sections if s["kind"] == "task"]
    inputs = [s for s in sections if s["kind"] == "input"]
    if len(workflows) != 1 or not 1 <= len(tasks) <= 32:
        raise _invalid("Add between one and 32 AI prompt or MCP tool steps.")
    if any(
        s["kind"] not in {"workflow", "task", "input", "connection", "group", "item"}
        for s in sections
    ):
        raise _invalid("The workflow contains an unsupported block.")
    blocks = {str(s["id"]): s for s in tasks + inputs}
    if len(blocks) != len(tasks + inputs):
        raise _invalid("Block names must be unique.")
    ports: dict[str, tuple[str, str, dict]] = {}
    for block_id, block in blocks.items():
        fields = block["fields"]
        if not isinstance(fields.get("name"), str) or not fields["name"].strip():
            raise _invalid(f"{block_id} needs a name.")
        for direction in ("inputs", "outputs"):
            values = fields.get(direction, [])
            if not isinstance(values, list):
                raise _invalid(f"{fields['name']}: invalid {direction}.")
            for port in values:
                if not isinstance(port, dict) or not isinstance(port.get("key"), str):
                    raise _invalid(
                        f"{fields['name']}: each connection point needs a key."
                    )
                endpoint = f"{block_id}.{port['key']}"
                if endpoint in ports:
                    raise _invalid(f"Duplicate connection point: {endpoint}.")
                ports[endpoint] = (block_id, direction, port)
    _require_connected_process(sections, blocks, ports)
    incoming: dict[str, list[str]] = {}
    dependencies: dict[str, set[str]] = {key: set() for key in blocks}
    outgoing: dict[str, set[str]] = {key: set() for key in blocks}
    revisions = {}
    for section in sections:
        if section["kind"] != "connection":
            continue
        fields = section["fields"]
        if fields.get("type") in {"revision", "approval"}:
            source_id, target_id = fields.get("from"), fields.get("to")
            if (
                not isinstance(source_id, str)
                or not isinstance(target_id, str)
                or source_id not in blocks
                or target_id not in blocks
                or blocks[target_id]["kind"] != "task"
                or blocks[source_id]["kind"] != "task"
            ):
                raise _invalid("A design-check path references a missing task.")
            settings = blocks[source_id]["fields"].get("settings", {})
            if (
                not isinstance(settings, dict)
                or settings.get("design_check") is not True
            ):
                raise _invalid(
                    "Only an executable design check can release or revise this native run."
                )
            expected = "revise" if fields["type"] == "revision" else "pass"
            if fields.get("when") != expected:
                raise _invalid(
                    f"Design-check {fields['type']} paths must use the condition {expected}."
                )
            if expected == "revise":
                if source_id in revisions:
                    raise _invalid("Choose one revision target for each design check.")
                revisions[source_id] = target_id
            else:
                dependencies[target_id].add(source_id)
                outgoing[source_id].add(target_id)
            continue
        if fields.get("type") != "item" or fields.get("when") is not None:
            raise _invalid(
                "This run contains a conditional or control connection.",
                "Use data connections between AI prompts and text inputs for this run.",
            )
        source_port, target_port = fields.get("from"), fields.get("to")
        if (
            not isinstance(source_port, str)
            or not isinstance(target_port, str)
            or source_port not in ports
            or target_port not in ports
        ):
            raise _invalid("A connection references a missing input or output.")
        source_id, source_direction, _ = ports[source_port]
        target_id, target_direction, _ = ports[target_port]
        source_kind = ports[source_port][2].get("kind")
        target_kind = ports[target_port][2].get("kind")
        if source_kind != target_kind and not (
            source_kind in TEXT_KINDS and target_kind in TEXT_KINDS
        ):
            raise _invalid(
                "These connected inputs and outputs have incompatible types.",
                "Connect an image only to an image input, and text to a text-compatible input.",
            )
        if (
            ports[source_port][2].get("quantity") == "many"
            and ports[target_port][2].get("quantity") != "many"
        ):
            raise _invalid("A collection cannot feed a single-item input.")
        if (
            source_direction != "outputs"
            or target_direction != "inputs"
            or blocks[target_id]["kind"] != "task"
        ):
            raise _invalid("Connect a block output to an AI step input.")
        incoming.setdefault(target_port, []).append(source_port)
        dependencies[target_id].add(source_id)
        outgoing[source_id].add(target_id)
    ordered: list[str] = []
    remaining = set(blocks)
    while remaining:
        ready = [
            key
            for key in blocks
            if key in remaining and dependencies[key].issubset(ordered)
        ]
        if not ready:
            raise _invalid(
                "The workflow contains a cycle.",
                "Remove the circular prompt connection before running.",
            )
        ordered.extend(ready)
        remaining.difference_update(ready)
    steps = []
    for block_id in ordered:
        block = blocks[block_id]
        fields = block["fields"]
        if block["kind"] != "task":
            continue
        title = fields["name"]
        settings = fields.get("settings", {})
        if not isinstance(settings, dict):
            raise _invalid(f"{title}: invalid settings.")
        if settings.get("authoring_template") == "manual-review":
            refs = [
                (str(port.get("name", "Document")), source)
                for port in fields.get("inputs", [])
                for source in incoming.get(f"{block_id}.{port['key']}", [])
            ]
            instructions = fields.get("instructions", fields.get("prompt", ""))
            if (
                fields.get("performed_by") != "engineer"
                or fields.get("step_type") != "work"
                or fields.get("tool") is not None
                or fields.get("reusable_step") is not None
                or outgoing[block_id]
                or len(fields.get("inputs", [])) != 1
                or len(refs) != 1
                or not isinstance(instructions, str)
                or not instructions.strip()
                or len(instructions) > 8000
            ):
                raise _invalid(
                    f"{title}: use one terminal Engineer review with one connected document and review instructions."
                )
            steps.append(
                PromptStep(
                    block_id,
                    title,
                    instructions,
                    None,
                    tuple(refs),
                    "text",
                    "",
                    False,
                    "indexed",
                    human_review=True,
                )
            )
            continue
        is_mcp = settings.get("authoring_template") == "mcp-tool"
        agent_task = settings.get("authoring_template") == "mcp-task"
        design_check = settings.get("design_check", False)
        max_revisions = settings.get("max_revisions", 0)
        if (
            type(design_check) is not bool
            or type(max_revisions) is not int
            or not 0 <= max_revisions <= 3
        ):
            raise _invalid(
                f"{title}: use a design-check toggle and a revision limit from zero to three."
            )
        if design_check and (not agent_task or settings.get("output_format") != "json"):
            raise _invalid(
                f"{title}: a design check needs an MCP task with a JSON response."
            )
        from .workflow_cad import parse_cad

        cad = (
            parse_cad(settings.get("cad"), terminal=not outgoing[block_id])
            if agent_task
            else None
        )
        cad_from = None
        from .workflow_application_task import parse_application

        application = (
            parse_application(settings.get("application_resource"))
            if agent_task
            else None
        )
        application_from = None
        if design_check and (
            not cad
            or cad.get("source") != "upstream"
            or cad.get("save_native", True)
            or cad.get("exports")
            or cad.get("edit_mode", "in_place") != "in_place"
        ):
            raise _invalid(
                f"{title}: inspect an upstream CAD model without saving, copying or exporting it."
            )
        if cad and application:
            raise _invalid("Choose one application resource adapter for this task.")
        if agent_task and (
            not isinstance(settings.get("mcp_server"), str)
            or not settings["mcp_server"].strip()
        ):
            raise _invalid(f"{title}: choose a workspace-enabled MCP server.")
        max_calls = settings.get("max_tool_calls", 8)
        timeout = settings.get("timeout_seconds", 300)
        guidance = settings.get("task_guidance", "")
        expected = settings.get("expected_result", "")
        if not isinstance(expected, str) or len(expected) > 16000:
            raise _invalid(f"{title}: expected result must be bounded text.")
        if isinstance(guidance, str) and expected:
            guidance += "\nExpected result: " + expected
        raw_files = settings.get("expected_files", "")
        if not isinstance(raw_files, str):
            raise _invalid(
                f"{title}: expected files must be workspace-relative paths, one per line."
            )
        expected_files = tuple(
            _safe_path(p.strip()) for p in raw_files.splitlines() if p.strip()
        )
        if len(expected_files) > 16 or (expected_files and not agent_task):
            raise _invalid(
                f"{title}: declared tool-created files require an MCP task (maximum 16)."
            )
        if agent_task and (
            type(max_calls) is not int
            or not 1 <= max_calls <= 32
            or type(timeout) is not int
            or not 30 <= timeout <= 600
            or not isinstance(guidance, str)
            or len(guidance) > 16000
        ):
            raise _invalid(
                f"{title}: use 1–32 tool calls and a 30–600 second task limit."
            )
        if (
            fields.get("step_type") != "work"
            or fields.get("tool") is not None
            or fields.get("reusable_step") is not None
            or fields.get("performed_by")
            != ("configured_tool" if is_mcp else "ai_assisted")
        ):
            raise _invalid(
                f"{title} needs a supported execution type.",
                "Use an AI prompt or an MCP tool block for this run.",
            )
        tool_name = str(settings.get("mcp_tool", "")) if is_mcp else ""
        if is_mcp and not tool_name:
            raise _invalid(f"{title}: choose an available MCP tool.")
        fmt = settings.get("output_format", "json" if is_mcp else "text")
        policy = settings.get("file_policy", "indexed")
        mode = settings.get("prompt_source", "inline")
        if (
            not all(isinstance(value, str) for value in (fmt, policy, mode))
            or fmt not in FORMATS
            or policy not in {"indexed", "overwrite"}
            or mode not in {"inline", "connection"}
        ):
            raise _invalid(
                f"{title}: choose a valid response format, prompt source and file policy."
            )
        if "save_output" in settings and not isinstance(settings["save_output"], bool):
            raise _invalid(f"{title}: save_output must be true or false.")
        prompt = fields.get("prompt", "")
        if not isinstance(prompt, str):
            raise _invalid(f"{title}: the prompt must be text.")
        prompt_key = settings.get("prompt_input", "")
        prompt_from = None
        references = []
        for port in fields.get("inputs", []):
            producers = incoming.get(f"{block_id}.{port['key']}", [])
            if len(producers) > 1:
                raise _invalid(
                    f"{title}: {port.get('name', 'input')} has multiple sources.",
                    "Connect one response to each input.",
                )
            is_prompt = mode == "connection" and port["key"] == prompt_key
            if (is_prompt or port.get("required", False)) and not producers:
                raise _invalid(
                    f"{title}: connect {port.get('name', 'the required input')}."
                )
            if producers:
                if (
                    application
                    and application.get("source") == "upstream"
                    and port["key"] == application.get("from_port")
                ):
                    application_from = producers[0]
                    continue
                if (
                    cad
                    and cad.get("source") == "upstream"
                    and port["key"] == cad.get("from_port")
                ):
                    if ports[producers[0]][2].get("kind") != "cad_model":
                        raise _invalid(f"{title}: connect a CAD model output.")
                    cad_from = producers[0]
                    continue
                producer_kind = ports[producers[0]][2].get("kind")
                if producer_kind == "cad_model":
                    raise _invalid(
                        f"{title}: choose this connection under Model to work on.",
                        "Connect CAD models to a CAD model input; use the response output for text.",
                    )
                if producer_kind == "reference_images" and (is_prompt or is_mcp):
                    raise _invalid(
                        f"{title}: this input cannot consume an image directly.",
                        "Write the task instructions and connect the image as reference material to an AI prompt or AI task.",
                    )
                if is_prompt:
                    prompt_from = producers[0]
                else:
                    references.append(
                        (str(port.get("name", "Reference material")), producers[0])
                    )
        if mode == "connection" and prompt_from is None:
            raise _invalid(
                f"{title}: choose the block output that supplies its prompt."
            )
        if not is_mcp and mode == "inline" and not prompt.strip():
            raise _invalid(f"{title}: enter a prompt.")
        if not fields.get("outputs"):
            raise _invalid(f"{title}: declare a response output.")
        if cad and cad.get("source") == "upstream" and cad_from is None:
            raise _invalid(f"{title}: connect the CAD model to work on.")
        if (
            application
            and application.get("source") == "upstream"
            and application_from is None
        ):
            raise _invalid(f"{title}: connect the application resource to work on.")
        save = (not outgoing[block_id] and not cad and not application) or settings.get(
            "save_output", False
        )
        filename = settings.get(
            "output_filename", f"{block_id.replace('_', '-')}{FORMATS[fmt]}"
        )
        if save:
            filename = _safe_path(filename)
            if PurePosixPath(filename).suffix.lower() != FORMATS[fmt]:
                raise _invalid(
                    f"{title}: the filename must end in {FORMATS[fmt]} for {fmt} output."
                )
        arguments, argument_sources, arguments_from = {}, {}, None
        if is_mcp:
            try:
                arguments = json.loads(settings.get("mcp_arguments", "{}"))
                argument_ports = json.loads(settings.get("mcp_argument_ports", "{}"))
                if not isinstance(arguments, dict) or not isinstance(
                    argument_ports, dict
                ):
                    raise ValueError()
            except (ValueError, TypeError):
                raise _invalid(
                    f"{title}: tool arguments must be a JSON object."
                ) from None
            if settings.get("mcp_arguments_source", "fields") == "connection":
                connected = incoming.get(
                    f"{block_id}.{settings.get('mcp_arguments_input', '')}", []
                )
                if len(connected) != 1:
                    raise _invalid(
                        f"{title}: connect one JSON response as tool arguments."
                    )
                arguments_from = connected[0]
            elif settings.get("mcp_arguments_source", "fields") != "fields":
                raise _invalid(
                    f"{title}: choose named inputs or connected JSON arguments."
                )
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
            handled = set(argument_sources.values()) | (
                {arguments_from} if arguments_from else set()
            )
            if any(source not in handled for _, source in references):
                raise _invalid(
                    f"{title}: a connected input is not assigned to a tool argument."
                )
        steps.append(
            PromptStep(
                block_id,
                title,
                prompt,
                prompt_from,
                tuple(references),
                fmt,
                str(filename),
                bool(save),
                policy,
                tuple(
                    (p["key"], str(p.get("kind", "engineering_document")))
                    for p in fields["outputs"]
                ),
                tool_name,
                str(settings.get("mcp_server", "")),
                str(settings.get("mcp_schema_digest", "")),
                arguments,
                argument_sources,
                arguments_from,
                agent_task,
                guidance,
                max_calls,
                timeout,
                expected_files if not cad else (),
                cad,
                cad_from,
                application,
                application_from,
                design_check,
                max_revisions,
            )
        )
    from .workflow_design_check import validate_rework

    reviews = [step for step in steps if step.human_review]
    if reviews:
        if (
            len(reviews) != 1
            or revisions
            or any(step.tool_name or step.agent_task for step in steps)
        ):
            raise _invalid(
                "Engineer review currently supports one terminal review after AI document tasks; MCP/CAD continuation is not supported."
            )
        review = reviews[0]
        producer_id = review.references[0][1].split(".")[0]
        producer = next((step for step in steps if step.id == producer_id), None)
        if producer is None or not producer.save or producer.file_policy != "indexed":
            raise _invalid(
                "Save the reviewed document as an indexed workspace file before Engineer review."
            )
        if any(step.save and step.file_policy != "indexed" for step in steps):
            raise _invalid(
                "A workflow with Engineer review must use indexed output files to preserve earlier drafts."
            )
        # Independent terminal branches finish before the review package is sealed.
        steps = [step for step in steps if not step.human_review] + reviews
    validate_rework(steps, revisions)
    # Reject output collisions within one run before calling any model.
    names: dict[str, str] = {}
    for step in steps:
        if step.save:
            key = step.output_path.casefold()
            if key in names and (
                step.file_policy == "overwrite" or names[key] == "overwrite"
            ):
                raise _invalid(
                    "Two steps would overwrite the same output file.",
                    "Give the steps different filenames or use indexed files for both.",
                )
            names[key] = step.file_policy
    return PromptWorkflow(
        str(workflows[0]["fields"].get("name", "Workflow")),
        tuple(steps),
        {str(s["id"]): s["fields"] for s in inputs},
        revisions,
    )


def validate_response(value: str, fmt: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.encode("utf-8")) > 1_048_576
    ):
        raise _invalid(
            "The model response is empty or exceeds 1 MiB.",
            "Shorten or clarify the prompt and run again.",
        )
    value = value.strip()
    if fmt in {"html", "json"}:
        match = re.fullmatch(r"```(?:html|json)?\s*\n?(.*?)\n?```", value, re.S | re.I)
        if match:
            value = match.group(1).strip()
    if fmt == "html" and (
        not re.search(r"<html\b", value, re.I)
        or not re.search(r"</html\s*>", value, re.I)
    ):
        raise _invalid(
            "The model response is not a complete HTML document.",
            "Correct the prompt or select a different response format.",
        )
    if fmt == "json":
        try:
            json.loads(
                value,
                parse_constant=lambda _: (_ for _ in ()).throw(
                    ValueError("Non-finite JSON")
                ),
            )
        except ValueError as error:
            raise _invalid(
                "The model response is not valid JSON.",
                "Clarify the requested JSON structure and run again.",
            ) from error
    return value


def validate_workspace_authoring_shape(source: str):
    """Check required editor fields and global port identities before execution.

    Storage may retain invalid source drafts, but those drafts must not execute
    merely because the runtime needs fewer fields than the canonical editor.
    """
    port_keys = set()
    for section in _parse(source):
        kind, fields = section["kind"], section["fields"]
        if kind == "workflow":
            required = {"name", "purpose", "discipline", "reviewed_ai_suggestions"}
        elif kind in {"task", "input"}:
            required = {
                "name",
                "purpose",
                "step_type",
                "group",
                "inputs",
                "outputs",
                "settings",
                "tool",
                "reusable_step",
                "performed_by" if kind == "task" else "provided_by",
                "prompt" if "prompt" in fields else "instructions",
            }
        elif kind == "connection":
            required = {"type", "from", "to", "label", "when"}
        else:
            continue
        missing = required - fields.keys()
        if missing:
            raise _invalid(
                f"{kind} {section['id']} is missing authoring fields: {', '.join(sorted(missing))}.",
                "Complete these fields in the workspace workflow source before running.",
            )
        if kind in {"task", "input"}:
            actor = fields.get("provided_by" if kind == "input" else "performed_by")
            if actor not in {
                "engineer",
                "configured_tool",
                "company_library",
                "ai_assisted",
                "ai_then_engineer",
            }:
                raise _invalid(
                    f"{section['id']}: unknown performer {actor!r}.",
                    "Use engineer, configured_tool, company_library, ai_assisted, or ai_then_engineer.",
                )
            for direction in ("inputs", "outputs"):
                for port in (
                    fields[direction] if isinstance(fields[direction], list) else []
                ):
                    expected = {
                        "key",
                        "name",
                        "kind",
                        "item",
                        "required",
                        "quantity",
                        "description",
                    }
                    if (
                        not isinstance(port, dict)
                        or set(port) != expected
                        or not isinstance(port.get("key"), str)
                    ):
                        raise _invalid(
                            f"{section['id']}: incomplete connection-point fields.",
                            "Use key, name, kind, item, required, quantity and description for every port.",
                        )
                    if port["key"] in port_keys:
                        raise _invalid(
                            f"Duplicate connection identity: {port['key']}.",
                            "Use a distinct port key for every connection point in the workspace workflow.",
                        )
                    port_keys.add(port["key"])


async def prepare_prompt_workflow(
    *, service, workspace_dir: str, path: str, expected_digest: str, tool_runtime=None
) -> tuple[PromptWorkflow, dict[str, str]]:
    try:
        document = await service.workflow_sources.read(workspace_dir, path)
    except WorkflowSourceStorageError as error:
        raise _invalid(
            "The saved workflow could not be read.",
            "Open and save the workflow in this workspace.",
        ) from error
    if document.storage_digest != expected_digest:
        raise _error(
            "WORKFLOW_SOURCE_CONFLICT",
            "The saved workflow changed.",
            "Reload or compare the workflow before running again.",
        )
    validate_workspace_authoring_shape(document.source)
    plan = compile_prompt_workflow(document.source)
    review_snapshots = []
    if any(step.human_review for step in plan.steps):
        from .workflow_artifact_review import snapshot

        review_snapshots.append(snapshot(path, document.source.encode("utf-8")))
        if review_snapshots[0]["sha256"] != expected_digest:
            raise _error(
                "WORKFLOW_SOURCE_CONFLICT",
                "The saved source bytes do not match their recorded identity.",
                "Reload the workflow before running.",
            )
    if any(step.tool_name or step.agent_task for step in plan.steps):
        if callable(tool_runtime):
            tool_runtime = tool_runtime()
        if tool_runtime is None:
            raise _invalid(
                "MCP execution is unavailable.",
                "Check the MCP server connection and try again.",
            )
        for step in plan.steps:
            if step.tool_name or step.agent_task:
                tool_runtime.preflight(step)
    values = {}
    from .workspace_path import WorkspacePath

    paths = WorkspacePath(workspace_dir)
    for step in plan.steps:
        if step.application:
            from .workflow_application_task import validate_application_connection

            validate_application_connection(tool_runtime, step, plan)
        if step.save:
            paths.resolve(step.output_path)
        if step.cad:
            from .workflow_cad import capabilities, list_documents

            caps = await capabilities(tool_runtime, step)
            if not caps.get("supported") or not caps.get("can_list"):
                raise _invalid(
                    f"{step.title}: the server does not support CAD document selection."
                )
            if (
                step.cad.get("save_native", True)
                or step.cad["source"] == "new"
                or step.cad.get("edit_mode") == "copy"
            ) and not caps.get("can_save"):
                raise _invalid(
                    f"{step.title}: native model saving is unavailable on this server."
                )
            for export in step.cad.get("exports", []):
                if export["format"] not in caps["formats"]:
                    raise _invalid(
                        f"{step.title}: export format {export['format']} is unavailable."
                    )
                paths.resolve(export["path"])
            for field in ("native_path", "copy_path"):
                if step.cad.get(field):
                    paths.resolve(step.cad[field])
            if step.cad["source"] == "workspace":
                try:
                    paths.resolve(step.cad["file"], must_exist=True)
                except (OSError, ValueError) as error:
                    raise _invalid(
                        f"{step.title}: select an existing CAD file in this workspace."
                    ) from error
            if step.cad["source"] == "session":
                if not any(
                    d.get("documentId") == step.cad["document_id"]
                    for d in await list_documents(tool_runtime, step)
                ):
                    raise _invalid(
                        f"{step.title}: the selected CAD document is no longer open.",
                        "Refresh open models and select the document again.",
                    )
        for expected_file in step.expected_files:
            paths.resolve(expected_file)
    for key, fields in plan.inputs.items():
        settings = fields.get("settings", {})
        if not isinstance(settings, dict):
            raise _invalid(f"{fields['name']}: invalid input settings.")
        if settings.get("input_mode") == "workspace-file" or settings.get(
            "workspace_file"
        ):
            path = _safe_path(settings.get("workspace_file"))
            try:
                data = await service.files.read_reference(workspace_dir, path)
                if review_snapshots:
                    review_snapshots.append(snapshot(path, data))
                image = any(
                    p.get("kind") == "reference_images"
                    for p in fields.get("outputs", [])
                )
                addresses = {
                    f"{key}.{port['key']}" for port in fields.get("outputs", [])
                }
                # Only an explicitly declared file import can consume opaque bytes.
                # Mixed prompt/file consumers must still have readable document text.
                file_import = any(
                    step.application_from in addresses for step in plan.steps
                )
                text_consumer = any(
                    step.prompt_from in addresses
                    or any(src in addresses for _, src in step.references)
                    or any(src in addresses for src in step.argument_sources.values())
                    or step.arguments_from in addresses
                    for step in plan.steps
                )
                value = WorkflowReference.from_bytes(
                    path,
                    data,
                    image=image,
                    allow_binary=file_import and not text_consumer,
                )
            except (OSError, UnicodeError, ValueError) as error:
                raise _invalid(
                    f"{fields['name']}: the workspace reference could not be read.",
                    str(error)
                    if isinstance(error, ValueError)
                    else "Choose an existing file in this workspace.",
                ) from error
        else:
            value = settings.get("input_text", "")
        if not isinstance(value, WorkflowReference) and (
            not isinstance(value, str)
            or not value.strip()
            or len(value.encode()) > 1_048_576
        ):
            raise _invalid(f"{fields['name']}: supply text before running.")
        values[key] = value
    if review_snapshots:
        from dataclasses import replace

        plan = replace(
            plan,
            review_context={
                "source_digest": expected_digest,
                "snapshots": review_snapshots,
                "input_values": {
                    key: (
                        {"path": value.path, "sha256": value.sha256}
                        if isinstance(value, WorkflowReference)
                        else value
                    )
                    for key, value in values.items()
                },
            },
        )
        if len(json.dumps(plan.review_context).encode()) > 8 * 1024 * 1024:
            raise _invalid(
                "The exact review source and inputs exceed the 8 MiB snapshot limit."
            )
    return plan, values


async def execute_prompt_workflow(
    *,
    service,
    workspace_dir: str,
    plan: PromptWorkflow,
    input_values: dict[str, str],
    response_generator: Callable[[str, str], Awaitable[str]],
    on_event=None,
    tool_runtime=None,
    action_generator=None,
) -> dict:
    from uuid import uuid4
    from dataclasses import replace
    from .workflow_results import (
        EngineeringResult,
        Representation,
        Provenance,
        file_representation,
        file_result,
    )

    run_id = uuid4().hex
    engineering_results = []

    async def emit(kind, **data):
        if on_event:
            await on_event(
                {"kind": kind, "at": datetime.now(timezone.utc).isoformat(), **data}
            )
            if kind == "output_saved" and data.get("artifact_role") == "diagnostic":
                # The existing results panel consumes result_ready. Expose the
                # verified report file there without adding it to execution
                # results, accepted output ports, or downstream bindings.
                diagnostic = file_result(
                    data,
                    Provenance(
                        run_id, data["task_id"], f"diagnostic:{data['output_path']}"
                    ),
                )
                diagnostic = replace(
                    diagnostic, name=data.get("artifact_title") or data["output_path"]
                )
                await on_event(
                    {
                        "kind": "result_ready",
                        "at": datetime.now(timezone.utc).isoformat(),
                        "task_id": data["task_id"],
                        "task_title": data["task_title"],
                        "artifact_role": "diagnostic",
                        "engineering_result": diagnostic.to_dict(),
                    }
                )

    async def save_response(step, record):
        import hashlib

        actual = await service.files.write_generated(
            workspace_dir, step.output_path, record["response"], step.file_policy
        )
        record["output_path"] = actual
        record["output_bytes"] = len(record["response"].encode())
        output = {
            key: record[key]
            for key in (
                "task_id",
                "task_title",
                "output_path",
                "output_bytes",
                "output_format",
            )
        }
        output["sha256"] = hashlib.sha256(record["response"].encode()).hexdigest()
        record["saved_response"] = output
        for index, result in enumerate(engineering_results):
            if result.provenance.task_id == step.id and result.kind in {
                "text",
                "structured",
            }:
                engineering_results[index] = replace(
                    result,
                    representations=(
                        *result.representations,
                        file_representation(output),
                    ),
                )
                await emit(
                    "result_ready",
                    task_id=step.id,
                    task_title=step.title,
                    engineering_result=engineering_results[index].to_dict(),
                )
                break
        await emit("output_saved", **output)
        return output

    responses = dict(input_values)
    artifacts_by_output = {}
    file_outputs = {
        f"{step.id}.{key}"
        for step in plan.steps
        for key, kind in step.output_ports
        if kind == "workspace_file"
    }

    async def document_value(source_id, title):
        value = responses[source_id]
        files = artifacts_by_output.get(source_id, [])
        if (
            source_id in file_outputs
            and files
            and not isinstance(value, EngineeringResult)
        ):
            if len(files) != 1:
                raise _invalid(
                    f"{title}: select one named file export.",
                    "A group of files cannot supply one document input.",
                )
            producer, port = source_id.split(".", 1)
            value = file_result(files[0], Provenance(run_id, producer, port))
        if isinstance(value, EngineeringResult):
            from .workflow_references import reference_from_result

            value = await reference_from_result(
                value, service=service, workspace_dir=workspace_dir, task_title=title
            )
        return value

    for key, fields in plan.inputs.items():
        for port in fields.get("outputs", []):
            responses[f"{key}.{port['key']}"] = input_values[key]
    records, attempts, revision_counts, feedback = [], [], {}, {}
    cursor = 0
    while cursor < len(plan.steps):
        step = plan.steps[cursor]
        if step.human_review:
            break  # Terminal review is persisted by the run recorder after all outputs are sealed.
        check_report = None
        if step.tool_name:
            if tool_runtime is None:
                raise _invalid(f"{step.title}: MCP execution is unavailable.")
            tool_values = {
                key: value.text
                if isinstance(value, WorkflowReference) and not value.image_url
                else value
                for key, value in responses.items()
            }
            reference_records = []
            for source_id in set(step.argument_sources.values()) | (
                {step.arguments_from} if step.arguments_from else set()
            ):
                value = responses[source_id]
                # Whole-argument inputs are document JSON. Legacy CAD scalar
                # file sockets keep their path semantics for exact tool calls.
                if source_id == step.arguments_from or isinstance(
                    value, EngineeringResult
                ):
                    value = await document_value(source_id, step.title)
                if isinstance(value, WorkflowReference):
                    if value.image_url or value.file_only:
                        raise _invalid(
                            f"{step.title}: this tool input requires readable text or JSON.",
                            "Use an AI task for image references or an application input that explicitly imports this file format.",
                        )
                    reference_records.append(
                        {"path": value.path, "sha256": value.sha256, "kind": "text"}
                    )
                    tool_values[source_id] = value.text
            arguments = tool_runtime.arguments(step, tool_values)
            await emit(
                "step_started",
                task_id=step.id,
                task_title=step.title,
                execution_kind="mcp",
                tool=step.tool_name,
                arguments=arguments,
                output_format=step.output_format,
            )
            value, text = await tool_runtime.call(step, arguments, on_event=emit)
            structured = json.dumps(
                value, ensure_ascii=False, indent=2, allow_nan=False
            )
            response = validate_response(
                text if step.output_format == "text" else structured, step.output_format
            )
            record = {
                "execution_kind": "mcp",
                "tool": step.tool_name,
                "arguments": arguments,
                "prompt": "",
                "response": response,
            }
            if reference_records:
                record["references"] = reference_records
            for key, kind in step.output_ports:
                responses[f"{step.id}.{key}"] = text if kind == "text" else structured
        else:
            images, reference_records = [], []
            prompt = (
                await document_value(step.prompt_from, step.title)
                if step.prompt_from
                else step.prompt
            )
            if isinstance(prompt, WorkflowReference):
                if prompt.file_only:
                    raise _invalid(
                        f"{step.title}: this file has no readable prompt text.",
                        "Connect it to an application that imports this format.",
                    )
                if prompt.image_url:
                    raise _invalid(
                        f"{step.title}: an image cannot supply task instructions.",
                        "Write the prompt and connect the image as reference material.",
                    )
                reference_records.append(
                    {"path": prompt.path, "sha256": prompt.sha256, "kind": "text"}
                )
                prompt = prompt.text
            for name, source_id in step.references:
                reference = await document_value(source_id, step.title)
                if isinstance(reference, WorkflowReference):
                    if reference.file_only:
                        raise _invalid(
                            f"{step.title}: this file cannot be read as reference text.",
                            "Connect it to an application that imports this format.",
                        )
                    reference_records.append(
                        {
                            "path": reference.path,
                            "sha256": reference.sha256,
                            "kind": "image" if reference.image_url else "text",
                        }
                    )
                    if reference.image_url:
                        images.append(reference.image_url)
                        prompt += f"\n\nReference image — {name}: {reference.path} (attached image)"
                    else:
                        prompt += f"\n\nReference document — {name} ({reference.path}):\n{reference.text}"
                else:
                    prompt += f"\n\nReference material — {name}:\n{reference}"
            for source_id in ([step.prompt_from] if step.prompt_from else []) + [
                source for _, source in step.references
            ]:
                artifacts = artifacts_by_output.get(source_id, [])
                if artifacts and source_id not in file_outputs:
                    prompt += (
                        "\n\nVerified workspace file references (contents are not inlined):\n"
                        + json.dumps(artifacts)
                    )
                    reference_records.extend(artifacts)
            if step.agent_task:
                prompt += f"\n\nWorkspace directory: {workspace_dir}. File references are relative to this directory."
            if step.id in feedback:
                prompt += (
                    "\n\nPrevious design check — create a corrected new revision, preserving satisfied requirements:\n"
                    + json.dumps(feedback[step.id])
                )
            if step.design_check:
                from .workflow_design_check import CHECK_INSTRUCTIONS

                prompt += "\n\n" + CHECK_INSTRUCTIONS
            if len(prompt.encode()) > 1_048_576:
                raise _invalid(
                    f"{step.title}: the assembled prompt exceeds 1 MiB.",
                    "Reduce the input or split it into smaller steps.",
                )
            execution_kind = "mcp_task" if step.agent_task else "ai"
            produced_files = []
            prior_files = {}
            if step.expected_files:
                from .workflow_references import snapshot_task_files

                prior_files = snapshot_task_files(workspace_dir, step.expected_files)
                prompt += "\n\nCreate these files in this workspace: " + ", ".join(
                    step.expected_files
                )
            await emit(
                "step_started",
                task_id=step.id,
                task_title=step.title,
                execution_kind=execution_kind,
                prompt=prompt,
                output_format=step.output_format,
            )
            try:
                if step.agent_task:
                    if tool_runtime is None or action_generator is None:
                        raise _invalid(
                            f"{step.title}: AI task execution is unavailable."
                        )
                    cad_document = None
                    if step.cad:
                        from .workflow_cad import CadTask

                        task = CadTask(
                            tool_runtime, step, workspace_dir, responses, emit
                        )
                        async with task.lock:
                            prompt += await task.start()
                            response, calls = await tool_runtime.run_task(
                                step,
                                prompt,
                                action_generator,
                                emit,
                                cad=task,
                                images=images,
                            )
                            if step.design_check:
                                from .workflow_design_check import inspect_verdict

                                check_report = inspect_verdict(
                                    validate_response(response, "json"), calls
                                )
                                await emit(
                                    "design_check",
                                    task_id=step.id,
                                    task_title=step.title,
                                    report=check_report,
                                    tool_calls=calls,
                                    revision=revision_counts.get(step.id, 0),
                                )
                            cad_document, produced_files = await task.finish()
                            model_result = task.engineering_result(run_id)
                            cad_document = replace(cad_document, result=model_result)
                            engineering_results.append(model_result)
                            await emit(
                                "result_ready",
                                task_id=step.id,
                                task_title=step.title,
                                engineering_result=model_result.to_dict(),
                            )
                            calls = task.records
                    elif step.application:
                        from .workflow_application_task import ApplicationResourceTask

                        application_values = dict(responses)
                        incoming = application_values.get(step.application_from)
                        if isinstance(incoming, WorkflowReference):
                            producer_id, port = step.application_from.split(".", 1)
                            from pathlib import PurePosixPath

                            application_values[step.application_from] = (
                                EngineeringResult(
                                    f"{run_id}:{producer_id}:{port}",
                                    "image" if incoming.image_url else "file",
                                    incoming.path,
                                    (
                                        Representation(
                                            "workspace_file",
                                            incoming.path,
                                            PurePosixPath(incoming.path)
                                            .suffix.lstrip(".")
                                            .lower(),
                                            durability="persistent",
                                            sha256=incoming.sha256,
                                            size_bytes=incoming.size_bytes,
                                        ),
                                    ),
                                    Provenance(run_id, producer_id, port),
                                )
                            )
                        exported_files = artifacts_by_output.get(
                            step.application_from, []
                        )
                        if exported_files:
                            if len(exported_files) != 1:
                                raise _invalid(
                                    "This application input accepts one exported file.",
                                    "Connect a named individual export rather than a collection of files.",
                                )
                            producer_id, port = step.application_from.split(".", 1)
                            application_values[step.application_from] = file_result(
                                exported_files[0], Provenance(run_id, producer_id, port)
                            )
                        task = ApplicationResourceTask(
                            tool_runtime,
                            step,
                            application_values,
                            emit,
                            workspace_dir=workspace_dir,
                            files=service.files,
                        )
                        async with task.lock:
                            prompt += await task.start()
                            response, calls = await tool_runtime.run_task(
                                step,
                                prompt,
                                action_generator,
                                emit,
                                cad=task,
                                images=images,
                            )
                            model_result = await task.finish(run_id)
                            produced_files = list(task.produced_files)
                            engineering_results.append(model_result)
                            await emit(
                                "result_ready",
                                task_id=step.id,
                                task_title=step.title,
                                engineering_result=model_result.to_dict(),
                            )
                            calls = task.records
                    else:
                        response, calls = await tool_runtime.run_task(
                            step, prompt, action_generator, emit, images=images
                        )
                    response = validate_response(response, step.output_format)
                    from .workflow_references import verify_task_files
                    import asyncio

                    if not step.cad:
                        produced_files.extend(
                            await asyncio.to_thread(
                                verify_task_files,
                                workspace_dir,
                                step.expected_files,
                                prior_files,
                            )
                        )
                else:
                    response = validate_response(
                        await response_generator(
                            prompt, step.output_format, images=images
                        )
                        if images
                        else await response_generator(prompt, step.output_format),
                        step.output_format,
                    )
            except TimeoutError as error:
                raise _error(
                    "MODEL_TIMEOUT",
                    str(error),
                    "Retry when the model is less busy or request a shorter response. Completed steps and files have been preserved.",
                ) from error
            except ValueError as error:
                raise _error(
                    "MODEL_UNAVAILABLE", str(error), "Check Model Setup and run again."
                ) from error
            record = {
                "execution_kind": execution_kind,
                "prompt": prompt,
                "response": response,
            }
            if reference_records:
                record["references"] = reference_records
            if step.agent_task:
                record.update(
                    server=step.server_id,
                    tool_calls=calls,
                    produced_files=produced_files,
                )
                if step.cad:
                    record["cad_document"] = {
                        "server_id": cad_document.server_id,
                        **cad_document.document,
                    }
                    record["engineering_result"] = model_result.to_dict()
                    record["input_resource"] = task.input_document
                if step.application:
                    record["engineering_result"] = model_result.to_dict()
                    record["input_resource"] = task.input_resource
                    record["resource_readback"] = task.resource_readback
                if not step.cad:
                    for produced in produced_files:
                        if step.application and produced.get("output_port") in {
                            ex["port"] for ex in step.application.get("exports", [])
                        }:
                            continue  # Named exports already belong to the application result.
                        output = {
                            "task_id": step.id,
                            "task_title": step.title,
                            **produced,
                        }
                        produced_result = file_result(
                            output,
                            Provenance(
                                run_id,
                                step.id,
                                produced.get("output_port") or produced["output_path"],
                            ),
                        )
                        engineering_results.append(produced_result)
                        await emit(
                            "result_ready",
                            task_id=step.id,
                            task_title=step.title,
                            engineering_result=produced_result.to_dict(),
                        )
            for key, kind in step.output_ports:
                if step.application and key == step.application.get(
                    "output_port", "resource"
                ):
                    responses[f"{step.id}.{key}"] = model_result
                    continue
                if step.application:
                    exported = next(
                        (
                            ex
                            for ex in model_result.exports
                            if ex.provenance.output_port == key
                        ),
                        None,
                    )
                    if exported:
                        responses[f"{step.id}.{key}"] = exported
                        continue
                files = (
                    [f for f in produced_files if f.get("output_port") == key]
                    if step.cad and kind == "workspace_file"
                    else produced_files
                )
                if step.cad and kind == "workspace_file" and not files:
                    if any(
                        f"{step.id}.{key}"
                        in (
                            [s.prompt_from, s.cad_from, s.application_from]
                            + [r[1] for r in s.references]
                            + list(s.argument_sources.values())
                        )
                        for s in plan.steps
                    ):
                        raise _invalid(
                            f"{step.title}: the connected file output was not produced.",
                            "Enable the requested native save or export in the producing block.",
                        )
                    continue
                responses[f"{step.id}.{key}"] = (
                    cad_document
                    if step.cad and kind == "cad_model"
                    else (
                        files[0]["output_path"]
                        if step.cad and kind == "workspace_file"
                        else response
                    )
                )
                artifacts_by_output[f"{step.id}.{key}"] = files
        record.update(
            task_id=step.id,
            task_title=step.title,
            output_format=step.output_format,
            output_path=None,
            output_bytes=0,
        )
        records.append(record)
        if not step.cad and not step.application:
            # The response remains usable downstream without a file. Saved files
            # will be attached as representations of this same result below.
            key = step.output_ports[0][0] if step.output_ports else "response"
            result_kind = "structured" if step.output_format == "json" else "text"
            engineering_results.append(
                EngineeringResult(
                    f"{run_id}:{step.id}:{key}",
                    result_kind,
                    step.title,
                    (
                        Representation(
                            "value", f"steps/{step.id}/response", step.output_format
                        ),
                    ),
                    Provenance(run_id, step.id, key),
                )
            )
        await emit(
            "step_completed",
            task_id=step.id,
            task_title=step.title,
            response=response,
            output_format=step.output_format,
        )
        # Preserve completed work when a later task blocks. Indexed publication
        # cannot replace a previous run; overwrite remains deferred until every
        # response validates. Rejected revisions remain in the attempt history.
        if step.save and step.file_policy == "indexed":
            await save_response(step, record)
        if check_report and check_report["verdict"] != "pass":
            if check_report["verdict"] == "needs_input":
                raise _error(
                    "DESIGN_CHECK_NEEDS_INPUT",
                    f"{step.title}: design decisions or inspection evidence are missing.",
                    " ".join(check_report["corrections"]),
                )
            target = plan.revisions.get(step.id)
            count = revision_counts.get(step.id, 0)
            if target is None or count >= step.max_revisions:
                raise _error(
                    "DESIGN_CHECK_REJECTED",
                    f"{step.title}: the design has not passed.",
                    " ".join(check_report["corrections"]),
                )
            revision_counts[step.id] = count + 1
            feedback[target] = check_report
            start = next(
                i for i, candidate in enumerate(plan.steps) if candidate.id == target
            )
            invalidated = {candidate.id for candidate in plan.steps[start : cursor + 1]}
            attempts.extend(records[start:])
            records = records[:start]
            responses = {
                key: value
                for key, value in responses.items()
                if key.split(".")[0] not in invalidated
            }
            artifacts_by_output = {
                key: value
                for key, value in artifacts_by_output.items()
                if key.split(".")[0] not in invalidated
            }
            engineering_results = [
                r
                for r in engineering_results
                if r.provenance.task_id not in invalidated
            ]
            await emit(
                "design_revision",
                task_id=target,
                task_title=plan.steps[start].title,
                revision=count + 1,
                invalidated_task_ids=sorted(invalidated),
                message="Design check requested a corrected CAD revision.",
                report=check_report,
            )
            cursor = start
            continue
        cursor += 1
    # Validate every model response before replacing any previous output.
    outputs = []
    for step, record in zip(
        (step for step in plan.steps if not step.human_review), records, strict=True
    ):
        for produced in record.get("produced_files", []):
            output = {"task_id": step.id, "task_title": step.title, **produced}
            outputs.append(output)
            await emit("output_saved", **output)
        if step.save:
            outputs.append(
                record.get("saved_response") or await save_response(step, record)
            )
    last = (
        outputs[-1]
        if outputs
        else {
            "output_path": "",
            "output_bytes": 0,
            "task_title": records[-1]["task_title"],
            "task_id": records[-1]["task_id"],
        }
    )
    result = {
        "workflow_title": plan.title,
        **last,
        "outputs": outputs,
        "steps": records,
        "run_id": run_id,
        "results": [result.to_dict() for result in engineering_results],
        "revision_attempts": attempts,
    }
    review = next((step for step in plan.steps if step.human_review), None)
    if review:
        if not plan.review_context:
            raise _invalid(
                "Engineer review requires the exact saved workflow and input snapshots."
            )
        producer = review.references[0][1].split(".")[0]
        reviewed_outputs = [
            output for output in outputs if output["task_id"] == producer
        ]
        if len(reviewed_outputs) != 1:
            raise _invalid("Engineer review needs one exact saved document output.")
        result.update(reviewed_outputs[0])
        result["_review_request"] = {
            "task_id": review.id,
            "task_title": review.title,
            "instructions": review.prompt,
            "artifacts": reviewed_outputs,
            "context": plan.review_context,
        }
    return result
