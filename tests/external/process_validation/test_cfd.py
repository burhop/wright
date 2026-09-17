"""Independent controls for bounded CFD contracts and field archives."""

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
from workspace_service.process_validation.readers.cfd import CfdEvidenceReader


def subject(role, content, fmt):
    return SubjectSnapshot(
        SubjectBinding(
            id=role,
            role=role,
            result_id=f"run:cfd:{role}",
            producer=ProducerIdentity(
                run_id="run", step_id="cfd", attempt=1, output_port=role
            ),
            kind="file",
            locator=f"{role}.{fmt}",
            format=fmt,
            encoding="raw-bytes",
            sha256=hashlib.sha256(content).hexdigest(),
        ),
        content,
    )


def check(operation, *, parameters=None, unit=None):
    return CheckDefinition(
        id="cfd-check",
        requirement_ids=("REQ",),
        subject_role="subject",
        reader="cfd-evidence",
        selector="cfd/check",
        constraint=Constraint(
            operator="range" if unit else "equals",
            maximum=100 if unit else None,
            expected=None if unit else True,
        ),
        unit=unit,
        evidence_method="independent_measurement",
        parameters={"operation": operation, **(parameters or {})},
    )


def vtk_temperature(values):
    header = (
        b"# vtk DataFile Version 2.0\ntest\nBINARY\n"
        b"DATASET UNSTRUCTURED_GRID\nPOINTS 1 float\n"
        + struct.pack(">3f", 0, 0, 0)
        + b"\nPOINT_DATA  1\nFIELD attributes 1\nT 1 "
        + str(len(values)).encode()
        + b" float\n"
    )
    return header + b"".join(struct.pack(">f", value) for value in values) + b"\n"


def archive(members):
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as output:
        for name, content in members.items():
            output.writestr(name, content)
    return stream.getvalue()


def test_binary_vtk_temperature_is_read_independently():
    content = archive({"variant-a/source.vtk": vtk_temperature([300, 310, 305])})
    measurement = CfdEvidenceReader().measure(
        subject("field_archive", content, "zip"),
        check(
            "maximum_temperature",
            parameters={"member": "variant-a/source.vtk"},
            unit="degC",
        ),
        ReaderContext.create(ResourceBudget(), "cfd-test"),
    )
    assert measurement.value == pytest.approx(36.85)


def test_contract_binds_load_material_and_exact_geometry():
    geometry = subject("source_primary_a", b"STEP", "step")
    contract = {
        "ambient_k": 300.0,
        "gravity_m_s2": [0, 0, -9.81],
        "regions": [
            {
                "name": "source",
                "heat_w": 6,
                "sha256": geometry.subject.sha256,
                "material": {"kappa": 120},
            }
        ],
    }
    primary = subject("contract_a", json.dumps(contract).encode(), "json")
    context = ReaderContext.create(ResourceBudget(), "cfd-test")
    context = context.__class__(
        context.budget,
        context.deadline,
        context.cancelled,
        context.trace_id,
        (geometry,),
    )
    result = CfdEvidenceReader().measure(
        primary,
        check(
            "contract",
            parameters={
                "expected": {
                    "ambient_k": 300.0,
                    "gravity_m_s2": [0, 0, -9.81],
                    "regions": {"source": {"heat_w": 6, "kappa": 120}},
                },
                "region_roles": {"source": "source_primary_a"},
            },
        ),
        context,
    )
    assert result.value is True


def test_missing_convergence_and_heat_balance_are_typed_missing_evidence():
    comparison = subject(
        "comparison",
        json.dumps(
            {
                "variants": [
                    {"variant": "variant-a", "steady_state_convergence_claimed": False},
                    {"variant": "variant-b", "steady_state_convergence_claimed": False},
                ]
            }
        ).encode(),
        "json",
    )
    context = ReaderContext.create(ResourceBudget(), "cfd-test")
    for operation, code in (
        ("convergence", "cfd.convergence_unproven"),
        ("heat_balance", "cfd.heat_balance_missing"),
    ):
        with pytest.raises(ValidationIssue) as captured:
            CfdEvidenceReader().measure(comparison, check(operation, unit="1" if operation == "heat_balance" else None), context)
        assert captured.value.code == code
        assert captured.value.category == "missing_evidence"
