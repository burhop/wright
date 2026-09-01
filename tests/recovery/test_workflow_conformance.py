from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.recovery.evaluate_workflow_syntaxes import (
    authoring_text,
    dsl_text,
    json_text,
    parse_authoring,
    yaml_text,
)
from scripts.recovery.workflow_conformance import (
    apply,
    canonical_bytes,
    format,
    parse,
    project,
    semanticDiff,
    semantic_digest,
    validate,
)


FEATURE = Path("specs/080-canonical-workflow-recovery")
JSON_FIXTURE = FEATURE / "fixtures/mounting-bracket.workflow.json"
YAML_FIXTURE = FEATURE / "fixtures/mounting-bracket.workflow.yaml"
AUTHORING_FIXTURE = FEATURE / "fixtures/mounting-bracket.workflow.wflow"
DSL_FIXTURE = FEATURE / "fixtures/mounting-bracket.workflow.internal-ir.wflow"
CONTRACTS = FEATURE / "contracts"


@pytest.fixture
def workflow() -> dict:
    return json.loads(JSON_FIXTURE.read_text(encoding="utf-8"))


def treatment_text(value: dict, syntax: str) -> str:
    return {"json": json_text, "yaml": yaml_text, "dsl": dsl_text}[syntax](value)


def test_committed_treatments_are_current_and_semantically_identical(workflow: dict) -> None:
    committed = {
        "json": JSON_FIXTURE.read_text(encoding="utf-8"),
        "yaml": YAML_FIXTURE.read_text(encoding="utf-8"),
        "dsl": DSL_FIXTURE.read_text(encoding="utf-8"),
    }
    for syntax, text in committed.items():
        result = parse(text, syntax)
        assert result.ok, result.diagnostics
        assert result.ir is not None
        assert canonical_bytes(result.ir) == canonical_bytes(workflow)
        formatted, source_map = format(result.ir, syntax, result.comments)
        reparsed = parse(formatted, syntax)
        assert reparsed.ok
        assert canonical_bytes(reparsed.ir) == canonical_bytes(workflow)
        if syntax == "dsl":
            assert len(source_map) == 66


def test_committed_engineering_source_is_current_lossless_and_engineer_facing(
    workflow: dict,
) -> None:
    text = AUTHORING_FIXTURE.read_text(encoding="utf-8")
    assert text == authoring_text(workflow)
    assert "workflow mounting_bracket" in text
    assert "item design_specification" in text
    assert "input design_intent" in text
    assert "task create_design_specification" in text
    assert "prompt:" in text
    assert "design_document" in text
    assert "step_file" in text
    assert "\ngroup " not in text
    assert "  group: null" in text
    assert "connection design_intent_to_specification" in text
    assert '"key":"design_specification_in"' in text
    assert '"assignment":"generate_geometry"' in text
    assert '"key":"review_cell"' in text
    for managed_field in (
        "version:",
        "schema_version:",
        "revision:",
        "parent_revision:",
        "semantic_sha256:",
        "digest:",
        "authorship:",
    ):
        assert managed_field not in text
    assert re.search(r"\bblock\.", text) is None
    assert re.search(r"\bport\.", text) is None
    assert re.search(r"\bartifact\.", text) is None
    assert re.search(r"\btype\.", text) is None
    assert '"kind":"design_intent"' in text
    assert '"kind":"cad_model"' in text
    assert "phase " not in text

    rebound = parse_authoring(text, workflow)
    assert canonical_bytes(rebound.ir) == canonical_bytes(workflow)
    assert validate(rebound.ir).valid
    assert len(rebound.source_map) == 62


