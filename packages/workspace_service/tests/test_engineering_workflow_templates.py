from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest
import yaml
from core.engineering_workflow_templates import (
    EngineeringWorkflowTemplateError,
    validate_template_exploration,
)
from workspace_service.engineering_workflow_templates import (
    EngineeringWorkflowTemplateCatalog,
)

TEMPLATE_IDS = (
    "printed-replacement-part",
    "raspberry-pi-enclosure",
    "sheet-metal-supplier-handoff",
    "lightweight-equipment-bracket",
    "sensor-interface-pcb",
    "parametric-drill-jig",
    "robot-tracking-diagnosis",
    "heat-spreader-sizing",
    "sensor-fan-harness",
    "water-heater-sizing",
    "replacement-drawer-handle",
)


def template_resource_root() -> Path:
    return (
        Path(__file__).parents[1]
        / "src"
        / "workspace_service"
        / "engineering_workflow_templates"
    )


def test_catalog_preserves_ten_reviewed_templates_and_appends_handle_starter():
    catalog = EngineeringWorkflowTemplateCatalog()
    templates = catalog.list()

    assert tuple(item.template_id for item in templates) == TEMPLATE_IDS
    assert all(item.version == "1.0.0" for item in templates[:-1])
    assert templates[-1].version == "1.0.3"
    assert all(item.definition_status == "reviewed" for item in templates)
    assert len({item.title for item in templates}) == len(TEMPLATE_IDS)


def test_catalog_resources_are_safe_digest_bound_and_attributed():
    root = template_resource_root().resolve()
    for template in EngineeringWorkflowTemplateCatalog().list():
        for resource, digest in (
            (template.source_resource, template.source_digest),
            (template.layout_resource, template.layout_digest),
        ):
            target = (root / resource).resolve(strict=True)
            assert root in target.parents
            assert ".." not in resource
            assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
        assert template.rights["fixture"]
        assert (root / template.preview_asset).is_file()
        assert template.preview_alt.strip()


