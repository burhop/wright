"""Authoritative Wright process language shared by programmatic and UI clients.

This module validates data and describes operations. It never opens a workspace,
invokes a tool, imports a canvas renderer, or interprets a Rivet document.
"""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path, PureWindowsPath
from typing import Any, Literal, Never

from jsonschema import Draft202012Validator

from core.canonical_json import canonical_json_bytes, strict_json_loads
from core.native_quantities import UNITS, Dimension, Quantity

FORMAT = "wright-native-process"
SCHEMA_VERSION = "1.0.0"
MAX_DOCUMENT_BYTES = 1024 * 1024
CANONICALIZATION = "wright-native-json-v1"


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    message: str
    recovery: str
    step_id: str | None = None
    port_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class NativeProcessError(ValueError):
    def __init__(self, finding: Finding):
        super().__init__(finding.message)
        self.findings = (finding,)


@dataclass(frozen=True, slots=True)
class NativeDocument:
    """Immutable validated semantics. Callers receive independent mutable copies."""

    process_id: str
    semantic_digest: str
    canonical_bytes: bytes

    def as_dict(self) -> dict[str, Any]:
        return strict_json_loads(self.canonical_bytes)


@dataclass(frozen=True, slots=True)
class PortSignature:
    key: str
    type: Literal["text", "quantity", "artifact"]
    cardinality: Literal["one"] = "one"
    required: Literal[True] = True


@dataclass(frozen=True, slots=True)
class Operation:
    id: str
    inputs: tuple[PortSignature, ...]
    outputs: tuple[PortSignature, ...]
    required_config_keys: tuple[str, ...] = ()


def _ports(
    *pairs: tuple[str, Literal["text", "quantity", "artifact"]],
) -> tuple[PortSignature, ...]:
    return tuple(PortSignature(key, kind) for key, kind in pairs)


OPERATIONS: dict[str, Operation] = {
    item.id: item
    for item in (
        Operation("text.input@1", (), _ports(("value", "text")), ("value",)),
        Operation("quantity.input@1", (), _ports(("value", "quantity")), ("value",)),
        Operation("artifact.input@1", (), _ports(("value", "artifact")), ("path",)),
        Operation(
            "text.join@1",
            _ports(("first", "text"), ("second", "text")),
            _ports(("text", "text")),
        ),
        Operation(
            "text.require@1",
            _ports(("text", "text")),
            _ports(("text", "text")),
            ("terms",),
        ),
        Operation(
            "quantity.multiply@1",
            _ports(("left", "quantity"), ("right", "quantity")),
            _ports(("value", "quantity")),
            ("unit",),
        ),
        Operation(
            "quantity.convert@1",
            _ports(("value", "quantity")),
            _ports(("value", "quantity")),
            ("unit",),
        ),
        Operation(
            "quantity.range@1",
            _ports(("value", "quantity")),
            _ports(("value", "quantity")),
            ("minimum", "maximum"),
        ),
        Operation(
            "quantity.format@1", _ports(("value", "quantity")), _ports(("text", "text"))
        ),
        Operation(
            "artifact.write-text@1",
            _ports(("text", "text")),
            _ports(("artifact", "artifact")),
            ("filename",),
        ),
        Operation(
            "artifact.read-text@1",
            _ports(("artifact", "artifact")),
            _ports(("text", "text")),
        ),
        Operation(
            "mcp.call@1", _ports(("arguments", "text")), _ports(("result", "text"))
        ),
    )
}


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    raw = (
        Path(__file__)
        .with_name("native_process_contract")
        .joinpath("definition.schema.json")
        .read_bytes()
    )
    schema = strict_json_loads(raw)
    Draft202012Validator.check_schema(schema)
    return schema


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    return Draft202012Validator(_schema())


