"""The native section grammar and source diagnostics. Reading has no host side effects."""

from __future__ import annotations

import json
import re


class WorkflowSourceExecutionError(RuntimeError):
    """A correction-oriented error returned for a source-run request."""

    def __init__(
        self, code: str, message: str, correction: str, *, block_id: str | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.correction = correction
        self.block_id = block_id


_SECTION = re.compile(r"(workflow|item|input|task|group|connection) ([a-z][a-z0-9_]*)$")
_FIELD = re.compile(r"([a-z][a-z0-9_]*):\s*(.+)$")
_STABLE_NAME = re.compile(r"[a-z][a-z0-9_]*$")


def _error(code: str, message: str, correction: str) -> WorkflowSourceExecutionError:
    return WorkflowSourceExecutionError(code, message, correction)


def parse_sections(source: str) -> list[dict[str, object]]:
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


def _invalid(
    message: str,
    correction: str = "Correct the highlighted workflow settings and save before running.",
    *,
    block_id: str | None = None,
):
    return WorkflowSourceExecutionError(
        "WORKFLOW_NOT_READY", message, correction, block_id=block_id
    )


def validate_authoring_sections(sections):
    """Check required editor fields and global port identities before execution.

    Storage may retain invalid source drafts, but those drafts must not execute
    merely because the runtime needs fewer fields than the canonical editor.
    """
    port_keys = set()
    for section in sections:
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
                if not isinstance(fields[direction], list):
                    raise _invalid(
                        f"{section['id']}.{direction} must be an array of connection points.",
                        "Use a JSON array of connection-point objects, or [] when none are declared.",
                    )
                for port in fields[direction]:
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
                    if (
                        not _STABLE_NAME.fullmatch(port["key"])
                        or any(
                            not isinstance(port.get(field), str)
                            or not port[field].strip()
                            for field in ("name", "kind", "description")
                        )
                        or not isinstance(port["required"], bool)
                        or port["quantity"] not in ("one", "optional", "many")
                        or (
                            port["item"] is not None
                            and (
                                not isinstance(port["item"], str)
                                or not _STABLE_NAME.fullmatch(port["item"])
                            )
                        )
                    ):
                        raise _invalid(
                            f"{section['id']}.{direction}: invalid values for connection point {port['key']!r}.",
                            "Use a lower_snake_case key, nonempty name/kind/description, a boolean required, "
                            "quantity one/optional/many (not null), and an item stable name or null.",
                        )
                    if port["key"] in port_keys:
                        raise _invalid(
                            f"Duplicate connection identity: {port['key']}.",
                            "Use a distinct port key for every connection point in the workspace workflow.",
                        )
                    port_keys.add(port["key"])