def test_handle_recorded_exploration_preserves_inputs_without_live_qualification():
    catalog = EngineeringWorkflowTemplateCatalog()
    template = catalog.get("replacement-drawer-handle").template
    summary = template.summary_document()
    exploration = summary["exploration"]
    assert exploration["preview_kind"] == "recorded_result"
    assert exploration["outcome_status"] == "recorded"
    record = exploration["recorded_result"]
    assert record["run_id"] == "de60e23084294148a3a8129bf2bcb1b8"
    assert record["source_digest"] == (
        "a215916fa57e9cc7813bf0b1ea3f2fff6066b8e362764dc2bab0f461a6feb617"
    )
    assert record["artifact_digest"] == (
        "303382840d71c7026b5db083838757a68c6e8119b9d21159185a4f72985ff54c"
    )
    assert summary["readiness"]["state"] == "setup_required"
    assert not any(
        summary["readiness"][key]
        for key in ("configured", "qualified", "available", "verified_run")
    )
    assert summary["external_effects"] == []
    instance = catalog.fresh_instance(
        template.template_id,
        version=template.version,
        expected_source_digest=template.source_digest,
    )
    supplied = {Path(name).name: data for name, data in instance.seed_files}
    repo = Path(__file__).resolve().parents[3]
    original = (
        repo
        / "tests/datasets/engineering-workflows/scenarios/printed-replacement-part/02-repair-cart-bow-handle"
    )
    for name in (
        "concept.svg",
        "concept.png",
        "context.md",
        "prompt.txt",
        "scenario.json",
        "user-profile.md",
    ):
        assert supplied[name] == (original / name).read_bytes()
    profile_path = (
        template_resource_root().parent
        / "process_validation/profiles/printed-replacement-part-02.json"
    )
    assert supplied["validation-profile.json"] == profile_path.read_bytes()
    # Presentation embeds the original input and exact actual mesh image bytes.
    preview, media_type = catalog.preview(template.template_id, "1.0.3")
    assert media_type == "image/svg+xml"
    svg = ET.fromstring(preview)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    images = {item.attrib["id"]: item for item in svg.findall("svg:image", namespace)}
    assert set(images) == {"supplied-sketch", "recorded-mesh"}
    sketch_uri = images["supplied-sketch"].attrib["href"]
    mesh_uri = images["recorded-mesh"].attrib["href"]
    assert sketch_uri.startswith("data:image/svg+xml;base64,")
    assert mesh_uri.startswith("data:image/png;base64,")
    assert (
        base64.b64decode(sketch_uri.split(",", 1)[1], validate=True)
        == supplied["concept.svg"]
    )
    mesh_bytes = base64.b64decode(mesh_uri.split(",", 1)[1], validate=True)
    assert hashlib.sha256(mesh_bytes).hexdigest() == (
        "e458883079a345cd1197c1a89368f77ad9bfda1a76f77c63c542593c851bbc24"
    )
    metadata = json.loads(svg.find("svg:metadata", namespace).text)
    assert metadata["recorded_result"] == record
    assert (
        metadata["supplied_sketch_sha256"]
        == hashlib.sha256(supplied["concept.svg"]).hexdigest()
    )
    assert (
        metadata["recorded_mesh_preview_sha256"]
        == hashlib.sha256(mesh_bytes).hexdigest()
    )
    assert "SUPPLIED SKETCH" in preview.decode()
    assert "RECORDED MESH" in preview.decode()
    assert "Setup required on your host" in preview.decode()
    assert all(
        node.tag.rsplit("}", 1)[-1] not in {"script", "foreignObject"}
        for node in svg.iter()
    )
    evidence = repo / record["evidence_reference"]
    assert evidence.is_file()
    completion = json.loads((evidence.parent / "receipt.json").read_text())
    assert completion["state"] == "completed"
    assert completion["run_id"] == record["run_id"]
    assert completion["source_digest"] == record["source_digest"]
    assert completion["assessment_summary"]["counts"] == {
        "pass": 43,
        "fail": 0,
        "blocked": 0,
        "inconclusive": 0,
        "error": 0,
        "not_applicable": 0,
    }
    assert completion["assessment_summary"]["physical_validation"] == "not_assessed"
    assert completion["subjects"] == 17
    assert len(completion["review_ids"]) == 6
    assessment = evidence.parent / (completion["assessment_id"] + ".json")
    assert hashlib.sha256(assessment.read_bytes()).hexdigest() == (
        "f84fe135acab8306270091b5bf38e0ebf29649f8154fdb90b0520d312add05bb"
    )
    actual_package = (
        evidence.parent.parent / "run-evidence/outputs/slice_package.gcode.3mf"
    )
    assert (
        hashlib.sha256(actual_package.read_bytes()).hexdigest()
        == record["artifact_digest"]
    )
    rights = json.loads(supplied["rights.json"])
    assert rights["license"] == "CC0-1.0"
    assert all(
        hashlib.sha256(supplied[name]).hexdigest() == digest
        for name, digest in rights["files"].items()
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"preview_kind": []},
        {"outcome_status": []},
        {"outcome_status": "recorded"},
        {"preview_kind": "recorded_result"},
        {"recorded_result": None},
        {"stages": [{"title": "Only a title"}]},
        {"limitations": [None]},
        {"run_authorized": True},
    ],
)
def test_exploration_rejects_missing_provenance_and_unknown_authority(changes):
    exploration = copy.deepcopy(
        EngineeringWorkflowTemplateCatalog()
        .get("replacement-drawer-handle")
        .template.exploration
    )
    # Start from an explicitly pending contract so negative cases remain negative
    # when the packaged example acquires real recorded provenance.
    exploration.update(preview_kind="supplied_sketch", outcome_status="pending")
    exploration.pop("recorded_result", None)
    exploration.update(changes)
    with pytest.raises(EngineeringWorkflowTemplateError) as error:
        validate_template_exploration(exploration)
    assert error.value.code == "template_exploration_invalid"


def test_recorded_exploration_requires_exact_source_and_artifact_provenance():
    exploration = copy.deepcopy(
        EngineeringWorkflowTemplateCatalog()
        .get("replacement-drawer-handle")
        .template.exploration
    )
    exploration.update(
        outcome_status="recorded",
        recorded_result={
            "run_id": "test-fixture-run",
            "source_digest": "a" * 64,
            "artifact_digest": "b" * 64,
            "evidence_reference": "fixtures/result.json",
            "scope": "Synthetic contract fixture, not engineering evidence",
        },
    )
    assert (
        validate_template_exploration(exploration)["recorded_result"]
        == exploration["recorded_result"]
    )
    exploration["recorded_result"]["artifact_digest"] = "unbound"
    with pytest.raises(EngineeringWorkflowTemplateError):
        validate_template_exploration(exploration)