def language_contract() -> dict[str, Any]:
    """Discovery for every client comes from the same validator and registry."""
    schema = copy.deepcopy(_schema())
    configs = {
        rule["if"]["properties"]["operation"]["const"]: copy.deepcopy(
            rule["then"]["properties"]["config"]
        )
        for rule in schema["$defs"]["step"]["allOf"]
    }
    configs["text.join@1"]["properties"]["separator"]["default"] = ""
    configs["quantity.format@1"]["properties"]["label"]["default"] = ""
    return {
        "format": FORMAT,
        "schema_version": SCHEMA_VERSION,
        "schema": schema,
        "canonicalization": CANONICALIZATION,
        "operations": [
            {
                "id": item.id,
                "inputs": [asdict(port) for port in item.inputs],
                "outputs": [asdict(port) for port in item.outputs],
                "required_config_keys": list(item.required_config_keys),
                "config_schema": configs[item.id],
            }
            for item in OPERATIONS.values()
        ],
    }


def _invalid(
    code: str, message: str, *, step_id: str | None = None, port_id: str | None = None
) -> Never:
    raise NativeProcessError(
        Finding(
            code,
            message,
            "Correct the indicated definition and retry.",
            step_id,
            port_id,
        )
    )


def validate_definition(value: bytes | Mapping[str, Any]) -> NativeDocument:
    try:
        material = strict_json_loads(value) if isinstance(value, bytes) else value
        raw = canonical_json_bytes(material)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise NativeProcessError(
            Finding(
                "INVALID_JSON",
                "Definition is not valid bounded canonical JSON.",
                "Use the published language schema and exact JSON profile.",
            )
        ) from exc
    if len(raw) > MAX_DOCUMENT_BYTES:
        _invalid("DOCUMENT_LIMIT", "Definition exceeds 1 MiB.")
    error = next(_validator().iter_errors(material), None)
    if error is not None:
        field = "/" + "/".join(str(part) for part in error.absolute_path)
        _invalid(
            "SCHEMA_INVALID",
            f"Definition does not match the language schema at {field[:160]}.",
        )
    _validate_semantics(material)
    return NativeDocument(material["id"], hashlib.sha256(raw).hexdigest(), raw)


def validate_presentation(
    document: NativeDocument, value: object
) -> dict[str, dict[str, int]]:
    if not isinstance(value, dict) or len(value) > 100:
        _invalid(
            "PRESENTATION_INVALID", "Presentation must be a bounded step-position map."
        )
    step_ids = {step["id"] for step in document.as_dict()["steps"]}
    for step_id, position in value.items():
        if (
            step_id not in step_ids
            or not isinstance(position, dict)
            or set(position) != {"x", "y"}
        ):
            _invalid(
                "PRESENTATION_INVALID",
                "Presentation refers to an unknown step or invalid position.",
            )
        if any(type(v) is not int or abs(v) > 100000 for v in position.values()):
            _invalid(
                "PRESENTATION_INVALID",
                "Positions must be integers within the coordinate bound.",
            )
    return copy.deepcopy(value)