def test_engineering_source_edits_rehydrate_without_exposing_host_authority(workflow: dict) -> None:
    text = AUTHORING_FIXTURE.read_text(encoding="utf-8")
    edited = text.replace('  name: "Create bracket CAD model"', '  name: "Create parametric bracket"', 1)
    edited = edited.replace('"thickness_mm":6', '"thickness_mm":8', 1)
    edited = edited.replace(
        '"item":"design_specification","key":"design_specification_check_in","kind":"design_specification","name":"Reviewed design specification","quantity":"one","required":true',
        '"item":"design_specification","key":"design_specification_check_in","kind":"design_specification","name":"Reviewed design specification","quantity":"optional","required":false',
        1,
    )
    edited = edited.replace(
        '"action":"tool.export-step-ap242","assignment":"export_step"',
        '"action":"tool.export-step-ap242-reviewed","assignment":"export_step"',
        1,
    )
    edited = edited.replace(
        '  when: "A design requirement or manufacturing issue is unresolved"',
        '  when: "Any required input is missing or a warning remains unresolved"',
        1,
    )
    rebound = parse_authoring(edited, workflow).ir
    geometry = next(block for block in rebound["blocks"] if block["id"] == "block.generate-geometry")
    assert geometry["title"] == "Create parametric bracket"
    assert geometry["configuration"]["thickness_mm"] == 8
    criteria_port = next(
        port
        for port in rebound["ports"]
        if port["id"] == "port.design-specification-check-in"
    )
    assert criteria_port["required"] is False
    assert criteria_port["cardinality"] == "optional"
    export_binding = next(
        binding
        for binding in rebound["bindings"]
        if binding["id"] == "binding.export-step"
    )
    assert export_binding["tool_id"] == "tool.export-step-ap242-reviewed"
    feedback = next(
        relationship
        for relationship in rebound["relationships"]
        if relationship["id"] == "rel.review-revise"
    )
    assert feedback["condition"] == (
        "Any required input is missing or a warning remains unresolved"
    )
    assert rebound["revision"] == workflow["revision"]
    assert rebound["parent_revision"] == workflow["parent_revision"]
    assert rebound["semantic_sha256"] is None
    assert validate(rebound).valid

    with pytest.raises(ValueError, match="WFR-SOURCE-FIELD-MANAGED"):
        parse_authoring(
            text.replace('  name: "Mounting bracket development"', '  revision: 99\n  name: "Mounting bracket development"', 1),
            workflow,
        )


@pytest.mark.parametrize(
    "mutate,code",
    [
        (lambda text: text.replace("  name:", "  name", 1), "WFR-SOURCE-FIELD-INVALID"),
        (lambda text: text.replace("  purpose:", "  unknown_field: true\n  purpose:", 1), "WFR-SOURCE-FIELD-UNKNOWN"),
        (lambda text: text.replace("  name:", "  name: duplicate\n  name:", 1), "WFR-SOURCE-FIELD-DUPLICATE"),
        (lambda text: text.replace("item geometry", "item unexpected_geometry", 1), "WFR-SOURCE-ITEM-MISSING"),
        (lambda text: text.replace("  type: cad_model", "  type: executable", 1), "WFR-SOURCE-TYPE-CHANGE"),
        (lambda text: text.replace("  performed_by: configured_tool", "  performed_by: untrusted_robot", 1), "WFR-SOURCE-ACTOR"),
        (lambda text: text.replace('"quantity":"many"', '"quantity":"sometimes"', 1), "WFR-SOURCE-PORT-INVALID"),
        (lambda text: text.replace("  to: generate_geometry", "  to: missing_step", 1), "WFR-SOURCE-ENDPOINT-UNKNOWN"),
        (lambda text: text.replace("  group: null", "  group: undocumented_group", 1), "WFR-SOURCE-GROUP-UNKNOWN"),
        (lambda text: text.replace("  type: item", "  type: stream", 1), "WFR-SOURCE-CONNECTION-TYPE"),
        (
            lambda text: text.replace(
                '"assignment":"generate_geometry"',
                '"assignment":"missing_assignment"',
                1,
            ),
            "WFR-SOURCE-TOOL-UNKNOWN",
        ),
    ],
)
def test_engineering_source_invalid_controls_fail_closed(workflow: dict, mutate, code: str) -> None:
    text = AUTHORING_FIXTURE.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match=code):
        parse_authoring(mutate(text), workflow)