def test_old_templates_keep_their_existing_optional_metadata_contract():
    catalog = EngineeringWorkflowTemplateCatalog()
    for template in catalog.list()[:-1]:
        assert "exploration" not in template.summary_document()


def test_sources_and_layouts_have_one_fresh_workflow_identity_and_valid_shape():
    catalog = EngineeringWorkflowTemplateCatalog()
    for template in catalog.list():
        detail = catalog.get(template.template_id)
        assert detail.source.splitlines().count("workflow __instance__") == 1
        assert "reviewed_ai_suggestions: true" in detail.source
        assert detail.layout == {
            "documentKind": "workflow-layout",
            "schemaVersion": "1.0.0-recovery.1",
            "workflowId": "workflow.__instance__",
            "semanticRevision": 1,
            "layoutRevision": 1,
            "positions": {},
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }


def test_each_instance_has_fresh_workflow_and_block_identities():
    catalog = EngineeringWorkflowTemplateCatalog()
    template = catalog.list()[0]
    left = catalog.fresh_instance(
        template.template_id,
        version=template.version,
        expected_source_digest=template.source_digest,
    )
    right = catalog.fresh_instance(
        template.template_id,
        version=template.version,
        expected_source_digest=template.source_digest,
    )

    assert left.workflow_id != right.workflow_id
    assert set(left.semantic_ids).isdisjoint(right.semantic_ids)
    assert "__instance__" not in left.source
    assert left.layout["workflowId"] == left.workflow_id
    assert right.layout["workflowId"] == right.workflow_id


def test_unknown_version_and_stale_preview_digest_fail_closed():
    catalog = EngineeringWorkflowTemplateCatalog()
    template = catalog.list()[0]

    with pytest.raises(EngineeringWorkflowTemplateError) as missing:
        catalog.get(template.template_id, "2.0.0")
    assert missing.value.code == "template_not_found"

    with pytest.raises(EngineeringWorkflowTemplateError) as stale:
        catalog.fresh_instance(
            template.template_id,
            version=template.version,
            expected_source_digest="0" * 64,
        )
    assert stale.value.code == "template_digest_mismatch"


def test_catalog_rejects_unsafe_resource_paths(tmp_path):
    document = yaml.safe_load(
        (template_resource_root() / "catalog.yaml").read_text("utf-8")
    )
    document["templates"][0]["source"] = "../escape"
    (tmp_path / "catalog.yaml").write_text(yaml.safe_dump(document), "utf-8")

    with pytest.raises(EngineeringWorkflowTemplateError) as error:
        EngineeringWorkflowTemplateCatalog(tmp_path)
    assert error.value.code == "template_resource_path_invalid"


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda document: document.update({"unknown": True}),
            "template_catalog_invalid",
        ),
        (
            lambda document: document["templates"][0].update({"api_key": "embedded"}),
            "template_credentials_forbidden",
        ),
    ],
)
def test_catalog_rejects_unknown_or_credential_valued_fields(tmp_path, mutation, code):
    document = yaml.safe_load(
        (template_resource_root() / "catalog.yaml").read_text("utf-8")
    )
    mutation(document)
    (tmp_path / "catalog.yaml").write_text(yaml.safe_dump(document), "utf-8")

    with pytest.raises(EngineeringWorkflowTemplateError) as error:
        EngineeringWorkflowTemplateCatalog(tmp_path)
    assert error.value.code == code


def test_handle_preview_version_changes_without_replacing_old_saved_source():
    catalog = EngineeringWorkflowTemplateCatalog()
    current = catalog.get("replacement-drawer-handle", "1.0.3").template
    for lookup in (
        lambda: catalog.get(current.template_id, "1.0.0"),
        lambda: catalog.preview(current.template_id, "1.0.0"),
        lambda: catalog.fresh_instance(
            current.template_id,
            version="1.0.0",
            expected_source_digest=current.source_digest,
        ),
    ):
        with pytest.raises(EngineeringWorkflowTemplateError) as error:
            lookup()
        assert error.value.code == "template_not_found"
