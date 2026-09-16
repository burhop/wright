"""The Pi CFD compiler accepts bounded CAD provenance without code injection."""

import hashlib
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "pi_cfd_operations", ROOT / "scripts/pi_cfd_operations.py"
)
operations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operations)


def _contract(root: Path) -> dict:
    fluid = root / "air.step"
    solid = root / "shell.step"
    fluid.write_bytes(b"fluid")
    solid.write_bytes(b"solid")

    def region(name: str, kind: str, path: Path) -> dict:
        return {
            "name": name,
            "kind": kind,
            "step": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "material": {
                "rho": 1.18 if kind == "fluid" else 1270,
                "cp": 1005 if kind == "fluid" else 1200,
                "kappa": 0.026 if kind == "fluid" else 0.2,
            },
            "heat_w": 0,
        }

    return {
        "schema_version": 2,
        "units": "mm",
        "ambient_k": 303.15,
        "gravity_m_s2": [0, 0, -9.81],
        "mesh_size_mm": 2,
        "numerics": {"mode": "steady", "iterations": 300, "write_interval": 50},
        "mesh_grading": {
            "far_size_mm": 10,
            "distance_min_mm": 2,
            "distance_max_mm": 25,
        },
        "regions": [region("air", "fluid", fluid), region("shell", "solid", solid)],
        "boundaries": [],
        "assumptions": ["test"],
        "evidence": {
            "fluid_step_sha256": hashlib.sha256(fluid.read_bytes()).hexdigest(),
            "fluid_domain_observed_bounds_mm": {
                "x_min": 0,
                "x_max": 10,
                "y_min": 0,
                "y_max": 10,
                "z_min": 0,
                "z_max": 10,
            },
        },
    }


def test_bounded_cad_evidence_is_accepted(tmp_path: Path):
    contract = _contract(tmp_path)
    assert len(operations.validate(contract, tmp_path)) == 2


def test_unrecognized_evidence_field_is_rejected(tmp_path: Path):
    contract = _contract(tmp_path)
    contract["evidence"]["arbitrary_dictionary"] = {"code": "not accepted"}
    with pytest.raises(ValueError, match="Unsupported CAD evidence field"):
        operations.validate(contract, tmp_path)


def test_cad_evidence_bounds_list_is_rejected(tmp_path: Path):
    contract = _contract(tmp_path)
    contract["evidence"]["fluid_domain_observed_bounds_mm"] = [0, 0, 0, 10, 10, 10]
    with pytest.raises(ValueError, match="CAD evidence domain bounds are invalid"):
        operations.validate(contract, tmp_path)