def invalid_treatments(workflow: dict, syntax: str) -> list[tuple[str, str]]:
    malformed = {
        "json": JSON_FIXTURE.read_text(encoding="utf-8").replace('"document_kind":', '"document_kind"', 1),
        "yaml": YAML_FIXTURE.read_text(encoding="utf-8").replace("document_kind:", "document_kind", 1),
        "dsl": DSL_FIXTURE.read_text(encoding="utf-8").replace("  title:", "  title", 1),
    }[syntax]

    unknown = copy.deepcopy(workflow)
    unknown["blocks"][0]["unknown_field"] = True
    unknown_text = treatment_text(unknown, syntax)
    if syntax == "dsl":
        unknown_text = DSL_FIXTURE.read_text(encoding="utf-8").replace(
            "  title: \"Reference images\"",
            "  title: \"Reference images\"\n  unknown_field: true",
            1,
        )

    bad_enum = copy.deepcopy(workflow)
    bad_enum["ports"][0]["cardinality"] = "sometimes"
    wrong_type = copy.deepcopy(workflow)
    wrong_type["ports"][0]["required"] = "yes"
    dangling = copy.deepcopy(workflow)
    dangling["relationships"][0]["target_id"] = "port.missing"
    duplicate_id = copy.deepcopy(workflow)
    duplicate_id["ports"][1]["id"] = duplicate_id["ports"][0]["id"]
    nonfinite = copy.deepcopy(workflow)
    nonfinite["phases"][0]["order"] = float("nan")

    duplicate_key = {
        "json": JSON_FIXTURE.read_text(encoding="utf-8").replace(
            '  "revision": 2,', '  "revision": 2,\n  "revision": 3,', 1
        ),
        "yaml": YAML_FIXTURE.read_text(encoding="utf-8").replace(
            "revision: 2", "revision: 2\nrevision: 3", 1
        ),
        "dsl": DSL_FIXTURE.read_text(encoding="utf-8").replace(
            "  revision: 2", "  revision: 2\n  revision: 3", 1
        ),
    }[syntax]
    return [
        ("malformed delimiter", malformed),
        ("unknown field", unknown_text),
        ("invalid enum", treatment_text(bad_enum, syntax)),
        ("wrong scalar type", treatment_text(wrong_type, syntax)),
        ("dangling reference", treatment_text(dangling, syntax)),
        ("duplicate stable id", treatment_text(duplicate_id, syntax)),
        ("duplicate key", duplicate_key),
        ("non-finite number", treatment_text(nonfinite, syntax)),
    ]


@pytest.mark.parametrize("syntax", ["json", "yaml", "dsl"])
def test_all_eight_invalid_controls_fail_closed(workflow: dict, syntax: str) -> None:
    outcomes = [(name, parse(text, syntax)) for name, text in invalid_treatments(workflow, syntax)]
    assert len(outcomes) == 8
    for name, result in outcomes:
        assert not result.ok, name
        assert result.ir is None, name
        assert result.diagnostics, name
        assert result.diagnostics[0].code.startswith("WFR-"), name
        assert result.diagnostics[0].explanation, name
        assert result.diagnostics[0].correction, name


def five_edit_batch(revision: int, origin: str = "graph") -> dict:
    return {
        "document_kind": "workflow-command-batch",
        "schema_version": "1.0.0-recovery.1",
        "base_revision": revision,
        "origin": origin,
        "commands": [
            {"kind": "set_block_title", "block_id": "block.generate-geometry", "title": "Create parametric bracket"},
            {"kind": "set_block_configuration", "block_id": "block.generate-geometry", "key": "thickness_mm", "value": 8},
            {"kind": "set_port_contract", "port_id": "port.design-specification-check-in", "required": False, "cardinality": "optional"},
            {"kind": "set_binding_tool", "binding_id": "binding.export-step", "tool_id": "tool.export-step-ap242-reviewed"},
            {"kind": "set_relationship_condition", "relationship_id": "rel.review-revise", "condition": "Any required input is missing or a warning remains unresolved"},
        ],
    }


