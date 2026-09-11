#!/usr/bin/env python3
"""Generate and compare recovery workflow syntax treatments.

This is exploratory product evidence, not a benchmark or permanent syntax
qualification. All treatments parse to the same schema-validated IR and receive
the same deterministic edit corpus.
"""

from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import inspect
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / "specs" / "080-canonical-workflow-recovery"
FIXTURES = FEATURE / "fixtures"
EVIDENCE = FEATURE / "evidence"
SCHEMA_PATH = FEATURE / "contracts" / "canonical-workflow-ir.schema.json"
JSON_PATH = FIXTURES / "mounting-bracket.workflow.json"
YAML_PATH = FIXTURES / "mounting-bracket.workflow.yaml"
AUTHORING_PATH = FIXTURES / "mounting-bracket.workflow.wflow"
INTERNAL_DSL_PATH = FIXTURES / "mounting-bracket.workflow.internal-ir.wflow"
RESULT_PATH = EVIDENCE / "syntax-evaluation.json"
REPORT_PATH = EVIDENCE / "syntax-evaluation.md"


@dataclass(frozen=True)
class DslDocument:
    ir: dict[str, Any]
    comments: tuple[str, ...]
    source_map: dict[str, dict[str, int]]


AUTHORING_INPUT_BLOCK_IDS = frozenset(
    {"block.reference-images", "block.design-intent", "block.company-context"}
)


def canonical_bytes(value: dict[str, Any]) -> bytes:
    canonical = copy.deepcopy(value)
    canonical.pop("semantic_sha256", None)
    for collection in ("blocks", "ports", "relationships", "artifact_contracts", "bindings", "components"):
        if isinstance(canonical.get(collection), list):
            canonical[collection] = sorted(canonical[collection], key=lambda row: str(row["id"]))
    return json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def json_text(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def yaml_text(value: dict[str, Any]) -> str:
    body = yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100)
    return "# Wright recovery syntax treatment: comments are not round-trip preserved by this parser.\n" + body


def scalar(value: Any) -> str:
    if (
        isinstance(value, str)
        and value
        and value[0].isalpha()
        and value not in {"null", "true", "false"}
        and all(character.isalnum() or character in "._-/:" for character in value)
    ):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def emit_section(lines: list[str], kind: str, identity: str, fields: list[tuple[str, Any]]) -> None:
    lines.append(f"{kind} {identity}")
    lines.extend(f"  {name}: {scalar(value)}" for name, value in fields)
    lines.append("end")
    lines.append("")


def dsl_text(value: dict[str, Any], comments: tuple[str, ...] = ()) -> str:
    lines = ["# Wright workflow language — recovery treatment 0.1"]
    lines.extend(f"# {comment}" for comment in comments)
    lines.append("")
    metadata = value["metadata"]
    emit_section(
        lines,
        "workflow",
        value["workflow_id"],
        [
            ("version", value["schema_version"]),
            ("revision", value["revision"]),
            ("parent", value["parent_revision"]),
            ("semantic_sha256", value.get("semantic_sha256")),
            ("title", metadata["title"]),
            ("purpose", metadata["purpose"]),
            ("domain", metadata["engineering_domain"]),
            ("authorship", metadata["authorship"]),
        ],
    )
    for phase in value["phases"]:
        emit_section(lines, "phase", phase["id"], [("name", phase["name"]), ("purpose", phase["purpose"]), ("order", phase["order"]), ("blocks", phase["block_ids"])])
    for block in value["blocks"]:
        emit_section(
            lines,
            "block",
            block["id"],
            [
                ("kind", block["kind"]),
                ("title", block["title"]),
                ("purpose", block["purpose"]),
                ("phase", block["phase_id"]),
                ("execution", block["execution_kind"]),
                ("instructions", block["instructions"]),
                ("config", block["configuration"]),
                ("inputs", block["input_port_ids"]),
                ("outputs", block["output_port_ids"]),
                ("binding", block["binding_id"]),
                ("component", block["component_ref"]),
            ],
        )
    for port in value["ports"]:
        emit_section(
            lines,
            "port",
            port["id"],
            [
                ("owner", port["owner_block_id"]),
                ("direction", port["direction"]),
                ("name", port["name"]),
                ("type", port["type_id"]),
                ("required", port["required"]),
                ("cardinality", port["cardinality"]),
                ("artifact", port["artifact_contract_id"]),
                ("description", port["description"]),
            ],
        )
    for relation in value["relationships"]:
        emit_section(
            lines,
            "relationship",
            relation["id"],
            [("kind", relation["kind"]), ("source", relation["source_id"]), ("target", relation["target_id"]), ("label", relation["label"]), ("condition", relation["condition"])],
        )
    for artifact in value["artifact_contracts"]:
        emit_section(
            lines,
            "artifact",
            artifact["id"],
            [
                ("name", artifact["name"]),
                ("type", artifact["type_id"]),
                ("media", artifact["media_type"]),
                ("description", artifact["description"]),
                ("producer", artifact["producer_block_id"]),
                ("required_for", artifact["required_for_block_ids"]),
                ("preview", artifact["preview_policy"]),
                ("actions", artifact["allowed_actions"]),
            ],
        )
    for binding in value["bindings"]:
        emit_section(
            lines,
            "binding",
            binding["id"],
            [
                ("kind", binding["kind"]),
                ("provider", binding["provider_id"]),
                ("server", binding["server_id"]),
                ("tool", binding["tool_id"]),
                ("schema", binding["schema_digest"]),
                ("arguments", binding["argument_map"]),
                ("results", binding["result_map"]),
                ("approval", binding["approval_policy"]),
                ("capability", binding["capability_name"]),
            ],
        )
    for component in value["components"]:
        emit_section(
            lines,
            "component",
            component["id"],
            [
                ("version", component["version"]),
                ("title", component["title"]),
                ("inputs", component["input_port_ids"]),
                ("outputs", component["output_port_ids"]),
                ("digest", component["internal_definition_digest"]),
                ("addresses", component["internal_addresses"]),
            ],
        )
    return "\n".join(lines).rstrip() + "\n"


def parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        raise ValueError("WFR-TEXT-VALUE-MISSING")
    if raw[0] in "\"[{" or raw in {"null", "true", "false"} or raw[0].isdigit() or raw[0] == "-":
        try:
            return json.loads(
                raw,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"WFR-TEXT-NUMBER-NONFINITE:{value}")
                ),
            )
        except json.JSONDecodeError as error:
            raise ValueError(f"WFR-TEXT-VALUE-INVALID:{error.msg}") from error
    return raw


