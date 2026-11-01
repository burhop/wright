"""Independent recorded-field and Wright-reader checks; no physical approval."""

import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from workspace_service.process_validation.readers.structural import (
    _displacements,
    _stresses,
)

root = Path(sys.argv[1])
report = json.loads((root / "structural-check.json").read_text())
for name, digest in report["files"].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest


def read(name):
    with (root / name).open() as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert all(math.isfinite(float(v)) for row in rows for v in row.values())
    return rows


cases = []
fields = []
for force in (1, 2):
    prefix = f"force-{force}n"
    displacement = read(prefix + "-displacement.csv")
    balance = read(prefix + "-balance.csv")
    stress = read(prefix + "-stress.csv")
    assert len(displacement) == len(balance) == report["nodes"]
    assert len({r["node_id"] for r in displacement}) == len(displacement)
    assert [r["node_id"] for r in balance] == [r["node_id"] for r in displacement]
    loads = [sum(float(r[f"f{axis}_n"]) for r in balance) for axis in "xyz"]
    reactions = [sum(float(r[f"r{axis}_n"]) for r in balance) for axis in "xyz"]
    assert math.isclose(loads[2], -force, abs_tol=1e-12)
    assert max(abs(f + r) for f, r in zip(loads, reactions)) < 1e-8
    for disp, row in zip(displacement, balance):
        if int(row["fixed"]):
            assert all(abs(float(disp[f"u{axis}_mm"])) < 1e-12 for axis in "xyz")
        else:
            assert all(abs(float(row[f"r{axis}_n"])) < 1e-8 for axis in "xyz")
    external_work = sum(
        float(d[f"u{axis}_mm"]) * float(b[f"f{axis}_n"])
        for d, b in zip(displacement, balance)
        for axis in "xyz"
    )
    assert external_work > 0
    assert math.isclose(
        external_work / 2,
        report["cases"][force - 1]["strain_energy_n_mm"],
        rel_tol=1e-10,
    )
    nd, maximum = _displacements(
        SimpleNamespace(content=(root / (prefix + "-displacement.csv")).read_bytes())
    )
    ns, maximum_stress = _stresses(
        SimpleNamespace(content=(root / (prefix + "-stress.csv")).read_bytes())
    )
    assert maximum > 0 and maximum_stress > 0
    assert math.isclose(
        maximum, report["cases"][force - 1]["maximum_displacement_mm"], rel_tol=1e-12
    )
    cases.append(
        {
            "force_n": force,
            "nodes": nd,
            "stress_samples": ns,
            "maximum_displacement_mm": maximum,
            "maximum_von_mises_mpa": maximum_stress,
            "force_balance_error_n": max(abs(f + r) for f, r in zip(loads, reactions)),
        }
    )
    fields.append((displacement, stress))
for first, second in zip(fields[0][0], fields[1][0]):
    assert first["node_id"] == second["node_id"]
    assert all(
        math.isclose(2 * float(first[k]), float(second[k]), rel_tol=1e-9, abs_tol=1e-12)
        for k in ("ux_mm", "uy_mm", "uz_mm")
    )
for first, second in zip(fields[0][1], fields[1][1]):
    for key in first:
        if key in ("element_id", "integration_point"):
            assert first[key] == second[key]
        else:
            assert math.isclose(
                2 * float(first[key]), float(second[key]), rel_tol=1e-9, abs_tol=1e-12
            )
result = {
    "status": "PASS",
    "scope": "independent CSV balance/constraints/load scaling and actual Wright field readers; not mesh convergence, accepted material, reviewed boundary conditions or strength compliance",
    "cases": cases,
    "linearity": "displacements and all stress components double at every recorded location",
    "digests_verified": len(report["files"]),
    "provider_critic_approval": False,
}
(root / "independent-structural-check.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result))