def _validate_semantics(d: Mapping[str, Any]) -> None:
    ids = [d["id"]] + [
        item["id"]
        for group in ("steps", "ports", "connections", "outputs")
        for item in d[group]
    ]
    if len(ids) != len(set(ids)):
        _invalid("DUPLICATE_ID", "Semantic identities must be globally unique.")
    steps = {step["id"]: step for step in d["steps"]}
    ports = {port["id"]: port for port in d["ports"]}
    keys: set[tuple[str, str, str]] = set()
    for port in ports.values():
        owner = steps.get(port["step_id"])
        if owner is None:
            _invalid(
                "PORT_OWNER", "Port refers to an unknown step.", port_id=port["id"]
            )
        identity = (port["step_id"], port["direction"], port["key"])
        if identity in keys:
            _invalid(
                "DUPLICATE_PORT_KEY",
                "Port keys must be unique within step and direction.",
                port_id=port["id"],
            )
        keys.add(identity)
        operation = OPERATIONS.get(owner["operation"])
        if operation:
            signatures = (
                operation.inputs if port["direction"] == "input" else operation.outputs
            )
            expected = next((p for p in signatures if p.key == port["key"]), None)
            if expected is None or (
                port["type"],
                port["cardinality"],
                port["required"],
            ) != (expected.type, expected.cardinality, expected.required):
                _invalid(
                    "PORT_SIGNATURE",
                    "Port does not match its registered operation signature.",
                    step_id=owner["id"],
                    port_id=port["id"],
                )
    connected: set[str] = set()
    for edge in d["connections"]:
        source, target = (
            ports.get(edge["source_port_id"]),
            ports.get(edge["target_port_id"]),
        )
        if source is None or target is None:
            _invalid("ENDPOINT_MISSING", "Connection endpoint does not exist.")
        if source["direction"] != "output" or target["direction"] != "input":
            _invalid("ENDPOINT_DIRECTION", "Connections must link output to input.")
        if (source["type"], source["cardinality"]) != (
            target["type"],
            target["cardinality"],
        ):
            _invalid(
                "ENDPOINT_TYPE",
                "Connection endpoint types and cardinalities must match.",
            )
        if target["id"] in connected:
            _invalid(
                "MULTIPLE_PRODUCERS",
                "An input may have only one producer.",
                port_id=target["id"],
            )
        connected.add(target["id"])
    for output in d["outputs"]:
        port = ports.get(output["port_id"])
        if port is None or port["direction"] != "output" or port["type"] != "artifact":
            _invalid(
                "OUTPUT_REFERENCE",
                "Declared outputs must refer to artifact output ports.",
            )
    topological_order(d)
    for step in steps.values():
        for value in step["config"].values():
            if isinstance(value, dict):
                try:
                    Quantity(**value)
                except (ValueError, TypeError) as exc:
                    raise NativeProcessError(
                        Finding(
                            "QUANTITY_INVALID",
                            "Configuration contains an invalid exact quantity.",
                            "Use a canonical decimal and a supported unit.",
                            step["id"],
                        )
                    ) from exc
        if step["operation"] == "artifact.input@1" and "path" in step["config"]:
            _validate_relative_path(step["config"]["path"], step["id"])


def _validate_relative_path(value: str, step_id: str) -> None:
    windows = PureWindowsPath(value)
    parts = value.replace("\\", "/").split("/")
    if (
        windows.drive
        or value.startswith(("/", "\\"))
        or any(part in {"", ".", ".."} for part in parts)
        or ":" in value
        or "\x00" in value
    ):
        _invalid(
            "ARTIFACT_PATH",
            "Artifact input requires a confined relative file path.",
            step_id=step_id,
        )


def topological_order(d: Mapping[str, Any]) -> tuple[str, ...]:
    """Stable sequential scheduling: declaration order resolves independent ties."""
    ordered = [step["id"] for step in d["steps"]]
    dependencies: dict[str, set[str]] = {step_id: set() for step_id in ordered}
    ports = {port["id"]: port for port in d["ports"]}
    for edge in d["connections"]:
        dependencies[ports[edge["target_port_id"]]["step_id"]].add(
            ports[edge["source_port_id"]]["step_id"]
        )
    result: list[str] = []
    remaining = set(ordered)
    while remaining:
        candidate = next(
            (
                step_id
                for step_id in ordered
                if step_id in remaining and not (dependencies[step_id] & remaining)
            ),
            None,
        )
        if candidate is None:
            _invalid(
                "DEPENDENCY_CYCLE",
                "Native execution requires acyclic forward dependencies.",
            )
        result.append(candidate)
        remaining.remove(candidate)
    return tuple(result)