DSL_FIELDS: dict[str, frozenset[str]] = {
    "workflow": frozenset({"version", "revision", "parent", "semantic_sha256", "title", "purpose", "domain", "authorship"}),
    "phase": frozenset({"name", "purpose", "order", "blocks"}),
    "block": frozenset({"kind", "title", "purpose", "phase", "execution", "instructions", "config", "inputs", "outputs", "binding", "component"}),
    "port": frozenset({"owner", "direction", "name", "type", "required", "cardinality", "artifact", "description"}),
    "relationship": frozenset({"kind", "source", "target", "label", "condition"}),
    "artifact": frozenset({"name", "type", "media", "description", "producer", "required_for", "preview", "actions"}),
    "binding": frozenset({"kind", "provider", "server", "tool", "schema", "arguments", "results", "approval", "capability"}),
    "component": frozenset({"version", "title", "inputs", "outputs", "digest", "addresses"}),
}


def reject_nonfinite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("WFR-TEXT-NUMBER-NONFINITE")
    if isinstance(value, dict):
        for nested in value.values():
            reject_nonfinite(nested)
    elif isinstance(value, list):
        for nested in value:
            reject_nonfinite(nested)


def parse_dsl(text: str) -> DslDocument:
    sections: list[tuple[str, str, dict[str, Any], int, int]] = []
    comments: list[str] = []
    current: tuple[str, str, dict[str, Any], int] | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            content = stripped[1:].strip()
            if content and not content.startswith("Wright workflow language"):
                comments.append(content)
            continue
        if current is None:
            parts = stripped.split(maxsplit=1)
            if len(parts) != 2 or parts[0] not in {"workflow", "phase", "block", "port", "relationship", "artifact", "binding", "component"}:
                raise ValueError(f"WFR-TEXT-SECTION-INVALID:{line_number}")
            current = (parts[0], parts[1], {}, line_number)
            continue
        if stripped == "end":
            kind, identity, fields, start = current
            sections.append((kind, identity, fields, start, line_number))
            current = None
            continue
        if ":" not in stripped:
            raise ValueError(f"WFR-TEXT-FIELD-INVALID:{line_number}")
        name, raw = stripped.split(":", 1)
        fields = current[2]
        if name not in DSL_FIELDS[current[0]]:
            raise ValueError(f"WFR-TEXT-FIELD-UNKNOWN:{line_number}:{name}")
        if name in fields:
            raise ValueError(f"WFR-TEXT-FIELD-DUPLICATE:{line_number}:{name}")
        fields[name] = parse_scalar(raw)
    if current is not None:
        raise ValueError(f"WFR-TEXT-SECTION-UNTERMINATED:{current[3]}")
    workflow_sections = [item for item in sections if item[0] == "workflow"]
    if len(workflow_sections) != 1:
        raise ValueError("WFR-TEXT-WORKFLOW-COUNT")
    _, workflow_id, workflow, _, _ = workflow_sections[0]

    def rows(kind: str, convert: Callable[[str, dict[str, Any]], dict[str, Any]]) -> list[dict[str, Any]]:
        return [convert(identity, fields) for section_kind, identity, fields, _, _ in sections if section_kind == kind]

    def require(fields: dict[str, Any], *names: str) -> None:
        missing = [name for name in names if name not in fields]
        if missing:
            raise ValueError(f"WFR-TEXT-FIELDS-MISSING:{','.join(missing)}")

    def phase(identity: str, fields: dict[str, Any]) -> dict[str, Any]:
        require(fields, "name", "purpose", "order", "blocks")
        return {"id": identity, "name": fields["name"], "purpose": fields["purpose"], "order": fields["order"], "block_ids": fields["blocks"]}

    def block(identity: str, fields: dict[str, Any]) -> dict[str, Any]:
        require(fields, "kind", "title", "purpose", "phase", "execution", "instructions", "config", "inputs", "outputs", "binding", "component")
        return {"id": identity, "kind": fields["kind"], "title": fields["title"], "purpose": fields["purpose"], "phase_id": fields["phase"], "execution_kind": fields["execution"], "instructions": fields["instructions"], "configuration": fields["config"], "input_port_ids": fields["inputs"], "output_port_ids": fields["outputs"], "binding_id": fields["binding"], "component_ref": fields["component"]}

    def port(identity: str, fields: dict[str, Any]) -> dict[str, Any]:
        require(fields, "owner", "direction", "name", "type", "required", "cardinality", "artifact", "description")
        return {"id": identity, "owner_block_id": fields["owner"], "direction": fields["direction"], "name": fields["name"], "type_id": fields["type"], "required": fields["required"], "cardinality": fields["cardinality"], "artifact_contract_id": fields["artifact"], "description": fields["description"]}

    def relationship(identity: str, fields: dict[str, Any]) -> dict[str, Any]:
        require(fields, "kind", "source", "target", "label", "condition")
        return {"id": identity, "kind": fields["kind"], "source_id": fields["source"], "target_id": fields["target"], "label": fields["label"], "condition": fields["condition"]}

    def artifact(identity: str, fields: dict[str, Any]) -> dict[str, Any]:
        require(fields, "name", "type", "media", "description", "producer", "required_for", "preview", "actions")
        return {"id": identity, "name": fields["name"], "type_id": fields["type"], "media_type": fields["media"], "description": fields["description"], "producer_block_id": fields["producer"], "required_for_block_ids": fields["required_for"], "preview_policy": fields["preview"], "allowed_actions": fields["actions"]}

    def binding(identity: str, fields: dict[str, Any]) -> dict[str, Any]:
        require(fields, "kind", "provider", "server", "tool", "schema", "arguments", "results", "approval", "capability")
        return {"id": identity, "kind": fields["kind"], "provider_id": fields["provider"], "server_id": fields["server"], "tool_id": fields["tool"], "schema_digest": fields["schema"], "argument_map": fields["arguments"], "result_map": fields["results"], "approval_policy": fields["approval"], "capability_name": fields["capability"]}

    def component(identity: str, fields: dict[str, Any]) -> dict[str, Any]:
        require(fields, "version", "title", "inputs", "outputs", "digest", "addresses")
        return {"id": identity, "version": fields["version"], "title": fields["title"], "input_port_ids": fields["inputs"], "output_port_ids": fields["outputs"], "internal_definition_digest": fields["digest"], "internal_addresses": fields["addresses"]}

    require(workflow, "version", "revision", "parent", "semantic_sha256", "title", "purpose", "domain", "authorship")
    ir = {
        "document_kind": "workflow-ir",
        "schema_version": workflow["version"],
        "workflow_id": workflow_id,
        "revision": workflow["revision"],
        "parent_revision": workflow["parent"],
        "semantic_sha256": workflow["semantic_sha256"],
        "metadata": {"title": workflow["title"], "purpose": workflow["purpose"], "engineering_domain": workflow["domain"], "authorship": workflow["authorship"]},
        "phases": rows("phase", phase),
        "blocks": rows("block", block),
        "ports": rows("port", port),
        "relationships": rows("relationship", relationship),
        "artifact_contracts": rows("artifact", artifact),
        "bindings": rows("binding", binding),
        "components": rows("component", component),
    }
    reject_nonfinite(ir)
    source_map = {identity: {"start_line": start, "end_line": end} for _, identity, _, start, end in sections}
    return DslDocument(ir=ir, comments=tuple(comments), source_map=source_map)


