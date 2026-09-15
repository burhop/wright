"""Offline safety/format tests; these do not qualify a numerical solve."""
import importlib.util
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "scripts/engineering/calculix_recorded_fields.py"
SPEC = importlib.util.spec_from_file_location("recorded_fields", SOURCE)
operation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operation)


def test_output_expansion_preserves_all_physical_deck_bytes():
    physical = "*NODE\n1,0,0,0\n*ELEMENT, TYPE=C3D4\n1,1,2,3,4\n*MATERIAL, NAME=MAT\n*ELASTIC\n69000,.33\n*STEP\n*STATIC\n*BOUNDARY\nFIXED,1,3\n*CLOAD\nLOADED,3,-1\n"
    expanded = operation.expand_output_requests(physical + operation.ORIGINAL_TAIL)
    assert expanded[:len(physical)] == physical
    assert expanded[len(physical):] == operation.EXPANDED_TAIL
    with pytest.raises(ValueError):
        operation.expand_output_requests("*STEP\n" + physical + operation.ORIGINAL_TAIL)


@pytest.mark.parametrize("path", ["../outside", "C:/outside", "/outside", "a/../../outside", "a\\outside"])
def test_output_confinement_rejects_escaped_paths(tmp_path, path):
    with pytest.raises(ValueError):
        operation.confined(tmp_path.resolve(), path)


def test_dat_parser_retains_all_fields_not_only_extrema():
    text = """ displacements (vx,vy,vz) for set NALL
1 0 0 0
2 1E-3 2E-3 0
 forces (fx,fy,fz) for set NALL
1 0 0 1
2 0 0 -1
 stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz)
1 1 2 3 4 5 6 7
1 2 3 4 5 6 7 8
"""
    fields = operation.parse_dat(text)
    assert len(fields["displacement"]) == len(fields["force"]) == len(fields["stress"]) == 2
    assert fields["displacement"][1][1:3] == [.001, .002]


def test_mesh_node_set_parser_preserves_union_and_generate():
    nodes, sets = operation.mesh_nodes_sets("*NODE\n1,0,0,0\n2,1,0,0\n3,2,0,0\n*NSET,NSET=FIXED,GENERATE\n1,3,1\n*NSET,NSET=FIXED\n2,3\n")
    assert nodes[2] == (1., 0., 0.)
    assert sets["FIXED"] == {1, 2, 3}