def readiness(
    document: NativeDocument, *, bound_step_ids: frozenset[str] = frozenset()
) -> tuple[Finding, ...]:
    """Pure readiness; workspace permissions/files/tool identity are service checks."""
    d = document.as_dict()
    findings: list[Finding] = []
    if not d["steps"]:
        findings.append(
            Finding(
                "EMPTY_PROCESS",
                "The process has no steps.",
                "Add and configure a source and an operation.",
            )
        )
    ports_by_step = {
        step["id"]: [p for p in d["ports"] if p["step_id"] == step["id"]]
        for step in d["steps"]
    }
    connected = {edge["target_port_id"] for edge in d["connections"]}
    for step in d["steps"]:
        operation = OPERATIONS.get(step["operation"])
        if operation is None:
            findings.append(
                Finding(
                    "OPERATION_UNBOUND",
                    "This operation version is not installed.",
                    "Select an installed versioned operation.",
                    step["id"],
                )
            )
            continue
        actual = {
            (port["direction"], port["key"]) for port in ports_by_step[step["id"]]
        }
        expected = {("input", p.key) for p in operation.inputs} | {
            ("output", p.key) for p in operation.outputs
        }
        if actual != expected:
            findings.append(
                Finding(
                    "PORTS_REQUIRED",
                    "Registered operation ports are missing.",
                    "Add the ports described by the operation contract.",
                    step["id"],
                )
            )
        for key in operation.required_config_keys:
            if key not in step["config"]:
                findings.append(
                    Finding(
                        "CONFIG_REQUIRED",
                        f"Configure {key} before running.",
                        "Complete this operation's Inspector fields.",
                        step["id"],
                    )
                )
        for port in ports_by_step[step["id"]]:
            if (
                port["direction"] == "input"
                and port["required"]
                and port["id"] not in connected
            ):
                findings.append(
                    Finding(
                        "INPUT_REQUIRED",
                        "This input has no producer.",
                        "Connect one compatible output to this exact input.",
                        step["id"],
                        port["id"],
                    )
                )
        if operation.id == "mcp.call@1" and step["id"] not in bound_step_ids:
            findings.append(
                Finding(
                    "BINDING_REQUIRED",
                    "An exact permitted tool binding is required.",
                    "Select and preflight the local tool.",
                    step["id"],
                )
            )
    findings.extend(_quantity_readiness(d))
    return tuple(findings)


def _quantity_readiness(d: Mapping[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    dimensions: dict[str, Dimension] = {}
    steps = {step["id"]: step for step in d["steps"]}
    sources = {
        edge["target_port_id"]: edge["source_port_id"] for edge in d["connections"]
    }
    for step_id in topological_order(d):
        step = steps[step_id]
        ports = [p for p in d["ports"] if p["step_id"] == step_id]
        inputs = {
            p["key"]: dimensions.get(sources.get(p["id"], ""))
            for p in ports
            if p["direction"] == "input"
        }
        config, operation = step["config"], step["operation"]
        dimension = None
        try:
            if operation == "quantity.input@1" and "value" in config:
                dimension = Quantity(**config["value"]).dimension
            elif operation == "quantity.multiply@1" and "unit" in config:
                dimension = UNITS[config["unit"]].dimension
                left, right = inputs.get("left"), inputs.get("right")
                if (
                    left is not None
                    and right is not None
                    and tuple(a + b for a, b in zip(left, right)) != dimension
                ):
                    raise ValueError("incompatible multiplication dimensions")
            elif operation == "quantity.convert@1" and "unit" in config:
                dimension = UNITS[config["unit"]].dimension
                if inputs.get("value") is not None and inputs["value"] != dimension:
                    raise ValueError("incompatible conversion dimensions")
            elif operation == "quantity.range@1":
                dimension = inputs.get("value")
                if "minimum" in config and "maximum" in config:
                    low, high = (
                        Quantity(**config["minimum"]),
                        Quantity(**config["maximum"]),
                    )
                    if low.compare(high) > 0 or (
                        dimension is not None and low.dimension != dimension
                    ):
                        raise ValueError("incompatible or reversed range")
            if dimension is not None:
                for port in ports:
                    if port["direction"] == "output" and port["type"] == "quantity":
                        dimensions[port["id"]] = dimension
        except ValueError:
            findings.append(
                Finding(
                    "QUANTITY_DIMENSION",
                    "Quantity configuration has incompatible dimensions or reversed limits.",
                    "Choose compatible explicit units and ordered limits.",
                    step_id,
                )
            )
    return findings