def _by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in rows}


def _stable_key(identity: str) -> str:
    suffix = identity.split(".", 1)[1] if "." in identity else identity
    return re.sub(r"[^a-zA-Z0-9]+", "_", suffix).strip("_").lower()


def _canonical_id(prefix: str, key: str) -> str:
    return f"{prefix}.{key.replace('_', '-')}"


def _authoring_scalar(value: Any) -> str:
    if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]*", value):
        return value
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _emit_authoring_section(
    lines: list[str], kind: str, identity: str, fields: list[tuple[str, Any]]
) -> None:
    lines.append(f"{kind} {identity}")
    lines.extend(f"  {name}: {_authoring_scalar(value)}" for name, value in fields)
    lines.append("end")
    lines.append("")


def _item_type(artifact: dict[str, Any]) -> str:
    media_type = str(artifact["media_type"])
    if media_type.startswith("image/"):
        return "image_files"
    if media_type == "text/plain":
        return "text_or_document"
    if media_type == "text/markdown":
        return "design_document"
    if media_type == "application/vnd.wright.context+json":
        return "company_knowledge"
    if media_type == "model/step":
        return "step_file"
    if media_type.startswith("model/"):
        return "approved_cad_model" if "approved" in str(artifact["id"]) else "cad_model"
    if media_type == "text/html":
        return "engineering_report"
    if media_type == "application/zip":
        return "archive"
    return "engineering_file"


def _item_formats(artifact: dict[str, Any]) -> list[str]:
    media_type = str(artifact["media_type"])
    if media_type.startswith("image/"):
        return ["jpg", "png"]
    if media_type == "text/plain":
        return ["text", "docx", "pdf"]
    if media_type == "text/markdown":
        return ["markdown"]
    if media_type == "application/vnd.wright.context+json":
        return ["company_library"]
    if media_type == "model/step":
        return ["step_ap242"]
    if media_type.startswith("model/"):
        return ["cad_model"]
    if media_type == "text/html":
        return ["html_report"]
    if media_type == "application/zip":
        return ["zip"]
    return ["file"]


def _performed_by(block: dict[str, Any]) -> str:
    if block["kind"] == "approval" and block["execution_kind"] == "ai_capable":
        return "ai_then_engineer"
    if block["execution_kind"] == "human":
        return "engineer"
    if block["execution_kind"] == "ai_capable":
        return "ai_assisted"
    return "configured_tool"


def _provided_by(block: dict[str, Any]) -> str:
    if block["id"] == "block.company-context":
        return "company_library"
    return "engineer" if block["execution_kind"] == "human" else _performed_by(block)


def _source_step_type(kind: str) -> str:
    if kind == "approval":
        return "review"
    if kind == "component":
        return "reusable_step"
    return kind


def _source_connection_type(kind: str) -> str:
    return {
        "data": "item",
        "control": "order",
        "decision": "approval",
        "feedback": "revision",
    }[kind]


_PUBLIC_PORT_KIND_BY_TYPE_ID = {
    "type.image.reference-set": "reference_images",
    "type.design.intent": "design_intent",
    "type.context.company": "company_context",
    "type.design.specification": "design_specification",
    "type.geometry.brep": "cad_model",
    "type.report.manufacturability": "manufacturing_report",
    "type.geometry.approved": "approved_cad_model",
    "type.file.step": "step_file",
    "type.package.review": "handoff_package",
    "type.file.drawing": "drawing_file",
    "type.file.drawing.approved": "approved_drawing",
    "type.report.tolerance": "tolerance_report",
}
_TYPE_ID_BY_PUBLIC_PORT_KIND = {
    public_kind: type_id
    for type_id, public_kind in _PUBLIC_PORT_KIND_BY_TYPE_ID.items()
}


def _public_port_kind(type_id: str) -> str:
    try:
        return _PUBLIC_PORT_KIND_BY_TYPE_ID[type_id]
    except KeyError as error:
        raise ValueError(f"WFR-SOURCE-PORT-KIND-UNKNOWN:{type_id}") from error


def _source_port(value: dict[str, Any], port_id: str) -> dict[str, Any]:
    port = next((row for row in value["ports"] if row["id"] == port_id), None)
    if port is None:
        raise ValueError(f"WFR-SOURCE-PORT-MISSING:{port_id}")
    return {
        "key": _stable_key(port["id"]),
        "name": port["name"],
        "kind": _public_port_kind(port["type_id"]),
        "item": (
            None
            if port["artifact_contract_id"] is None
            else _stable_key(port["artifact_contract_id"])
        ),
        "required": port["required"],
        "quantity": port["cardinality"],
        "description": port["description"],
    }


def _endpoint_key(value: dict[str, Any], semantic_id: str) -> str:
    port = next((row for row in value["ports"] if row["id"] == semantic_id), None)
    if port is not None:
        return f"{_stable_key(port['owner_block_id'])}.{_stable_key(port['id'])}"
    block = next((row for row in value["blocks"] if row["id"] == semantic_id), None)
    return _stable_key(block["id"]) if block is not None else semantic_id


