"""Independent controls for sheet-metal inspection and handoff evidence."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json

import pytest

from core.process_validation import (
    CheckDefinition,
    Constraint,
    ProducerIdentity,
    ResourceBudget,
    SubjectBinding,
)
from workspace_service.process_validation.readers.base import (
    ReaderContext,
    SubjectSnapshot,
    ValidationIssue,
)
from workspace_service.process_validation.readers.sheet_metal import SheetMetalEvidenceReader


def subject(role, content, fmt):
    return SubjectSnapshot(
        SubjectBinding(
            id=role,
            role=role,
            result_id=f"run:sheet:{role}",
            producer=ProducerIdentity(
                run_id="run", step_id="sheet", attempt=1, output_port=role
            ),
            kind="file",
            locator=f"{role}.{fmt}",
            format=fmt,
            encoding="raw-bytes",
            sha256=hashlib.sha256(content).hexdigest(),
        ),
        content,
    )


def check(operation, *, parameters=None, unit=None, minimum=None):
    return CheckDefinition(
        id="sheet-check",
        requirement_ids=("REQ",),
        subject_role="subject",
        reader="sheet-metal-evidence",
        selector="sheet/check",
        constraint=Constraint(
            operator="range" if unit else "equals",
            minimum=minimum,
            expected=None if unit else True,
        ),
        unit=unit,
        evidence_method="independent_measurement",
        parameters={"operation": operation, **(parameters or {})},
    )


def context(*related):
    return replace(
        ReaderContext.create(ResourceBudget(), "sheet-test"),
        related_snapshots=tuple(related),
    )


def dxf(*, units="4", entity="LWPOLYLINE"):
    return (
        "0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n"
        + units
        + "\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n0\n"
        + entity
        + "\n90\n2\n10\n0\n20\n0\n10\n10\n20\n0\n0\nENDSEC\n0\nEOF\n"
    ).encode()


def test_native_design_check_requires_evidenced_pass_and_source_id():
    report = {
        "verdict": "pass",
        "checks": [
            {
                "requirement": "SHEET01-NATIVE thickness and material",
                "expected": "1.5 mm and selected label",
                "observed": "1.5 mm and selected label",
                "status": "pass",
                "evidence": [1, 2],
            }
        ],
        "corrections": [],
    }
    result = SheetMetalEvidenceReader().measure(
        subject("native_check", json.dumps(report).encode(), "json"),
        check(
            "design_check",
            parameters={"required_requirement_ids": ["SHEET01-NATIVE"]},
        ),
        context(),
    )
    assert result.value is True
    report["checks"][0]["observed"] = "unknown"
    with pytest.raises(ValidationIssue) as captured:
        SheetMetalEvidenceReader().measure(
            subject("native_check", json.dumps(report).encode(), "json"),
            check(
                "design_check",
                parameters={"required_requirement_ids": ["SHEET01-NATIVE"]},
            ),
            context(),
        )
    assert captured.value.code == "sheet_metal.native_check_schema"


def test_dxf_requires_mm_flat_geometry_and_rejects_embedded_substitute():
    reader = SheetMetalEvidenceReader()
    result = reader.measure(
        subject("flat", dxf(), "dxf"),
        check("dxf_contract", unit="1", minimum=1),
        context(),
    )
    assert result.value == 1
    with pytest.raises(ValidationIssue) as captured:
        reader.measure(
            subject("flat", dxf(entity="IMAGE"), "dxf"),
            check("dxf_contract", unit="1", minimum=1),
            context(),
        )
    assert captured.value.code == "sheet_metal.dxf_substitute"


def test_final_manifest_binds_exact_native_and_export_bytes():
    native = subject("part_native", b"native psm", "psm")
    folded = subject("part_step", b"folded step", "step")
    files = []
    for path, item in (("output/part.psm", native), ("output/part.step", folded)):
        files.append(
            {
                "path": path,
                "role": item.subject.role,
                "bytes": len(item.content),
                "sha256": item.subject.sha256,
            }
        )
    manifest = {
        "operation": "collect_artifact_manifest",
        "content_validation": "not_measured",
        "executing_source_sha256": "f" * 64,
        "files": files,
    }
    result = SheetMetalEvidenceReader().measure(
        subject("manifest", json.dumps(manifest).encode(), "json"),
        check(
            "manifest_binding",
            parameters={
                "related_roles": ["part_native", "part_step"],
                "expected_basenames": {
                    "part_native": "part.psm",
                    "part_step": "part.step",
                },
            },
            unit="1",
            minimum=2,
        ),
        context(native, folded),
    )
    assert result.value == 2


def test_supplier_receipt_must_be_local_simulation_for_exact_case():
    receipt = {
        "schema_version": 1,
        "integration_test": True,
        "simulated_handoff": True,
        "run_id": "run",
        "step_id": "preview",
        "checkpoint_id": "checkpoint",
        "subject_digest": "a" * 64,
        "action_id": "action",
        "campaign_id": "081-engineering-datasets-v1",
        "dataset_id": "sheet-metal-supplier-handoff-01",
        "integration_policy_digest": "b" * 64,
        "destination": {
            "kind": "integration_test",
            "id": "test://081-engineering-datasets-v1/supplier/sheet-metal-supplier-handoff-01",
        },
        "action_kind": "supplier_upload_preview",
        "artifact_digests": ["c" * 64],
        "network_dispatch": False,
    }
    parameters = {
        "action_kind": "supplier_upload_preview",
        "scenario_id": "sheet-metal-supplier-handoff-01",
        "destination": "test://081-engineering-datasets-v1/supplier/sheet-metal-supplier-handoff-01",
    }
    result = SheetMetalEvidenceReader().measure(
        subject("receipt", json.dumps(receipt).encode(), "json"),
        check("simulated_handoff", parameters=parameters),
        context(),
    )
    assert result.value is True
    receipt["network_dispatch"] = True
    with pytest.raises(ValidationIssue) as captured:
        SheetMetalEvidenceReader().measure(
            subject("receipt", json.dumps(receipt).encode(), "json"),
            check("simulated_handoff", parameters=parameters),
            context(),
        )
    assert captured.value.code == "sheet_metal.handoff_contract"
