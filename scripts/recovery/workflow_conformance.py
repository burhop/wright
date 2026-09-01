#!/usr/bin/env python3
"""Pure recovery conformance kernel for canonical workflow IR vNext.

This module is deliberately small and side-effect free. It is concept evidence,
not a production persistence or execution service.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Mapping, Sequence

import jsonschema
import yaml

from scripts.recovery.evaluate_workflow_syntaxes import (
    DslDocument,
    dsl_text,
    json_text,
    parse_dsl,
    yaml_text,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT
    / "specs"
    / "080-canonical-workflow-recovery"
    / "contracts"
    / "canonical-workflow-ir.schema.json"
)
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
SCHEMA_VALIDATOR = jsonschema.Draft202012Validator(SCHEMA)
Syntax = Literal["json", "yaml", "dsl"]


@dataclass(frozen=True)
class SourceSpan:
    start_line: int
    start_column: int = 1
    end_line: int | None = None
    end_column: int | None = None


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Literal["error", "warning"]
    explanation: str
    correction: str
    semantic_id: str | None = None
    source_span: SourceSpan | None = None
    path: str | None = None


@dataclass(frozen=True)
class ParseResult:
    ok: bool
    ir: dict[str, Any] | None
    diagnostics: tuple[Diagnostic, ...]
    source_map: dict[str, SourceSpan]
    comments: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    diagnostics: tuple[Diagnostic, ...]


@dataclass(frozen=True)
class ApplyResult:
    ok: bool
    candidate: dict[str, Any] | None
    diagnostics: tuple[Diagnostic, ...]
    semantic_diff: tuple[dict[str, Any], ...]


class DuplicateKeyError(ValueError):
    def __init__(self, key: object, line: int | None = None) -> None:
        super().__init__(str(key))
        self.key = str(key)
        self.line = line


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _strict_yaml_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as error:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from error
        if duplicate:
            raise DuplicateKeyError(key, key_node.start_mark.line + 1)
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _strict_yaml_mapping
)


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite number {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, Mapping):
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            yield from _walk(nested)


def _nonfinite(value: Any) -> bool:
    return any(isinstance(item, float) and not math.isfinite(item) for item in _walk(value))


def _line_map(text: str) -> dict[str, SourceSpan]:
    result: dict[str, SourceSpan] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        identity: str | None = None
        if '"id":' in stripped:
            try:
                identity = str(json.loads("{" + stripped.rstrip(",") + "}")["id"])
            except (json.JSONDecodeError, KeyError, TypeError):
                identity = None
        elif stripped.startswith("- id:") or stripped.startswith("id:"):
            identity = stripped.split(":", 1)[1].strip().strip('"\'')
        if identity:
            result[identity] = SourceSpan(line_number, max(1, line.find(identity) + 1), line_number, len(line) + 1)
    return result


def _parse_error(code: str, explanation: str, correction: str, line: int | None = None) -> ParseResult:
    span = SourceSpan(line) if line is not None else None
    return ParseResult(False, None, (Diagnostic(code, "error", explanation, correction, source_span=span),), {})


def parse(text: str, syntax: Syntax) -> ParseResult:
    """Parse one complete document with duplicate-key and numeric strictness."""

    try:
        comments: tuple[str, ...] = ()
        if syntax == "json":
            value = json.loads(
                text,
                object_pairs_hook=_strict_object,
                parse_constant=_reject_json_constant,
            )
            source_map = _line_map(text)
        elif syntax == "yaml":
            value = yaml.load(text, Loader=StrictSafeLoader)
            source_map = _line_map(text)
        elif syntax == "dsl":
            document: DslDocument = parse_dsl(text)
            value = document.ir
            comments = document.comments
            source_map = {
                key: SourceSpan(span["start_line"], 1, span["end_line"], None)
                for key, span in document.source_map.items()
            }
        else:
            return _parse_error(
                "WFR-SYNTAX-UNSUPPORTED",
                f"Syntax {syntax!r} is not supported.",
                "Choose json, yaml, or dsl for recovery evidence.",
            )
    except DuplicateKeyError as error:
        return _parse_error(
            "WFR-TEXT-DUPLICATE-KEY",
            f"Field {error.key!r} is declared more than once.",
            "Keep exactly one value for the field.",
            error.line,
        )
    except json.JSONDecodeError as error:
        return _parse_error(
            "WFR-TEXT-SYNTAX",
            error.msg,
            "Correct the delimiter or scalar at the reported location.",
            error.lineno,
        )
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        return _parse_error(
            "WFR-TEXT-SYNTAX",
            str(getattr(error, "problem", None) or error),
            "Correct the YAML structure at the reported location.",
            None if mark is None else mark.line + 1,
        )
    except ValueError as error:
        message = str(error)
        parts = message.split(":")
        line = next((int(part) for part in parts if part.isdigit()), None)
        code = parts[0] if parts[0].startswith("WFR-") else "WFR-TEXT-VALUE-INVALID"
        return _parse_error(code, message, "Correct or remove the reported value.", line)

    if not isinstance(value, dict):
        return _parse_error(
            "WFR-TEXT-DOCUMENT-TYPE",
            "A workflow document must be an object.",
            "Provide one complete workflow document.",
        )
    if _nonfinite(value):
        return _parse_error(
            "WFR-TEXT-NUMBER-NONFINITE",
            "NaN and infinite numbers are not portable canonical values.",
            "Use a finite number or an explicit string value.",
        )
    validation = validate(value, source_map)
    if not validation.valid:
        return ParseResult(False, None, validation.diagnostics, source_map, comments)
    return ParseResult(True, copy.deepcopy(value), (), source_map, comments)


def format(ir: Mapping[str, Any], syntax: Syntax, comments: tuple[str, ...] = ()) -> tuple[str, dict[str, SourceSpan]]:
    """Canonicalize a valid IR into one recovery syntax treatment."""

    validation = validate(ir)
    if not validation.valid:
        raise ValueError(validation.diagnostics[0].code)
    value = copy.deepcopy(dict(ir))
    if syntax == "json":
        text = json_text(value)
    elif syntax == "yaml":
        text = yaml_text(value)
    elif syntax == "dsl":
        text = dsl_text(value, comments)
    else:
        raise ValueError("WFR-SYNTAX-UNSUPPORTED")
    reparsed = parse(text, syntax)
    if not reparsed.ok:
        raise AssertionError(reparsed.diagnostics)
    return text, reparsed.source_map


def _pointer(error: jsonschema.ValidationError) -> str:
    return "/" + "/".join(str(part) for part in error.absolute_path)


def _semantic_id_at_path(ir: Mapping[str, Any], path: Sequence[Any]) -> str | None:
    value: Any = ir
    semantic_id: str | None = None
    try:
        for part in path:
            value = value[part]
            if isinstance(value, Mapping) and isinstance(value.get("id"), str):
                semantic_id = value["id"]
    except (KeyError, IndexError, TypeError):
        pass
    return semantic_id


def _diag(
    code: str,
    explanation: str,
    correction: str,
    *,
    semantic_id: str | None = None,
    source_map: Mapping[str, SourceSpan] | None = None,
    path: str | None = None,
) -> Diagnostic:
    return Diagnostic(
        code,
        "error",
        explanation,
        correction,
        semantic_id,
        None if source_map is None or semantic_id is None else source_map.get(semantic_id),
        path,
    )


def validate(
    ir: Mapping[str, Any], source_map: Mapping[str, SourceSpan] | None = None
) -> ValidationResult:
    """Apply JSON Schema and cross-entity semantic invariants."""

    diagnostics: list[Diagnostic] = []
    for error in sorted(SCHEMA_VALIDATOR.iter_errors(ir), key=lambda item: list(item.absolute_path)):
        semantic_id = _semantic_id_at_path(ir, list(error.absolute_path))
        diagnostics.append(
            _diag(
                "WFR-SCHEMA-INVALID",
                error.message,
                "Use the declared field, type, enum, or required property.",
                semantic_id=semantic_id,
                source_map=source_map,
                path=_pointer(error),
            )
        )
    if diagnostics:
        return ValidationResult(False, tuple(diagnostics))
    if _nonfinite(ir):
        return ValidationResult(
            False,
            (_diag("WFR-TEXT-NUMBER-NONFINITE", "Canonical numbers must be finite.", "Replace NaN or infinity with a finite value."),),
        )

    collections = ("phases", "blocks", "ports", "relationships", "artifact_contracts", "bindings", "components")
    by_id: dict[str, tuple[str, Mapping[str, Any]]] = {}
    for collection in collections:
        for item in ir.get(collection, []):
            identity = str(item["id"])
            if identity in by_id:
                diagnostics.append(
                    _diag(
                        "WFR-ID-DUPLICATE",
                        f"Stable identity {identity} appears in both {by_id[identity][0]} and {collection}.",
                        "Assign a globally unique stable identity.",
                        semantic_id=identity,
                        source_map=source_map,
                    )
                )
            else:
                by_id[identity] = (collection, item)

    block_by_id = {str(row["id"]): row for row in ir["blocks"]}
    block_ids = set(block_by_id)
    phase_ids = {str(row["id"]) for row in ir["phases"]}
    port_by_id = {str(row["id"]): row for row in ir["ports"]}
    artifact_ids = {str(row["id"]) for row in ir["artifact_contracts"]}
    binding_ids = {str(row["id"]) for row in ir["bindings"]}
    component_ids = {str(row["id"]) for row in ir["components"]}
    block_order: dict[str, int] = {}
    phase_memberships: dict[str, list[str]] = {}
    for phase in sorted(ir["phases"], key=lambda row: int(row["order"])):
        for index, block_id in enumerate(phase["block_ids"]):
            identity = str(block_id)
            block_order[identity] = int(phase["order"]) * 10000 + index
            phase_memberships.setdefault(identity, []).append(str(phase["id"]))

    def require_ref(owner: str, ref: Any, allowed: set[str], field: str) -> None:
        if ref is not None and str(ref) not in allowed:
            diagnostics.append(
                _diag(
                    "WFR-REFERENCE-DANGLING",
                    f"{owner}.{field} references missing identity {ref}.",
                    "Choose an existing compatible identity or remove the reference.",
                    semantic_id=owner,
                    source_map=source_map,
                    path=field,
                )
            )

    for phase in ir["phases"]:
        for block_id in phase["block_ids"]:
            require_ref(str(phase["id"]), block_id, block_ids, "block_ids")
    for block in ir["blocks"]:
        owner = str(block["id"])
        require_ref(owner, block["phase_id"], phase_ids, "phase_id")
        memberships = phase_memberships.get(owner, [])
        declared_phase = None if block["phase_id"] is None else str(block["phase_id"])
        if (declared_phase is None and memberships) or (
            declared_phase is not None and memberships != [declared_phase]
        ):
            diagnostics.append(
                _diag(
                    "WFR-PHASE-MEMBERSHIP",
                    f"{owner} and its declared phase are not exactly reciprocal.",
                    "List the block exactly once in its declared phase, or in no phase when phase_id is null.",
                    semantic_id=owner,
                    source_map=source_map,
                    path="phase_id",
                )
            )
        require_ref(owner, block["binding_id"], binding_ids, "binding_id")
        if block["component_ref"] is not None:
            require_ref(owner, block["component_ref"]["component_id"], component_ids, "component_ref.component_id")
        for field, direction in (("input_port_ids", "input"), ("output_port_ids", "output")):
            for port_id in block[field]:
                require_ref(owner, port_id, set(port_by_id), field)
                port = port_by_id.get(str(port_id))
                if port and (port["owner_block_id"] != owner or port["direction"] != direction):
                    diagnostics.append(
                        _diag(
                            "WFR-PORT-OWNERSHIP",
                            f"{port_id} is not a {direction} owned by {owner}.",
                            "Use a port owned by the block with the declared direction.",
                            semantic_id=str(port_id),
                            source_map=source_map,
                        )
                    )
    for port in ir["ports"]:
        owner = str(port["id"])
        require_ref(owner, port["owner_block_id"], block_ids, "owner_block_id")
        require_ref(owner, port["artifact_contract_id"], artifact_ids, "artifact_contract_id")
        owner_block = block_by_id.get(str(port["owner_block_id"]))
        if owner_block is not None:
            reciprocal_field = "input_port_ids" if port["direction"] == "input" else "output_port_ids"
            reciprocal_count = sum(1 for port_id in owner_block[reciprocal_field] if str(port_id) == owner)
            if reciprocal_count != 1:
                diagnostics.append(
                    _diag(
                        "WFR-PORT-OWNERSHIP",
                        f"{owner} is not listed exactly once as a {port['direction']} by {port['owner_block_id']}.",
                        "Add the port exactly once to the owning block's matching direction list.",
                        semantic_id=owner,
                        source_map=source_map,
                        path="owner_block_id",
                    )
                )
    endpoint_ids = block_ids | set(port_by_id)
    endpoint_pairs: dict[tuple[str, str], str] = {}
    incoming_data: dict[str, list[str]] = {}
    adjacency: dict[str, list[tuple[str, str]]] = {}
    for relation in ir["relationships"]:
        owner = str(relation["id"])
        source_id = str(relation["source_id"])
        target_id = str(relation["target_id"])
        endpoint_key = (source_id, target_id)
        if endpoint_key in endpoint_pairs:
            diagnostics.append(
                _diag(
                    "WFR-RELATIONSHIP-DUPLICATE",
                    f"{owner} duplicates the endpoints of {endpoint_pairs[endpoint_key]}.",
                    "Keep one relationship for an endpoint pair or introduce a distinct semantic target.",
                    semantic_id=owner,
                    source_map=source_map,
                )
            )
        else:
            endpoint_pairs[endpoint_key] = owner
        require_ref(owner, relation["source_id"], endpoint_ids, "source_id")
        require_ref(owner, relation["target_id"], endpoint_ids, "target_id")
        source_block_id: str | None = None
        target_block_id: str | None = None
        if relation["kind"] == "data":
            source_port = port_by_id.get(source_id)
            target_port = port_by_id.get(target_id)
            if not source_port or not target_port or source_port["direction"] != "output" or target_port["direction"] != "input":
                diagnostics.append(
                    _diag(
                        "WFR-DATA-ENDPOINTS",
                        "A data relationship must connect an output port to an input port.",
                        "Reconnect from a right-side output socket to a compatible left-side input socket.",
                        semantic_id=owner,
                        source_map=source_map,
                    )
                )
            elif source_port["type_id"] != target_port["type_id"]:
                diagnostics.append(
                    _diag(
                        "WFR-PORT-TYPE-MISMATCH",
                        f"{source_port['type_id']} cannot feed {target_port['type_id']}.",
                        "Choose ports with the same declared type or insert an explicit adapter block.",
                        semantic_id=owner,
                        source_map=source_map,
                    )
                )
            if source_port and target_port:
                source_block_id = str(source_port["owner_block_id"])
                target_block_id = str(target_port["owner_block_id"])
                incoming_data.setdefault(target_id, []).append(owner)
        else:
            if source_id not in block_ids or target_id not in block_ids:
                diagnostics.append(
                    _diag(
                        "WFR-NONDATA-ENDPOINTS",
                        f"{owner} must connect block identities for {relation['kind']} flow.",
                        "Choose existing block endpoints; ports are only valid for data relationships.",
                        semantic_id=owner,
                        source_map=source_map,
                    )
                )
            else:
                source_block_id = source_id
                target_block_id = target_id
            source_block = block_by_id.get(source_id)
            if relation["kind"] in {"decision", "feedback"} and source_block and source_block["kind"] not in {"decision", "approval"}:
                diagnostics.append(
                    _diag(
                        "WFR-RELATIONSHIP-SOURCE-KIND",
                        f"{owner} must originate at a decision or approval block.",
                        "Choose a decision/approval source or use data/control flow.",
                        semantic_id=owner,
                        source_map=source_map,
                    )
                )
            if relation["kind"] == "feedback" and source_id in block_order and target_id in block_order and block_order[target_id] >= block_order[source_id]:
                diagnostics.append(
                    _diag(
                        "WFR-FEEDBACK-DIRECTION",
                        f"{owner} must return to an earlier block or component.",
                        "Choose an earlier revision target or use forward control flow.",
                        semantic_id=owner,
                        source_map=source_map,
                    )
                )
        if relation["kind"] != "feedback" and source_block_id and target_block_id:
            adjacency.setdefault(source_block_id, []).append((target_block_id, owner))
    for port_id, relationship_ids in incoming_data.items():
        port = port_by_id[port_id]
        if port["cardinality"] != "many" and len(relationship_ids) > 1:
            diagnostics.append(
                _diag(
                    "WFR-PORT-CARDINALITY",
                    f"{port_id} accepts {port['cardinality']} but has {len(relationship_ids)} incoming data relationships.",
                    "Remove extra connections or declare many cardinality.",
                    semantic_id=port_id,
                    source_map=source_map,
                )
            )
    visit_state: dict[str, int] = {}
    cycle_reported = False

    def visit(block_id: str) -> None:
        nonlocal cycle_reported
        if cycle_reported:
            return
        visit_state[block_id] = 1
        for target_id, relationship_id in adjacency.get(block_id, []):
            if visit_state.get(target_id, 0) == 1:
                diagnostics.append(
                    _diag(
                        "WFR-CYCLE-NON-FEEDBACK",
                        f"{relationship_id} closes a cycle without an explicit feedback relationship.",
                        "Mark the intentional revision back-edge as feedback or remove the cycle.",
                        semantic_id=relationship_id,
                        source_map=source_map,
                    )
                )
                cycle_reported = True
                return
            if visit_state.get(target_id, 0) == 0:
                visit(target_id)
        visit_state[block_id] = 2

    for block_id in block_ids:
        if visit_state.get(block_id, 0) == 0:
            visit(block_id)
    for artifact in ir["artifact_contracts"]:
        owner = str(artifact["id"])
        require_ref(owner, artifact["producer_block_id"], block_ids, "producer_block_id")
        for block_id in artifact["required_for_block_ids"]:
            require_ref(owner, block_id, block_ids, "required_for_block_ids")
    artifacts_by_id = {str(row["id"]): row for row in ir["artifact_contracts"]}
    for binding in ir["bindings"]:
        owner = str(binding["id"])
        binding_owner_ids = {
            str(block["id"])
            for block in ir["blocks"]
            if block["binding_id"] is not None and str(block["binding_id"]) == owner
        }
        for mapping in binding["argument_map"]:
            semantic_source = str(mapping["semantic_source"])
            port = port_by_id.get(semantic_source)
            configuration_owner = None
            for block_id in binding_owner_ids:
                prefix = f"{block_id}.configuration."
                if semantic_source.startswith(prefix):
                    key = semantic_source[len(prefix):]
                    if key in block_by_id[block_id]["configuration"]:
                        configuration_owner = block_id
                        break
            if port is None and configuration_owner is None:
                diagnostics.append(
                    _diag(
                        "WFR-REFERENCE-DANGLING",
                        f"{owner} maps missing argument source {semantic_source}.",
                        "Map an owned input port or declared configuration value.",
                        semantic_id=owner,
                        source_map=source_map,
                        path="argument_map.semantic_source",
                    )
                )
            elif port is not None and (
                port["direction"] != "input"
                or (binding_owner_ids and str(port["owner_block_id"]) not in binding_owner_ids)
            ):
                diagnostics.append(
                    _diag(
                        "WFR-BINDING-MAP-DIRECTION",
                        f"{owner} argument source {semantic_source} is not an owned input.",
                        "Map an input port owned by a block using this binding.",
                        semantic_id=owner,
                        source_map=source_map,
                        path="argument_map.semantic_source",
                    )
                )
        for mapping in binding["result_map"]:
            semantic_source = str(mapping["semantic_source"])
            port = port_by_id.get(semantic_source)
            artifact = artifacts_by_id.get(semantic_source)
            if port is None and artifact is None:
                diagnostics.append(
                    _diag(
                        "WFR-REFERENCE-DANGLING",
                        f"{owner} maps missing result target {semantic_source}.",
                        "Map an owned output port or produced artifact contract.",
                        semantic_id=owner,
                        source_map=source_map,
                        path="result_map.semantic_source",
                    )
                )
            elif port is not None and (
                port["direction"] != "output"
                or (binding_owner_ids and str(port["owner_block_id"]) not in binding_owner_ids)
            ):
                diagnostics.append(
                    _diag(
                        "WFR-BINDING-MAP-DIRECTION",
                        f"{owner} result target {semantic_source} is not an owned output.",
                        "Map an output port owned by a block using this binding.",
                        semantic_id=owner,
                        source_map=source_map,
                        path="result_map.semantic_source",
                    )
                )
            elif artifact is not None and binding_owner_ids and (
                artifact["producer_block_id"] is None
                or str(artifact["producer_block_id"]) not in binding_owner_ids
            ):
                diagnostics.append(
                    _diag(
                        "WFR-BINDING-MAP-DIRECTION",
                        f"{owner} result artifact {semantic_source} is not produced by an owning block.",
                        "Map an artifact produced by a block using this binding.",
                        semantic_id=owner,
                        source_map=source_map,
                        path="result_map.semantic_source",
                    )
                )
    for component in ir["components"]:
        owner = str(component["id"])
        for field, direction in (("input_port_ids", "input"), ("output_port_ids", "output")):
            for port_id in component[field]:
                require_ref(owner, port_id, set(port_by_id), field)
                port = port_by_id.get(str(port_id))
                if port is not None and port["direction"] != direction:
                    diagnostics.append(
                        _diag(
                            "WFR-COMPONENT-PORT-DIRECTION",
                            f"{owner} exposes {port_id} as {direction}, but the port is {port['direction']}.",
                            "Use a component interface port with the matching direction.",
                            semantic_id=owner,
                            source_map=source_map,
                            path=field,
                        )
                    )
    return ValidationResult(not diagnostics, tuple(diagnostics))


def canonical_bytes(ir: Mapping[str, Any]) -> bytes:
    value = copy.deepcopy(dict(ir))
    value.pop("semantic_sha256", None)
    for collection in ("blocks", "ports", "relationships", "artifact_contracts", "bindings", "components"):
        if isinstance(value.get(collection), list):
            value[collection] = sorted(value[collection], key=lambda row: str(row["id"]))
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def semantic_digest(ir: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(ir)).hexdigest()


def _entity(candidate: dict[str, Any], collection: str, identity: str) -> dict[str, Any]:
    try:
        return next(row for row in candidate[collection] if row["id"] == identity)
    except StopIteration as error:
        raise ValueError(f"WFR-COMMAND-TARGET-MISSING:{identity}") from error


def _execute_command(candidate: dict[str, Any], command: Mapping[str, Any]) -> None:
    kind = command.get("kind")
    if kind == "set_block_title" and set(command) == {"kind", "block_id", "title"}:
        _entity(candidate, "blocks", str(command["block_id"]))["title"] = command["title"]
    elif kind == "set_block_configuration" and set(command) == {"kind", "block_id", "key", "value"}:
        _entity(candidate, "blocks", str(command["block_id"]))["configuration"][str(command["key"])] = copy.deepcopy(command["value"])
    elif kind == "set_port_contract" and set(command) == {"kind", "port_id", "required", "cardinality"}:
        port = _entity(candidate, "ports", str(command["port_id"]))
        port["required"] = command["required"]
        port["cardinality"] = command["cardinality"]
    elif kind == "set_binding_tool" and set(command) == {"kind", "binding_id", "tool_id"}:
        _entity(candidate, "bindings", str(command["binding_id"]))["tool_id"] = command["tool_id"]
    elif kind == "set_relationship_condition" and set(command) == {"kind", "relationship_id", "condition"}:
        _entity(candidate, "relationships", str(command["relationship_id"]))["condition"] = command["condition"]
    elif kind == "connect" and set(command) == {"kind", "relationship"}:
        candidate["relationships"].append(copy.deepcopy(command["relationship"]))
    elif kind == "disconnect" and set(command) == {"kind", "relationship_id"}:
        identity = str(command["relationship_id"])
        before = len(candidate["relationships"])
        candidate["relationships"] = [row for row in candidate["relationships"] if row["id"] != identity]
        if len(candidate["relationships"]) == before:
            raise ValueError(f"WFR-COMMAND-TARGET-MISSING:{identity}")
    else:
        raise ValueError(f"WFR-COMMAND-UNSUPPORTED:{kind}")


def semanticDiff(before: Mapping[str, Any], after: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Return a deterministic JSON-pointer fact diff."""

    changes: list[dict[str, Any]] = []

    def visit(left: Any, right: Any, path: str) -> None:
        if type(left) is not type(right):
            changes.append({"kind": "changed", "path": path or "/", "before": left, "after": right})
        elif isinstance(left, Mapping):
            for key in sorted(set(left) | set(right)):
                child = f"{path}/{key}"
                if key not in left:
                    changes.append({"kind": "added", "path": child, "after": right[key]})
                elif key not in right:
                    changes.append({"kind": "removed", "path": child, "before": left[key]})
                else:
                    visit(left[key], right[key], child)
        elif isinstance(left, list):
            left_ids = {row.get("id"): row for row in left if isinstance(row, Mapping) and "id" in row}
            right_ids = {row.get("id"): row for row in right if isinstance(row, Mapping) and "id" in row}
            if len(left_ids) == len(left) and len(right_ids) == len(right):
                for identity in sorted(set(left_ids) | set(right_ids), key=str):
                    child = f"{path}/{identity}"
                    if identity not in left_ids:
                        changes.append({"kind": "added", "path": child, "after": right_ids[identity]})
                    elif identity not in right_ids:
                        changes.append({"kind": "removed", "path": child, "before": left_ids[identity]})
                    else:
                        visit(left_ids[identity], right_ids[identity], child)
            elif left != right:
                changes.append({"kind": "changed", "path": path or "/", "before": left, "after": right})
        elif left != right:
            changes.append({"kind": "changed", "path": path or "/", "before": left, "after": right})

    visit(before, after, "")
    return tuple(changes)