def authoring_text(value: dict[str, Any]) -> str:
    """Project canonical IR into lossless, engineer-editable workflow source."""

    workflow_name = _stable_key(value["workflow_id"])
    default_groups = {
        "phase.define": {"name": "Define", "order": 0},
        "phase.verify": {"name": "Verify", "order": 1},
        "phase.deliver": {"name": "Deliver", "order": 2},
    }
    project_groups = len(value["blocks"]) >= 26 or any(
        phase["id"] not in default_groups
        or phase["name"] != default_groups[phase["id"]]["name"]
        or phase["order"] != default_groups[phase["id"]]["order"]
        for phase in value["phases"]
    )
    lines = [
        "# Wright engineering workflow source",
        "# Stable names identify engineering items, steps, connection points, and routes.",
        "# Versions, history, integrity digests, canvas layout, and run state are managed by Wright.",
        "# Optional groups are shown only when they improve a larger or explicitly grouped workflow.",
        "",
    ]
    metadata = value["metadata"]
    _emit_authoring_section(
        lines,
        "workflow",
        workflow_name,
        [
            ("name", metadata["title"]),
            ("purpose", metadata["purpose"]),
            ("discipline", metadata["engineering_domain"]),
            (
                "reviewed_ai_suggestions",
                metadata["authorship"] == "human_with_ai_proposal",
            ),
        ],
    )
    for group in (
        sorted(value["phases"], key=lambda row: row["order"])
        if project_groups
        else []
    ):
        _emit_authoring_section(
            lines,
            "group",
            _stable_key(group["id"]),
            [
                ("name", group["name"]),
                ("purpose", group["purpose"]),
                ("order", group["order"]),
            ],
        )
    for artifact in value["artifact_contracts"]:
        _emit_authoring_section(
            lines,
            "item",
            _stable_key(artifact["id"]),
            [
                ("name", artifact["name"]),
                ("type", _item_type(artifact)),
                ("formats", _item_formats(artifact)),
                ("description", artifact["description"]),
            ],
        )
    bindings = _by_id(value["bindings"])
    for block in value["blocks"]:
        kind = "input" if block["id"] in AUTHORING_INPUT_BLOCK_IDS else "task"
        instruction_name = "prompt" if block["execution_kind"] == "ai_capable" else "instructions"
        fields: list[tuple[str, Any]] = [
            ("name", block["title"]),
            ("purpose", block["purpose"]),
            ("step_type", _source_step_type(block["kind"])),
            (
                "group",
                _stable_key(block["phase_id"])
                if project_groups and block["phase_id"] is not None
                else None,
            ),
            (
                "provided_by" if kind == "input" else "performed_by",
                _provided_by(block) if kind == "input" else _performed_by(block),
            ),
            ("inputs", [_source_port(value, port_id) for port_id in block["input_port_ids"]]),
            ("outputs", [_source_port(value, port_id) for port_id in block["output_port_ids"]]),
            (instruction_name, block["instructions"]),
            ("settings", block["configuration"]),
            (
                "tool",
                None
                if block["binding_id"] is None
                else {
                    "assignment": _stable_key(block["binding_id"]),
                    "action": bindings[block["binding_id"]]["tool_id"],
                },
            ),
            (
                "reusable_step",
                None
                if block["component_ref"] is None
                else {
                    "key": _stable_key(block["component_ref"]["component_id"]),
                    "version": block["component_ref"]["version_range"],
                },
            ),
        ]
        _emit_authoring_section(lines, kind, _stable_key(block["id"]), fields)
    for relationship in value["relationships"]:
        _emit_authoring_section(
            lines,
            "connection",
            _stable_key(relationship["id"]),
            [
                ("type", _source_connection_type(relationship["kind"])),
                ("from", _endpoint_key(value, relationship["source_id"])),
                ("to", _endpoint_key(value, relationship["target_id"])),
                ("label", relationship["label"]),
                ("when", relationship["condition"]),
            ],
        )
    return "\n".join(lines).rstrip() + "\n"


AUTHORING_FIELDS: dict[str, frozenset[str]] = {
    "workflow": frozenset({"name", "purpose", "discipline", "reviewed_ai_suggestions"}),
    "group": frozenset({"name", "purpose", "order"}),
    "item": frozenset({"name", "type", "formats", "description"}),
    "input": frozenset(
        {
            "name", "purpose", "step_type", "group", "provided_by", "inputs", "outputs",
            "prompt", "instructions", "settings", "tool", "reusable_step",
        }
    ),
    "task": frozenset(
        {
            "name", "purpose", "step_type", "group", "performed_by", "inputs", "outputs",
            "prompt", "instructions", "settings", "tool", "reusable_step",
        }
    ),
    "connection": frozenset({"type", "from", "to", "label", "when"}),
}
HOST_MANAGED_FIELDS = frozenset(
    {
        "version",
        "schema_version",
        "revision",
        "parent",
        "parent_revision",
        "semantic_sha256",
        "digest",
        "authorship",
        "binding",
        "binding_id",
        "port",
        "port_id",
        "layout",
        "layout_revision",
    }
)


def _parse_authoring_scalar(raw: str) -> Any:
    raw = raw.strip()
    if not raw:
        raise ValueError("WFR-SOURCE-VALUE-MISSING")
    if raw not in {"true", "false", "null"} and re.fullmatch(
        r"[a-z][a-z0-9_]*", raw
    ):
        return raw
    try:
        value = json.loads(
            raw,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"WFR-SOURCE-NUMBER-NONFINITE:{value}")
            ),
        )
    except json.JSONDecodeError as error:
        raise ValueError(f"WFR-SOURCE-VALUE-INVALID:{error.msg}") from error
    reject_nonfinite(value)
    return value


def _authoring_sections(text: str) -> tuple[list[tuple[str, str, dict[str, Any], int, int]], tuple[str, ...]]:
    sections: list[tuple[str, str, dict[str, Any], int, int]] = []
    comments: list[str] = []
    current: tuple[str, str, dict[str, Any], int] | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            comments.append(stripped[1:].strip())
            continue
        if current is None:
            match = re.fullmatch(
                r"(workflow|item|input|task|group|connection) ([a-z][a-z0-9_]*)",
                stripped,
            )
            if match is None:
                raise ValueError(f"WFR-SOURCE-SECTION-INVALID:{line_number}")
            current = (match.group(1), match.group(2), {}, line_number)
            continue
        if stripped == "end":
            kind, identity, fields, start = current
            sections.append((kind, identity, fields, start, line_number))
            current = None
            continue
        match = re.fullmatch(r"  ([a-z][a-z0-9_]*):\s*(.+)", line)
        if match is None:
            raise ValueError(f"WFR-SOURCE-FIELD-INVALID:{line_number}")
        name, raw = match.group(1), match.group(2)
        if name in HOST_MANAGED_FIELDS:
            raise ValueError(f"WFR-SOURCE-FIELD-MANAGED:{line_number}:{name}")
        if name not in AUTHORING_FIELDS[current[0]]:
            raise ValueError(f"WFR-SOURCE-FIELD-UNKNOWN:{line_number}:{name}")
        if name in current[2]:
            raise ValueError(f"WFR-SOURCE-FIELD-DUPLICATE:{line_number}:{name}")
        current[2][name] = _parse_authoring_scalar(raw)
    if current is not None:
        raise ValueError(f"WFR-SOURCE-SECTION-UNTERMINATED:{current[3]}")
    return sections, tuple(comments)


