from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest

from tool_registry.process_definition import (
    DEFINITION_FILENAME,
    MAX_PROCESS_DEFINITION_BYTES,
    PROCESS_ID,
    SCHEMA_FILENAME,
    SOURCE_ID,
    SUPPORTED_SCHEMA_VERSIONS,
    ProcessDefinitionErrorCode,
    ProcessDefinitionReadError,
    ProcessDefinitionReader,
    canonical_process_json_bytes,
    load_strict_process_json,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_ROOT = REPOSITORY_ROOT / "specs" / "078-process-definition-view" / "contracts"
PACKAGED_ROOT = (
    REPOSITORY_ROOT / "src" / "wright_engineering" / "static" / "process-definitions"
)
SAMPLE_SOURCE = CONTRACT_ROOT / "product-definition-v1.sample.json"
SCHEMA_SOURCE = CONTRACT_ROOT / SCHEMA_FILENAME
VECTOR_SOURCE = CONTRACT_ROOT / "wright-process-json-v1-vectors.json"
RAW_SAMPLE_SHA256 = "6a02f71e35f9c3d9a3184509ddeab2df251cff454b6d6ce66d7244d015eefdef"
CONTENT_SHA256 = "4617a8a6424b7c15712cd951c0b97a8c4ec5e77e29633e46e105d30ec65d5883"


def _sample() -> dict[str, Any]:
    value = load_strict_process_json(SAMPLE_SOURCE.read_bytes())
    assert isinstance(value, dict)
    return value


def _definition_bytes(value: dict[str, Any]) -> bytes:
    material = copy.deepcopy(value)
    material.pop("content_sha256", None)
    value = copy.deepcopy(value)
    value["content_sha256"] = hashlib.sha256(
        canonical_process_json_bytes(material)
    ).hexdigest()
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _write_packaged(root: Path, *, definition: bytes | None = None) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / SCHEMA_FILENAME).write_bytes(SCHEMA_SOURCE.read_bytes())
    (root / DEFINITION_FILENAME).write_bytes(
        SAMPLE_SOURCE.read_bytes() if definition is None else definition
    )


def _error(
    reader: ProcessDefinitionReader,
    expected: ProcessDefinitionErrorCode,
) -> ProcessDefinitionReadError:
    with pytest.raises(ProcessDefinitionReadError) as raised:
        reader.read(PROCESS_ID)
    assert raised.value.code is expected
    assert str(raised.value) == expected.value
    assert str(REPOSITORY_ROOT) not in str(raised.value)
    assert "customer-needs" not in str(raised.value)
    return raised.value


def test_cross_language_canonicalization_vectors() -> None:
    vectors = json.loads(VECTOR_SOURCE.read_text(encoding="utf-8"))
    assert vectors["profile"] == "wright-process-json-v1"

    for vector in vectors["valid"]:
        raw = bytes.fromhex(vector["input_utf8_hex"])
        expected = bytes.fromhex(vector["canonical_utf8_hex"])
        actual = canonical_process_json_bytes(load_strict_process_json(raw))
        assert actual == expected, vector["name"]
        assert hashlib.sha256(actual).hexdigest() == vector["canonical_sha256"]


def test_cross_language_strict_json_negative_vectors() -> None:
    vectors = json.loads(VECTOR_SOURCE.read_text(encoding="utf-8"))

    for vector in vectors["invalid"]:
        with pytest.raises((UnicodeError, ValueError, json.JSONDecodeError)):
            load_strict_process_json(bytes.fromhex(vector["input_utf8_hex"]))


def test_frozen_source_and_packaged_files_are_exact() -> None:
    source = SAMPLE_SOURCE.read_bytes()
    installed = (PACKAGED_ROOT / DEFINITION_FILENAME).read_bytes()

    assert source == installed
    assert hashlib.sha256(source).hexdigest() == RAW_SAMPLE_SHA256
    assert SCHEMA_SOURCE.read_bytes() == (PACKAGED_ROOT / SCHEMA_FILENAME).read_bytes()


