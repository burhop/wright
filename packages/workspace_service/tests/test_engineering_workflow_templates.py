from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
import yaml
from core.engineering_workflow_templates import EngineeringWorkflowTemplateError
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
)


def template_resource_root() -> Path:
    return (
        Path(__file__).parents[1]
        / "src"
        / "workspace_service"
        / "engineering_workflow_templates"
    )


def test_catalog_contains_exactly_ten_reviewed_templates_in_reviewed_order():
    catalog = EngineeringWorkflowTemplateCatalog()
    templates = catalog.list()

    assert tuple(item.template_id for item in templates) == TEMPLATE_IDS
    assert all(item.version == "1.0.0" for item in templates)
    assert all(item.definition_status == "reviewed" for item in templates)
    assert len({item.title for item in templates}) == 10


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


def test_sources_and_layouts_have_one_fresh_workflow_identity_and_valid_shape():
    catalog = EngineeringWorkflowTemplateCatalog()
    for template in catalog.list():
        detail = catalog.get(template.template_id)
        assert (
            len(re.findall(r"^workflow __instance__$", detail.source, re.MULTILINE))
            == 1
        )
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