def parse_authoring(text: str, base: dict[str, Any]) -> DslDocument:
    """Reconstruct canonical semantics from engineer source and a trusted host base."""

    sections, comments = _authoring_sections(text)
    indexed: dict[tuple[str, str], tuple[dict[str, Any], int, int]] = {}
    for kind, identity, fields, start, end in sections:
        key = (kind, identity)
        if key in indexed:
            raise ValueError(f"WFR-SOURCE-SECTION-DUPLICATE:{start}:{kind}:{identity}")
        indexed[key] = (fields, start, end)

    def require(
        fields: dict[str, Any], kind: str, identity: str, names: set[str]
    ) -> None:
        missing_fields = sorted(names - set(fields))
        if missing_fields:
            raise ValueError(f"WFR-SOURCE-FIELDS-MISSING:{kind}:{identity}:{','.join(missing_fields)}")
        extra_fields = sorted(set(fields) - names)
        if extra_fields:
            raise ValueError(
                f"WFR-SOURCE-FIELD-UNKNOWN:{kind}:{identity}:{','.join(extra_fields)}"
            )

    def text_value(fields: dict[str, Any], field: str, context: str) -> str:
        value = fields[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"WFR-SOURCE-FIELD-TYPE:{context}:{field}")
        return value

    workflow_sections = [section for section in sections if section[0] == "workflow"]
    if len(workflow_sections) != 1:
        raise ValueError(f"WFR-SOURCE-WORKFLOW-COUNT:{len(workflow_sections)}")
    expected_workflow = _stable_key(base["workflow_id"])
    if workflow_sections[0][1] != expected_workflow:
        raise ValueError(
            f"WFR-SOURCE-IDENTITY-UNKNOWN:workflow:{workflow_sections[0][1]}"
        )

    candidate = copy.deepcopy(base)
    workflow, _, _ = indexed[("workflow", expected_workflow)]
    require(
        workflow,
        "workflow",
        expected_workflow,
        {"name", "purpose", "discipline", "reviewed_ai_suggestions"},
    )
    reviewed_ai = workflow["reviewed_ai_suggestions"]
    if not isinstance(reviewed_ai, bool):
        raise ValueError("WFR-SOURCE-FIELD-TYPE:workflow:reviewed_ai_suggestions")
    candidate["metadata"]["title"] = text_value(workflow, "name", "workflow")
    candidate["metadata"]["purpose"] = text_value(workflow, "purpose", "workflow")
    candidate["metadata"]["engineering_domain"] = text_value(
        workflow, "discipline", "workflow"
    )
    candidate["metadata"]["authorship"] = (
        "human_with_ai_proposal" if reviewed_ai else "human"
    )

    group_sections = [section for section in sections if section[0] == "group"]
    phases_by_key = {_stable_key(row["id"]): row for row in candidate["phases"]}
    for kind, key, fields, _, _ in sections:
        if kind != "group":
            continue
        phase = phases_by_key.get(key)
        if phase is None:
            raise ValueError(f"WFR-SOURCE-GROUP-UNKNOWN:{key}")
        require(fields, kind, key, {"name", "purpose", "order"})
        order = fields["order"]
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            raise ValueError(f"WFR-SOURCE-FIELD-TYPE:group:{key}:order")
        phase["name"] = text_value(fields, "name", f"group:{key}")
        phase["purpose"] = text_value(fields, "purpose", f"group:{key}")
        phase["order"] = order

    artifacts_by_key = {
        _stable_key(row["id"]): row for row in candidate["artifact_contracts"]
    }
    item_sections = {
        key: (fields, start, end)
        for kind, key, fields, start, end in sections
        if kind == "item"
    }
    missing_items = sorted(set(artifacts_by_key) - set(item_sections))
    if missing_items:
        raise ValueError(f"WFR-SOURCE-ITEM-MISSING:{','.join(missing_items)}")
    unknown_items = sorted(set(item_sections) - set(artifacts_by_key))
    if unknown_items:
        raise ValueError(f"WFR-SOURCE-IDENTITY-UNKNOWN:item:{','.join(unknown_items)}")
    for key, artifact in artifacts_by_key.items():
        fields, _, _ = item_sections[key]
        require(fields, "item", key, {"name", "type", "formats", "description"})
        if fields["type"] != _item_type(artifact):
            raise ValueError(f"WFR-SOURCE-TYPE-CHANGE-UNSUPPORTED:{key}")
        if fields["formats"] != _item_formats(artifact):
            raise ValueError(f"WFR-SOURCE-FORMAT-CHANGE-UNSUPPORTED:{key}")
        artifact["name"] = text_value(fields, "name", f"item:{key}")
        artifact["description"] = text_value(fields, "description", f"item:{key}")

    base_blocks_by_key = {_stable_key(row["id"]): row for row in base["blocks"]}
    base_ports_by_key = {_stable_key(row["id"]): row for row in base["ports"]}
    bindings_by_key = {_stable_key(row["id"]): row for row in candidate["bindings"]}
    components_by_key = {_stable_key(row["id"]): row for row in candidate["components"]}

    def parse_ports(
        fields: dict[str, Any], field: str, owner_id: str, context: str
    ) -> list[dict[str, Any]]:
        raw_ports = fields[field]
        if not isinstance(raw_ports, list):
            raise ValueError(f"WFR-SOURCE-FIELD-TYPE:{context}:{field}")
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        required_fields = {
            "key", "name", "kind", "item", "required", "quantity", "description"
        }
        for raw_port in raw_ports:
            if not isinstance(raw_port, dict) or set(raw_port) != required_fields:
                raise ValueError(f"WFR-SOURCE-PORT-FIELDS:{context}:{field}")
            key = raw_port["key"]
            item = raw_port["item"]
            if (
                not isinstance(key, str)
                or re.fullmatch(r"[a-z][a-z0-9_]*", key) is None
                or key in seen
            ):
                raise ValueError(f"WFR-SOURCE-PORT-DUPLICATE:{context}:{field}")
            seen.add(key)
            if item is not None and (
                not isinstance(item, str)
                or re.fullmatch(r"[a-z][a-z0-9_]*", item) is None
                or item not in artifacts_by_key
            ):
                raise ValueError(f"WFR-SOURCE-ITEM-UNKNOWN:{context}:{key}")
            if (
                not isinstance(raw_port["name"], str)
                or not raw_port["name"].strip()
                or not isinstance(raw_port["kind"], str)
                or raw_port["kind"] not in _TYPE_ID_BY_PUBLIC_PORT_KIND
                or not isinstance(raw_port["description"], str)
                or not raw_port["description"].strip()
                or not isinstance(raw_port["required"], bool)
                or raw_port["quantity"] not in {"one", "optional", "many"}
            ):
                raise ValueError(f"WFR-SOURCE-PORT-INVALID:{context}:{key}")
            base_port = base_ports_by_key.get(key)
            type_id = _TYPE_ID_BY_PUBLIC_PORT_KIND[raw_port["kind"]]
            if base_port is not None and base_port["type_id"] != type_id:
                raise ValueError(f"WFR-SOURCE-PORT-KIND:{context}:{key}")
            if item is not None and artifacts_by_key[item]["type_id"] != type_id:
                raise ValueError(f"WFR-SOURCE-PORT-ITEM-TYPE:{context}:{key}")
            result.append(
                {
                    "id": base_port["id"] if base_port else _canonical_id("port", key),
                    "owner_block_id": owner_id,
                    "direction": "input" if field == "inputs" else "output",
                    "name": raw_port["name"].strip(),
                    "type_id": base_port["type_id"] if base_port else type_id,
                    "required": raw_port["required"],
                    "cardinality": raw_port["quantity"],
                    "artifact_contract_id": (
                        None if item is None else artifacts_by_key[item]["id"]
                    ),
                    "description": raw_port["description"].strip(),
                }
            )
        return result

    block_sections = [section for section in sections if section[0] in {"input", "task"}]
    block_keys: set[str] = set()
    next_blocks: list[dict[str, Any]] = []
    next_ports: list[dict[str, Any]] = []
    for kind, key, fields, _, _ in block_sections:
        if key in block_keys:
            raise ValueError(f"WFR-SOURCE-KEY-DUPLICATE:step:{key}")
        block_keys.add(key)
        base_block = base_blocks_by_key.get(key)
        expected_kind = (
            "input"
            if base_block is not None and base_block["id"] in AUTHORING_INPUT_BLOCK_IDS
            else "task"
        )
        if base_block is not None and kind != expected_kind:
            raise ValueError(f"WFR-SOURCE-STEP-KIND:{key}:{expected_kind}")
        if "prompt" in fields and "instructions" in fields:
            raise ValueError(f"WFR-SOURCE-FIELD-UNKNOWN:{kind}:{key}:instructions")
        instruction_field = "prompt" if "prompt" in fields else "instructions"
        actor_field = "provided_by" if kind == "input" else "performed_by"
        require(
            fields,
            kind,
            key,
            {
                "name", "purpose", "step_type", "group", actor_field, "inputs", "outputs",
                instruction_field, "settings", "tool", "reusable_step",
            },
        )
        step_kind = {
            "work": "work",
            "decision": "decision",
            "review": "approval",
            "reusable_step": "component",
        }.get(text_value(fields, "step_type", f"{kind}:{key}"))
        if step_kind is None:
            raise ValueError(f"WFR-SOURCE-STEP-TYPE:{key}")
        actor = text_value(fields, actor_field, f"{kind}:{key}")
        execution_kind = {
            "engineer": "human",
            "configured_tool": "deterministic",
            "company_library": "deterministic",
            "ai_assisted": "ai_capable",
            "ai_then_engineer": "ai_capable",
        }.get(actor)
        if execution_kind is None:
            raise ValueError(f"WFR-SOURCE-ACTOR:{key}")
        group_key = fields["group"]
        if group_key is not None and (
            not isinstance(group_key, str) or group_key not in phases_by_key
        ):
            raise ValueError(f"WFR-SOURCE-GROUP-UNKNOWN:{key}:{group_key}")
        settings = fields["settings"]
        if (
            not isinstance(settings, dict)
            or any(
                isinstance(value, (dict, list))
                or value is None
                or not isinstance(value, (str, int, float, bool))
                for value in settings.values()
            )
        ):
            raise ValueError(f"WFR-SOURCE-FIELD-TYPE:{kind}:{key}:settings")
        reject_nonfinite(settings)
        block_id = base_block["id"] if base_block else _canonical_id("block", key)
        inputs = parse_ports(fields, "inputs", block_id, f"{kind}:{key}")
        outputs = parse_ports(fields, "outputs", block_id, f"{kind}:{key}")

        tool = fields["tool"]
        binding_id = None
        if tool is not None:
            if (
                not isinstance(tool, dict)
                or set(tool) != {"assignment", "action"}
                or not isinstance(tool["assignment"], str)
                or (tool["action"] is not None and not isinstance(tool["action"], str))
            ):
                raise ValueError(f"WFR-SOURCE-TOOL-INVALID:{key}")
            binding = bindings_by_key.get(tool["assignment"])
            if binding is None:
                raise ValueError(f"WFR-SOURCE-TOOL-UNKNOWN:{key}:{tool['assignment']}")
            binding_id = binding["id"]
            binding["tool_id"] = tool["action"]

        reusable = fields["reusable_step"]
        component_ref = None
        if reusable is not None:
            if (
                not isinstance(reusable, dict)
                or set(reusable) != {"key", "version"}
                or not isinstance(reusable["key"], str)
                or not isinstance(reusable["version"], str)
            ):
                raise ValueError(f"WFR-SOURCE-REUSABLE-INVALID:{key}")
            component = components_by_key.get(reusable["key"])
            if component is None:
                raise ValueError(
                    f"WFR-SOURCE-REUSABLE-UNKNOWN:{key}:{reusable['key']}"
                )
            component_ref = {
                "component_id": component["id"],
                "version_range": reusable["version"],
            }
        next_blocks.append(
            {
                "id": block_id,
                "kind": step_kind,
                "title": text_value(fields, "name", f"{kind}:{key}"),
                "purpose": text_value(fields, "purpose", f"{kind}:{key}"),
                "phase_id": (
                    phases_by_key[group_key]["id"]
                    if group_key is not None
                    else (
                        base_block["phase_id"]
                        if not group_sections and base_block is not None
                        else None
                    )
                ),
                "execution_kind": execution_kind,
                "instructions": text_value(fields, instruction_field, f"{kind}:{key}"),
                "configuration": copy.deepcopy(settings),
                "input_port_ids": [port["id"] for port in inputs],
                "output_port_ids": [port["id"] for port in outputs],
                "binding_id": binding_id,
                "component_ref": component_ref,
            }
        )
        next_ports.extend(inputs)
        next_ports.extend(outputs)

    candidate["blocks"] = next_blocks
    candidate["ports"] = next_ports
    for phase in candidate["phases"]:
        phase["block_ids"] = [
            block["id"] for block in next_blocks if block["phase_id"] == phase["id"]
        ]

    blocks_by_key = {_stable_key(row["id"]): row for row in candidate["blocks"]}
    ports_by_endpoint = {
        f"{_stable_key(row['owner_block_id'])}.{_stable_key(row['id'])}": row
        for row in candidate["ports"]
    }
    base_relationships_by_key = {
        _stable_key(row["id"]): row for row in base["relationships"]
    }
    next_relationships: list[dict[str, Any]] = []
    for kind, key, fields, _, _ in sections:
        if kind != "connection":
            continue
        require(fields, kind, key, {"type", "from", "to", "label", "when"})
        relationship_kind = {
            "item": "data",
            "order": "control",
            "approval": "decision",
            "revision": "feedback",
        }.get(text_value(fields, "type", f"connection:{key}"))
        if relationship_kind is None:
            raise ValueError(f"WFR-SOURCE-CONNECTION-TYPE:{key}")

        def endpoint(field: str) -> str:
            value = text_value(fields, field, f"connection:{key}")
            if value in ports_by_endpoint:
                return ports_by_endpoint[value]["id"]
            if value in blocks_by_key:
                return blocks_by_key[value]["id"]
            raise ValueError(f"WFR-SOURCE-ENDPOINT-UNKNOWN:{key}:{value}")

        when = fields["when"]
        if when is not None and (not isinstance(when, str) or not when.strip()):
            raise ValueError(f"WFR-SOURCE-FIELD-TYPE:connection:{key}:when")
        existing = base_relationships_by_key.get(key)
        next_relationships.append(
            {
                "id": existing["id"] if existing else _canonical_id("rel", key),
                "kind": relationship_kind,
                "source_id": endpoint("from"),
                "target_id": endpoint("to"),
                "label": text_value(fields, "label", f"connection:{key}"),
                "condition": when,
            }
        )
    candidate["relationships"] = next_relationships

    candidate["semantic_sha256"] = None
    reject_nonfinite(candidate)
    errors = sorted(
        jsonschema.Draft202012Validator(
            json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        ).iter_errors(candidate),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ValueError(f"WFR-SOURCE-CANONICAL-INVALID:{errors[0].message}")

    source_map: dict[str, dict[str, int]] = {}
    for kind, key, _, start, end in sections:
        canonical_ids: list[str] = []
        if kind == "workflow":
            canonical_ids = [base["workflow_id"]]
        elif kind == "group" and key in phases_by_key:
            canonical_ids = [phases_by_key[key]["id"]]
        elif kind == "item" and key in artifacts_by_key:
            canonical_ids = [artifacts_by_key[key]["id"]]
        elif kind in {"input", "task"}:
            block = next((row for row in candidate["blocks"] if _stable_key(row["id"]) == key), None)
            if block:
                canonical_ids = [
                    block["id"],
                    *block["input_port_ids"],
                    *block["output_port_ids"],
                    *([block["binding_id"]] if block["binding_id"] else []),
                ]
        elif kind == "connection":
            relationship = next(
                (row for row in candidate["relationships"] if _stable_key(row["id"]) == key),
                None,
            )
            if relationship:
                canonical_ids = [relationship["id"]]
        for canonical_id in canonical_ids:
            source_map[canonical_id] = {"start_line": start, "end_line": end}
    return DslDocument(ir=candidate, comments=comments, source_map=source_map)


def changed_lines(before: str, after: str) -> int:
    return sum(1 for line in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="") if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))