def layout_document(workflow: dict, positions: dict | None = None) -> dict:
    return {
        "document_kind": "workflow-layout",
        "schema_version": "1.0.0-recovery.1",
        "workflow_id": workflow["workflow_id"],
        "semantic_revision": workflow["revision"],
        "layout_revision": 1,
        "positions": positions or {},
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }


def run_document(workflow: dict) -> dict:
    return {
        "document_kind": "workflow-run",
        "schema_version": "1.0.0-recovery.1",
        "run_id": "run.test-001",
        "workflow_id": workflow["workflow_id"],
        "workflow_revision": workflow["revision"],
        "semantic_sha256": semantic_digest(workflow),
        "created_at": "2026-08-31T05:00:00Z",
        "completed_at": None,
        "mode": "simulated",
        "state": "running",
        "active_block_id": "block.check-manufacturability",
        "active_relationship_id": "rel.geometry-to-check",
        "steps": {
            "block.check-manufacturability": {"state": "running", "label": "ACTIVE", "detail": "Checking the accepted geometry."},
            "block.review-design": {
                "state": "queued",
                "label": "QUEUED",
                "detail": "Waiting for the manufacturability result.",
                "component_scope": {
                    "component_instance_id": "block.review-design",
                    "component_id": "component.review-cell",
                    "component_version": "1.0.0",
                    "internal_semantic_id": "component.review-cell.block.evaluate",
                },
            },
        },
        "activity": [],
        "artifact_records": [],
        "material_supplied": False,
        "outputs_ready": False,
    }