def test_frozen_sample_has_exact_semantic_identity_and_valid_graph(
    tmp_path: Path,
) -> None:
    definition = _sample()
    material = dict(definition)
    material.pop("content_sha256")

    assert definition["content_sha256"] == CONTENT_SHA256
    assert (
        hashlib.sha256(canonical_process_json_bytes(material)).hexdigest()
        == CONTENT_SHA256
    )

    reader = ProcessDefinitionReader(
        tmp_path / "installed",
        PACKAGED_ROOT,
    )
    document = reader.read(PROCESS_ID)
    assert document.process_id == PROCESS_ID
    assert document.content_sha256 == CONTENT_SHA256


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value["phases"][0].update(id="capture-requirements"),
        lambda value: value["phases"][1]["action_ids"].append(
            "release-product-definition"
        ),
        lambda value: value["ports"][0].update(owner_action_id="define-product"),
        lambda value: value["ports"][2].update(source_port_id="customer-needs"),
        lambda value: value["ports"][2].update(value_type="customer-need"),
        lambda value: (
            value["ports"][8].update(value_type="product-model"),
            value["ports"][6].update(source_port_id="released-package"),
        ),
        lambda value: value["gates"][0].update(pass_target_id="define-product"),
        lambda value: (
            value["gates"][0].update(fail_target_id="release-product-definition"),
            value["feedback_paths"][0].update(to_id="release-product-definition"),
        ),
        lambda value: value["feedback_paths"][0].update(to_id="capture-requirements"),
        lambda value: value["artifacts"][0].update(
            produced_by_action_id="define-product"
        ),
        lambda value: value["phases"][0].update(action_ids=["missing-action"]),
        lambda value: value["actions"][0].update(input_port_ids=["missing-input-port"]),
        lambda value: value["actions"][0].update(
            output_port_ids=["missing-output-port"]
        ),
        lambda value: value["actions"][2].update(gate_ids=["missing-gate"]),
        lambda value: value["actions"][2].update(
            feedback_path_ids=["missing-feedback"]
        ),
        lambda value: value["actions"][0].update(
            expected_artifact_ids=["missing-artifact"]
        ),
        lambda value: value["gates"][0].update(pass_target_id="missing-action"),
        lambda value: value["gates"][0].update(fail_target_id="missing-action"),
        lambda value: value["ports"][2].update(source_port_id="missing-port"),
    ],
    ids=[
        "global-id",
        "phase-membership",
        "port-owner",
        "port-source-direction",
        "port-source-type",
        "port-source-order",
        "gate-pass-order",
        "gate-fail-order",
        "feedback-reciprocity",
        "artifact-reciprocity",
        "dangling-phase-action",
        "dangling-action-input-port",
        "dangling-action-output-port",
        "dangling-action-gate",
        "dangling-action-feedback",
        "dangling-action-artifact",
        "dangling-gate-pass-target",
        "dangling-gate-fail-target",
        "dangling-input-source-port",
    ],
)
def test_graph_invariant_failures_are_rejected(
    tmp_path: Path,
    mutate: Any,
) -> None:
    definition = _sample()
    mutate(definition)
    packaged = tmp_path / "packaged"
    _write_packaged(packaged, definition=_definition_bytes(definition))

    error = _error(
        ProcessDefinitionReader(tmp_path / "installed", packaged),
        ProcessDefinitionErrorCode.INVALID,
    )

    assert error.recovery_class == "replace_validated_definition"


def test_installed_definition_wins_and_fallback_is_only_for_absence(
    tmp_path: Path,
) -> None:
    installed = tmp_path / "installed"
    packaged = tmp_path / "packaged"
    _write_packaged(installed)
    _write_packaged(packaged, definition=SAMPLE_SOURCE.read_bytes() + b"\n")

    document = ProcessDefinitionReader(installed, packaged).read(PROCESS_ID)

    assert document.source_kind == "installed"
    assert document.source_sha256 == RAW_SAMPLE_SHA256


def test_packaged_definition_is_used_when_installed_definition_is_absent(
    tmp_path: Path,
) -> None:
    packaged = tmp_path / "packaged"
    _write_packaged(packaged)

    document = ProcessDefinitionReader(tmp_path / "installed", packaged).read(
        PROCESS_ID
    )

    assert document.source_kind == "packaged_fallback"
    assert document.source_id == SOURCE_ID
    assert document.source_available is True
    assert document.supported_schema_versions == SUPPORTED_SCHEMA_VERSIONS


def test_invalid_installed_definition_never_falls_back(tmp_path: Path) -> None:
    installed = tmp_path / "installed"
    packaged = tmp_path / "packaged"
    _write_packaged(installed, definition=b'{"partial":')
    _write_packaged(packaged)

    _error(
        ProcessDefinitionReader(installed, packaged),
        ProcessDefinitionErrorCode.INVALID,
    )


