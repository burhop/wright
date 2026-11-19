import hashlib
import json
from importlib.resources import files

import pytest
from wright_workflow import WorkflowSourceExecutionError, parse
from wright_workflow.bundle import WorkflowBundle
from wright_workflow.contracts import canonical_digest
from wright_workflow.human_input import HumanInputDeclaration
from wright_workflow.instructions import WorkflowInstructionSet

SOURCE = """workflow inspection
  name: "Inspect part"
  purpose: "Record the measured dimension"
  discipline: mechanical
  reviewed_ai_suggestions: false
end
task measure
  name: "Measure part"
  purpose: "Retain the measurement"
  step_type: work
  group: null
  performed_by: configured_tool
  inputs: []
  outputs: [{"key":"length","name":"Length","kind":"structured_result","item":null,"required":true,"quantity":"one","description":"Measured length"}]
  prompt: ""
  settings: {"authoring_template":"mcp-tool","mcp_server":"caliper","mcp_tool":"caliper__measure","mcp_schema_digest":"1234"}
  tool: null
  reusable_step: null
end
"""


def bundle(source):
    return {
        "schema_version": "wright.workflow-bundle/1",
        "mode": "source",
        "source": source,
        "source_digest": hashlib.sha256(source.encode()).hexdigest(),
        "dependencies": [
            {
                "category": "instructions",
                "identity": "legacy-local-defaults",
                "disposition": "external",
                "details": {"migration_required": True},
            },
            {
                "category": "provider",
                "identity": "measure",
                "disposition": "external",
                "details": {
                    "server_id": "caliper",
                    "tool_name": "caliper__measure",
                    "schema_digest": "1234",
                    "qualification": "requires-local-registry-review",
                },
            },
        ],
    }


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_preserve_exact_bytes_and_line_endings(tmp_path, newline):
    raw = ("# mesure en µm\n" + SOURCE).replace("\n", newline).encode()
    path = tmp_path / "part.workflow.wflow"
    path.write_bytes(raw)
    doc = parse(path)
    assert doc.source == doc.raw == raw
    assert doc.source_digest == hashlib.sha256(raw).hexdigest()
    assert doc.graph.ordered == ["measure"]


def test_reader_accepts_native_export_wrapper():
    raw = bundle(SOURCE)
    wrapper = {
        "bundle": raw,
        "bundle_digest": canonical_digest(WorkflowBundle.model_validate(raw)),
    }
    assert parse(json.dumps(wrapper)).source == SOURCE.encode()


def test_required_manifest_entry_and_source_hash():
    raw = bundle(SOURCE)
    raw["dependencies"].pop()
    with pytest.raises(WorkflowSourceExecutionError, match="Missing provider"):
        parse(json.dumps(raw))
    raw["source_digest"] = "0" * 64
    with pytest.raises(WorkflowSourceExecutionError, match="differs from its digest"):
        parse(json.dumps(raw))


def test_duplicate_source_field_reports_actionable_location():
    source = SOURCE.replace("  discipline: mechanical", "  name: duplicate")
    with pytest.raises(WorkflowSourceExecutionError, match="line 4") as info:
        parse(source)
    assert info.value.code == "WORKFLOW_SOURCE_INVALID"
    assert info.value.correction


@pytest.mark.parametrize(
    "change", ["extra_ui", "grant", "provider_build", "credential"]
)
def test_bundle_metadata_cannot_change_local_authority(change):
    raw = bundle(SOURCE)
    if change == "extra_ui":
        raw["dependencies"].append(
            {"category": "ui", "identity": "other", "disposition": "embedded"}
        )
    elif change == "provider_build":
        raw["dependencies"][1]["details"]["schema_digest"] = "different"
    else:
        raw["dependencies"][1]["details"][
            {"grant": "approved", "credential": "api_key"}[change]
        ] = "test"
    with pytest.raises(WorkflowSourceExecutionError):
        parse(json.dumps(raw))


def test_native_reader_exposes_source_declarations_without_a_manifest():
    doc = parse(SOURCE)
    assert [(d.category, d.identity) for d in doc.dependencies] == [
        ("instructions", "legacy-local-defaults"),
        ("provider", "measure"),
    ]
    assert (
        doc.graph.blocks["measure"]["fields"]["settings"]["mcp_schema_digest"] == "1234"
    )


@pytest.mark.parametrize(
    "name,model",
    [
        ("workflow-bundle-1", WorkflowBundle),
        ("workflow-instructions-1", WorkflowInstructionSet),
        ("human-input", HumanInputDeclaration),
    ],
)
def test_distributed_schemas_match_the_wire_models(name, model):
    schema = files("wright_workflow").joinpath("schemas", name + ".schema.json")
    assert json.loads(schema.read_text(encoding="utf-8")) == model.model_json_schema()
