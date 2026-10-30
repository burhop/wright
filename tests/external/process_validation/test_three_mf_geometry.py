"""Passive geometry controls including exact retained native Orca output."""

from dataclasses import replace
import io
from pathlib import Path
import struct
from zipfile import ZipFile

import pytest

from workspace_service.process_validation.readers import three_mf_geometry as reader
from workspace_service.process_validation.readers.base import (
    ReaderContext,
    ValidationIssue,
)
from workspace_service.process_validation.readers.printing import PrintingArtifactReader
from core.process_validation import ResourceBudget
from test_printing import check, subject

FIXTURE = (
    Path(__file__).parents[2] / "datasets/process-validation/orca-2.4.2-standard3mf"
)
ROTATION = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]


@pytest.fixture
def inputs():
    points = [
        tuple(map(float, line.split()[1:]))
        for line in (FIXTURE / "source-model.stl").read_text().splitlines()
        if line.startswith("vertex ")
    ]
    binary = bytes(80) + struct.pack("<I", len(points) // 3)
    for i in range(0, len(points), 3):
        binary += struct.pack(
            "<12fH", 0, 0, 0, *(v for p in points[i : i + 3] for v in p), 0
        )
    return (
        binary,
        (FIXTURE / "source-model-side.3mf").read_bytes(),
        (FIXTURE / "side-native.gcode.3mf").read_bytes(),
    )


def altered(package, mutate):
    members = reader.archive_members(package)
    mutate(members)
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
    return output.getvalue()


def test_retained_native_mesh_recenter_and_build_transform_match_original_frame(inputs):
    result = reader.correspondence(*inputs, ROTATION, [128, 128])
    assert result["triangle_count"] == 12
    assert result["source_model_bounds_mm"] == [[0, 0, 0], [10, 10, 5]]
    assert result["prepared_model_error_mm"] == 0
    assert result["native_world_error_mm"] < 1e-12
    assert result["inverse_model_error_mm"] < 1e-12


@pytest.mark.parametrize(
    "fault",
    [
        "unit",
        "matrix",
        "winding",
        "coordinate",
        "multiple_build",
        "cycle",
        "path",
        "entities_utf16",
        "nonfinite",
    ],
)
def test_prepared_package_tampering_cannot_pass(inputs, fault):
    source, prepared, native = inputs

    def mutate(members):
        name = "3D/3dmodel.model"
        raw = members[name].decode()
        if fault == "unit":
            raw = raw.replace("millimeter", "inch")
        elif fault == "matrix":
            raw = raw.replace("123 130.5 0", "124 130.5 0")
        elif fault == "winding":
            raw = raw.replace('v1="0" v2="1" v3="2"', 'v1="0" v2="2" v3="1"')
        elif fault == "coordinate":
            raw = raw.replace('x="10"', 'x="11"')
        elif fault == "multiple_build":
            raw = raw.replace("</build>", '<item objectid="1"/></build>')
        elif fault == "cycle":
            begin, end = raw.index("<mesh>"), raw.index("</mesh>") + len("</mesh>")
            raw = (
                raw[:begin]
                + '<components><component objectid="1"/></components>'
                + raw[end:]
            )
        elif fault == "path":
            members["../outside"] = b"x"
        elif fault == "entities_utf16":
            members[name] = (
                '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE model [<!ENTITY x "1">]>'
                + raw[raw.index("<model") :]
            ).encode("utf-16")
            return
        else:
            raw = raw.replace('x="10"', 'x="1e309"')
        members[name] = raw.encode()

    with pytest.raises((ValueError, KeyError)):
        reader.correspondence(
            source, altered(prepared, mutate), native, ROTATION, [128, 128]
        )


def test_finite_matrices_cannot_overflow_into_false_match():
    matrix = reader.identity()
    matrix[0][0] = 1e308
    with pytest.raises(ValueError, match="Nonfinite"):
        reader.multiply(matrix, matrix)
    with pytest.raises(ValueError, match="Nonfinite"):
        reader.transform([(10, 0, 0)], matrix)
    with pytest.raises(ValueError, match="finite"):
        reader.match_error([((0, 0, 0),) * 3], [((float("nan"), 0, 0),) * 3], 1e-6)


def test_tiny_reversed_triangle_cannot_hide_inside_coordinate_tolerance():
    triangle = ((0.0, 0.0, 0.0), (0.00001, 0.0, 0.0), (0.0, 0.00001, 0.0))
    assert reader.match_error([triangle], [triangle[1:] + triangle[:1]], 1e-4) <= 1e-4
    with pytest.raises(ValueError, match="winding"):
        reader.match_error([triangle], [(triangle[0], triangle[2], triangle[1])], 1e-4)


def test_backend_measures_exact_related_artifacts_and_preserves_budget_failure(inputs):
    source, prepared, native = inputs
    context = replace(
        ReaderContext.create(ResourceBudget(), "fixture"),
        related_snapshots=(
            subject("repaired_mesh", source, "stl"),
            subject("prepared_3mf", prepared, "3mf"),
        ),
    )
    definition = check(
        "prepared_mesh_correspondence",
        parameters={"rotation": ROTATION, "build_center_xy_mm": [128, 128]},
    )
    snapshot = subject("slice_package", native, "3mf")
    result = PrintingArtifactReader().measure(snapshot, definition, context)
    assert result.value is True
    with pytest.raises(ValidationIssue) as caught:
        PrintingArtifactReader().measure(
            snapshot,
            definition,
            replace(context, budget=ResourceBudget(max_entities=1)),
        )
    assert caught.value.code == "reader.entity_limit"
    changed = bytearray(source)
    changed[96:100] = struct.pack("<f", 99)
    with pytest.raises(ValidationIssue, match="preserve"):
        PrintingArtifactReader().measure(
            snapshot,
            definition,
            replace(
                context,
                related_snapshots=(
                    subject("repaired_mesh", bytes(changed), "stl"),
                    subject("prepared_3mf", prepared, "3mf"),
                ),
            ),
        )


def test_actual_engine_header_is_literal_package_evidence(inputs):
    context = ReaderContext.create(ResourceBudget(), "fixture")
    definition = check(
        "package_text_prefix",
        parameters={
            "entry": "Metadata/plate_1.gcode",
            "prefix": "; generated by OrcaSlicer 2.4.2 on ",
        },
    )
    assert (
        PrintingArtifactReader()
        .measure(subject("slice_package", inputs[2], "3mf"), definition, context)
        .value
        is True
    )
    wrong = definition.model_copy(
        update={
            "parameters": {
                **definition.parameters,
                "prefix": "; generated by BambuStudio",
            }
        }
    )
    assert (
        PrintingArtifactReader()
        .measure(subject("slice_package", inputs[2], "3mf"), wrong, context)
        .value
        is False
    )


def test_duplicate_archive_and_bounded_geometry_are_rejected(inputs, monkeypatch):
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("3D/3dmodel.model", b"one")
        with pytest.warns(UserWarning, match="Duplicate"):
            archive.writestr("3D/3dmodel.model", b"two")
    with pytest.raises(ValueError, match="duplicate"):
        reader.read_package(output.getvalue())
    monkeypatch.setattr(reader, "MAX_TRIANGLES", 4)
    with pytest.raises(ValueError, match="count/size"):
        reader.correspondence(*inputs, ROTATION, [128, 128])


@pytest.mark.parametrize(
    "rotation,center,tolerance",
    [
        ([[-1, 0, 0], [0, 1, 0], [0, 0, 1]], [128, 128], 1e-4),
        ([[2, 0, 0], [0, 1, 0], [0, 0, 1]], [128, 128], 1e-4),
        (ROTATION, [float("nan"), 128], 1e-4),
        (ROTATION, [128, 128], 1e-3),
    ],
)
def test_explicit_rigid_frame_and_numerical_bound_are_required(
    inputs, rotation, center, tolerance
):
    with pytest.raises(ValueError):
        reader.correspondence(*inputs, rotation, center, tolerance)


def test_slice_binding_requires_exact_prepared_digest_when_declared(inputs):
    import json

    source, prepared, package = inputs
    related = (
        subject("repaired_mesh", source, "stl"),
        subject("prepared_3mf", prepared, "3mf"),
        subject("slice_package", package, "3mf"),
    )
    context = replace(
        ReaderContext.create(ResourceBudget(), "fixture"), related_snapshots=related
    )
    record = dict(
        operation="actual_local_orca_slice",
        simulation=False,
        exit_code=0,
        source_sha256=related[0].subject.sha256,
        prepared_sha256=related[1].subject.sha256,
        package_sha256=related[2].subject.sha256,
    )
    definition = check(
        "slice_binding",
        parameters={
            "expected_operation": "actual_local_orca_slice",
            "prepared_role": "prepared_3mf",
        },
    )
    assert (
        PrintingArtifactReader()
        .measure(
            subject("slice_evidence", json.dumps(record).encode(), "json"),
            definition,
            context,
        )
        .value
        is True
    )
    record["prepared_sha256"] = "0" * 64
    with pytest.raises(ValidationIssue):
        PrintingArtifactReader().measure(
            subject("slice_evidence", json.dumps(record).encode(), "json"),
            definition,
            context,
        )


def shifted_triangle(x=0.0, y=0.0, z=0.0):
    return ((x, y, z), (x + 1.0, y, z), (x, y + 1.0, z))


def test_native_handle_serialization_crossing_sort_bin_preserves_winding():
    # Exact two-face reproduction from retained source7/native package: the old
    # rounded global sort paired the two unrelated faces and rejected winding.
    expected = [
        (
            (82.41475200653076, 127.00471258163452, 5.0),
            (82.72118949890137, 127.21515941619873, 5.005160331726074),
            (82.40149927139282, 127.18155860900879, 5.005160331726074),
        ),
        (
            (82.7725019454956, 129.8538589477539, 16.66053581237793),
            (82.4011857509613, 129.76860094070435, 16.679807662963867),
            (82.53253722190857, 129.8766622543335, 16.0),
        ),
    ]
    actual = [
        (
            (82.41475299999999, 127.004711582, 5.0),
            (82.72119140000001, 127.21515841600001, 5.0051603),
            (82.4015007, 127.18155760900001, 5.0051603),
        ),
        (
            (82.7725029, 129.85385795, 16.660535812),
            (82.4011841, 129.76859994, 16.679807663),
            (82.5325356, 129.87666125, 16.0),
        ),
    ]
    assert reader.match_error(expected, actual[::-1], 1e-4) == pytest.approx(
        1.9010986420653353e-6
    )


@pytest.mark.parametrize("copies", [1, 2, 1000])
def test_ambiguous_candidates_reassign_earlier_match_with_duplicate_capacity(copies):
    first, second = shifted_triangle(), shifted_triangle(y=0.00015)
    flexible = shifted_triangle(y=0.00006)
    constrained = shifted_triangle(x=0.00001, y=-0.00008)
    # Flexible sorts first and initially takes first's capacity. Constrained can
    # only use first, so a complete match must move flexible to second.
    assert (
        reader.match_error(
            [first] * copies + [second], [flexible] + [constrained] * copies, 1e-4
        )
        <= 1e-4
    )


@pytest.mark.parametrize("fault", ["duplicate_multiplicity", "hall_deficit", "winding"])
def test_triangle_bijection_and_orientation_cannot_be_waived(fault):
    first, second = shifted_triangle(), shifted_triangle(x=10.0)
    if fault == "duplicate_multiplicity":
        expected, actual = [first, first, second], [first, second, second]
    elif fault == "hall_deficit":
        expected = [first, shifted_triangle(y=0.00015)]
        actual = [shifted_triangle(y=-0.00008)] * 2
    else:
        expected = [first, second]
        actual = [first, tuple(reversed(second))]
    with pytest.raises(ValueError):
        reader.match_error(expected, actual, 1e-4)


@pytest.mark.parametrize("direction", [-1, 1])
def test_actual_tolerance_boundary_not_spatial_bin_controls_acceptance(direction):
    import math

    expected = [shifted_triangle(x=-0.00019999)]
    on_boundary = [shifted_triangle(x=-0.00019999, z=direction * 1e-4)]
    outside = [
        shifted_triangle(x=-0.00019999, z=direction * math.nextafter(1e-4, math.inf))
    ]
    assert reader.match_error(expected, on_boundary, 1e-4) == 1e-4
    with pytest.raises(ValueError):
        reader.match_error(expected, outside, 1e-4)
    with pytest.raises(ValueError):
        reader.match_error(expected, on_boundary, 0)


def test_face_order_cyclic_start_and_duplicate_counts_are_preserved():
    triangles = [shifted_triangle(), shifted_triangle(x=2), shifted_triangle(y=3)]
    expected = triangles + [triangles[0]]
    actual = [t[1:] + t[:1] for t in reversed(expected)]
    assert reader.match_error(expected, actual, 0) == 0
    assert reader.match_error(expected, actual, 1e-4) == 0


@pytest.mark.parametrize("limit", ["MAX_MATCH_CANDIDATES", "MAX_MATCH_WORK"])
def test_pathological_matching_work_fails_closed(monkeypatch, limit):
    monkeypatch.setattr(reader, limit, 0)
    with pytest.raises(ValueError, match="bound"):
        reader.match_error([shifted_triangle()], [shifted_triangle(z=1e-6)], 1e-4)


def test_matching_preserves_checkpoint_resource_failure():
    def exhausted(**_):
        raise ValidationIssue("reader.entity_limit", "fixture resource limit")

    with pytest.raises(ValidationIssue) as caught:
        reader.match_error(
            [shifted_triangle()], [shifted_triangle(z=1e-6)], 1e-4, exhausted
        )
    assert caught.value.code == "reader.entity_limit"