def apply(
    ir: Mapping[str, Any], command_batch: Mapping[str, Any], current_revision: int
) -> ApplyResult:
    """Atomically apply a closed command batch to a clone."""

    if set(command_batch) != {"base_revision", "origin", "commands"}:
        diagnostic = _diag("WFR-COMMAND-BATCH-SHAPE", "Command batch fields are not the closed contract.", "Provide base_revision, origin, and commands only.")
        return ApplyResult(False, None, (diagnostic,), ())
    if command_batch["origin"] not in {"graph", "form", "text", "ai_proposal"}:
        diagnostic = _diag("WFR-COMMAND-ORIGIN", "Command origin is not supported.", "Use graph, form, text, or ai_proposal.")
        return ApplyResult(False, None, (diagnostic,), ())
    if command_batch["base_revision"] != current_revision or ir.get("revision") != current_revision:
        diagnostic = _diag("WFR-COMMAND-STALE-BASE", "The command base is not the current accepted revision.", "Refresh, rebase the proposal, and review the new diff.")
        return ApplyResult(False, None, (diagnostic,), ())
    if not isinstance(command_batch["commands"], list) or not command_batch["commands"]:
        diagnostic = _diag("WFR-COMMAND-BATCH-EMPTY", "A command batch needs at least one command.", "Add a reviewed command or reject the change.")
        return ApplyResult(False, None, (diagnostic,), ())
    candidate = copy.deepcopy(dict(ir))
    try:
        for command in command_batch["commands"]:
            if not isinstance(command, Mapping):
                raise ValueError("WFR-COMMAND-SHAPE")
            _execute_command(candidate, command)
    except ValueError as error:
        code = str(error).split(":", 1)[0]
        diagnostic = _diag(code, str(error), "Correct or remove the unsupported command; no commands were applied.")
        return ApplyResult(False, None, (diagnostic,), ())
    validation = validate(candidate)
    if not validation.valid:
        return ApplyResult(False, None, validation.diagnostics, ())
    return ApplyResult(True, candidate, (), semanticDiff(ir, candidate))


