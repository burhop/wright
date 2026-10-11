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
from workspace_service.process_validation.readers.cfd import (
    CfdEvidenceReader,
    _convergence_measurement,
    _heat_balance_measurement,
)


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


def steady_log(initial_residual, final_residual, temperatures):
    rows = []
    for iteration, temperature in enumerate(temperatures, start=1):
        rows.extend(
            [
                f"Time = {iteration}s",
                "",
                "DILUPBiCGStab:  Solving for h, Initial residual = "
                f"{initial_residual}, Final residual = {final_residual}, No Iterations 1",
                f"Min/max T:298.15 {temperature}",
            ]
        )
    return ("\n".join(rows) + "\n\nEnd\n").encode()


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


def _convergence_subjects(initial_residual, final_residual, temperatures):
    logs = {
        name: steady_log(initial_residual, final_residual, temperatures)
        for name in ("variant-a/solver.log", "variant-b/solver.log")
    }
    variants = []
    for variant in ("variant-a", "variant-b"):
        log = logs[f"{variant}/solver.log"]
        evidence = {
            **_convergence_measurement(log, 5),
            "solver_log_sha256": hashlib.sha256(log).hexdigest(),
        }
        variants.append(
            {
                "variant": variant,
                "numerical_profile": {"mode": "steady", "end": 5},
                "steady_state_convergence_claimed": evidence["passed"],
                "convergence_evidence": evidence,
            }
        )
    comparison = subject(
        "comparison", json.dumps({"variants": variants}).encode(), "json"
    )
    field_archive = subject("field_archive", archive(logs), "zip")
    context = ReaderContext.create(ResourceBudget(), "cfd-test")
    return comparison, context.__class__(
        context.budget,
        context.deadline,
        context.cancelled,
        context.trace_id,
        (field_archive,),
    )


def test_convergence_is_independently_recomputed_from_archived_logs():
    comparison, context = _convergence_subjects(
        1e-5, 1e-7, [300.0, 300.0001, 300.0002, 300.0003, 300.0004]
    )
    measurement = CfdEvidenceReader().measure(
        comparison, check("convergence"), context
    )
    assert measurement.value is True


def test_unsettled_convergence_reports_measured_correction_values():
    comparison, context = _convergence_subjects(
        0.014, 2e-5, [300.0, 300.01, 300.02, 300.03, 300.04]
    )
    with pytest.raises(ValidationIssue) as captured:
        CfdEvidenceReader().measure(comparison, check("convergence"), context)
    assert captured.value.code == "cfd.convergence_failed"
    assert captured.value.category == "output_defect"
    assert "initial residual 0.014" in str(captured.value)


def test_heat_balance_is_integrated_from_archived_per_face_fields():
    header = (
        "patch,role,area_m2,normal_velocity_m_s,density_kg_m3,temperature_k,"
        "temperature_gradient_normal_k_m,cp_j_kg_k,conductivity_w_m_k,ambient_k\n"
    )
    row = "outlet,outlet,1,0.01,1,301,0,1000,0.02,300\n"
    content = (header + row).encode()
    digest = hashlib.sha256(content).hexdigest()
    variants = [
        {
            "variant": variant,
            "heat_balance_file": "boundary-energy.csv",
            "heat_balance_file_sha256": digest,
            "input_heat_w": 10.0,
            "net_outward_heat_w": 10.0,
            "heat_balance_relative": 0.0,
        }
        for variant in ("variant-a", "variant-b")
    ]
    comparison = subject(
        "comparison", json.dumps({"variants": variants}).encode(), "json"
    )
    fields = subject(
        "field_archive",
        archive(
            {
                f"{variant}/boundary-energy.csv": content
                for variant in ("variant-a", "variant-b")
            }
        ),
        "zip",
    )
    context = ReaderContext.create(ResourceBudget(), "cfd-test")
    context = context.__class__(
        context.budget,
        context.deadline,
        context.cancelled,
        context.trace_id,
        (fields,),
    )
    measurement = CfdEvidenceReader().measure(
        comparison, check("heat_balance", unit="1"), context
    )
    assert measurement.value == pytest.approx(0.0)


@pytest.mark.parametrize("cancelled,expected", [(False, "reader.entity_limit"), (True, "validation.cancelled")])
def test_heat_balance_preserves_resource_and_cancellation_issues(cancelled, expected):
    content = b"patch,role,area_m2,normal_velocity_m_s,density_kg_m3,temperature_k,temperature_gradient_normal_k_m,cp_j_kg_k,conductivity_w_m_k,ambient_k\nsolid/feet,wall,1,0,1000,301,-1,1000,1,300\n"
    context = ReaderContext.create(ResourceBudget(max_entities=1), "budget-test")
    if cancelled:
        context.cancelled.set()
    with pytest.raises(ValidationIssue) as captured:
        _heat_balance_measurement(content, context)
    assert captured.value.code == expected


def test_heat_balance_rejects_summary_that_disagrees_with_face_fields():
    header = (
        "patch,role,area_m2,normal_velocity_m_s,density_kg_m3,temperature_k,"
        "temperature_gradient_normal_k_m,cp_j_kg_k,conductivity_w_m_k,ambient_k\n"
    )
    content = (header + "wall,wall,1,0,1,300,-50,1000,0.02,300\n").encode()
    digest = hashlib.sha256(content).hexdigest()
    variants = [
        {
            "variant": variant,
            "heat_balance_file": "boundary-energy.csv",
            "heat_balance_file_sha256": digest,
            "input_heat_w": 1.0,
            "net_outward_heat_w": 0.0,
            "heat_balance_relative": 1.0,
        }
        for variant in ("variant-a", "variant-b")
    ]
    comparison = subject(
        "comparison", json.dumps({"variants": variants}).encode(), "json"
    )
    fields = subject(
        "field_archive",
        archive(
            {
                f"{variant}/boundary-energy.csv": content
                for variant in ("variant-a", "variant-b")
            }
        ),
        "zip",
    )
    context = ReaderContext.create(ResourceBudget(), "cfd-test")
    context = context.__class__(
        context.budget,
        context.deadline,
        context.cancelled,
        context.trace_id,
        (fields,),
    )
    with pytest.raises(ValidationIssue) as captured:
        CfdEvidenceReader().measure(
            comparison, check("heat_balance", unit="1"), context
        )
    assert captured.value.code == "cfd.heat_balance_mismatch"
