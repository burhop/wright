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


def _steady_log(initial_residual: float, final_residual: float, temperatures: list[float]) -> str:
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
    return "\n".join(rows) + "\n\nEnd\n"


def test_convergence_summary_uses_residual_and_temperature_window():
    result = operations.summarize_steady_convergence(
        _steady_log(1e-5, 1e-7, [300.0, 300.0001, 300.0002, 300.0003, 300.0004]),
        5,
    )
    assert result["passed"] is True
    assert result["criteria"]["window_iterations"] == 5


def test_convergence_summary_rejects_unsettled_solve():
    result = operations.summarize_steady_convergence(
        _steady_log(0.014, 2e-5, [300.0, 300.01, 300.02, 300.03, 300.04]),
        5,
    )
    assert result["passed"] is False
    assert result["observed"]["maximum_initial_residual"] == pytest.approx(0.014)
