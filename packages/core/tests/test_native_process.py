from __future__ import annotations

import hashlib
import json
from decimal import localcontext
from pathlib import Path

import pytest

from core.canonical_json import canonical_json_bytes, strict_json_loads
from core.native_process import (
    NativeProcessError,
    language_contract,
    readiness,
    topological_order,
    validate_definition,
    validate_presentation,
)
from core.native_quantities import Quantity, decimal_value

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS = ROOT / "specs/079-wright-native-authoring/contracts"


def fixture(name: str) -> dict:
    return json.loads(
        (CONTRACTS / "examples" / f"{name}.json").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize(
    "name",
    [
        "concept-brief",
        "mass-check",
        "package-review",
        "mass-check-fails",
        "study-trace",
    ],
)
def test_frozen_examples_are_structural_and_ready(name):
    document = validate_definition(fixture(name))
    assert readiness(document) == ()
    assert validate_definition(document.canonical_bytes) == document
    assert len(topological_order(document.as_dict())) == len(
        document.as_dict()["steps"]
    )


def test_shared_discovery_schema_is_the_frozen_schema_without_mutable_aliases():
    schema = json.loads(
        (CONTRACTS / "native-process.schema.json").read_text(encoding="utf-8")
    )
    contract = language_contract()
    assert contract["schema"] == schema
    assert len(contract["operations"]) == 12
    join = next(v for v in contract["operations"] if v["id"] == "text.join@1")
    assert join["config_schema"]["properties"]["separator"]["default"] == ""
    assert join["inputs"] == [
        {"key": "first", "type": "text", "cardinality": "one", "required": True},
        {"key": "second", "type": "text", "cardinality": "one", "required": True},
    ]
    contract["schema"]["properties"].clear()
    assert language_contract()["schema"] == schema


@pytest.mark.parametrize("field", ["id", "operation", "config_key", "filename"])
def test_terminal_newline_cannot_bypass_closed_identifiers(field):
    definition = fixture("concept-brief")
    if field == "id":
        definition["id"] += "\n"
    elif field == "operation":
        definition["steps"][0]["operation"] += "\n"
    elif field == "config_key":
        definition["steps"][0]["config"] = {"value\n": "bad"}
    else:
        step = next(
            s for s in definition["steps"] if s["operation"] == "artifact.write-text@1"
        )
        step["config"]["filename"] += "\n"
    with pytest.raises(NativeProcessError):
        validate_definition(definition)


def test_packaged_development_definitions_and_oracles_match_reviewed_contract():
    packaged = ROOT / "src/wright_engineering/static/native-processes"
    for name in (
        "concept-brief",
        "mass-check",
        "package-review",
        "mass-check-fails",
        "oracles",
    ):
        assert (packaged / f"{name}.json").read_bytes() == (
            CONTRACTS / "examples" / f"{name}.json"
        ).read_bytes()


def test_independently_frozen_canonical_vectors():
    vectors = json.loads(
        (CONTRACTS / "canonical-vectors.json").read_text(encoding="utf-8")
    )
    for case in vectors["accepted"]:
        raw = canonical_json_bytes(
            strict_json_loads(case["input_json"].encode("utf-8"))
        )
        assert raw.hex() == case["canonical_utf8_hex"], case["id"]
        assert hashlib.sha256(raw).hexdigest() == case["sha256"], case["id"]
    for case in vectors["rejected"]:
        with pytest.raises(ValueError):
            strict_json_loads(case["input_json"].encode("utf-8"))


def test_invalid_and_saveable_draft_contract_cases():
    for case in fixture("invalid-and-draft-cases")["cases"]:
        if case["expected"] == "structural_error":
            with pytest.raises(NativeProcessError):
                validate_definition(case["definition"])
        else:
            document = validate_definition(case["definition"])
            assert readiness(document), case["id"]


def test_exact_endpoints_cycle_and_multiple_producers():
    definition = fixture("concept-brief")
    definition["connections"][0]["source_port_id"] = "brief-compose-output-text"
    with pytest.raises(NativeProcessError, match="acyclic"):
        validate_definition(definition)
    definition = fixture("concept-brief")
    duplicate = dict(definition["connections"][0], id="duplicate-connection")
    definition["connections"].append(duplicate)
    with pytest.raises(NativeProcessError, match="one producer"):
        validate_definition(definition)


def test_deterministic_topology_uses_declaration_order_not_titles():
    definition = fixture("study-trace")
    first = topological_order(definition)
    for step in definition["steps"]:
        step["title"] = "Same title"
    assert topological_order(definition) == first
    assert (
        first.index("base-compose")
        < first.index("full-compose")
        < first.index("brief-file")
    )


def test_document_copy_and_layout_cannot_mutate_semantics():
    document = validate_definition(fixture("concept-brief"))
    digest = document.semantic_digest
    working = document.as_dict()
    working["steps"][0]["config"]["value"] = "Different content"
    assert validate_definition(working).semantic_digest != digest
    layout = {"need-source": {"x": 40, "y": -100}}
    saved = validate_presentation(document, layout)
    layout["need-source"]["x"] = 60
    assert saved["need-source"]["x"] == 40
    assert document.semantic_digest == digest
    assert document.as_dict()["steps"][0]["config"]["value"] == "Design a desk bracket."
    for invalid in (
        {"absent": {"x": 0, "y": 0}},
        {"need-source": {"x": True, "y": 0}},
        {"need-source": {"x": 100001, "y": 0}},
    ):
        with pytest.raises(NativeProcessError):
            validate_presentation(document, invalid)


def test_empty_draft_and_missing_operation_config_do_not_claim_readiness():
    definition = fixture("concept-brief")
    for group in ("steps", "ports", "connections", "outputs"):
        definition[group] = []
    assert readiness(validate_definition(definition))[0].code == "EMPTY_PROCESS"
    definition = fixture("concept-brief")
    definition["steps"][0]["config"] = {}
    assert any(
        f.code == "CONFIG_REQUIRED" for f in readiness(validate_definition(definition))
    )


def test_quantity_dimensions_are_checked_without_executing_assertions():
    definition = fixture("mass-check")
    source = next(
        s for s in definition["steps"] if s["operation"] == "quantity.input@1"
    )
    source["config"]["value"]["unit"] = "N"
    assert any(
        f.code == "QUANTITY_DIMENSION"
        for f in readiness(validate_definition(definition))
    )
    assert not readiness(validate_definition(fixture("mass-check-fails")))
    definition = fixture("mass-check")
    check = next(s for s in definition["steps"] if s["operation"] == "quantity.range@1")
    check["config"]["minimum"] = {"value": "201", "unit": "g"}
    assert any(
        f.code == "QUANTITY_DIMENSION"
        for f in readiness(validate_definition(definition))
    )


@pytest.mark.parametrize(
    "raw",
    [b'{"id":1,"id":2}', b"\xef\xbb\xbf{}", b"[]", b"{}" * (1024 * 1024), b'{"x":1.0}'],
    ids=["duplicate", "bom", "array", "oversized", "float"],
)
def test_malformed_or_oversized_document_is_bounded(raw):
    with pytest.raises(NativeProcessError):
        validate_definition(raw)


@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "C:/secret",
        "folder/../../secret",
        "//host/share",
        "file:stream",
        "folder\\..\\secret",
    ],
)
def test_artifact_input_rejects_unconfined_paths(path):
    definition = fixture("concept-brief")
    definition["steps"][0].update(operation="artifact.input@1", config={"path": path})
    definition["ports"][0]["type"] = "artifact"
    definition["connections"] = []
    with pytest.raises(NativeProcessError, match="relative"):
        validate_definition(definition)


