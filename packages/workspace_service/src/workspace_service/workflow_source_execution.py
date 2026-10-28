"""Native execution for the first workspace-owned workflow source capability.

The source file is authoritative: clients provide only its workspace path and
the digest they read. This module reads and validates the stored source before
executing connected AI prompts and saving their declared response files.
"""

from __future__ import annotations

import json
import hashlib
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from pathlib import PurePosixPath
from datetime import datetime, timezone
from core.workflow_step_outcomes import InvalidStepOutcomeError
from core.workflow_instructions import (
    WorkflowInstructionSet,
    WorkflowInstructionOverride,
)

from .workflow_sources import WorkflowSourceStorageError
from .workflow_references import WorkflowReference, allows_binary_file_reference


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


async def require_unattended_completion(step, outcome, emit):
    """A model disposition can fail a step, never create a checkpoint or default.

    MCP tasks retain their existing evidence envelope; plain model adapters carry
    a validated disposition outside the document string. Do not classify document
    prose or question marks as interaction requests.
    """
    if (
        outcome.get("reason") == "input_required"
        or outcome.get("status") == "input_required"
    ):
        code = "INTERACTION_NOT_DECLARED"
        message = (
            f"{step.title}: additional user input was requested in an unattended step."
        )
        correction = (
            "Supply the missing requirement before starting, connect an upstream "
            "producer, or declare a human-input step before this task. Inspect "
            "completed operations before another run; they have not been replayed."
        )
    elif outcome.get("status") in {"blocked", "error"}:
        code = "TASK_BLOCKED" if outcome["status"] == "blocked" else "TASK_FAILED"
        # Model prose stays in bounded recorded diagnostics, never action authority.
        message = f"{step.title}: {str(outcome.get('response', 'the task could not finish'))[:4000]}"
        correction = "Correct the task requirements or server setup before retrying."
    else:
        return
    await emit(
        "step_diagnostic",
        task_id=step.id,
        task_title=step.title,
        code=code,
        message=message,
        correction=correction,
        # Preserve the reported missing dependency without publishing a form,
        # a human response or a generated engineering result.
        diagnostic=str(outcome.get("response", ""))[:4000],
    )
    raise _error(code, message, correction)


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
    external_action: dict | None = None
    expected_file_ports: dict[str, str] = field(default_factory=dict)
    source_contract: str = ""
    reference_inline_max_bytes: int = 1_048_576
    validation: dict | None = None
    validation_sources: tuple[tuple[str, str], ...] = ()
    revision_policy: str = ""
    file_dependencies: dict[str, str | dict] = field(default_factory=dict)
    task_tool_allowlist: tuple[str, ...] = ()
    human_interaction: dict | None = None
    run_path_template: str = ""
    native_image_format: str = ""
    native_image_resolution: dict = field(default_factory=dict)
    model_resolution: dict = field(default_factory=dict)
    instruction_set: dict | None = None
    instruction_override: dict | None = None
    mcp_image_outputs: dict = field(default_factory=dict)
    mcp_reconciliation_contracts: dict = field(default_factory=dict)
    mcp_context_budget_bytes: int | None = None
    mcp_completion_policy: str = "tool_evidence_required"


def _bind_expected_file_ports(step: PromptStep, produced_files: list[dict]) -> None:
    """Bind verified receipts only; a model's response is not a file output."""
    for produced in produced_files:
        port = next(
            (
                key
                for key, path in step.expected_file_ports.items()
                if path == produced["output_path"]
            ),
            None,
        )
        if port:
            produced["output_port"] = port


def _reference_prompt_context(
    name: str,
    reference: WorkflowReference,
    inline_max_bytes: int,
) -> tuple[str, dict[str, object]]:
    """Render a connected text reference without discarding its durable identity."""
    record: dict[str, object] = {
        "path": reference.path,
        "sha256": reference.sha256,
        "kind": "text",
    }
    if reference.run_path_id:
        record.update(
            run_path_version="wright.run-path/1",
            run_id=reference.run_path_id,
            resolved_content_sha256=reference.resolved_sha256,
        )
    size_bytes = (
        len(reference.text.encode()) if reference.run_path_id else reference.size_bytes
    )
    if size_bytes is None:
        size_bytes = len(reference.text.encode())
    if size_bytes <= inline_max_bytes:
        return (
            f"\n\nReference document — {name} ({reference.path}):\n{reference.text}",
            record,
        )
    if reference.run_path_id:
        raise _invalid(
            "A resolved run-path reference exceeds this step's inline budget.",
            "Use a smaller declared template or increase the reviewed bounded reference budget.",
        )
    identity = {
        "path": reference.path,
        "sha256": reference.sha256,
        "size_bytes": size_bytes,
        "contents_inlined": False,
    }
    record.update(size_bytes=size_bytes, contents_inlined=False)
    return (
        f"\n\nReference document identity — {name}:\n"
        + json.dumps(identity, separators=(",", ":")),
        record,
    )


