"""Strict validation and immutable reading for bundled process definitions."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final, Literal, Mapping

from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

from core.canonical_json import canonical_json_bytes, strict_json_loads


MAX_PROCESS_DEFINITION_BYTES: Final = 1024 * 1024
PROCESS_ID: Final = "product-definition-v1"
DEFINITION_FILENAME: Final = "product-definition-v1.json"
SCHEMA_FILENAME: Final = "process-definition.schema.json"
SOURCE_ID: Final = f"process-definitions/{DEFINITION_FILENAME}"
SUPPORTED_SCHEMA_VERSIONS: Final = ("1.0.0",)


class ProcessDefinitionErrorCode(StrEnum):
    UNAVAILABLE = "PROCESS_DEFINITION_UNAVAILABLE"
    IDENTITY_MISMATCH = "PROCESS_DEFINITION_IDENTITY_MISMATCH"
    INVALID = "PROCESS_DEFINITION_INVALID"
    UNSUPPORTED_VERSION = "PROCESS_DEFINITION_UNSUPPORTED_VERSION"
    READ_FAILED = "PROCESS_DEFINITION_READ_FAILED"


class ProcessDefinitionReadError(RuntimeError):
    """Typed process-definition failure that never contains source data or paths."""

    def __init__(
        self,
        code: ProcessDefinitionErrorCode,
        recovery_class: str,
    ) -> None:
        super().__init__(code.value)
        self.code = code
        self.recovery_class = recovery_class
        self.supported_schema_versions = SUPPORTED_SCHEMA_VERSIONS


@dataclass(frozen=True, slots=True)
class ProcessDefinitionDocument:
    """Validated immutable response bytes and their exact identities."""

    process_id: str
    content_sha256: str
    source_kind: Literal["installed", "packaged_fallback"]
    source_id: str
    source_sha256: str
    source_available: Literal[True]
    etag: str
    canonical_bytes: bytes
    supported_schema_versions: tuple[str, ...] = SUPPORTED_SCHEMA_VERSIONS

    def as_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_bytes)
        if not isinstance(value, dict):  # pragma: no cover - constructor invariant
            raise AssertionError("validated process definition must be an object")
        return copy.deepcopy(value)


def load_strict_process_json(raw: bytes) -> object:
    """Preserve the legacy profile while sharing the generic exact JSON parser."""
    return strict_json_loads(raw, safe_integers=False)


def canonical_process_json_bytes(value: object) -> bytes:
    """Serialize the unchanged ``wright-process-json-v1`` legacy profile."""
    return canonical_json_bytes(value, safe_integers=False)


def _raw_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _content_digest(value: Mapping[str, Any]) -> str:
    material = dict(value)
    material.pop("content_sha256", None)
    return _raw_digest(canonical_process_json_bytes(material))


def _read_bounded(path: Path) -> bytes:
    with path.open("rb") as handle:
        raw = handle.read(MAX_PROCESS_DEFINITION_BYTES + 1)
    if len(raw) > MAX_PROCESS_DEFINITION_BYTES:
        raise ValueError("process definition exceeds its fixed byte bound")
    return raw


def _assert_local_schema_references(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"$ref", "$dynamicRef"} and (
                not isinstance(item, str) or not item.startswith("#")
            ):
                raise ValueError("process-definition schema references must be local")
            _assert_local_schema_references(item)
    elif isinstance(value, list):
        for item in value:
            _assert_local_schema_references(item)


def _validate_graph(definition: Mapping[str, Any]) -> None:
    phases = definition["phases"]
    actions = definition["actions"]
    ports = definition["ports"]
    gates = definition["gates"]
    feedback_paths = definition["feedback_paths"]
    artifacts = definition["artifacts"]

    registries = (phases, actions, ports, gates, feedback_paths, artifacts)
    identifiers = [str(definition["process_id"])] + [
        str(item["id"]) for registry in registries for item in registry
    ]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("process-definition IDs must be globally unique")

    action_by_id = {str(item["id"]): item for item in actions}
    port_by_id = {str(item["id"]): item for item in ports}
    gate_by_id = {str(item["id"]): item for item in gates}
    feedback_by_id = {str(item["id"]): item for item in feedback_paths}
    artifact_by_id = {str(item["id"]): item for item in artifacts}

    ordered_actions = [
        str(action_id) for phase in phases for action_id in phase["action_ids"]
    ]
    if len(ordered_actions) != len(set(ordered_actions)) or set(ordered_actions) != set(
        action_by_id
    ):
        raise ValueError("every action must belong to exactly one phase")
    action_order = {action_id: index for index, action_id in enumerate(ordered_actions)}

    port_references: dict[str, list[tuple[str, str]]] = {
        port_id: [] for port_id in port_by_id
    }
    gate_references: dict[str, list[str]] = {gate_id: [] for gate_id in gate_by_id}
    feedback_references: dict[str, list[str]] = {
        feedback_id: [] for feedback_id in feedback_by_id
    }
    artifact_references: dict[str, list[str]] = {
        artifact_id: [] for artifact_id in artifact_by_id
    }

    for action_id, action in action_by_id.items():
        for port_id in action["input_port_ids"]:
            if port_id not in port_references:
                raise ValueError("input port reference does not resolve")
            port_references[port_id].append((action_id, "input"))
        for port_id in action["output_port_ids"]:
            if port_id not in port_references:
                raise ValueError("output port reference does not resolve")
            port_references[port_id].append((action_id, "output"))
        for gate_id in action["gate_ids"]:
            if gate_id not in gate_references:
                raise ValueError("gate reference does not resolve")
            gate_references[gate_id].append(action_id)
        for feedback_id in action["feedback_path_ids"]:
            if feedback_id not in feedback_references:
                raise ValueError("feedback reference does not resolve")
            feedback_references[feedback_id].append(action_id)
        for artifact_id in action["expected_artifact_ids"]:
            if artifact_id not in artifact_references:
                raise ValueError("artifact reference does not resolve")
            artifact_references[artifact_id].append(action_id)

    for port_id, port in port_by_id.items():
        owner = str(port["owner_action_id"])
        direction = str(port["direction"])
        if owner not in action_by_id or port_references[port_id] != [
            (owner, direction)
        ]:
            raise ValueError("port ownership and action references must be reciprocal")
        source_id = port["source_port_id"]
        if direction == "output":
            if source_id is not None:
                raise ValueError("output ports cannot declare a source port")
            continue
        if source_id is None:
            continue
        source = port_by_id.get(str(source_id))
        if (
            source is None
            or source["direction"] != "output"
            or source["value_type"] != port["value_type"]
            or action_order[str(source["owner_action_id"])] >= action_order[owner]
        ):
            raise ValueError("internal inputs require one earlier type-equal output")

    for gate_id, gate in gate_by_id.items():
        owner = str(gate["owner_action_id"])
        pass_target = str(gate["pass_target_id"])
        fail_target = str(gate["fail_target_id"])
        if (
            owner not in action_by_id
            or pass_target not in action_by_id
            or fail_target not in action_by_id
            or gate_references[gate_id] != [owner]
            or action_order[pass_target] <= action_order[owner]
            or action_order[fail_target] >= action_order[owner]
        ):
            raise ValueError("gate ownership and ordered targets are invalid")
        matches = [
            feedback_id
            for feedback_id, feedback in feedback_by_id.items()
            if feedback["from_id"] == gate_id and feedback["to_id"] == fail_target
        ]
        if len(matches) != 1 or feedback_references[matches[0]] != [owner]:
            raise ValueError("gate failure and feedback references must be reciprocal")

    for feedback_id, feedback in feedback_by_id.items():
        gate = gate_by_id.get(str(feedback["from_id"]))
        if gate is None or feedback["to_id"] != gate["fail_target_id"]:
            raise ValueError("feedback must connect a gate to its failure target")
        owner = str(gate["owner_action_id"])
        if feedback_references[feedback_id] != [owner]:
            raise ValueError("feedback ownership must be reciprocal")

    for artifact_id, artifact in artifact_by_id.items():
        producer = str(artifact["produced_by_action_id"])
        if producer not in action_by_id or artifact_references[artifact_id] != [
            producer
        ]:
            raise ValueError(
                "artifact producer and action reference must be reciprocal"
            )


class ProcessDefinitionReader:
    """Read installed content first and use packaged content only when absent."""

    def __init__(
        self,
        installed_root: Path,
        packaged_root: Path,
        *,
        schema_root: Path | None = None,
    ) -> None:
        self.installed_root = installed_root
        self.packaged_root = packaged_root
        self.schema_root = schema_root or packaged_root

    def _schema(self) -> Mapping[str, Any]:
        try:
            raw = _read_bounded(self.schema_root / SCHEMA_FILENAME)
            value = load_strict_process_json(raw)
        except FileNotFoundError as exc:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.UNAVAILABLE, "enable_or_reinstall"
            ) from exc
        except OSError as exc:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.READ_FAILED, "inspect_local_data_root"
            ) from exc
        except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.INVALID, "replace_validated_definition"
            ) from exc
        if not isinstance(value, Mapping):
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.INVALID, "replace_validated_definition"
            )
        try:
            _assert_local_schema_references(value)
            Draft202012Validator.check_schema(value)
        except Exception as exc:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.INVALID, "replace_validated_definition"
            ) from exc
        return value

    def _validate(
        self,
        raw: bytes,
        source_kind: Literal["installed", "packaged_fallback"],
    ) -> ProcessDefinitionDocument:
        try:
            value = load_strict_process_json(raw)
            if not isinstance(value, Mapping):
                raise ValueError("process definition must be an object")
            version = value.get("schema_version")
            if isinstance(version, str) and version not in SUPPORTED_SCHEMA_VERSIONS:
                raise ProcessDefinitionReadError(
                    ProcessDefinitionErrorCode.UNSUPPORTED_VERSION,
                    "install_compatible_wright",
                )
            first_error = next(
                Draft202012Validator(
                    self._schema(), format_checker=FormatChecker()
                ).iter_errors(value),
                None,
            )
            if first_error is not None:
                raise ValueError("process definition schema validation failed")
            if value["process_id"] != PROCESS_ID:
                raise ProcessDefinitionReadError(
                    ProcessDefinitionErrorCode.IDENTITY_MISMATCH,
                    "reinstall_exact_artifact",
                )
            content_sha256 = _content_digest(value)
            if value["content_sha256"] != content_sha256:
                raise ProcessDefinitionReadError(
                    ProcessDefinitionErrorCode.IDENTITY_MISMATCH,
                    "reinstall_exact_artifact",
                )
            _validate_graph(value)
            source_sha256 = _raw_digest(raw)
            envelope_without_etag = {
                "definition": value,
                "source_kind": source_kind,
                "source_id": SOURCE_ID,
                "source_sha256": source_sha256,
                "source_available": True,
                "supported_schema_versions": list(SUPPORTED_SCHEMA_VERSIONS),
            }
            etag = _raw_digest(canonical_process_json_bytes(envelope_without_etag))
            canonical_bytes = canonical_process_json_bytes(
                {**envelope_without_etag, "etag": etag}
            )
            return ProcessDefinitionDocument(
                process_id=PROCESS_ID,
                content_sha256=content_sha256,
                source_kind=source_kind,
                source_id=SOURCE_ID,
                source_sha256=source_sha256,
                source_available=True,
                etag=etag,
                canonical_bytes=canonical_bytes,
            )
        except ProcessDefinitionReadError:
            raise
        except Exception as exc:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.INVALID, "replace_validated_definition"
            ) from exc

    def read(self, process_id: str) -> ProcessDefinitionDocument:
        if process_id != PROCESS_ID:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.UNAVAILABLE, "enable_or_reinstall"
            )
        try:
            raw = _read_bounded(self.installed_root / DEFINITION_FILENAME)
        except FileNotFoundError:
            try:
                raw = _read_bounded(self.packaged_root / DEFINITION_FILENAME)
            except FileNotFoundError as exc:
                raise ProcessDefinitionReadError(
                    ProcessDefinitionErrorCode.UNAVAILABLE, "enable_or_reinstall"
                ) from exc
            except OSError as exc:
                raise ProcessDefinitionReadError(
                    ProcessDefinitionErrorCode.READ_FAILED, "inspect_local_data_root"
                ) from exc
            except ValueError as exc:
                raise ProcessDefinitionReadError(
                    ProcessDefinitionErrorCode.INVALID, "replace_validated_definition"
                ) from exc
            return self._validate(raw, "packaged_fallback")
        except OSError as exc:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.READ_FAILED, "inspect_local_data_root"
            ) from exc
        except ValueError as exc:
            raise ProcessDefinitionReadError(
                ProcessDefinitionErrorCode.INVALID, "replace_validated_definition"
            ) from exc
        return self._validate(raw, "installed")

    def read_definition(self, process_id: str) -> ProcessDefinitionDocument:
        return self.read(process_id)


__all__ = [
    "ProcessDefinitionDocument",
    "ProcessDefinitionErrorCode",
    "ProcessDefinitionReadError",
    "ProcessDefinitionReader",
]