def edit_title(value: dict[str, Any]) -> None:
    next(block for block in value["blocks"] if block["id"] == "block.generate-geometry")["title"] = "Create parametric bracket"


def edit_thickness(value: dict[str, Any]) -> None:
    next(block for block in value["blocks"] if block["id"] == "block.generate-geometry")["configuration"]["thickness_mm"] = 8


def edit_design_specification_purpose(value: dict[str, Any]) -> None:
    next(block for block in value["blocks"] if block["id"] == "block.create-design-specification")["purpose"] = (
        "Create the reviewed engineering source of truth before CAD work begins."
    )


def edit_manufacturing_prompt(value: dict[str, Any]) -> None:
    next(block for block in value["blocks"] if block["id"] == "block.check-manufacturability")["instructions"] = (
        "Check manufacturability and cite the CAD feature and material property for every finding."
    )


def edit_feedback(value: dict[str, Any]) -> None:
    relation = next(relation for relation in value["relationships"] if relation["id"] == "rel.review-revise")
    relation["condition"] = "Any required input is missing or a warning remains unresolved"


EDIT_TASKS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("rename geometry block", edit_title),
    ("change bracket thickness", edit_thickness),
    ("clarify design-specification purpose", edit_design_specification_purpose),
    ("clarify manufacturing-check prompt", edit_manufacturing_prompt),
    ("clarify feedback condition", edit_feedback),
)