def test_unsupported_version_is_distinct_from_structurally_invalid_version(
    tmp_path: Path,
) -> None:
    packaged = tmp_path / "packaged"
    unsupported = _sample()
    unsupported["schema_version"] = "99.0.0"
    _write_packaged(packaged, definition=_definition_bytes(unsupported))
    error = _error(
        ProcessDefinitionReader(tmp_path / "installed", packaged),
        ProcessDefinitionErrorCode.UNSUPPORTED_VERSION,
    )
    assert error.recovery_class == "install_compatible_wright"
    assert error.supported_schema_versions == SUPPORTED_SCHEMA_VERSIONS

    invalid = _sample()
    invalid["schema_version"] = 1
    _write_packaged(packaged, definition=_definition_bytes(invalid))
    _error(
        ProcessDefinitionReader(tmp_path / "installed", packaged),
        ProcessDefinitionErrorCode.INVALID,
    )


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda value: value.update(process_id="different-process"),
            ProcessDefinitionErrorCode.IDENTITY_MISMATCH,
        ),
        (
            lambda value: value.update(content_sha256="0" * 64),
            ProcessDefinitionErrorCode.IDENTITY_MISMATCH,
        ),
    ],
    ids=["process-id", "content-digest"],
)
def test_identity_mismatch_is_closed(
    tmp_path: Path,
    mutation: Any,
    expected: ProcessDefinitionErrorCode,
) -> None:
    definition = _sample()
    mutation(definition)
    if definition["process_id"] != PROCESS_ID:
        raw = _definition_bytes(definition)
    else:
        raw = json.dumps(definition, separators=(",", ":")).encode()
    packaged = tmp_path / "packaged"
    _write_packaged(packaged, definition=raw)

    error = _error(ProcessDefinitionReader(tmp_path / "installed", packaged), expected)
    assert error.recovery_class == "reinstall_exact_artifact"


def test_missing_unknown_oversize_and_read_failures_are_typed(tmp_path: Path) -> None:
    reader = ProcessDefinitionReader(tmp_path / "installed", tmp_path / "packaged")
    assert _error(reader, ProcessDefinitionErrorCode.UNAVAILABLE).recovery_class == (
        "enable_or_reinstall"
    )
    with pytest.raises(ProcessDefinitionReadError) as unknown:
        reader.read("unknown-process")
    assert unknown.value.code is ProcessDefinitionErrorCode.UNAVAILABLE

    packaged = tmp_path / "oversize"
    _write_packaged(
        packaged,
        definition=b" " * (MAX_PROCESS_DEFINITION_BYTES + 1),
    )
    _error(
        ProcessDefinitionReader(tmp_path / "installed", packaged),
        ProcessDefinitionErrorCode.INVALID,
    )

    installed = tmp_path / "unreadable"
    _write_packaged(installed)
    definition_path = installed / DEFINITION_FILENAME
    definition_path.unlink()
    definition_path.mkdir()
    _error(
        ProcessDefinitionReader(installed, PACKAGED_ROOT),
        ProcessDefinitionErrorCode.READ_FAILED,
    )


def test_schema_failures_are_typed_and_safe(tmp_path: Path) -> None:
    packaged = tmp_path / "packaged"
    _write_packaged(packaged)
    (packaged / SCHEMA_FILENAME).write_bytes(b'{"$ref":"#/$defs/missing"}')

    _error(
        ProcessDefinitionReader(tmp_path / "installed", packaged),
        ProcessDefinitionErrorCode.INVALID,
    )


@pytest.mark.parametrize("reference_keyword", ["$ref", "$dynamicRef"])
def test_external_schema_references_fail_without_network_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reference_keyword: str,
) -> None:
    packaged = tmp_path / "packaged"
    _write_packaged(packaged)
    (packaged / SCHEMA_FILENAME).write_bytes(
        json.dumps(
            {reference_keyword: "https://example.invalid/process-definition.json"}
        ).encode()
    )
    network_calls: list[str] = []

    def reject_network(*args: Any, **kwargs: Any) -> None:
        network_calls.append(repr((args, kwargs)))
        raise AssertionError("schema validation attempted network access")

    monkeypatch.setattr("urllib.request.urlopen", reject_network)

    _error(
        ProcessDefinitionReader(tmp_path / "installed", packaged),
        ProcessDefinitionErrorCode.INVALID,
    )
    assert network_calls == []


def test_document_is_copy_safe_and_etag_binds_the_exact_envelope(
    tmp_path: Path,
) -> None:
    packaged = tmp_path / "packaged"
    _write_packaged(packaged)
    reader = ProcessDefinitionReader(tmp_path / "installed", packaged)

    first = reader.read(PROCESS_ID)
    body = first.as_dict()
    etag = body.pop("etag")
    assert etag == first.etag
    assert hashlib.sha256(canonical_process_json_bytes(body)).hexdigest() == etag
    assert body["source_id"] == SOURCE_ID
    assert body["source_available"] is True
    assert body["source_sha256"] == RAW_SAMPLE_SHA256
    assert body["supported_schema_versions"] == list(SUPPORTED_SCHEMA_VERSIONS)

    body["definition"]["title"] = "mutated caller copy"
    assert (
        reader.read(PROCESS_ID).as_dict()["definition"]["title"]
        != body["definition"]["title"]
    )
    with pytest.raises(FrozenInstanceError):
        first.etag = "0" * 64  # type: ignore[misc]

    (packaged / DEFINITION_FILENAME).write_bytes(SAMPLE_SOURCE.read_bytes() + b"\n")
    raw_changed = reader.read(PROCESS_ID)
    assert raw_changed.content_sha256 == first.content_sha256
    assert raw_changed.source_sha256 != first.source_sha256
    assert raw_changed.etag != first.etag