@pytest.mark.parametrize(
    "value",
    [
        "1.0",
        "01",
        "+1",
        "1e0",
        "-0",
        "NaN",
        "1000000000000000001",
        "0.0000000000000000001",
        "123456789012345678.12345678901234567",
    ],
)
def test_decimal_rejects_ambiguous_or_unbounded_values(value):
    with pytest.raises(ValueError):
        decimal_value(value)


def test_quantity_calculation_conversion_and_range_are_exact():
    volume = Quantity("0.00005", "m3")
    density = Quantity("2700", "kg/m3")
    mass = volume.multiply(density, "g")
    assert mass.as_dict() == {"value": "135", "unit": "g"}
    assert mass.convert("kg") == Quantity("0.135", "kg")
    assert mass.compare(Quantity("100", "g")) == 1
    assert mass.compare(Quantity("0.2", "kg")) == -1
    assert mass.compare(Quantity("0.135", "kg")) == 0
    with pytest.raises(ValueError):
        mass.convert("mm")
    with pytest.raises(ValueError):
        volume.multiply(density, "N")
    with pytest.raises(ValueError):
        Quantity("0.000000000000000001", "mm").convert("m")


def test_quantities_are_independent_of_callers_decimal_context():
    exact = "999999999999999999.1234567890123456"
    with localcontext() as context:
        context.prec = 5
        assert str(decimal_value(exact)) == exact
        assert Quantity("0.00005", "m3").multiply(
            Quantity("2700", "kg/m3"), "g"
        ) == Quantity("135", "g")


def test_quantity_context_isolates_exponents_clamp_and_all_traps():
    with localcontext() as context:
        context.prec = 5
        context.Emin = -2
        context.Emax = 2
        context.clamp = 1
        context.clear_flags()
        for signal in context.traps:
            context.traps[signal] = True
        assert Quantity("1", "kg").convert("g") == Quantity("1000", "g")
        assert Quantity("0.001", "g").convert("kg") == Quantity("0.000001", "kg")
        assert Quantity("0.00005", "m3").multiply(
            Quantity("2700", "kg/m3"), "g"
        ) == Quantity("135", "g")
        assert Quantity("0.001", "g").compare(Quantity("0.000001", "kg")) == 0
        assert (context.prec, context.Emin, context.Emax, context.clamp) == (
            5,
            -2,
            2,
            1,
        )
        assert not any(context.flags.values())
