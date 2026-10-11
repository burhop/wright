"""Numerical fixture checks for the authored study; live slicer proof is separate."""

import importlib.util
from pathlib import Path
import struct

import pytest

ASSET = (
    Path(__file__).parents[1]
    / "examples/process-interfaces/printed-replacement-part/orientation-study.py"
)
spec = importlib.util.spec_from_file_location("orientation_study", ASSET)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def cube():
    points = [
        (0, 0, 0),
        (1, 0, 0),
        (1, 1, 0),
        (0, 1, 0),
        (0, 0, 1),
        (1, 0, 1),
        (1, 1, 1),
        (0, 1, 1),
    ]
    faces = [
        (0, 2, 1),
        (0, 3, 2),
        (4, 5, 6),
        (4, 6, 7),
        (0, 1, 5),
        (0, 5, 4),
        (1, 2, 6),
        (1, 6, 5),
        (2, 3, 7),
        (2, 7, 6),
        (3, 0, 4),
        (3, 4, 7),
    ]
    raw = bytearray(bytes(80) + struct.pack("<I", 12))
    for face in faces:
        triangle = tuple(points[i] for i in face)
        normal, _ = study.normal_area(triangle)
        raw.extend(struct.pack("<12fH", *normal, *(v for p in triangle for v in p), 0))
    return bytes(raw)


@pytest.mark.parametrize("socket_up", [False, True])
def test_rigid_transform_preserves_exported_area_volume_and_places_on_bed(socket_up):
    source = cube()
    raw, facts = study.transform(source, socket_up)
    assert len(study.read_triangles(raw)) == 12
    assert facts["source_sha256"] == study.sha(source)
    assert facts["signed_volume_mm3"] == pytest.approx(1)
    assert facts["surface_area_mm2"] == pytest.approx(6)
    assert facts["coplanar_bed_contact_mm2"] == pytest.approx(1)
    assert facts["bounds_mm"][0][2] == 0
    assert facts["volume_relative_error"] == 0
    assert facts["area_relative_error"] == 0
    assert facts["transform"][1][1] == (-1 if socket_up else 1)
    assert facts["transform"][2][3] == (1 if socket_up else 0)


@pytest.mark.parametrize("data", [b"bad", bytes(84), cube() + b"extra"])
def test_invalid_stl_is_not_an_orientation_candidate(data):
    with pytest.raises(ValueError):
        study.read_triangles(data)


def test_nonfinite_geometry_is_rejected():
    raw = bytearray(cube())
    struct.pack_into("<f", raw, 96, float("nan"))
    with pytest.raises(ValueError, match="Non-finite"):
        study.read_triangles(raw)


def test_socket_screen_uses_actual_support_midpoints_and_records_unknown_paths():
    view = {
        "classification_source": "gcode_feature_comments",
        "provenance": {"unclassified_features": ["unknown"]},
        "layers": [
            {
                "z": 2,
                "model": [[109, 109, 147, 147]],
                "support": [[127, 128, 129, 128], [120, 120, 121, 120]],
                "unclassified": [[128, 128, 129, 128]],
            },
            {
                "z": 12,
                "model": [[109, 109, 147, 147]],
                "support": [[127, 128, 129, 128]],
                "unclassified": [],
            },
        ],
    }
    down = study.path_facts(view, False)
    up = study.path_facts(view, True)
    assert down["model_path_center_xy_mm"] == [128, 128]
    assert down["support_midpoint_length_in_nominal_socket_mm"] == 2
    assert up["support_midpoint_length_in_nominal_socket_mm"] == 2
    assert down["path_length_mm"]["support"] == 5
    assert down["path_length_mm"]["unclassified"] == 1
    assert down["unclassified_features"] == ["unknown"]
    assert down["classification_known"] is True
    del view["classification_source"]
    assert study.path_facts(view, False)["classification_known"] is False


def test_empty_model_paths_remain_unavailable():
    with pytest.raises(ValueError, match="No actual model"):
        study.path_facts({"layers": [{"model": []}]}, False)


def test_preparation_retains_exact_source_and_does_not_overwrite(tmp_path):
    raw = cube()
    (tmp_path / "original.stl").write_bytes(raw)
    config = {
        "workspace_root": str(tmp_path),
        "source_mesh": "original.stl",
        "source_sha256": study.sha(raw),
        "output_root": "outputs",
    }
    study.prepare(config)
    assert (tmp_path / "outputs/source_mesh.stl").read_bytes() == raw
    assert (tmp_path / "original.stl").read_bytes() == raw
    assert (tmp_path / "outputs/socket_up/oriented.stl").is_file()
    with pytest.raises(FileExistsError):
        study.prepare(config)


@pytest.mark.parametrize("changed", ["original.stl", "outputs/source_mesh.stl"])
def test_comparison_rejects_changed_upstream_or_retained_copy(tmp_path, changed):
    raw = cube()
    (tmp_path / "original.stl").write_bytes(raw)
    config = {
        "workspace_root": str(tmp_path),
        "source_mesh": "original.stl",
        "source_sha256": study.sha(raw),
        "output_root": "outputs",
    }
    study.prepare(config)
    (tmp_path / changed).write_bytes(raw + b"changed")
    with pytest.raises(ValueError, match="exact upstream geometry"):
        study.compare(config)