def test_all_recovery_wire_examples_validate_against_their_published_schemas(workflow: dict) -> None:
    examples = [
        ("canonical-workflow-ir.schema.json", workflow),
        ("workflow-command-batch.schema.json", five_edit_batch(workflow["revision"])),
        ("workflow-layout.schema.json", layout_document(workflow)),
        ("workflow-run-record.schema.json", run_document(workflow)),
    ]
    for schema_name, example in examples:
        schema = json.loads((CONTRACTS / schema_name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = sorted(Draft202012Validator(schema).iter_errors(example), key=lambda error: list(error.path))
        assert errors == [], f"{schema_name}: {[error.message for error in errors]}"

        unknown = copy.deepcopy(example)
        unknown["unknown_field"] = "must fail closed"
        assert list(Draft202012Validator(schema).iter_errors(unknown)), schema_name

    command_schema = json.loads((CONTRACTS / "workflow-command-batch.schema.json").read_text(encoding="utf-8"))
    invalid_command = five_edit_batch(workflow["revision"])
    invalid_command["commands"][0]["kind"] = "unknown_command"
    assert list(Draft202012Validator(command_schema).iter_errors(invalid_command))

    run_schema = json.loads((CONTRACTS / "workflow-run-record.schema.json").read_text(encoding="utf-8"))
    invalid_run = run_document(workflow)
    invalid_run["steps"]["block.check-manufacturability"]["unknown_field"] = True
    assert list(Draft202012Validator(run_schema).iter_errors(invalid_run))

    layout_schema = json.loads((CONTRACTS / "workflow-layout.schema.json").read_text(encoding="utf-8"))
    invalid_layout = layout_document(workflow)
    invalid_layout["viewport"]["zoom"] = 0
    assert list(Draft202012Validator(layout_schema).iter_errors(invalid_layout))

    canonical_schema = json.loads((CONTRACTS / "canonical-workflow-ir.schema.json").read_text(encoding="utf-8"))
    invalid_canonical = copy.deepcopy(workflow)
    invalid_canonical["blocks"][0]["configuration"]["nested"] = {"not": "portable"}
    assert list(Draft202012Validator(canonical_schema).iter_errors(invalid_canonical))


def test_graph_commands_round_trip_through_every_text_treatment(workflow: dict) -> None:
    result = apply(workflow, five_edit_batch(workflow["revision"]), workflow["revision"])
    assert result.ok
    assert result.candidate is not None
    assert len(result.semantic_diff) == 6
    for syntax in ("json", "yaml", "dsl"):
        text, _ = format(result.candidate, syntax)
        reparsed = parse(text, syntax)
        assert reparsed.ok
        assert canonical_bytes(reparsed.ir) == canonical_bytes(result.candidate)


def test_valid_text_edit_updates_projection_and_invalid_text_preserves_last_valid(workflow: dict) -> None:
    baseline_text, _ = format(workflow, "dsl")
    valid_text = baseline_text.replace(
        "  title: \"Create bracket CAD model\"",
        "  title: \"Create parametric bracket\"",
        1,
    )
    valid = parse(valid_text, "dsl")
    assert valid.ok and valid.ir is not None
    canvas = project(valid.ir, layout_document(valid.ir))
    assert next(node for node in canvas["nodes"] if node["id"] == "block.generate-geometry")["title"] == "Create parametric bracket"

    last_valid = copy.deepcopy(valid.ir)
    invalid_text = valid_text.replace("  cardinality: one", "  cardinality: sometimes", 1)
    invalid = parse(invalid_text, "dsl")
    assert not invalid.ok and invalid.ir is None
    assert canonical_bytes(last_valid) == canonical_bytes(valid.ir)


def test_invalid_graph_and_stale_ai_batches_are_atomic(workflow: dict) -> None:
    before = copy.deepcopy(workflow)
    invalid = apply(
        workflow,
        {
            "document_kind": "workflow-command-batch",
            "schema_version": "1.0.0-recovery.1",
            "base_revision": workflow["revision"],
            "origin": "graph",
            "commands": [
                {
                    "kind": "connect",
                    "relationship": {
                        "id": "rel.bad",
                        "kind": "data",
                        "source_id": "port.design-intent-out",
                        "target_id": "port.step-in",
                        "label": "bad types",
                        "condition": None,
                    },
                }
            ],
        },
        workflow["revision"],
    )
    assert not invalid.ok and invalid.candidate is None
    assert canonical_bytes(workflow) == canonical_bytes(before)

    stale_ai = apply(workflow, five_edit_batch(0, "ai_proposal"), workflow["revision"])
    assert not stale_ai.ok and stale_ai.candidate is None
    assert stale_ai.diagnostics[0].code == "WFR-COMMAND-STALE-BASE"
    assert canonical_bytes(workflow) == canonical_bytes(before)


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (
            lambda value: value["relationships"].append(
                {
                    **copy.deepcopy(value["relationships"][0]),
                    "id": "rel.duplicate-endpoints",
                }
            ),
            "WFR-RELATIONSHIP-DUPLICATE",
        ),
        (
            lambda value: value["relationships"].append(
                {
                    "id": "rel.invalid-feedback-source",
                    "kind": "feedback",
                    "source_id": "block.generate-geometry",
                    "target_id": "block.design-intent",
                    "label": "Invalid feedback",
                    "condition": "invalid source kind",
                }
            ),
            "WFR-RELATIONSHIP-SOURCE-KIND",
        ),
        (
            lambda value: value["relationships"].append(
                {
                    "id": "rel.non-feedback-cycle",
                    "kind": "control",
                    "source_id": "block.release-package",
                    "target_id": "block.design-intent",
                    "label": "Invalid loop",
                    "condition": None,
                }
            ),
            "WFR-CYCLE-NON-FEEDBACK",
        ),
        (
            lambda value: value["relationships"].append(
                {
                    "id": "rel.second-geometry-input",
                    "kind": "data",
                    "source_id": "port.geometry-out",
                    "target_id": "port.geometry-check-in",
                    "label": "Duplicate input",
                    "condition": "alternate",
                }
            ),
            "WFR-RELATIONSHIP-DUPLICATE",
        ),
    ],
)
def test_invalid_relationship_topologies_fail_closed(workflow: dict, mutate, expected_code: str) -> None:
    candidate = copy.deepcopy(workflow)
    mutate(candidate)
    result = validate(candidate)
    assert not result.valid
    assert expected_code in {diagnostic.code for diagnostic in result.diagnostics}


