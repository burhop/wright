"""Final-byte measurements catch defects hidden by nominal CAD dimensions."""
import importlib.util
import math
from pathlib import Path
import struct

import pytest

spec = importlib.util.spec_from_file_location(
    "handle_repair", Path(__file__).resolve().parents[1] / "scripts/engineering_dataset_mesh_repair.py"
)
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)


def mesh(path, central_z):
    triangles = []
    for center in (0.0, 96.0):
        for index in range(64):
            a, b = [2 * math.pi * i / 64 for i in (index, index + 1)]
            p, q = [(center + 2.25 * math.cos(t), 2.25 * math.sin(t)) for t in (a, b)]
            triangles.extend([
                [(*p, 0), (*q, 0), (*q, 5)],
                [(*p, 0), (*q, 5), (*p, 5)],
            ])
    # No vertex at X=15.5: clipping must see the intersection, not just vertices
    # that happen to fall inside the central interval.
    triangles.append([(15, 0, central_z - 1), (16, 0, central_z + 1), (80.5, 1, central_z + 1)])
    data = b"\0" * 80 + struct.pack("<I", len(triangles))
    for triangle in triangles:
        data += struct.pack("<12fH", 0, 0, 0, *(v for p in triangle for v in p), 0)
    path.write_bytes(data)


@pytest.mark.parametrize("clearance, passes", [(24.8, False), (25.0, True)])
def test_exact_triangle_clipping_and_independent_bore_sections(tmp_path, clearance, passes):
    path = tmp_path / "measured.stl"
    mesh(path, clearance)
    result = repair.measure_handle_features(path)
    # The longer crossing edge has a lower intersection than the nearby edge.
    assert result["minimum_clearance_mm"] < clearance
    assert result["clearance_pass"] is False
    # Set a horizontal underside at exactly the requirement to test inclusive pass.
    if passes:
        data = bytearray(path.read_bytes())
        for vertex in range(3):
            struct.pack_into("<f", data, len(data) - 50 + 12 + 12 * vertex + 8, 25.0)
        path.write_bytes(data)
        result = repair.measure_handle_features(path)
        assert result["minimum_clearance_mm"] == 25.0
        assert result["clearance_pass"] is True
    for section in result["bore_sections"]:
        assert section["center_spacing_mm"] == 96
        for hole in section["holes"]:
            assert hole["diameter_xy_mm"] == [4.5, 4.5]
            assert hole["minimum_centered_clearance_diameter_mm"] == pytest.approx(4.5 * math.cos(math.pi / 64), abs=1e-5)


def test_rejects_truncated_mesh(tmp_path):
    path = tmp_path / "truncated.stl"
    path.write_bytes(b"\0" * 80 + struct.pack("<I", 1))
    with pytest.raises(ValueError, match="bounded binary STL"):
        repair.measure_handle_features(path)
