"""Resolve native block identities, typed connections and supported execution order."""

from __future__ import annotations

from dataclasses import dataclass

from .instructions import WorkflowInstructionSet
from .source import _error, _invalid

TEXT_KINDS = {
    "text",
    "workspace_file",
    "engineering_document",
    "design_specification",
    "check_report",
    "structured_result",
}


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


@dataclass
class WorkflowGraph:
    workflow: dict
    inputs: list
    blocks: dict
    ports: dict
    incoming: dict
    outgoing: dict
    ordered: list[str]
    revisions: dict
    instructions: WorkflowInstructionSet | None


def compile_graph(sections) -> WorkflowGraph:
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
    return WorkflowGraph(
        workflows[0],
        inputs,
        blocks,
        ports,
        incoming,
        outgoing,
        ordered,
        revisions,
        instruction_set,
    )