def test_single_cardinality_input_rejects_a_second_distinct_source(workflow: dict) -> None:
    candidate = copy.deepcopy(workflow)
    extra_port = copy.deepcopy(next(port for port in candidate["ports"] if port["id"] == "port.geometry-out"))
    extra_port["id"] = "port.geometry-out-secondary"
    candidate["ports"].append(extra_port)
    next(block for block in candidate["blocks"] if block["id"] == "block.generate-geometry")["output_port_ids"].append(extra_port["id"])
    candidate["relationships"].append(
        {
            "id": "rel.second-geometry-source",
            "kind": "data",
            "source_id": extra_port["id"],
            "target_id": "port.geometry-check-in",
            "label": "second geometry",
            "condition": None,
        }
    )
    result = validate(candidate)
    assert not result.valid
    assert "WFR-PORT-CARDINALITY" in {diagnostic.code for diagnostic in result.diagnostics}


@pytest.mark.parametrize(
    ("mutate", "expected_code"),
    [
        (
            lambda value: next(phase for phase in value["phases"] if phase["id"] == "phase.define")["block_ids"].remove("block.generate-geometry"),
            "WFR-PHASE-MEMBERSHIP",
        ),
        (
            lambda value: next(block for block in value["blocks"] if block["id"] == "block.generate-geometry")["input_port_ids"].remove("port.design-specification-in"),
            "WFR-PORT-OWNERSHIP",
        ),
        (
            lambda value: next(binding for binding in value["bindings"] if binding["id"] == "binding.generate-geometry")["argument_map"].__setitem__(0, {"semantic_source": "port.missing", "implementation_target": "arguments.requirements"}),
            "WFR-REFERENCE-DANGLING",
        ),
        (
            lambda value: next(binding for binding in value["bindings"] if binding["id"] == "binding.generate-geometry")["result_map"].__setitem__(0, {"semantic_source": "port.design-specification-in", "implementation_target": "result.geometry"}),
            "WFR-BINDING-MAP-DIRECTION",
        ),
        (
            lambda value: value["components"].append({
                "id": "component.invalid-interface",
                "version": "1.0.0",
                "title": "Invalid interface",
                "input_port_ids": ["port.design-intent-out"],
                "output_port_ids": [],
                "internal_definition_digest": f"sha256:{'a' * 64}",
                "internal_addresses": [{"semantic_id": "component.invalid-interface.block.inner", "concept_kind": "block", "relative_path": "blocks/block.inner"}],
            }),
            "WFR-COMPONENT-PORT-DIRECTION",
        ),
    ],
)
def test_reciprocal_binding_and_component_invariants_fail_closed(workflow: dict, mutate, expected_code: str) -> None:
    candidate = copy.deepcopy(workflow)
    mutate(candidate)
    result = validate(candidate)
    assert not result.valid
    assert expected_code in {diagnostic.code for diagnostic in result.diagnostics}

def test_ai_uses_the_same_command_protocol_and_deterministic_diff(workflow: dict) -> None:
    graph = apply(workflow, five_edit_batch(workflow["revision"], "graph"), workflow["revision"])
    ai = apply(workflow, five_edit_batch(workflow["revision"], "ai_proposal"), workflow["revision"])
    assert graph.ok and ai.ok
    assert canonical_bytes(graph.candidate) == canonical_bytes(ai.candidate)
    assert graph.semantic_diff == ai.semantic_diff
    assert semanticDiff(workflow, graph.candidate) == graph.semantic_diff


