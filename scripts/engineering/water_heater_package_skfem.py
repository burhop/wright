"""Bounded scikit-fem screens for an approved water-heater packaging design.

The operation consumes the exact Modelica selection and same-attempt CAD
measurements.  It solves two one-dimensional P1 finite-element models: peak
through-thickness carrier conduction and vessel-to-ambient insulation/convection.
This is a digital packaging screen, not an electrical, food-contact, pressure,
or physical heater qualification.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bound_geometry(config, measurements):
    """Resolve one pinned runtime path, never a producer's host-specific path."""
    workspace = Path(config["workspace_root"]).resolve(strict=True)
    output = Path(config["output_root"]).resolve()
    step = Path(config["geometry_step"]).resolve(strict=True)
    if not output.is_relative_to(workspace) or step.parent != output:
        raise ValueError("CAD geometry must be in the same-attempt output directory")
    expected_reference = step.relative_to(workspace).as_posix()
    if measurements.get("step_path") != expected_reference:
        raise ValueError("CAD measurements must use the exact workspace-relative POSIX reference")
    if digest(step) != measurements.get("step_sha256"):
        raise ValueError("CAD measurement identity differs from current STEP")
    return step


def _selected_power(path: Path) -> float:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    passing = {}
    for row in rows:
        if str(row.get("meets_time", "")).lower() == "true" and str(
            row.get("numerically_stable", "")
        ).lower() == "true":
            power = float(row["electrical_power_W"])
            passing.setdefault(power, []).append(row)
    loss_cases = {float(row["loss_W_per_K"]) for row in rows}
    eligible = [
        power
        for power, evidence in passing.items()
        if {float(row["loss_W_per_K"]) for row in evidence} == loss_cases
    ]
    if not eligible:
        raise ValueError("No numerically stable power meets every approved loss case")
    return min(eligible)


def _slab(thickness_m, conductivity, left_temperature_c, right_flux_w_m2, *,
          convection=None, nodes=81):
    import numpy as np
    from skfem import Basis, BilinearForm, ElementLineP1, LinearForm, MeshLine, asm, solve
    from skfem.helpers import dot, grad

    mesh = MeshLine(np.linspace(0.0, thickness_m, nodes)[None, :])
    basis = Basis(mesh, ElementLineP1())

    @BilinearForm
    def conduction(u, v, w):
        return conductivity * dot(grad(u), grad(v))

    @LinearForm
    def surface(v, w):
        return v

    matrix = asm(conduction, basis)
    rhs = np.zeros(basis.N)
    left = basis.get_dofs(lambda x: np.isclose(x[0], 0.0)).all()
    right_facets = mesh.facets_satisfying(lambda x: np.isclose(x[0], thickness_m))
    right = basis.boundary(facets=right_facets)
    if convection is None:
        rhs += right_flux_w_m2 * asm(surface, right)
    else:
        h, ambient = convection

        @BilinearForm
        def film(u, v, w):
            return h * u * v

        matrix += asm(film, right)
        rhs += h * ambient * asm(surface, right)
    fixed = np.zeros(basis.N)
    fixed[left] = left_temperature_c
    from skfem import condense

    temperature = solve(*condense(matrix, rhs, x=fixed, D=left))
    return mesh.p[0], temperature


def run(config):
    import numpy as np

    output = Path(config["output_root"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    measurements_path = Path(config["geometry_measurements"])
    comparison_path = Path(config["power_comparison"])
    requirements_path = Path(config["approved_engineering_brief"])
    measurements = json.loads(measurements_path.read_text(encoding="utf-8"))
    step_path = _bound_geometry(config, measurements)
    contract = json.loads(requirements_path.read_text(encoding="utf-8"))
    fixed = contract["approved_engineering_inputs"]["new_fixed_requirements"]
    power = _selected_power(comparison_path)
    efficiency = float(config["heater_efficiency"])
    thermal_power = power * efficiency
    diameter_m = float(measurements["heater_contact_diameter_mm"]) / 1000.0
    area = np.pi * diameter_m**2 / 4.0
    carrier_thickness_m = float(measurements["carrier_thickness_mm"]) / 1000.0
    insulation_thickness_m = float(measurements["insulation_thickness_mm"]) / 1000.0
    target = float(config["target_temperature_c"])
    ambient = float(config["ambient_temperature_c"])
    carrier_x, carrier_t = _slab(
        carrier_thickness_m,
        float(fixed["carrier_thermal_conductivity_w_mk"]),
        target,
        thermal_power / area,
    )
    shell_x, shell_t = _slab(
        insulation_thickness_m,
        float(fixed["insulation_thermal_conductivity_w_mk"]),
        target,
        0.0,
        convection=(float(fixed["external_film_coefficient_w_m2k"]), ambient),
    )
    field = output / "thermal-package-field.csv"
    with field.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("model", "x_m", "temperature_c"))
        writer.writerows(("carrier", x, t) for x, t in zip(carrier_x, carrier_t))
        writer.writerows(("insulation", x, t) for x, t in zip(shell_x, shell_t))
    carrier_limit = float(fixed["maximum_carrier_temperature_c"])
    shell_limit_key = next(
        key
        for key in (
            "maximum_accessible_shell_temperature_c",
            "maximum_other_accessible_shell_temperature_c",
        )
        if key in fixed
    )
    shell_limit = float(fixed[shell_limit_key])
    checks = {
        "carrier_temperature": {
            "observed_c": float(carrier_t.max()),
            "limit_c": carrier_limit,
            "pass": float(carrier_t.max()) <= carrier_limit,
        },
        "accessible_shell_temperature": {
            "observed_c": float(shell_t[-1]),
            "limit_c": shell_limit,
            "pass": float(shell_t[-1]) <= shell_limit,
        },
        "envelope": {
            "observed_mm": measurements["envelope_mm"],
            "limit_mm": fixed["maximum_envelope_mm"],
            "pass": all(
                float(actual) <= float(limit)
                for actual, limit in zip(
                    measurements["envelope_mm"], fixed["maximum_envelope_mm"]
                )
            ),
        },
        "dry_mass": {
            "observed_kg": float(measurements["dry_mass_kg"]),
            "limit_kg": float(fixed["maximum_dry_package_mass_kg"]),
            "pass": float(measurements["dry_mass_kg"])
            <= float(fixed["maximum_dry_package_mass_kg"]),
        },
    }
    result = {
        "schema": "wright-water-thermal-package-verification-v1",
        "status": "pass" if all(item["pass"] for item in checks.values()) else "fail",
        "selected_electrical_power_w": power,
        "heater_efficiency": efficiency,
        "thermal_power_w": thermal_power,
        "geometry": {
            "path": str(step_path),
            "sha256": measurements["step_sha256"],
            "measurements_sha256": digest(measurements_path),
        },
        "modelica_selection_sha256": digest(comparison_path),
        "approved_requirements_sha256": digest(requirements_path),
        "field": {"path": str(field), "sha256": digest(field)},
        "checks": checks,
        "limitations": [
            "One-dimensional steady carrier and insulation screens only.",
            "No electrical safety, food-contact, pressure, battery, wiring, certification or physical heating claim.",
        ],
    }
    (output / "thermal-package-verification.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": result["status"], "selected_power_w": power}))
    return result


if __name__ == "__main__":
    configuration = globals().get("WATER_CONFIG")
    if configuration is None:
        configuration = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    run(configuration)