def project(
    ir: Mapping[str, Any],
    layout: Mapping[str, Any],
    run_projection: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce a renderer-neutral canvas model without mutating inputs."""

    validation = validate(ir)
    if not validation.valid:
        raise ValueError(validation.diagnostics[0].code)
    positions = layout.get("positions", {})
    run_steps = {} if run_projection is None else run_projection.get("steps", {})
    port_by_id = {row["id"]: row for row in ir["ports"]}
    nodes = []
    for index, block in enumerate(ir["blocks"]):
        position = positions.get(block["id"], {"x": 80 + (index % 3) * 340, "y": 80 + (index // 3) * 240})
        nodes.append(
            {
                "id": block["id"],
                "title": block["title"],
                "kind": block["kind"],
                "execution_kind": block["execution_kind"],
                "position": copy.deepcopy(position),
                "inputs": [copy.deepcopy(port_by_id[identity]) for identity in block["input_port_ids"]],
                "outputs": [copy.deepcopy(port_by_id[identity]) for identity in block["output_port_ids"]],
                "run": copy.deepcopy(run_steps.get(block["id"])),
            }
        )
    active_relationship = None if run_projection is None else run_projection.get("active_relationship_id")
    edges = [
        {
            **copy.deepcopy(relation),
            "active": relation["id"] == active_relationship,
        }
        for relation in ir["relationships"]
    ]
    return {
        "workflow_id": ir["workflow_id"],
        "revision": ir["revision"],
        "semantic_digest": semantic_digest(ir),
        "nodes": nodes,
        "edges": edges,
        "viewport": copy.deepcopy(layout.get("viewport", {"x": 0, "y": 0, "zoom": 1})),
    }


def diagnostic_dicts(diagnostics: Sequence[Diagnostic]) -> list[dict[str, Any]]:
    return [asdict(diagnostic) for diagnostic in diagnostics]
