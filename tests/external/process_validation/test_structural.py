"""Independent controls for structural request, field and reaction evidence."""

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
from workspace_service.process_validation.readers.structural import StructuralEvidenceReader


def subject(role, content, fmt):
    return SubjectSnapshot(
        SubjectBinding(
            id=role,
            role=role,
            result_id=f"run:structural:{role}",
            producer=ProducerIdentity(
                run_id="run", step_id="structural", attempt=1, output_port=role
            ),
            kind="file",
            locator=f"{role}.{fmt}",
            format=fmt,
            encoding="raw-bytes",
            sha256=hashlib.sha256(content).hexdigest(),
        ),
        content,
    )


def check(operation, *, parameters=None, unit=None, maximum=None, minimum=None):
    return CheckDefinition(
        id="structural-check",
        requirement_ids=("REQ",),
        subject_role="subject",
        reader="structural-evidence",
        selector="structural/check",
        constraint=Constraint(
            operator="range" if unit else "equals",
            maximum=maximum,
            minimum=minimum,
            expected=None if unit else True,
        ),
        unit=unit,
        evidence_method="independent_measurement",
        parameters={"operation": operation, **(parameters or {})},
    )


def context(*related):
    return replace(
        ReaderContext.create(ResourceBudget(), "structural-test"),
        related_snapshots=tuple(related),
    )


def test_request_contract_binds_geometry_load_material_and_meshes():
    baseline = subject("baseline_step", b"baseline step", "step")
    revised = subject("revised_step", b"revised step", "step")
    runs = []
    for variant, geometry in (("baseline", baseline), ("revised", revised)):
        for mesh, size in (("coarse", 3), ("fine", 2)):
            runs.append(
                {
                    "variant": variant,
                    "mesh": mesh,
                    "arguments": {
                        "request_id": f"test-{variant}-{mesh}",
                        "step_path": f"/inputs/{variant}.step",
                        "expected_step_sha256": geometry.subject.sha256,
                        "mesh_size_mm": size,
                        "element_order": 2,
                        "material": {"e_mpa": 69000, "nu": 0.33},
                        "selections": [{"name": "FIXED"}, {"name": "LOADED"}],
                        "fixed": ["FIXED"],
                        "loads": [{"selection": "LOADED", "force_n": [0, 0, -100]}],
                    },
                }
            )
    primary = subject("fea_requests", json.dumps({"runs": runs}).encode(), "json")
    result = StructuralEvidenceReader().measure(
        primary,
        check(
            "request_contract",
            parameters={
                "force_n": [0, 0, -100],
                "related_roles": ["baseline_step", "revised_step"],
            },
        ),
        context(baseline, revised),
    )
    assert result.value is True


def test_fields_are_measured_and_refinement_is_independent():
    coarse = subject(
        "coarse",
        b"node_id,ux_mm,uy_mm,uz_mm\n1,0,0,0.10\n2,0,0,0.19\n",
        "csv",
    )
    fine = subject(
        "fine",
        b"node_id,ux_mm,uy_mm,uz_mm\n1,0,0,0.10\n2,0,0,0.195\n3,0,0,0.20\n",
        "csv",
    )
    reader = StructuralEvidenceReader()
    maximum = reader.measure(
        fine,
        check("displacement_maximum", unit="mm", maximum=0.5),
        context(),
    )
    refined = reader.measure(
        fine,
        check(
            "refinement",
            parameters={
                "field": "displacement",
                "coarse_role": "coarse",
                "related_roles": ["coarse"],
            },
            unit="1",
            maximum=0.05,
        ),
        context(coarse),
    )
    assert maximum.value == pytest.approx(0.2)
    assert refined.value == pytest.approx(0.05)


def test_reactions_balance_force_and_global_moment():
    reaction = subject(
        "reaction",
        json.dumps(
            {
                "reaction_force_n": [0, 0, 100],
                "reaction_moment_about_global_origin_nmm": [0, -7250, 0],
            }
        ).encode(),
        "json",
    )
    result = StructuralEvidenceReader().measure(
        reaction,
        check(
            "reaction_equilibrium",
            parameters={
                "force_n": [0, 0, -100],
                "load_centroid_mm": [72.5, 0, 60],
            },
            unit="1",
            maximum=0.01,
        ),
        context(),
    )
    assert result.value == pytest.approx(0)


def test_mass_is_recomputed_and_bound_to_both_step_revisions():
    baseline = subject("baseline_step", b"baseline step", "step")
    revised = subject("revised_step", b"revised step", "step")
    content = (
        "variant,volume_mm3,mass_g,step_sha256\n"
        f"baseline,100000,270,{baseline.subject.sha256}\n"
        f"revised,75000,202.5,{revised.subject.sha256}\n"
    ).encode()
    result = StructuralEvidenceReader().measure(
        subject("mass", content, "csv"),
        check(
            "mass_reduction",
            parameters={
                "density_kg_m3": 2700,
                "related_roles": ["baseline_step", "revised_step"],
            },
            unit="1",
            minimum=0.2,
        ),
        context(baseline, revised),
    )
    assert result.value == pytest.approx(0.25)


def test_receipt_rejects_a_field_whose_hash_does_not_match():
    geometry = subject("baseline_step", b"step", "step")
    displacement = subject(
        "baseline_coarse_displacement",
        b"node_id,ux_mm,uy_mm,uz_mm\n1,0,0,0\n",
        "csv",
    )
    receipt = {
        "status": "completed",
        "original_run_id": "r-00000000-0000-0000-0000-000000000000",
        "expected_step_sha256": geometry.subject.sha256,
        "physics_deck_changed": False,
        "expansion_kind": "explicit_separate_native_solve_output_requests_only",
        "nodal_displacement_rows": 1,
        "stress_integration_point_rows": 1,
        "files": [
            {
                "path": "native-field-expansion/displacement-field.csv",
                "sha256": "0" * 64,
                "bytes": len(displacement.content),
            }
        ],
    }
    with pytest.raises(ValidationIssue) as captured:
        StructuralEvidenceReader().measure(
            subject("receipt", json.dumps(receipt).encode(), "json"),
            check(
                "receipt_binding",
                parameters={
                    "geometry_role": "baseline_step",
                    "related_roles": ["baseline_step", "baseline_coarse_displacement"],
                    "expected_paths": {
                        "baseline_coarse_displacement": "native-field-expansion/displacement-field.csv"
                    },
                },
            ),
            context(geometry, displacement),
        )
    assert captured.value.code == "structural.receipt_file_mismatch"
