"""Independent controls for printable mesh and slicer evidence inspection."""

from __future__ import annotations

import hashlib
import io
import json
import struct
from zipfile import ZIP_DEFLATED, ZipFile

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
from workspace_service.process_validation.readers.printing import PrintingArtifactReader


def subject(role, content, fmt):
    return SubjectSnapshot(
        SubjectBinding(
            id=role,
            role=role,
            result_id=f"run:print:{role}",
            producer=ProducerIdentity(
                run_id="run", step_id="print", attempt=1, output_port=role
            ),
            kind="file",
            locator=f"{role}.{fmt}",
            format=fmt,
            encoding="raw-bytes",
            sha256=hashlib.sha256(content).hexdigest(),
        ),
        content,
    )


def check(operation, *, selector="printing/check", parameters=None, unit=None):
    return CheckDefinition(
        id="printing-check",
        requirement_ids=("REQ",),
        subject_role="subject",
        reader="printing",
        selector=selector,
        constraint=Constraint(operator="equals", expected=True),
        unit=unit,
        evidence_method="independent_measurement",
        parameters={"operation": operation, **(parameters or {})},
    )


def binary_stl(vertices):
    triangles = [
        (vertices[0], vertices[2], vertices[1]),
        (vertices[0], vertices[1], vertices[3]),
        (vertices[1], vertices[2], vertices[3]),
        (vertices[2], vertices[0], vertices[3]),
    ]
    result = bytearray(b"bounded-test".ljust(80, b"\0"))
    result.extend(struct.pack("<I", len(triangles)))
    for triangle in triangles:
        values = (0.0, 0.0, 0.0) + tuple(
            coordinate for vertex in triangle for coordinate in vertex
        )
        result.extend(struct.pack("<12fH", *values, 0))
    return bytes(result)


def package():
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("3D/3dmodel.model", "model")
        archive.writestr("Metadata/plate_1.gcode", "G1 X1")
    return output.getvalue()


def test_binary_stl_envelope_and_integrity_are_measured():
    mesh = subject(
        "repaired_mesh",
        binary_stl(((1, 2, 3), (5, 2, 3), (1, 8, 3), (1, 2, 12))),
        "stl",
    )
    context = ReaderContext.create(ResourceBudget(), "print-test")
    dimension = check(
        "stl_dimension",
        selector="mesh/x_span_mm",
        parameters={"unit_convention": "mm"},
        unit="mm",
    )
    assert PrintingArtifactReader().measure(mesh, dimension, context).value == 4
    integrity = check(
        "mesh_integrity",
        selector="mesh/integrity",
        parameters={"unit_convention": "mm"},
    )
    assert PrintingArtifactReader().measure(mesh, integrity, context).value is True


def test_identical_source_and_repaired_mesh_are_rejected():
    content = binary_stl(((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)))
    repaired = subject("repaired_mesh", content, "stl")
    source = subject("source_mesh", content, "stl")
    context = ReaderContext.create(ResourceBudget(), "print-test")
    context = context.__class__(
        context.budget,
        context.deadline,
        context.cancelled,
        context.trace_id,
        (source,),
    )
    with pytest.raises(ValidationIssue) as captured:
        PrintingArtifactReader().measure(
            repaired,
            check(
                "mesh_lineage",
                selector="mesh/lineage",
                parameters={"related_roles": ["source_mesh"]},
            ),
            context,
        )
    assert captured.value.code == "printing.mesh_not_distinct"
    assert captured.value.action == "revise_output"


def test_slice_and_transfer_evidence_bind_exact_package_bytes():
    repaired = subject(
        "repaired_mesh",
        binary_stl(((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))),
        "stl",
    )
    package_snapshot = subject("slice_package", package(), "3mf")
    evidence = subject(
        "slice_evidence",
        json.dumps(
            {
                "operation": "actual_local_bambu_slice",
                "simulation": False,
                "exit_code": 0,
                "source_sha256": repaired.subject.sha256,
                "package_sha256": package_snapshot.subject.sha256,
            }
        ).encode(),
        "json",
    )
    context = ReaderContext.create(ResourceBudget(), "print-test")
    context = context.__class__(
        context.budget,
        context.deadline,
        context.cancelled,
        context.trace_id,
        (repaired, package_snapshot),
    )
    assert (
        PrintingArtifactReader()
        .measure(
            evidence,
            check(
                "slice_binding",
                selector="slice/hash_binding",
                parameters={"related_roles": ["repaired_mesh", "slice_package"]},
            ),
            context,
        )
        .value
        is True
    )
    broken = subject(
        "slice_evidence",
        evidence.content.replace(package_snapshot.subject.sha256.encode(), b"0" * 64),
        "json",
    )
    with pytest.raises(ValidationIssue) as captured:
        PrintingArtifactReader().measure(
            broken,
            check(
                "slice_binding",
                selector="slice/hash_binding",
                parameters={"related_roles": ["repaired_mesh", "slice_package"]},
            ),
            context,
        )
    assert captured.value.code == "printing.slice_binding"


def test_package_inventory_rejects_missing_required_member():
    snapshot = subject("slice_package", package(), "3mf")
    context = ReaderContext.create(ResourceBudget(), "print-test")
    with pytest.raises(ValidationIssue) as captured:
        PrintingArtifactReader().measure(
            snapshot,
            check(
                "package_inventory",
                selector="package/required_members",
                parameters={"required_members": ["Metadata/not-there.gcode"]},
                unit="1",
            ),
            context,
        )
    assert captured.value.code == "printing.package_missing"