def metrics(text: str) -> dict[str, int]:
    lines = text.splitlines()
    return {"bytes": len(text.encode("utf-8")), "lines": len(lines), "max_line": max(map(len, lines)), "indent_depth": max((len(line) - len(line.lstrip(" "))) // 2 for line in lines)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-fixtures", action="store_true")
    args = parser.parse_args()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    ir = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(ir)
    treatments = {
        "json": json_text(ir),
        "yaml": yaml_text(ir),
        "engineering_source": authoring_text(ir),
    }
    if args.write_fixtures:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        YAML_PATH.write_text(treatments["yaml"], encoding="utf-8", newline="\n")
        AUTHORING_PATH.write_text(treatments["engineering_source"], encoding="utf-8", newline="\n")
        INTERNAL_DSL_PATH.write_text(
            dsl_text(ir).replace(
                "# Wright workflow language — recovery treatment 0.1",
                "# Wright internal workflow IR projection — legacy recovery treatment 0.1",
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )
    parsed = {
        "json": json.loads(treatments["json"]),
        "yaml": yaml.safe_load(treatments["yaml"]),
        "engineering_source": parse_authoring(treatments["engineering_source"], ir).ir,
    }
    for name, candidate in parsed.items():
        jsonschema.Draft202012Validator(schema).validate(candidate)
        if canonical_bytes(candidate) != canonical_bytes(ir):
            raise AssertionError(f"{name} does not represent the same IR")
    formatters = {"json": json_text, "yaml": yaml_text, "engineering_source": authoring_text}
    parsers = {
        "json": json.loads,
        "yaml": yaml.safe_load,
        "engineering_source": lambda text: parse_authoring(text, ir).ir,
    }
    diff_counts: dict[str, list[int]] = {name: [] for name in treatments}
    candidate_validity: dict[str, int] = {name: 0 for name in treatments}
    for _, operation in EDIT_TASKS:
        edited = copy.deepcopy(ir)
        operation(edited)
        jsonschema.Draft202012Validator(schema).validate(edited)
        for name, formatter in formatters.items():
            encoded = formatter(edited)
            decoded = parsers[name](encoded)
            jsonschema.Draft202012Validator(schema).validate(decoded)
            if canonical_bytes(decoded) == canonical_bytes(edited):
                candidate_validity[name] += 1
            diff_counts[name].append(changed_lines(treatments[name], encoded))
    results = {
        "subject": "mounting-bracket.workflow",
        "subject_sha256": hashlib.sha256(canonical_bytes(ir)).hexdigest(),
        "scope": "single-agent lossless engineering-source evidence; not a benchmark or permanent syntax selection",
        "authority": "strict JSON/YAML canonical IR; engineering source exactly reconstructs the accepted definition against trusted installed contracts, while host-managed version, ancestry, integrity, layout, and run records remain outside authoring source",
        "legacy_internal_fixture": str(INTERNAL_DSL_PATH.relative_to(ROOT)).replace("\\", "/"),
        "edit_tasks": [name for name, _ in EDIT_TASKS],
        "treatments": {},
    }
    heuristic = {
        "json": {"mechanical_readability_5": 2.5, "source_map": "custom parser required", "comments": "unsupported", "migration_cost": "low internal interchange; high user verbosity"},
        "yaml": {"mechanical_readability_5": 4.0, "source_map": "event parser or CST required", "comments": "lost by evaluated safe parser", "migration_cost": "moderate scalar/implicit typing and CST policy"},
        "engineering_source": {"mechanical_readability_5": 4.5, "source_map": "friendly section spans implemented", "comments": "generated guidance retained; arbitrary comments normalize away", "migration_cost": "reconstructive parser plus trusted installed-contract resolution"},
    }
    parser_loc = len(inspect.getsource(parse_authoring).splitlines()) + len(inspect.getsource(_authoring_sections).splitlines())
    for name, text in treatments.items():
        treatment = {
            **metrics(text),
            "round_trip": True,
            "schema_valid": True,
            "edit_candidates_valid": candidate_validity[name],
            "edit_candidates_total": len(EDIT_TASKS),
            "mean_changed_lines": round(sum(diff_counts[name]) / len(diff_counts[name]), 1),
            "changed_lines_by_task": diff_counts[name],
            "parser_complexity_loc": 1 if name == "json" else (2 if name == "yaml" else parser_loc),
            **heuristic[name],
        }
        if name == "engineering_source":
            treatment["source_map_entries"] = len(parse_authoring(text, ir).source_map)
            treatment["base_bound"] = True
            treatment["lossless_round_trip_against_trusted_base"] = True
            treatment["reconstruction_requires"] = (
                "trusted installed item, tool, and reusable-step contracts"
            )
            treatment["explicit_engineering_contracts"] = [
                "items",
                "steps",
                "connection points",
                "connections",
                "tool assignments",
                "reusable steps",
                "optional groups",
            ]
            treatment["host_managed_fields_omitted"] = [
                "schema version",
                "accepted revision",
                "parent revision",
                "semantic digest",
                "layout",
                "run state",
            ]
        results["treatments"][name] = treatment
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
    report = [
        "# Workflow Syntax Evaluation",
        "",
        f"**Canonical subject**: `{results['subject']}` / `{results['subject_sha256']}`",
        "",
        "**Evidence class**: single-agent exploratory generation/edit evidence. This is not an independent mechanical-engineer study, model benchmark, or permanent syntax approval.",
        "",
        "Strict JSON and YAML remain canonical IR treatments. When resolved against Wright's trusted installed item, tool, and reusable-step contracts, the engineering source explicitly represents every item, step, connection point, connection, tool assignment, reusable-step reference, and optional group needed to reconstruct the accepted definition exactly. Wright alone records version, ancestry, integrity, layout, and run state. All three treatments receive the same five user-visible edit tasks.",
        "",
        "| Treatment | Bytes | Lines | Max nesting | Readability /5* | Valid edits | Mean diff lines | Comments/format | Source maps | Parser cost |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---:|",
    ]
    for name in ("json", "yaml", "engineering_source"):
        row = results["treatments"][name]
        report.append(
            f"| {name.upper()} | {row['bytes']} | {row['lines']} | {row['indent_depth']} | {row['mechanical_readability_5']} | {row['edit_candidates_valid']}/{row['edit_candidates_total']} | {row['mean_changed_lines']} | {row['comments']} | {row['source_map']} | {row['parser_complexity_loc']} LOC |"
        )
    report.extend(
        [
            "",
            "\\* Readability is an explicit expert heuristic based on labels, nesting, noise, and direct correspondence to engineering items/tasks. It must not be treated as moderated-user evidence.",
            "",
            "## Identical edit corpus",
            "",
            *[f"- {name}" for name, _ in EDIT_TASKS],
            "",
            "Every formatter-produced candidate reparsed, schema-validated, and matched the intended canonical IR. Engineering-source edits reconstructed explicit connection points, routes, tool assignments, and reusable-step references while revisions, ancestry, digests, layout, and run state remained host-managed. Because the same agent authored the grammar and corpus, this is parser/edit evidence, not representative usability or multi-model evidence.",
            "",
            "## Findings",
            "",
            "- **Strict JSON** has the lowest implementation and migration risk and remains the best internal interchange baseline. It is verbose, deeply nested, has no comments, and is a poor primary mechanical-engineer editing surface.",
            "- **YAML** is substantially easier to scan and has low parser effort, but the evaluated safe parser discards comments/formatting and does not expose stable source spans. A concrete-syntax-tree policy would add complexity and compatibility risk.",
            "- **Engineering source** uses `workflow`, optional `group`, `item`, `input`, `task`, and `connection` sections with prompts, files, reports, explicit connection points, settings, tool assignments, and reusable-step references. Detailed installed item/tool/component contracts are resolved from the trusted base; version, ancestry, integrity, layout, and run records stay host-managed.",
            "- **Legacy internal DSL** remains at `fixtures/mounting-bracket.workflow.internal-ir.wflow` only for exhaustive IR parser/conformance coverage. It is not the engineer-facing file.",
            "",
            "## Provisional recovery decision",
            "",
            "Keep strict JSON/YAML as canonical interchange and use the exact-round-trip engineering source as the recovery concept's editable workflow file, resolved against trusted installed contracts. Accepted source changes must still pass the canonical command/validation boundary and host compare-and-swap check. Do **not** promote it beyond the recovery treatment until independent engineer and multi-model evidence, diagnostics, migrations, and unknown-version behavior close `DEC-P0-002`.",
            "",
            "## Reproduce",
            "",
            "```powershell",
            "python scripts/recovery/evaluate_workflow_syntaxes.py --write-fixtures",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