def test_layout_and_run_projection_never_change_semantic_digest(workflow: dict) -> None:
    before = copy.deepcopy(workflow)
    digest = semantic_digest(workflow)
    layout_a = layout_document(workflow, {"block.design-intent": {"x": 80, "y": 80}})
    layout_b = layout_document(workflow, {"block.design-intent": {"x": 640, "y": 220}})
    run = run_document(workflow)
    projection_a = project(workflow, layout_a)
    projection_b = project(workflow, layout_b, run)
    assert projection_a["semantic_digest"] == projection_b["semantic_digest"] == digest
    assert next(edge for edge in projection_b["edges"] if edge["id"] == "rel.geometry-to-check")["active"] is True
    assert canonical_bytes(workflow) == canonical_bytes(before)


def test_command_layout_and_run_unknown_versions_fail_closed_without_rewrite(workflow: dict) -> None:
    batch = five_edit_batch(workflow["revision"])
    unknown_batch = copy.deepcopy(batch)
    unknown_batch["schema_version"] = "99.0.0"
    batch_before = copy.deepcopy(unknown_batch)
    command_result = apply(workflow, unknown_batch, workflow["revision"])
    assert not command_result.ok
    assert command_result.diagnostics[0].code == "WFR-COMMAND-VERSION-UNSUPPORTED"
    assert unknown_batch == batch_before

    layout = layout_document(workflow)
    unknown_layout = copy.deepcopy(layout)
    unknown_layout["schema_version"] = "99.0.0"
    layout_before = copy.deepcopy(unknown_layout)
    with pytest.raises(ValueError, match="WFR-LAYOUT-VERSION-UNSUPPORTED"):
        project(workflow, unknown_layout)
    assert unknown_layout == layout_before

    run = run_document(workflow)
    unknown_run = copy.deepcopy(run)
    unknown_run["schema_version"] = "99.0.0"
    run_before = copy.deepcopy(unknown_run)
    with pytest.raises(ValueError, match="WFR-RUN-VERSION-UNSUPPORTED"):
        project(workflow, layout, unknown_run)
    assert unknown_run == run_before


def test_reusable_component_internal_addresses_round_trip_and_reject_duplicates(workflow: dict) -> None:
    component = workflow["components"][0]
    assert component["id"] == "component.review-cell"
    instance = next(block for block in workflow["blocks"] if block["id"] == "block.review-design")
    assert instance["kind"] == "component"
    assert instance["component_ref"] == {"component_id": "component.review-cell", "version_range": "^1.0.0"}
    scoped_step = run_document(workflow)["steps"]["block.review-design"]["component_scope"]
    assert scoped_step == {
        "component_instance_id": "block.review-design",
        "component_id": "component.review-cell",
        "component_version": "1.0.0",
        "internal_semantic_id": "component.review-cell.block.evaluate",
    }
    assert {address["concept_kind"] for address in component["internal_addresses"]} >= {"block", "port", "relationship", "artifact_contract"}
    for syntax in ("json", "yaml", "dsl"):
        text, _ = format(workflow, syntax)
        reparsed = parse(text, syntax)
        assert reparsed.ok
        assert reparsed.ir["components"][0]["internal_addresses"] == component["internal_addresses"]

    duplicate = copy.deepcopy(workflow)
    duplicate_address = copy.deepcopy(duplicate["components"][0]["internal_addresses"][0])
    duplicate["components"][0]["internal_addresses"].append(duplicate_address)
    result = validate(duplicate)
    assert not result.valid
    assert "WFR-COMPONENT-ADDRESS-DUPLICATE" in {diagnostic.code for diagnostic in result.diagnostics}


def test_dsl_leading_comment_and_source_identity_survive_format(workflow: dict) -> None:
    text, source_map = format(workflow, "dsl", ("Keep the 6061-T6 assumption visible.",))
    assert "# Keep the 6061-T6 assumption visible." in text
    assert "block.generate-geometry" in source_map
    reparsed = parse(text, "dsl")
    assert reparsed.comments == ("Keep the 6061-T6 assumption visible.",)
    assert validate(reparsed.ir).valid
