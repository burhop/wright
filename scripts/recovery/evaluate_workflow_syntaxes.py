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
DSL_PATH = FIXTURES / "mounting-bracket.workflow.wflow"
RESULT_PATH = EVIDENCE / "syntax-evaluation.json"
REPORT_PATH = EVIDENCE / "syntax-evaluation.md"


@dataclass(frozen=True)
class DslDocument:
    ir: dict[str, Any]
    comments: tuple[str, ...]
    source_map: dict[str, dict[str, int]]


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


def changed_lines(before: str, after: str) -> int:
    return sum(1 for line in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="") if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))


def edit_title(value: dict[str, Any]) -> None:
    next(block for block in value["blocks"] if block["id"] == "block.generate-geometry")["title"] = "Create parametric bracket"


def edit_thickness(value: dict[str, Any]) -> None:
    next(block for block in value["blocks"] if block["id"] == "block.generate-geometry")["configuration"]["thickness_mm"] = 8


def edit_material_optional(value: dict[str, Any]) -> None:
    port = next(port for port in value["ports"] if port["id"] == "port.material-in")
    port["required"] = False
    port["cardinality"] = "optional"


def edit_binding(value: dict[str, Any]) -> None:
    next(binding for binding in value["bindings"] if binding["id"] == "binding.export-step")["tool_id"] = "tool.export-step-ap242-reviewed"


def edit_feedback(value: dict[str, Any]) -> None:
    relation = next(relation for relation in value["relationships"] if relation["id"] == "rel.review-revise")
    relation["condition"] = "Any required input is missing or a warning remains unresolved"


EDIT_TASKS: tuple[tuple[str, Callable[[dict[str, Any]], None]], ...] = (
    ("rename geometry block", edit_title),
    ("change bracket thickness", edit_thickness),
    ("make material optional", edit_material_optional),
    ("change exact export tool", edit_binding),
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
    treatments = {"json": json_text(ir), "yaml": yaml_text(ir), "dsl": dsl_text(ir)}
    if args.write_fixtures:
        FIXTURES.mkdir(parents=True, exist_ok=True)
        YAML_PATH.write_text(treatments["yaml"], encoding="utf-8", newline="\n")
        DSL_PATH.write_text(treatments["dsl"], encoding="utf-8", newline="\n")
    parsed = {
        "json": json.loads(treatments["json"]),
        "yaml": yaml.safe_load(treatments["yaml"]),
        "dsl": parse_dsl(treatments["dsl"]).ir,
    }
    for name, candidate in parsed.items():
        jsonschema.Draft202012Validator(schema).validate(candidate)
        if canonical_bytes(candidate) != canonical_bytes(ir):
            raise AssertionError(f"{name} does not represent the same IR")
    formatters = {"json": json_text, "yaml": yaml_text, "dsl": dsl_text}
    parsers = {"json": json.loads, "yaml": yaml.safe_load, "dsl": lambda text: parse_dsl(text).ir}
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
    dsl_comment = "Reviewer note: keep the 6061-T6 assumption visible."
    dsl_with_comment = dsl_text(ir, (dsl_comment,))
    dsl_parsed = parse_dsl(dsl_with_comment)
    comment_preserved = dsl_comment in dsl_text(dsl_parsed.ir, dsl_parsed.comments)
    results = {
        "subject": "mounting-bracket.workflow",
        "subject_sha256": hashlib.sha256(canonical_bytes(ir)).hexdigest(),
        "scope": "single-agent exploratory syntax evidence; not a benchmark or permanent selection",
        "edit_tasks": [name for name, _ in EDIT_TASKS],
        "treatments": {},
    }
    heuristic = {
        "json": {"mechanical_readability_5": 2.5, "source_map": "custom parser required", "comments": "unsupported", "migration_cost": "low internal interchange; high user verbosity"},
        "yaml": {"mechanical_readability_5": 4.0, "source_map": "event parser or CST required", "comments": "lost by evaluated safe parser", "migration_cost": "moderate scalar/implicit typing and CST policy"},
        "dsl": {"mechanical_readability_5": 4.5, "source_map": "section spans implemented", "comments": "leading comments preserved; canonical formatting normalized", "migration_cost": "highest parser/grammar/version ownership"},
    }
    parser_loc = len(inspect.getsource(parse_dsl).splitlines())
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
        if name == "dsl":
            treatment["source_map_entries"] = len(parse_dsl(text).source_map)
            treatment["comment_preservation_probe"] = comment_preserved
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
        "All three files validate against the same IR schema, parse to byte-identical canonical semantics, and receive the same five edit tasks.",
        "",
        "| Treatment | Bytes | Lines | Max nesting | Readability /5* | Valid edits | Mean diff lines | Comments/format | Source maps | Parser cost |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---:|",
    ]
    for name in ("json", "yaml", "dsl"):
        row = results["treatments"][name]
        report.append(
            f"| {name.upper()} | {row['bytes']} | {row['lines']} | {row['indent_depth']} | {row['mechanical_readability_5']} | {row['edit_candidates_valid']}/{row['edit_candidates_total']} | {row['mean_changed_lines']} | {row['comments']} | {row['source_map']} | {row['parser_complexity_loc']} LOC |"
        )
    report.extend(
        [
            "",
            "\\* Readability is an explicit expert heuristic based on labels, nesting, noise, and direct correspondence to blocks/ports. It must not be treated as moderated-user evidence.",
            "",
            "## Identical edit corpus",
            "",
            *[f"- {name}" for name, _ in EDIT_TASKS],
            "",
            "Every formatter-produced candidate reparsed, schema-validated, and matched the intended canonical IR. Because the same agent authored the grammar and corpus, this is useful parser/edit evidence but optimistic AI-generation evidence. A permanent choice still requires independent model samples with invalid controls and representative engineers.",
            "",
            "## Findings",
            "",
            "- **Strict JSON** has the lowest implementation and migration risk and remains the best internal interchange baseline. It is verbose, deeply nested, has no comments, and is a poor primary mechanical-engineer editing surface.",
            "- **YAML** is substantially easier to scan and has low parser effort, but the evaluated safe parser discards comments/formatting and does not expose stable source spans. A concrete-syntax-tree policy would add complexity and compatibility risk.",
            "- **Small DSL** has the clearest one-section-per-concept correspondence, implemented semantic-ID source spans, and preserved leading comments. It has the highest grammar/parser/migration ownership and the weakest ecosystem maturity.",
            "",
            "## Provisional recovery decision",
            "",
            "Use strict JSON as canonical interchange and the small DSL only as the disposable recovery concept's Code treatment. This is reversible and maximizes evidence about block/port correspondence. Do **not** select a permanent user-facing syntax until independent mechanical-engineer readability and multi-model generation/edit studies, comment/CST policy, migrations, and unknown-version behavior close `DEC-P0-002`.",
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