@dataclass(frozen=True)
class PromptWorkflow:
    title: str
    steps: tuple[PromptStep, ...]
    inputs: dict[str, dict]
    revisions: dict[str, str] = field(default_factory=dict)
    review_context: dict = field(default_factory=dict)
    definition_digest: str = ""
    input_snapshot: object | None = None
    run_path_id: str = ""
    run_path_roots: tuple[str, ...] = ()
    instruction_set: dict | None = None
    review_only: bool = False


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
    instruction_set = None
    if "instructions" in workflows[0]["fields"]:
        try:
            instruction_set = WorkflowInstructionSet.model_validate(
                workflows[0]["fields"]["instructions"]
            )
        except (ValueError, TypeError) as error:
            raise _invalid(
                "The saved workflow instructions are incomplete or incompatible.",
                "Inspect the workflow instruction collection, body digests, role bindings "
                "and supported version. Use an explicit migration or default-update diff.",
            ) from error
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
        if (
            block["kind"] == "input"
            and isinstance(settings := fields.get("settings"), dict)
            and (
                "human_interaction" in settings
                or settings.get("authoring_template") == "human-input"
            )
        ):
            raise _invalid(
                f"{block_id}: a declared human interaction must be a task barrier.",
                "Use interaction_input for preparation metadata or a human-input task for a declared runtime response.",
            )
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
            if not isinstance(settings, dict) or (
                settings.get("design_check") is not True
                and settings.get("authoring_template") != "process-validator"
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
        if fields.get("type") == "order" and fields.get("when") is None:
            source_id, target_id = fields.get("from"), fields.get("to")
            if (
                not isinstance(source_id, str)
                or not isinstance(target_id, str)
                or source_id not in blocks
                or target_id not in blocks
                or blocks[target_id]["kind"] != "task"
            ):
                raise _invalid(
                    "An execution-order connection references a missing block."
                )
            dependencies[target_id].add(source_id)
            outgoing[source_id].add(target_id)
            continue
        if fields.get("type") != "item" or fields.get("when") is not None:
            raise _invalid(
                "This version of Wright cannot run one of the connections "
                "that controls which step happens next.",
                "You can still inspect and edit the diagram. Running this workflow "
                "needs support for that connection; keep its required decisions and reviews.",
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
        if settings.get("authoring_template") == "human-input":
            from .workflow_human_input import compile_human_input

            steps.append(compile_human_input(block_id, fields, incoming, blocks))
            continue
        if "human_interaction" in settings:
            raise _invalid(
                f"{title}: a human interaction must use the human-input template.",
                "Declare the input barrier explicitly; do not add questions to an unattended step.",
            )
        if settings.get("authoring_template") == "process-validator":
            from .process_validation.configuration import compile_validator

            steps.append(compile_validator(block_id, fields, incoming, blocks))
            continue
        if settings.get("authoring_template") == "external-action-approval":
            action_kind = settings.get("action_kind")

            def approval_object(name, fallback):
                value = settings.get(name)
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except ValueError:
                        value = None
                return value if value is not None else fallback

            binding = approval_object(
                "approval_binding",
                {
                    "server": settings.get("approval_server"),
                    "tool": settings.get("approval_tool"),
                    "schema": settings.get("approval_schema"),
                },
            )
            destination = approval_object(
                "approval_destination",
                {
                    "kind": settings.get("approval_destination_kind"),
                    "id": settings.get("approval_destination_id"),
                },
            )
            action_settings = approval_object("approval_settings", None)
            action = approval_object("approval_action", None)
            declared_outputs = fields.get("outputs", [])
            receipt_outputs = tuple(
                (port["key"], str(port.get("kind", "engineering_document")))
                for port in declared_outputs
                if isinstance(port, dict) and isinstance(port.get("key"), str)
            )
            receipt_path = ""
            receipt_declaration = settings.get("run_path_template", "")
            if receipt_declaration or "output_filename" in settings:
                from .workflow_run_paths import VERSION

                if (
                    receipt_declaration != VERSION
                    or action_kind == "local_review"
                    or not isinstance(action_settings, dict)
                    or "receipt_path" in action_settings
                    or len(declared_outputs) != 1
                    or len(receipt_outputs) != 1
                    or receipt_outputs[0][1] != "workspace_file"
                    or not receipt_outputs[0][0].endswith("receipt")
                ):
                    raise _invalid(
                        f"{title}: declare one run-scoped receipt output, without a separate approval receipt path."
                    )
                receipt_path = _safe_path(settings.get("output_filename"))
                if PurePosixPath(receipt_path).suffix.lower() != ".json":
                    raise _invalid(f"{title}: the receipt filename must end in .json.")
            valid_receipt_output = not declared_outputs or (
                action_kind != "local_review"
                and isinstance(action_settings, dict)
                and (
                    receipt_path or isinstance(action_settings.get("receipt_path"), str)
                )
                and len(receipt_outputs) == 1
                and receipt_outputs[0][1] == "workspace_file"
                and receipt_outputs[0][0].endswith("receipt")
            )
            if (
                action_kind
                not in {
                    "local_review",
                    "printer_transfer",
                    "supplier_upload_preview",
                    "cart_quote_handoff",
                    "mcp-operation",
                }
                or fields.get("performed_by") != "engineer"
                or fields.get("step_type") != "review"
                or fields.get("tool") is not None
                or fields.get("reusable_step") is not None
                or not valid_receipt_output
                or not dependencies[block_id]
                or not all(
                    isinstance(value, dict) and value
                    for value in (binding, destination, action)
                )
                or not isinstance(action_settings, dict)
                or not (action_settings or receipt_path)
                or action.get("kind") != action_kind
            ):
                raise _invalid(
                    f"{title}: configure an Engineer external-action approval with an upstream dependency and exact binding, destination, settings, and action details."
                )
            instructions = fields.get("instructions", "")
            if not isinstance(instructions, str) or not instructions.strip():
                raise _invalid(f"{title}: enter approval instructions.")
            steps.append(
                PromptStep(
                    block_id,
                    title,
                    instructions,
                    None,
                    tuple(
                        (str(port.get("name", "Document")), source)
                        for port in fields.get("inputs", [])
                        for source in incoming.get(f"{block_id}.{port['key']}", [])
                    ),
                    "json" if receipt_path else "text",
                    receipt_path,
                    False,
                    "overwrite" if receipt_path else "indexed",
                    output_ports=receipt_outputs,
                    expected_files=(receipt_path,) if receipt_path else (),
                    expected_file_ports={receipt_outputs[0][0]: receipt_path}
                    if receipt_path
                    else {},
                    run_path_template=receipt_declaration,
                    external_action={
                        "action_kind": action_kind,
                        "binding": binding,
                        "destination": destination,
                        "settings": action_settings,
                        "action": action,
                    },
                )
            )
            if action_kind == "mcp-operation":
                from .workflow_mcp_operations import operation_step

                operation_step(steps[-1])
            continue
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
                or len(fields.get("inputs", [])) != 1
                or len(refs) != 1
                or not isinstance(instructions, str)
                or not instructions.strip()
                or len(instructions) > 8000
            ):
                raise _invalid(
                    f"{title}: use an Engineer review with one connected document and review instructions."
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
                    output_ports=tuple(
                        (p["key"], str(p.get("kind", "engineering_document")))
                        for p in fields.get("outputs", [])
                    ),
                    human_review=True,
                )
            )
            continue
        is_mcp = settings.get("authoring_template") == "mcp-tool"
        agent_task = settings.get("authoring_template") == "mcp-task"
        native_image = (
            bool(settings.get("image_output"))
            and settings.get("authoring_template") == "ai-prompt"
        )
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
        reference_inline_max_bytes = settings.get(
            "reference_inline_max_bytes", 1_048_576
        )
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
        if len(expected_files) > 32 or (
            expected_files and not (agent_task or is_mcp or native_image)
        ):
            raise _invalid(
                f"{title}: declared tool-created files require an MCP tool or task (maximum 32)."
            )
        file_ports = settings.get("expected_file_ports", {})
        if isinstance(file_ports, str):
            try:
                file_ports = json.loads(file_ports)
            except ValueError:
                raise _invalid(
                    f"{title}: expected file ports must be a JSON object."
                ) from None
        declared_file_ports = {
            p["key"]
            for p in fields.get("outputs", [])
            if p.get("kind") == "workspace_file"
        }
        if not isinstance(file_ports, dict) or any(
            port not in declared_file_ports or path not in expected_files
            for port, path in file_ports.items()
        ):
            raise _invalid(f"{title}: map file outputs to declared expected files.")
        if is_mcp and declared_file_ports and expected_files:
            if not file_ports and len(declared_file_ports) == len(expected_files) == 1:
                file_ports = {next(iter(declared_file_ports)): expected_files[0]}
            if declared_file_ports != set(file_ports):
                raise _invalid(
                    f"{title}: map each file output to one exact expected file."
                )
        image_output = settings.get("image_output", "")
        if image_output:
            try:
                image_output = (
                    json.loads(image_output)
                    if isinstance(image_output, str)
                    else image_output
                )
                image_path = _safe_path(image_output["path"])
                image_port = image_output["port"]
                image_format = image_output["format"]
                extensions = {"png": {".png"}, "jpeg": {".jpg", ".jpeg"}}
                if (
                    not (agent_task or native_image)
                    or cad
                    or application
                    or not isinstance(image_port, str)
                    or image_format not in extensions
                    or PurePosixPath(image_path).suffix.lower()
                    not in extensions[image_format]
                    or set(file_ports) != {image_port}
                    or declared_file_ports != {image_port}
                    or len(fields.get("outputs", [])) != 1
                    or len(expected_files) != 1
                    or (
                        file_ports[image_port] != image_path
                        and not file_ports[image_port].endswith("/" + image_path)
                    )
                    or PurePosixPath(file_ports[image_port]).suffix.lower()
                    not in extensions[image_format]
                ):
                    raise ValueError("Invalid image output")
            except (KeyError, TypeError, ValueError):
                raise _invalid(
                    f"{title}: configure one PNG or JPEG file output on an AI prompt or MCP task.",
                    "Choose a matching .png or .jpg/.jpeg filename before running.",
                ) from None
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
        raw_task_tools = settings.get("mcp_task_tools", [])
        if (
            not isinstance(raw_task_tools, list)
            or len(raw_task_tools) > 32
            or any(not isinstance(name, str) or not name for name in raw_task_tools)
            or len(raw_task_tools) != len(set(raw_task_tools))
            or (raw_task_tools and not agent_task)
        ):
            raise _invalid(f"{title}: select distinct tool names for an MCP task.")
        from .workflow_mcp_image_outputs import validate_image_output_bindings

        mcp_image_outputs = validate_image_output_bindings(
            settings.get("mcp_image_outputs", {}),
            agent_task=agent_task,
            file_ports=file_ports,
            allowed_tools=raw_task_tools,
            incompatible=bool(cad or application or image_output),
        )
        from .workflow_mcp_reconciliation import validate_reconciliation_contracts

        mcp_reconciliation_contracts = validate_reconciliation_contracts(
            settings.get("mcp_reconciliation_contracts", {}),
            agent_task=agent_task and not bool(cad or application),
            allowed_tools=raw_task_tools,
        )
        context_budget = settings.get("mcp_context_budget_bytes")
        if context_budget is not None and (
            not agent_task
            or type(context_budget) is not int
            or not 16_384 <= context_budget <= 1_048_576
        ):
            raise _invalid(
                f"{title}: use a 16384–1048576 byte context budget only for an MCP task."
            )
        completion_policy = settings.get(
            "mcp_completion_policy", "tool_evidence_required"
        )
        if not isinstance(completion_policy, str) or completion_policy not in {
            "tool_evidence_required",
            "supplied_inputs_or_tools",
        }:
            raise _invalid(f"{title}: choose a supported MCP completion policy.")
        if completion_policy == "supplied_inputs_or_tools" and (
            not agent_task
            or cad
            or application
            or design_check
            or expected_files
            or declared_file_ports
            or mcp_image_outputs
            or mcp_reconciliation_contracts
            or settings.get("external_action")
        ):
            raise _invalid(
                f"{title}: supplied-input completion is only available for read-only analysis tasks without tool-produced files or engineering actions."
            )
        revision_policy = settings.get("revision_policy", "")
        if revision_policy not in {"", "create_new_files"} or (
            revision_policy and not (agent_task or native_image)
        ):
            raise _invalid(
                f"{title}: use the create-new file revision policy only for an MCP task."
            )
        if revision_policy and (
            not expected_files
            or not file_ports
            or set(file_ports) != declared_file_ports
            or len(set(file_ports.values())) != len(file_ports)
        ):
            raise _invalid(
                f"{title}: map every declared workspace-file output to one expected file before enabling correction."
            )
        if (
            type(reference_inline_max_bytes) is not int
            or not 1_024 <= reference_inline_max_bytes <= 1_048_576
        ):
            raise _invalid(f"{title}: reference inline limit must be 1 KiB to 1 MiB.")
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
        file_only_result = bool(file_ports) and set(file_ports) == {
            port["key"] for port in fields.get("outputs", [])
        }
        save = (
            not outgoing[block_id]
            and not cad
            and not application
            and not file_only_result
        ) or settings.get("save_output", False)
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
            handled = (
                set(argument_sources.values())
                | set(file_dependencies)
                | ({arguments_from} if arguments_from else set())
            )
            if any(source not in handled for _, source in references):
                raise _invalid(
                    f"{title}: a connected input is not assigned to a tool argument."
                )
        source_contract = settings.get("mcp_source_contract", "")
        if source_contract:
            from .workflow_mcp_source_contracts import SUPPORTED_MCP_SOURCE_CONTRACTS

            if not is_mcp or source_contract not in SUPPORTED_MCP_SOURCE_CONTRACTS:
                raise _invalid(f"{title}: choose a supported MCP source contract.")
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
                expected_file_ports=file_ports,
                source_contract=source_contract,
                reference_inline_max_bytes=reference_inline_max_bytes,
                revision_policy=revision_policy,
                run_path_template=settings.get("run_path_template", ""),
                file_dependencies=file_dependencies,
                task_tool_allowlist=tuple(raw_task_tools),
                native_image_format=image_output["format"] if native_image else "",
                mcp_image_outputs=mcp_image_outputs,
                mcp_reconciliation_contracts=mcp_reconciliation_contracts,
                mcp_context_budget_bytes=context_budget,
                mcp_completion_policy=completion_policy,
            )
        )
    from .workflow_design_check import validate_rework

    reviews = [step for step in steps if step.human_review]
    if reviews:
        for review in reviews:
            producer_id = review.references[0][1].split(".")[0]
            producer = next((step for step in steps if step.id == producer_id), None)
            if producer is None or not (
                (producer.save and producer.file_policy == "indexed")
                or producer.expected_files
                or producer.cad
                or producer.application
                or producer.human_review
            ):
                raise _invalid(
                    "Save the reviewed document as an indexed workspace file before Engineer review."
                )
        if any(step.save and step.file_policy != "indexed" for step in steps):
            raise _invalid(
                "A workflow with Engineer review must use indexed output files to preserve earlier drafts."
            )
        if (
            len(reviews) == 1
            and not outgoing[reviews[0].id]
            and not revisions
            and not any(
                step.tool_name or step.agent_task or step.external_action
                for step in steps
            )
        ):
            # Preserve existing single terminal document-review packages.
            steps = [step for step in steps if not step.human_review] + reviews
        else:
            import hashlib

            steps = [
                replace(
                    step,
                    human_review=False,
                    external_action={
                        "action_kind": "local_review",
                        "binding": {
                            "server": "wright",
                            "tool": "review_artifacts",
                            "schema": hashlib.sha256(
                                b"wright.local_review.v1"
                            ).hexdigest(),
                        },
                        "destination": {"kind": "local_review", "id": "workspace"},
                        "settings": {"review_task_id": step.id},
                        "action": {"kind": "local_review", "mode": "review_only"},
                    },
                )
                if step.human_review
                else step
                for step in steps
            ]
    from .workflow_human_input import validate_human_input_rework

    validate_human_input_rework(steps, revisions)
    validate_rework(steps, revisions)
    # Reject output collisions within one run before calling any model.
    names: dict[str, str] = {}
    for step in steps:
        if step.save or (step.external_action and step.output_path):
            key = step.output_path.casefold()
            if key in names and (
                step.file_policy == "overwrite" or names[key] == "overwrite"
            ):
                raise _invalid(
                    "Two steps would overwrite the same output file.",
                    "Give the steps different filenames or use indexed files for both.",
                )
            names[key] = step.file_policy
    if instruction_set is None and any(
        blocks[step.id]["fields"].get("settings", {}).get("instruction_override")
        is not None
        for step in steps
    ):
        raise _invalid(
            "Step instruction overrides require an embedded workflow instruction collection.",
            "Make the workflow instructions explicit before applying step overrides.",
        )
    if instruction_set is not None:
        bound_roles = {binding.role for binding in instruction_set.bindings}
        retained_steps = []
        for step in steps:
            raw_override = (
                blocks[step.id]["fields"]
                .get("settings", {})
                .get("instruction_override")
            )
            try:
                override = (
                    WorkflowInstructionOverride.model_validate(raw_override)
                    if raw_override is not None
                    else None
                )
            except (ValueError, TypeError) as error:
                raise _invalid(
                    f"{step.title}: the step instruction override is invalid."
                ) from error
            role = (
                "mcp-task"
                if step.agent_task
                else "image-generation"
                if step.native_image_format
                else "workflow-task"
            )
            uses_ai = step.agent_task or (
                not step.tool_name
                and not step.human_interaction
                and not step.human_review
                and not step.external_action
                and not step.validation
            )
            if uses_ai and role not in bound_roles:
                raise _invalid(
                    f"{step.title}: saved instructions do not include the {role} role.",
                    "Explicitly update the workflow's instruction collection before starting.",
                )
            retained_steps.append(
                replace(
                    step,
                    instruction_set=instruction_set.model_dump(mode="json"),
                    instruction_override=override.model_dump(mode="json")
                    if override
                    else None,
                )
            )
        steps = retained_steps
    return PromptWorkflow(
        str(workflows[0]["fields"].get("name", "Workflow")),
        tuple(steps),
        {str(s["id"]): s["fields"] for s in inputs},
        revisions,
        instruction_set=instruction_set.model_dump(mode="json")
        if instruction_set
        else None,
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
        elif kind == "group":
            required = {"name", "purpose", "order"}
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


def _preflight_tools(runtime, steps, *, responses=None):
    selected = tuple(step for step in steps if step.tool_name or step.agent_task)
    if not selected:
        return
    batch = getattr(runtime, "preflight_many", None)
    if callable(batch):
        batch(selected, responses=responses)
        return
    # Preserve the existing contract for separately supplied runtime adapters.
    for step in selected:
        runtime.preflight(step)
        if (
            responses is not None
            and step.tool_name
            and hasattr(runtime, "preflight_values")
        ):
            runtime.preflight_values(step, responses)


async def prepare_prompt_workflow(
    *,
    service,
    workspace_dir: str,
    path: str,
    expected_digest: str,
    tool_runtime=None,
    workspace_id: str | None = None,
    input_snapshot=None,
    run_id=None,
    review_only: bool = False,
) -> tuple[PromptWorkflow, dict[str, object]]:
    """Validate accepted source/inputs; qualify live capabilities for execution.

    The approval owner may prepare an inert review plan using frozen inputs.
    Its files, instructions and criteria are still checked. It cannot execute;
    continuation must prepare again with the default live qualification.
    """
    from dataclasses import replace

    if input_snapshot is not None:
        from core.process_interactions import InputSnapshot
        from pydantic import ValidationError
        from .process_interfaces.errors import ProcessInterfaceError

        try:
            input_snapshot = InputSnapshot.model_validate_json(
                input_snapshot.model_dump_json()
            )
        except (ValidationError, AttributeError, TypeError, ValueError) as error:
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "The input preparation failed its immutable identity check.",
                "Prepare the process's inputs again before starting.",
            ) from error
        if (
            workspace_id != input_snapshot.process.workspace_id
            or path != input_snapshot.process.source_path
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "The prepared inputs belong to another process workspace.",
                "Select this workspace's exact prepared input snapshot.",
            )
        if expected_digest != input_snapshot.process.source_digest:
            raise ProcessInterfaceError(
                "SOURCE_CHANGED",
                "The prepared inputs belong to another source revision.",
                "Prepare values for the current accepted workflow.",
            )
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
    if plan.instruction_set is not None:
        from agent_adapters.workflow_instructions import (
            validate_workflow_instruction_dependencies,
            embedded_asset,
            validate_workflow_helper_instructions,
        )

        saved_instructions = WorkflowInstructionSet.model_validate(plan.instruction_set)

        for step in plan.steps:
            if step.agent_task or (
                not step.tool_name
                and not step.human_interaction
                and not step.human_review
                and not step.external_action
                and not step.validation
            ):
                role = (
                    "mcp-task"
                    if step.agent_task
                    else "image-generation"
                    if step.native_image_format
                    else "workflow-task"
                )
                try:
                    validate_workflow_instruction_dependencies(
                        plan.instruction_set, role, step.instruction_override
                    )
                    for helper_id in (
                        *(("context.task-workspace",) if step.agent_task else ()),
                        *(
                            ("context.mcp-input-completion",)
                            if step.mcp_completion_policy == "supplied_inputs_or_tools"
                            else ()
                        ),
                        *(("validation.design-check",) if step.design_check else ()),
                        *(
                            ("validation.design-revision",)
                            if step.id in plan.revisions.values()
                            else ()
                        ),
                        *(
                            ("context.expected-files",)
                            if step.expected_files and not step.native_image_format
                            else ()
                        ),
                    ):
                        validate_workflow_helper_instructions(
                            step.instruction_set, helper_id
                        )
                    for asset_id in (
                        *(("context.cad",) if step.cad else ()),
                        *(("context.application",) if step.application else ()),
                        *(("validation.feedback",) if plan.revisions else ()),
                    ):
                        asset = embedded_asset(saved_instructions, asset_id)
                        expected_role = (
                            "validation"
                            if asset_id == "validation.feedback"
                            else "resource-context"
                        )
                        if asset.role != expected_role or asset.variables:
                            raise ValueError(
                                "Instruction helper asset has an incompatible role or variable contract"
                            )
                except (ValueError, TypeError) as error:
                    raise _invalid(
                        f"{step.title}: portable instruction dependencies are missing or incompatible.",
                        "Inspect the saved role, policy, formatting and recovery assets. Update explicitly before starting.",
                    ) from error
    from .workflow_run_paths import bind_run_paths, bind_run_input_values

    plan = bind_run_paths(plan, run_id)
    qualified_image_resolutions = {}
    if not review_only and any(step.native_image_format for step in plan.steps):
        capability_reader = getattr(service, "workflow_image_capabilities", None)
        if capability_reader is None:
            raise _invalid(
                "The configured AI image-output connection is unavailable.",
                "Connect an AI adapter with native image output before starting.",
            )
        try:
            capability = await capability_reader()
            if not capability.get("available") or any(
                step.native_image_format not in capability.get("formats", [])
                for step in plan.steps
                if step.native_image_format
            ):
                raise ValueError(
                    "The configured AI connection does not support the requested image format."
                )
            from dataclasses import replace

            plan = replace(
                plan,
                steps=tuple(
                    replace(step, native_image_resolution=capability["resolution"])
                    if step.native_image_format
                    else step
                    for step in plan.steps
                ),
            )
            qualified_image_resolutions = {
                step.id: step.native_image_resolution
                for step in plan.steps
                if step.native_image_format
            }
        except (OSError, ValueError, TimeoutError, KeyError) as error:
            raise _invalid(
                "The configured AI image-output connection is unavailable.",
                "Check the AI connection and its native image capability before starting.",
            ) from error
    if any(step.human_interaction for step in plan.steps) and not getattr(
        service, "process_interfaces", None
    ):
        raise _error(
            "WORKFLOW_HUMAN_INPUT_UNAVAILABLE",
            "This workflow declares human input, but durable input continuation is not available yet.",
            "Use the common view after the declared-input continuation capability is installed.",
        )
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
    metadata_inputs = any(
        "interaction_input" in fields.get("settings", {})
        for fields in plan.inputs.values()
    )
    option_sources = any(
        isinstance(
            metadata := fields.get("settings", {}).get("interaction_input"), dict
        )
        and metadata.get("option_source")
        for fields in plan.inputs.values()
    )
    approved_operations = [
        step
        for step in plan.steps
        if (step.external_action or {}).get("action_kind") == "mcp-operation"
    ]
    if not review_only and (
        any(step.tool_name or step.agent_task for step in plan.steps)
        or option_sources
        or approved_operations
    ):
        if callable(tool_runtime):
            tool_runtime = tool_runtime()
        if tool_runtime is None:
            raise _invalid(
                "MCP execution is unavailable.",
                "Check the MCP server connection and try again.",
            )
        _preflight_tools(tool_runtime, plan.steps)
        if approved_operations:
            from .workflow_mcp_operations import qualify_operation

            for step in approved_operations:
                qualify_operation(tool_runtime, step)
    values = {}
    from .workspace_path import WorkspacePath

    paths = WorkspacePath(workspace_dir)
    for step in plan.steps:
        if step.validation:
            from .process_validation.configuration import ValidatorConfiguration
            from .process_validation.readers.base import ValidationIssue
            from .process_validation.service import default_reader_registry

            try:
                profile = ValidatorConfiguration.model_validate(step.validation).load(
                    workspace_dir
                )
            except (OSError, ValueError) as exc:
                raise _invalid(
                    f"{step.title}: the pinned validation profile is unavailable or changed.",
                    "Select and save a matching profile, baseline and subject roles before running.",
                ) from exc
            if not review_only:
                try:
                    default_reader_registry().qualify_required_readers(profile)
                except ValidationIssue as exc:
                    raise _error(
                        "PROCESS_VALIDATION_CAPABILITY_UNAVAILABLE",
                        f"{step.title}: {exc}",
                        "Restore the required validation reader and evidence method, then check readiness again. Keep the pinned requirements unchanged.",
                    ) from exc
        if step.application and not review_only:
            from .workflow_application_task import validate_application_connection

            validate_application_connection(tool_runtime, step, plan)
        if step.save:
            paths.resolve(step.output_path)
        if step.cad:
            from .workflow_cad import capabilities, list_documents

            if not review_only:
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
                if not review_only and export["format"] not in caps["formats"]:
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
            if not review_only and step.cad["source"] == "session":
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
    converted = None
    if input_snapshot is not None or metadata_inputs:
        from core.process_interactions import ProcessRef
        from .process_interfaces.inputs import prepare_inputs, input_readiness
        from .process_interfaces.errors import ProcessInterfaceError

        if not workspace_id:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "Typed process inputs require a registered workspace identity.",
                "Run this process through its scoped Wright workspace service.",
            )
        if review_only and option_sources and input_snapshot is None:
            raise _invalid(
                "Reviewing provider choices requires this run's frozen input snapshot.",
                "Inspect the recorded inputs; do not substitute current choices for this review.",
            )
        converted = await prepare_inputs(
            service=service,
            workspace_dir=workspace_dir,
            process=input_snapshot.process
            if input_snapshot is not None
            else ProcessRef(
                workspace_id=workspace_id,
                source_path=path,
                source_digest=expected_digest,
            ),
            source=document.source,
            bindings=input_snapshot.bindings if input_snapshot else (),
            snapshot_id=input_snapshot.snapshot_id if input_snapshot else None,
            created_at=input_snapshot.created_at if input_snapshot else None,
            review_snapshots=review_snapshots if review_snapshots else None,
            tool_runtime=tool_runtime,
            review_snapshot=input_snapshot if review_only else None,
        )
        readiness = input_readiness(converted)
        if readiness.state != "ready":
            reason = readiness.reasons[0]
            raise ProcessInterfaceError(reason.code, reason.message, reason.correction)
        if input_snapshot is not None and converted.snapshot != input_snapshot:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The prepared input content no longer matches its frozen snapshot.",
                "Prepare the current exact values before starting this process.",
            )
        plan, values = bind_run_paths(converted.plan, run_id), converted.values
        values = bind_run_input_values(plan, values)
        # Input preparation recompiles the accepted source. Preserve the public
        # adapter qualification just obtained for those exact source step IDs.
        plan = replace(
            plan,
            input_snapshot=converted.snapshot,
            steps=tuple(
                replace(
                    step, native_image_resolution=qualified_image_resolutions[step.id]
                )
                if step.id in qualified_image_resolutions
                else step
                for step in plan.steps
            ),
        )
        if tool_runtime is not None and not review_only:
            connected_values = {
                f"{key}.{port['key']}": (
                    values[key].text
                    if isinstance(values[key], WorkflowReference)
                    and not values[key].image_url
                    and not values[key].file_only
                    else values[key]
                )
                for key, fields in plan.inputs.items()
                for port in fields.get("outputs", [])
                if key in values
            }
            _preflight_tools(tool_runtime, plan.steps, responses=connected_values)
    for key, fields in () if converted is not None else plan.inputs.items():
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
                value = WorkflowReference.from_bytes(
                    path,
                    data,
                    image=image,
                    allow_binary=allows_binary_file_reference(plan.steps, addresses),
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
    values = bind_run_input_values(plan, values)
    plan = replace(plan, definition_digest=expected_digest, review_only=review_only)
    if review_snapshots:
        from dataclasses import replace

        plan = replace(
            plan,
            review_context={
                "source_digest": expected_digest,
                "snapshots": review_snapshots,
                "input_values": {
                    key: (
                        {
                            "path": value.path,
                            "sha256": value.sha256,
                            **(
                                {
                                    "run_path_version": "wright.run-path/1",
                                    "run_id": value.run_path_id,
                                    "resolved_content_sha256": value.resolved_sha256,
                                }
                                if value.run_path_id
                                else {}
                            ),
                        }
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


def _execution_snapshot(
    *,
    input_values,
    responses,
    records,
    engineering_results,
    artifacts_by_output,
    attempts,
    revision_counts,
    feedback,
):
    from .workflow_execution_continuation import encode_value, input_identities

    # Round-tripping here guarantees the checkpoint repository receives plain
    # JSON and the current execution cannot mutate its already sealed state.
    return json.loads(
        json.dumps(
            {
                "input_identities": input_identities(input_values),
                "responses": {
                    key: encode_value(value) for key, value in responses.items()
                },
                "records": records,
                "results": [value.to_dict() for value in engineering_results],
                "artifacts_by_output": artifacts_by_output,
                "revision_attempts": attempts,
                "revision_counts": revision_counts,
                "feedback": feedback,
            },
            allow_nan=False,
        )
    )


def _approval_settings(
    *,
    pending_action: PromptStep,
    plan: PromptWorkflow,
    workspace_dir: str,
) -> dict:
    """Bind human-readable requirements to a local review's exact subject."""
    action = pending_action.external_action or {}
    settings = dict(action.get("settings") or {})
    configured = settings.get("validation_review")
    if action.get("action_kind") != "local_review" or configured is None:
        return settings
    if (
        not isinstance(configured, dict)
        or set(configured) != {"profile_ref", "requirement_ids"}
        or not isinstance(configured.get("requirement_ids"), list)
        or not configured["requirement_ids"]
        or any(not isinstance(item, str) for item in configured["requirement_ids"])
        or len(set(configured["requirement_ids"])) != len(configured["requirement_ids"])
    ):
        raise _invalid(
            f"{pending_action.title}: validation review settings are incomplete.",
            "Pin one validation profile and its exact unique review-required requirement IDs.",
        )

    from core.process_validation import VersionReference
    from .process_validation.configuration import ValidatorConfiguration

    try:
        expected = VersionReference.model_validate(configured["profile_ref"])
        matching = []
        for step in plan.steps:
            if step.validation is None:
                continue
            candidate = ValidatorConfiguration.model_validate(step.validation)
            if candidate.profile.reference == expected:
                matching.append(candidate.load(workspace_dir))
    except (OSError, ValueError, TypeError) as exc:
        raise _invalid(
            f"{pending_action.title}: the pinned validation review profile is unavailable or changed.",
            "Restore the exact profile or update the workflow pins before requesting review.",
        ) from exc
    if not matching:
        raise _invalid(
            f"{pending_action.title}: the pinned validation review profile is not used by this workflow.",
            "Bind the review to the exact profile used by a validator step in this workflow.",
        )
    profile = matching[0]
    review_requirements = {
        requirement.id: requirement
        for requirement in profile.baseline.requirements
        if requirement.review_required
    }
    requested = configured["requirement_ids"]
    if set(requested) != set(review_requirements):
        raise _invalid(
            f"{pending_action.title}: the validation review requirement set does not match the pinned profile.",
            "Review every and only the profile requirements marked review_required.",
        )
    settings["validation_review_requirements"] = [
        review_requirements[requirement_id].model_dump(
            mode="json", include={"id", "text", "scope", "sources"}
        )
        for requirement_id in requested
    ]
    return settings


async def _resolved_approval_settings(
    *,
    pending_action,
    plan,
    workspace_dir,
    service,
    responses=None,
    continuation=None,
    artifacts_by_output=None,
    engineering_results=(),
):
    """Resolve operation arguments using the same durable producer values on resume."""
    if (pending_action.external_action or {}).get("action_kind") != "mcp-operation":
        return _approval_settings(
            pending_action=pending_action, plan=plan, workspace_dir=workspace_dir
        )
    from .workflow_mcp_operations import resolved_operation_settings

    if continuation is not None:
        from .workflow_execution_continuation import decode_value, restore_result

        responses = {
            key: decode_value(value)
            for key, value in continuation.get("responses", {}).items()
        }
        artifacts_by_output = continuation.get("artifacts_by_output", {})
        engineering_results = [
            restore_result(value) for value in continuation.get("results", [])
        ]
    return await resolved_operation_settings(
        pending_action,
        responses or {},
        service=service,
        workspace_dir=workspace_dir,
        artifacts_by_output=artifacts_by_output,
        engineering_results=engineering_results,
    )


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
    continuation=None,
    completed_checkpoint=None,
    execution_context=None,
    run_id=None,
) -> dict:
    if plan.review_only:
        raise _error(
            "WORKFLOW_NOT_READY",
            "A review-only preparation cannot execute workflow steps.",
            "Check current execution readiness before continuing this run.",
        )
    import asyncio
    from uuid import uuid4
    from dataclasses import replace
    from .workflow_results import (
        EngineeringResult,
        Representation,
        Provenance,
        file_representation,
        file_result,
    )

    if any(step.human_interaction for step in plan.steps):
        from .workflow_human_input_runtime import input_runtime_owner

        input_runtime_owner(service, plan)
    run_id = run_id or uuid4().hex
    from .workflow_model_routing import step_requires_model

    if any(step_requires_model(step) for step in plan.steps):
        from .workflow_reasoning_dispatch import resolve_workflow_reasoning_callbacks

        reasoning = resolve_workflow_reasoning_callbacks(
            service,
            workspace_dir=workspace_dir,
            run_id=run_id,
            execution_context=execution_context,
            response=response_generator,
            action=action_generator,
        )
        response_generator, action_generator = reasoning.response, reasoning.action
    from .workflow_run_paths import (
        ATTEMPT_VERSION,
        bind_attempt_paths,
        reserve_run_paths,
        verify_prior_attempt_files,
    )

    reserve_run_paths(plan, workspace_dir, run_id, continuing=continuation is not None)
    engineering_results = []
    validation_application = None
    if any(step.validation for step in plan.steps):
        from .process_validation.process import application_for_workspace

        validation_application = application_for_workspace(service, workspace_dir)

    assumptions_by_step = {}
    instructions_by_step = {}

    async def emit(kind, **data):
        if kind == "instructions_resolved":
            instructions_by_step[data["task_id"]] = data["instructions"]
        if kind == "assumptions_recorded":
            from core.workflow_instructions import WorkflowAssumption

            owner = next(step for step in plan.steps if step.id == data["task_id"])
            permitted_outputs = {key for key, _ in owner.output_ports}
            protected = set(
                (owner.instruction_set or {})
                .get("policy", {})
                .get("protected_requirements", ())
            )
            assumptions = [
                WorkflowAssumption.model_validate(value).model_dump(mode="json")
                for value in data["assumptions"]
            ]
            violations = [
                {
                    "parameter": value["parameter"],
                    "protected_requirement": value["parameter"] in protected,
                    "undeclared_outputs": sorted(
                        set(value["affected_outputs"]) - permitted_outputs
                    ),
                }
                for value in assumptions
                if value["parameter"] in protected
                or not set(value["affected_outputs"]).issubset(permitted_outputs)
            ]
            if violations:
                from .process_interfaces.errors import safe_diagnostic

                if on_event:
                    await on_event(
                        {
                            "kind": "assumptions_rejected",
                            "at": datetime.now(timezone.utc).isoformat(),
                            "task_id": owner.id,
                            "task_title": owner.title,
                            "diagnostic": safe_diagnostic(
                                {
                                    "assumptions": assumptions,
                                    "violations": violations,
                                    "permitted_outputs": sorted(permitted_outputs),
                                }
                            ),
                        }
                    )
                rejected = "; ".join(
                    f"{value['parameter']}: "
                    + (
                        "protected requirement"
                        if value["protected_requirement"]
                        else ""
                    )
                    + (
                        f" undeclared outputs {', '.join(value['undeclared_outputs'])}"
                        if value["undeclared_outputs"]
                        else ""
                    )
                    for value in violations
                )
                raise _error(
                    "WORKFLOW_ASSUMPTION_INVALID",
                    f"{owner.title}: rejected assumptions ({rejected}).",
                    "Keep supplied requirements intact and bind assumptions to "
                    f"this step's declared output ports: {', '.join(sorted(permitted_outputs))}. "
                    "Inspect this run's assumptions_rejected evidence; no question or approval was created.",
                )
            assumptions_by_step[owner.id] = assumptions
        if on_event:
            await on_event(
                {"kind": kind, "at": datetime.now(timezone.utc).isoformat(), **data}
            )
            if kind == "output_saved" and data.get("artifact_role") in {
                "diagnostic",
                "verification",
            }:
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
                        "artifact_role": data["artifact_role"],
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

    async def task_reference(step, source_id):
        try:
            return await document_value(source_id, step.title)
        except WorkflowSourceExecutionError as error:
            await reference_failure(step, error)
            raise

    async def task_file_dependencies(step):
        from .workflow_references import verified_file_dependencies

        try:
            return verified_file_dependencies(step, responses, workspace_dir)
        except WorkflowSourceExecutionError as error:
            await reference_failure(step, error)
            raise

    async def reference_failure(step, error):
        await emit(
            "step_diagnostic",
            task_id=step.id,
            task_title=step.title,
            code=error.code,
            message=str(error),
            correction=error.correction,
        )

    for key, fields in plan.inputs.items():
        for port in fields.get("outputs", []):
            responses[f"{key}.{port['key']}"] = input_values[key]
    records, attempts, revision_counts, feedback = [], [], {}, {}
    cursor = 0
    if continuation is not None:
        from .workflow_execution_continuation import restore_continuation

        restored = await restore_continuation(
            state=continuation,
            checkpoint=completed_checkpoint,
            plan=plan,
            input_values=input_values,
            service=service,
            workspace_dir=workspace_dir,
        )
        run_id = restored["run_id"]
        cursor = restored["cursor"]
        responses = restored["responses"]
        artifacts_by_output = restored["artifacts_by_output"]
        records = restored["records"]
        engineering_results = restored["engineering_results"]
        attempts = restored["attempts"]
        revision_counts = restored["revision_counts"]
        feedback = restored["feedback"]
        execution_context = continuation.get("execution_context")
        released = plan.steps[cursor]
        if released.human_interaction:
            from .workflow_human_input_runtime import input_response_result

            answer = restored["human_response"]
            answered_result, answered_record = input_response_result(
                step=released,
                plan=plan,
                response=answer,
                checkpoint=completed_checkpoint,
            )
            responses[f"{released.id}.{released.human_interaction['output_port']}"] = (
                json.loads(answered_record["response"])
            )
            engineering_results.append(answered_result)
            if validation_application:
                from .process_validation.process import register_outputs

                answered_record["producer_attempt"] = 1 + sum(
                    1 for item in attempts if item["task_id"] == released.id
                )
                register_outputs(
                    validation_application,
                    released,
                    answered_record,
                    run_id,
                    responses,
                    artifacts_by_output,
                    engineering_results,
                )
            records.append(answered_record)
            await emit(
                "step_started",
                task_id=released.id,
                task_title=released.title,
                execution_kind="human_input",
            )
            await emit(
                "result_ready",
                task_id=released.id,
                task_title=released.title,
                engineering_result=answered_result.to_dict(),
            )
            await emit(
                "step_completed",
                task_id=released.id,
                task_title=released.title,
                checkpoint_id=answer.checkpoint_id,
                response_id=answer.response_id,
                response=answered_record["response"],
                output_format="json",
            )
        else:
            receipt_files = (
                completed_checkpoint.get("external_action", {}).get("evidence") or {}
            ).get("produced_files", [])
            verified_receipts = []
            if receipt_files:
                for receipt in receipt_files:
                    path = _safe_path(receipt.get("output_path"))
                    raw = await service.files.read_reference(workspace_dir, path)
                    if (
                        not raw
                        or len(raw) != receipt.get("output_bytes")
                        or hashlib.sha256(raw).hexdigest() != receipt.get("sha256")
                    ):
                        raise _invalid(
                            "The completed handoff receipt changed before continuation."
                        )
                    declared_receipt_ports = [
                        port
                        for port, kind in released.output_ports
                        if kind == "workspace_file"
                    ]
                    port = receipt.get("output_port") or "receipt"
                    if (
                        port not in declared_receipt_ports
                        and len(declared_receipt_ports) == 1
                    ):
                        port = declared_receipt_ports[0]
                    output = {
                        **receipt,
                        "output_port": port,
                        "task_id": released.id,
                        "task_title": released.title,
                        "artifact_role": "external_action_receipt",
                    }
                    receipt_result = file_result(
                        output,
                        Provenance(run_id, released.id, port),
                    )
                    engineering_results.append(receipt_result)
                    verified_receipts.append(output)
                    if (port, "workspace_file") in released.output_ports:
                        address = f"{released.id}.{port}"
                        responses[address] = receipt_result
                        artifacts_by_output[address] = [output]
                    await emit(
                        "result_ready",
                        task_id=released.id,
                        task_title=released.title,
                        engineering_result=receipt_result.to_dict(),
                    )
            # A review may expose the same exact artifact to downstream tasks. The
            # approval never creates a replacement engineering artifact.
            if (
                released.external_action["action_kind"] == "local_review"
                and released.references
            ):
                approved_source = released.references[0][1]
                for port, _ in released.output_ports:
                    responses[f"{released.id}.{port}"] = responses[approved_source]
                    artifacts_by_output[f"{released.id}.{port}"] = (
                        artifacts_by_output.get(approved_source, [])
                    )
            approval_record = {
                "task_id": released.id,
                "task_title": released.title,
                "execution_kind": "approval",
                "output_format": "text",
                "output_path": None,
                "output_bytes": 0,
                "response": "Approved",
                "checkpoint_id": completed_checkpoint["checkpoint_id"],
                "subject_digest": completed_checkpoint["subject_digest"],
                "review_authority": {
                    "action_kind": released.external_action["action_kind"],
                    "settings": released.external_action["settings"],
                    "actor": completed_checkpoint.get("actor"),
                    "reason": completed_checkpoint.get("reason"),
                    "subject": completed_checkpoint.get("subject"),
                    "subject_digest": completed_checkpoint["subject_digest"],
                    "checkpoint_id": completed_checkpoint["checkpoint_id"],
                },
                "external_action": completed_checkpoint["external_action"],
                "produced_files": verified_receipts,
            }
            if validation_application:
                approval_record["producer_attempt"] = 1 + sum(
                    1 for item in attempts if item["task_id"] == released.id
                )
            records.append(approval_record)
            if validation_application:
                from .process_validation.process import register_outputs

                register_outputs(
                    validation_application,
                    released,
                    approval_record,
                    run_id,
                    responses,
                    artifacts_by_output,
                    engineering_results,
                )
            await emit(
                "step_completed",
                task_id=released.id,
                task_title=released.title,
                checkpoint_id=completed_checkpoint["checkpoint_id"],
                response="Approved",
                output_format="text",
            )
        cursor += 1
    while cursor < len(plan.steps):
        if (
            tool_runtime is not None
            and getattr(tool_runtime, "_integration_file_copy_authority", None)
            is not None
        ):
            tool_runtime._verified_copy_sources = tuple(engineering_results)
        step = plan.steps[cursor]
        producer_attempt = 1 + sum(1 for item in attempts if item["task_id"] == step.id)
        declared_step = step
        if step.run_path_template == ATTEMPT_VERSION:
            await asyncio.to_thread(
                verify_prior_attempt_files, step, attempts, workspace_dir
            )
            step = bind_attempt_paths(step, producer_attempt, workspace_dir)
        assumptions_by_step.pop(step.id, None)
        instructions_by_step.pop(step.id, None)
        if step.human_interaction:
            from .workflow_human_input_runtime import (
                evaluate_input_condition,
                input_skip_result,
            )

            evaluation = evaluate_input_condition(step=step, responses=responses)
            if evaluation is not None:
                await emit(
                    "input_condition_evaluated",
                    task_id=step.id,
                    task_title=step.title,
                    evaluation=evaluation.model_dump(mode="json"),
                )
                if evaluation.decision == "skip":
                    skipped_result, skipped_record = input_skip_result(
                        step=step,
                        plan=plan,
                        run_id=run_id,
                        evaluation=evaluation,
                        responses=responses,
                    )
                    responses[f"{step.id}.{step.human_interaction['output_port']}"] = (
                        json.loads(skipped_record["response"])
                    )
                    engineering_results.append(skipped_result)
                    if validation_application:
                        from .process_validation.process import register_outputs

                        skipped_record["producer_attempt"] = 1 + sum(
                            1 for item in attempts if item["task_id"] == step.id
                        )
                        register_outputs(
                            validation_application,
                            step,
                            skipped_record,
                            run_id,
                            responses,
                            artifacts_by_output,
                            engineering_results,
                        )
                    records.append(skipped_record)
                    await emit(
                        "step_started",
                        task_id=step.id,
                        task_title=step.title,
                        execution_kind="human_input_skipped",
                    )
                    await emit(
                        "result_ready",
                        task_id=step.id,
                        task_title=step.title,
                        engineering_result=skipped_result.to_dict(),
                    )
                    await emit(
                        "step_completed",
                        task_id=step.id,
                        task_title=step.title,
                        response=skipped_record["response"],
                        output_format="json",
                        condition_evaluation=evaluation.model_dump(mode="json"),
                    )
                    cursor += 1
                    continue
            break  # Seal the declared response subject; never call an AI at this cursor.
        if step.human_review:
            break  # Terminal review is persisted by the run recorder after all outputs are sealed.
        if step.external_action:
            break  # The recorder seals an exact durable approval checkpoint below.
        check_report = None
        delivered_feedback = None
        if step.validation:
            from .process_validation.process import execute_validator

            response, check_report, evidence = await execute_validator(
                validation_application,
                step,
                records=records,
                run_id=run_id,
                revision=revision_counts.get(step.id, 0),
                service=service,
                workspace_dir=workspace_dir,
                emit=emit,
            )
            record = {
                "execution_kind": "validator",
                "prompt": "",
                "response": response,
                "validation": check_report,
                "produced_files": [evidence],
            }
            for key, _ in step.output_ports:
                responses[f"{step.id}.{key}"] = response
                artifacts_by_output[f"{step.id}.{key}"] = [evidence]
        elif step.tool_name:
            if tool_runtime is None:
                raise _invalid(f"{step.title}: MCP execution is unavailable.")
            file_dependency_records = await task_file_dependencies(step)
            tool_values = {
                key: value.text
                if isinstance(value, WorkflowReference) and not value.image_url
                else value
                for key, value in responses.items()
            }
            reference_records = file_dependency_records
            for source_id in set(step.argument_sources.values()) | (
                {step.arguments_from} if step.arguments_from else set()
            ):
                value = responses[source_id]
                # Whole-argument inputs are document JSON. Legacy CAD scalar
                # file sockets keep their path semantics for exact tool calls.
                if source_id == step.arguments_from or isinstance(
                    value, EngineeringResult
                ):
                    value = await task_reference(step, source_id)
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
            from .workflow_mcp_source_contracts import validate_mcp_source_contract

            source_contract_receipt = validate_mcp_source_contract(
                step, workspace_dir, arguments
            )
            if source_contract_receipt is not None:
                await emit(
                    "stage_contract_validated",
                    task_id=step.id,
                    task_title=step.title,
                    contract=source_contract_receipt,
                )
            from .workflow_references import snapshot_task_files, verify_task_files

            prior_files = snapshot_task_files(workspace_dir, step.expected_files)
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
            produced_files = verify_task_files(
                workspace_dir, step.expected_files, prior_files
            )
            _bind_expected_file_ports(step, produced_files)
            for produced in produced_files:
                port = produced.get("output_port")
                produced_result = file_result(
                    {"task_id": step.id, "task_title": step.title, **produced},
                    Provenance(run_id, step.id, port or produced["output_path"]),
                )
                engineering_results.append(produced_result)
                await emit(
                    "result_ready",
                    task_id=step.id,
                    task_title=step.title,
                    engineering_result=produced_result.to_dict(),
                )
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
                "produced_files": produced_files,
            }
            if reference_records:
                record["references"] = reference_records
            for key, kind in step.output_ports:
                mapped = [
                    item for item in produced_files if item.get("output_port") == key
                ]
                if mapped:
                    responses[f"{step.id}.{key}"] = file_result(
                        mapped[0], Provenance(run_id, step.id, key)
                    )
                    artifacts_by_output[f"{step.id}.{key}"] = mapped
                else:
                    responses[f"{step.id}.{key}"] = (
                        text if kind == "text" else structured
                    )
                    artifacts_by_output[f"{step.id}.{key}"] = produced_files
        else:
            images = []
            reference_records = await task_file_dependencies(step)
            file_context = {
                record["source_port"]: record for record in reference_records
            }
            prompt = (
                await task_reference(step, step.prompt_from)
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
            if not isinstance(prompt, str):
                from core.process_validation import canonical_json

                prompt = canonical_json(prompt)
            for name, source_id in step.references:
                if source_id in file_context:
                    prompt += (
                        f"\n\nVerified tool file dependency — {name} (contents are not inlined):\n"
                        + json.dumps(file_context[source_id])
                    )
                    continue
                reference = await task_reference(step, source_id)
                if isinstance(reference, WorkflowReference):
                    if reference.file_only:
                        raise _invalid(
                            f"{step.title}: this file cannot be read as reference text.",
                            "Connect it to an application that imports this format.",
                        )
                    if reference.image_url:
                        reference_records.append(
                            {
                                "path": reference.path,
                                "sha256": reference.sha256,
                                "kind": "image",
                            }
                        )
                        images.append(reference.image_url)
                        prompt += f"\n\nReference image — {name}: {reference.path} (attached image)"
                    else:
                        context, reference_record = _reference_prompt_context(
                            name,
                            reference,
                            step.reference_inline_max_bytes,
                        )
                        reference_records.append(reference_record)
                        prompt += context
                else:
                    if not isinstance(reference, str):
                        from core.process_validation import canonical_json

                        reference = canonical_json(reference)
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
                from agent_adapters.workflow_instructions import (
                    workflow_helper_instructions,
                )

                prompt += "\n\n" + workflow_helper_instructions(
                    step.instruction_set,
                    "context.task-workspace",
                    variables={"workspace_dir": workspace_dir},
                )
            if step.id in feedback:
                feedback_state = feedback[step.id]
                if feedback_state.get("kind") == "process_validation":
                    from core.process_validation import RepairFeedback, canonical_digest
                    from .process_validation.feedback import feedback_prompt

                    packet = RepairFeedback.model_validate(feedback_state["packet"])
                    delivered_feedback = packet.model_dump(mode="json")
                    prompt += "\n\n" + feedback_prompt(
                        packet, instruction_set=step.instruction_set
                    )
                    await emit(
                        "validation_feedback_delivered",
                        task_id=step.id,
                        task_title=step.title,
                        target_step_id=step.id,
                        assessment_id=packet.assessment_id,
                        assessment_digest=packet.assessment_digest,
                        feedback_digest=canonical_digest(packet),
                        remaining_revisions=packet.remaining_revisions,
                        complete_result_ref=packet.complete_result_ref,
                    )
                else:
                    from agent_adapters.workflow_instructions import (
                        workflow_design_revision_feedback,
                    )

                    try:
                        prompt += "\n\n" + workflow_design_revision_feedback(
                            feedback_state, instruction_set=step.instruction_set
                        )
                    except ValueError as error:
                        raise _invalid(
                            f"{step.title}: saved design revision guidance is unavailable or exceeds its bounded feedback contract.",
                            "Inspect the saved design-revision resource and complete check report before starting a new run.",
                        ) from error
            if step.design_check:
                from agent_adapters.workflow_instructions import (
                    workflow_helper_instructions,
                )

                prompt += "\n\n" + workflow_helper_instructions(
                    step.instruction_set, "validation.design-check"
                )
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
                external_files = tuple(
                    path
                    for path in step.expected_files
                    if path
                    not in {
                        step.expected_file_ports[port]
                        for port in step.mcp_image_outputs
                    }
                )
                if not step.native_image_format and external_files:
                    from agent_adapters.workflow_instructions import (
                        workflow_helper_instructions,
                    )

                    prompt += "\n\n" + workflow_helper_instructions(
                        step.instruction_set,
                        "context.expected-files",
                        variables={"files": ", ".join(external_files)},
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
                        captured_images = []
                        response, calls = await tool_runtime.run_task(
                            step,
                            prompt,
                            action_generator,
                            emit,
                            images=images,
                            **(
                                {"captured_images": captured_images}
                                if step.mcp_image_outputs
                                else {}
                            ),
                        )
                        if step.mcp_image_outputs:
                            from .workflow_mcp_image_outputs import (
                                publish_image_outputs,
                            )

                            image_receipts = await publish_image_outputs(
                                service, workspace_dir, step, captured_images
                            )
                            await emit(
                                "mcp_images_saved",
                                task_id=step.id,
                                task_title=step.title,
                                images=image_receipts,
                            )
                    if step.run_path_template == ATTEMPT_VERSION:
                        await asyncio.to_thread(
                            verify_prior_attempt_files, step, attempts, workspace_dir
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
                        _bind_expected_file_ports(step, produced_files)
                else:
                    if step.instruction_set is not None:
                        prompt += "\n\nwright_step_context: " + json.dumps(
                            {
                                "step_id": step.id,
                                "outputs": [
                                    {"output_id": key, "kind": kind}
                                    for key, kind in step.output_ports
                                ],
                                "protected_requirement_identifiers": list(
                                    step.instruction_set.get("policy", {}).get(
                                        "protected_requirements", ()
                                    )
                                ),
                            },
                            sort_keys=True,
                        )

                    async def record_invocation(invocation):
                        await emit(
                            "model_invocation",
                            task_id=step.id,
                            task_title=step.title,
                            invocation=invocation,
                        )

                    instruction_arguments = (
                        {
                            "instruction_set": step.instruction_set,
                            "instruction_override": step.instruction_override,
                            "invocation_observer": record_invocation,
                        }
                        if step.instruction_set is not None
                        else {}
                    )
                    if step.model_resolution:
                        instruction_arguments["expected_resolution"] = (
                            step.model_resolution
                        )
                        instruction_arguments.setdefault(
                            "invocation_observer", record_invocation
                        )
                    generated = (
                        await response_generator(
                            prompt,
                            f"image-{step.native_image_format}",
                            images=images,
                            expected_resolution=step.native_image_resolution,
                            **instruction_arguments,
                        )
                        if step.native_image_format
                        else (
                            await response_generator(
                                prompt,
                                step.output_format,
                                images=images,
                                **instruction_arguments,
                            )
                            if images
                            else await response_generator(
                                prompt, step.output_format, **instruction_arguments
                            )
                        )
                    )
                    for invocation in (
                        getattr(generated, "wright_invocations", ())
                        if not instruction_arguments
                        else ()
                    ):
                        await emit(
                            "model_invocation",
                            task_id=step.id,
                            task_title=step.title,
                            invocation=invocation,
                        )
                    resolved_instructions = getattr(
                        generated, "wright_instructions", None
                    )
                    if resolved_instructions is not None:
                        await emit(
                            "instructions_resolved",
                            task_id=step.id,
                            task_title=step.title,
                            instructions=resolved_instructions,
                        )
                    assumptions = getattr(generated, "wright_assumptions", ())
                    if assumptions:
                        from core.workflow_instructions import WorkflowAssumption

                        retained_assumptions = [
                            WorkflowAssumption.model_validate(value).model_dump(
                                mode="json"
                            )
                            for value in assumptions
                        ]
                        if (
                            not isinstance(resolved_instructions, dict)
                            or resolved_instructions.get("assumption_policy")
                            != "document_reasonable"
                        ):
                            raise _invalid(
                                f"{step.title}: assumptions are outside the saved instruction policy."
                            )
                        await emit(
                            "assumptions_recorded",
                            task_id=step.id,
                            task_title=step.title,
                            assumptions=retained_assumptions,
                        )
                    usage = getattr(generated, "wright_usage", None)
                    if isinstance(usage, dict):
                        await emit(
                            "model_usage",
                            task_id=step.id,
                            task_title=step.title,
                            usage=usage,
                        )
                    outcome = getattr(generated, "wright_outcome", None)
                    if outcome is not None:
                        from core.workflow_step_outcomes import UnattendedStepOutcome

                        try:
                            disposition = UnattendedStepOutcome.model_validate(outcome)
                            if disposition.response != generated:
                                raise ValueError()
                        except (TypeError, ValueError):
                            raise _invalid(
                                f"{step.title}: the unattended model disposition is invalid.",
                                "Inspect the model adapter and prepared step instructions before retrying.",
                            ) from None
                        await require_unattended_completion(
                            step, disposition.model_dump(mode="json"), emit
                        )
                    response = validate_response(generated, step.output_format)
                    if step.native_image_format:
                        image = getattr(generated, "wright_image", None)
                        if (
                            not isinstance(image, dict)
                            or image.get("format") != step.native_image_format
                            or not isinstance(image.get("content"), bytes)
                        ):
                            raise ValueError(
                                "The AI connection did not return the declared image bytes."
                            )
                        from .workflow_references import (
                            image_media_type,
                            verify_task_files,
                        )

                        image_path = step.expected_files[0]
                        # Validate format before publishing; the shared file verifier checks dimensions/digest.
                        from .workflow_mcp_images import _dimensions

                        media = image_media_type(image_path, image["content"][:16])
                        width, height = _dimensions(image["content"], media)
                        if (
                            not 0 < width <= 4096
                            or not 0 < height <= 4096
                            or len(image["content"]) > 12 * 1024 * 1024
                        ):
                            raise ValueError(
                                "The AI image exceeds the supported output bounds."
                            )
                        actual = await service.files.write_generated_bytes(
                            workspace_dir, image_path, image["content"], "indexed"
                        )
                        if actual != image_path:
                            raise ValueError(
                                "The image output path was already used. Inspect the recorded run before retrying."
                            )
                        produced_files = verify_task_files(
                            workspace_dir, step.expected_files
                        )
                        _bind_expected_file_ports(step, produced_files)
            except TimeoutError as error:
                raise _error(
                    "MODEL_TIMEOUT",
                    str(error),
                    "Retry when the model is less busy or request a shorter response. Completed steps and files have been preserved.",
                ) from error
            except InvalidStepOutcomeError as error:
                raise _error(
                    "MODEL_OUTCOME_INVALID",
                    f"{step.title}: the model returned no valid unattended-step disposition.",
                    "Inspect the prepared instructions and model response. No user interaction or output was accepted; completed operations have not been replayed.",
                ) from error
            except ValueError as error:
                raise _error(
                    "MODEL_UNAVAILABLE",
                    str(error),
                    "Inspect this run's recorded tool outcomes and model configuration before recovery. "
                    "Completed external operations are preserved; do not repeat them to recover a response.",
                ) from error
            record = {
                "execution_kind": execution_kind,
                "prompt": prompt,
                "response": response,
            }
            if step.id in assumptions_by_step:
                record["assumptions"] = assumptions_by_step[step.id]
            if step.id in instructions_by_step:
                record["instructions"] = instructions_by_step[step.id]
            if step.instruction_set is not None:
                record["instruction_set_digest"] = (
                    WorkflowInstructionSet.model_validate(step.instruction_set).digest
                )
            if reference_records:
                record["references"] = reference_records
            if step.agent_task or step.native_image_format:
                record.update(
                    produced_files=produced_files,
                )
                if step.agent_task:
                    record.update(server=step.server_id, tool_calls=calls)
                else:
                    record["image_generation"] = image.get("provenance", {})
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
                if key in step.expected_file_ports:
                    mapped = [
                        item
                        for item in produced_files
                        if item.get("output_port") == key
                    ]
                    if len(mapped) != 1:
                        raise _invalid(
                            f"{step.title}: the named file output {key} was not produced.",
                            "Create the exact expected file before continuing.",
                        )
                    responses[f"{step.id}.{key}"] = file_result(
                        mapped[0], Provenance(run_id, step.id, key)
                    )
                    artifacts_by_output[f"{step.id}.{key}"] = mapped
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
                            + list(s.file_dependencies)
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
                        file_result(files[0], Provenance(run_id, step.id, key))
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
        if step.run_path_template == ATTEMPT_VERSION:
            record["file_attempt_binding"] = {
                "version": ATTEMPT_VERSION,
                "run_id": run_id,
                "producer_attempt": producer_attempt,
                "declared_files": list(declared_step.expected_files),
                "resolved_files": list(step.expected_files),
            }
        if delivered_feedback is not None:
            record["repair_feedback"] = delivered_feedback
        if validation_application:
            record["producer_attempt"] = 1 + sum(
                1 for item in attempts if item["task_id"] == step.id
            )
        records.append(record)
        if not step.cad and not step.application:
            # The response remains usable downstream without a file. Saved files
            # will be attached as representations of this same result below.
            key = step.output_ports[0][0] if step.output_ports else "response"
            if key in step.expected_file_ports:
                # Do not reuse a named file result's ID for the task summary.
                # All-file producers still retain their response for diagnostics.
                key = next(
                    (
                        port
                        for port, _ in step.output_ports
                        if port not in step.expected_file_ports
                    ),
                    "__task_response",
                )
            result_kind = "structured" if step.output_format == "json" else "text"
            engineering_results.append(
                EngineeringResult(
                    f"{run_id}:{step.id}:{key}",
                    result_kind,
                    step.title,
                    (
                        Representation(
                            "value",
                            f"steps/{step.id}/response",
                            step.output_format,
                            sha256=hashlib.sha256(response.encode("utf-8")).hexdigest(),
                            size_bytes=len(response.encode("utf-8")),
                        ),
                    ),
                    Provenance(run_id, step.id, key),
                    artifact_role="verification"
                    if step.validation
                    or all(
                        key in step.expected_file_ports for key, _ in step.output_ports
                    )
                    else "deliverable",
                )
            )
        # Retain only file dependencies verified by Wright before dispatch.
        # This records submitted inputs, not provider-internal consumption.
        # Persist on the new record so continuation never infers evidence for
        # older outputs from current files or newly installed code.
        record["verified_file_input_digests"] = sorted(
            {
                item["sha256"]
                for item in record.get("references", [])
                if item.get("kind") == "workspace_file"
                and item.get("source_port") in step.file_dependencies
            }
        )
        if validation_application:
            from .process_validation.process import register_outputs

            register_outputs(
                validation_application,
                step,
                record,
                run_id,
                responses,
                artifacts_by_output,
                engineering_results,
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
            if check_report["verdict"] == "error":
                raise _error(
                    "PROCESS_VALIDATION_ERROR",
                    f"{step.title}: validation could not complete because a reader or evaluator failed.",
                    "Inspect the saved assessment and restore the validator before retrying the producer.",
                )
            if check_report["verdict"] == "needs_input":
                raise _error(
                    "PROCESS_VALIDATION_NEEDS_INPUT"
                    if step.validation
                    else "DESIGN_CHECK_NEEDS_INPUT",
                    f"{step.title}: validation needs additional evidence, capability or review."
                    if step.validation
                    else f"{step.title}: design decisions or inspection evidence are missing.",
                    " ".join(check_report["corrections"]),
                )
            target = plan.revisions.get(step.id)
            count = revision_counts.get(step.id, 0)
            if target is None:
                raise _error(
                    "PROCESS_VALIDATION_REJECTED"
                    if step.validation
                    else "DESIGN_CHECK_REJECTED",
                    f"{step.title}: the output has not passed validation."
                    if step.validation
                    else f"{step.title}: the design has not passed.",
                    " ".join(check_report["corrections"]),
                )
            feedback_state = feedback.get(target)
            feedback_packet_digest = None
            if step.validation:
                from core.process_validation import canonical_digest
                from .process_validation.feedback import (
                    build_feedback,
                    repair_fingerprint,
                )

                assessment = validation_application.repository.assessment(
                    validation_application.workspace_id,
                    check_report["assessment_id"],
                )
                fingerprint = repair_fingerprint(assessment)
                if (
                    feedback_state
                    and feedback_state.get("kind") == "process_validation"
                    and feedback_state.get("fingerprint") == fingerprint
                ):
                    raise _error(
                        "PROCESS_VALIDATION_NO_PROGRESS",
                        f"{step.title}: the corrected output and measured defects did not change.",
                        "Inspect the complete assessment and revise the producer instructions or obtain the missing capability before starting a new run.",
                    )
            if count >= step.max_revisions:
                if step.validation:
                    await emit(
                        "validation_exhausted",
                        task_id=step.id,
                        task_title=step.title,
                        status="exhausted",
                        revision=count,
                        remaining_revisions=0,
                        assessment_id=check_report["assessment_id"],
                        assessment_digest=check_report["assessment_digest"],
                        complete_result_ref=f"wright://workspace/{validation_application.workspace_id}/validation/{check_report['assessment_id']}",
                        message="The configured correction budget is exhausted; downstream work remains held.",
                    )
                raise _error(
                    "PROCESS_VALIDATION_REJECTED"
                    if step.validation
                    else "DESIGN_CHECK_REJECTED",
                    f"{step.title}: the output has not passed validation."
                    if step.validation
                    else f"{step.title}: the design has not passed.",
                    "The configured revision budget is exhausted. "
                    + " ".join(check_report["corrections"]),
                )
            revision_counts[step.id] = count + 1
            if step.validation:
                try:
                    packet = build_feedback(
                        assessment,
                        target_step_id=target,
                        remaining_revisions=step.max_revisions - count,
                        instruction_set=next(
                            producer.instruction_set
                            for producer in plan.steps
                            if producer.id == target
                        ),
                    )
                except ValueError as exc:
                    raise _error(
                        "PROCESS_VALIDATION_REJECTED",
                        f"{step.title}: findings cannot be routed safely to the configured producer.",
                        str(exc),
                    ) from exc
                feedback[target] = {
                    "kind": "process_validation",
                    "packet": packet.model_dump(mode="json"),
                    "fingerprint": fingerprint,
                }
                feedback_packet_digest = canonical_digest(packet)
            else:
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
                message=(
                    "Validation requested a corrected output revision."
                    if step.validation
                    else "Design check requested a corrected CAD revision."
                ),
                report=check_report,
                remaining_revisions=step.max_revisions - count - 1,
                feedback_digest=feedback_packet_digest,
            )
            cursor = start
            continue
        cursor += 1
    # Validate every model response before replacing any previous output.
    outputs = []
    executed_steps = [
        next(step for step in plan.steps if step.id == record["task_id"])
        for record in records
    ]
    for step, record in zip(executed_steps, records, strict=True):
        for produced in record.get("produced_files", []):
            output = {"task_id": step.id, "task_title": step.title, **produced}
            outputs.append(output)
            await emit("output_saved", **output)
        if step.save:
            outputs.append(
                record.get("saved_response") or await save_response(step, record)
            )
    pending_action = (
        plan.steps[cursor]
        if cursor < len(plan.steps) and plan.steps[cursor].external_action
        else None
    )
    last = (
        outputs[-1]
        if outputs
        else records[-1]
        if records
        else {
            "output_path": "",
            "output_bytes": 0,
            "task_title": pending_action.title if pending_action else plan.title,
            "task_id": pending_action.id if pending_action else "",
        }
    )
    result = {
        "workflow_title": plan.title,
        **last,
        "output_path": last.get("output_path") or "",
        "outputs": outputs,
        "steps": records,
        "run_id": run_id,
        "results": [result.to_dict() for result in engineering_results],
        "revision_attempts": attempts,
    }
    if cursor < len(plan.steps) and plan.steps[cursor].human_interaction:
        from .workflow_human_input_runtime import input_checkpoint_request

        result["_input_request"] = input_checkpoint_request(
            plan=plan,
            step=plan.steps[cursor],
            run_id=run_id,
            cursor=cursor,
            execution_context=execution_context,
            input_values=input_values,
            responses=responses,
            records=records,
            engineering_results=engineering_results,
            artifacts_by_output=artifacts_by_output,
            attempts=attempts,
            revision_counts=revision_counts,
            feedback=feedback,
        )
    review = (
        plan.steps[cursor]
        if cursor < len(plan.steps) and plan.steps[cursor].human_review
        else None
    )
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
    if pending_action:

        def digest_input(value):
            from .workflow_execution_continuation import input_identities

            return input_identities({"value": value})["value"]

        artifact_digests = sorted(
            {
                representation.sha256
                for engineering_result in engineering_results
                for representation in (
                    *engineering_result.representations,
                    *(
                        rep
                        for exported in engineering_result.exports
                        for rep in exported.representations
                    ),
                )
                if representation.sha256
            }
        )
        artifact_files = sorted(
            (
                {"path": representation.location, "sha256": representation.sha256}
                for engineering_result in engineering_results
                for representation in (
                    *engineering_result.representations,
                    *(
                        rep
                        for exported in engineering_result.exports
                        for rep in exported.representations
                    ),
                )
                if representation.kind == "workspace_file" and representation.sha256
            ),
            key=lambda item: item["path"],
        )
        # A workflow may explicitly opt into handing off supplied files without
        # regenerating them. Seal only connected frozen references; approval and
        # continuation recheck their exact bytes and all existing effect authority.
        from .workflow_references import is_artifact_approval

        if is_artifact_approval(pending_action):
            from .workflow_execution_continuation import approval_input_files

            reviewed_inputs = approval_input_files(pending_action, input_values)
            artifact_digests = sorted(
                set(artifact_digests) | set(reviewed_inputs.values())
            )
            artifact_files = sorted(
                (
                    {"path": path, "sha256": sha}
                    for path, sha in {
                        **{item["path"]: item["sha256"] for item in artifact_files},
                        **reviewed_inputs,
                    }.items()
                ),
                key=lambda item: item["path"],
            )
        if not plan.definition_digest or not artifact_digests:
            raise _invalid(
                f"{pending_action.title}: exact source and artifact digests are required before approval."
            )
        action = pending_action.external_action
        subject = {
            "definition_digest": plan.definition_digest,
            "input_digests": sorted(
                digest_input(value) for value in input_values.values()
            ),
            "artifact_digests": artifact_digests,
            "binding": action["binding"],
            "destination": action["destination"],
            "settings": await _resolved_approval_settings(
                pending_action=pending_action,
                plan=plan,
                workspace_dir=workspace_dir,
                service=service,
                responses=responses,
                artifacts_by_output=artifacts_by_output,
                engineering_results=engineering_results,
            ),
            "action": action["action"],
        }
        result["_approval_request"] = {
            "step_id": pending_action.id,
            "step_title": pending_action.title,
            "instructions": pending_action.prompt,
            "action_kind": action["action_kind"],
            "subject": subject,
            "continuation": {
                "schema_version": 2,
                "run_id": run_id,
                "definition_digest": plan.definition_digest,
                "execution_context": execution_context,
                "next_step_index": cursor,
                "completed_step_ids": [step.id for step in executed_steps],
                "result_ids": [item.id for item in engineering_results],
                "input_files": sorted(
                    (
                        {"path": value.path, "sha256": value.sha256}
                        for value in input_values.values()
                        if isinstance(value, WorkflowReference)
                    ),
                    key=lambda item: item["path"],
                ),
                "artifact_files": artifact_files,
                **_execution_snapshot(
                    input_values=input_values,
                    responses=responses,
                    records=records,
                    engineering_results=engineering_results,
                    artifacts_by_output=artifacts_by_output,
                    attempts=attempts,
                    revision_counts=revision_counts,
                    feedback=feedback,
                ),
            },
        }
        if plan.input_snapshot is not None:
            result["_approval_request"]["continuation"].update(
                schema_version=3,
                checkpoint_kind="approval",
                input_snapshot_id=plan.input_snapshot.snapshot_id,
                input_digest=plan.input_snapshot.digest,
                response_id=None,
                response_digest=None,
            )
    return result
