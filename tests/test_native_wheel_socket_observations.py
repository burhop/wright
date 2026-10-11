"""Socket observation fixtures; native CAD qualification is separate."""

import ast
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

ASSET = Path(__file__).parents[1] / "examples/process-interfaces/printed-replacement-part/wheel-inspection-operation.py"


class Circle:
    def __init__(self, radius):
        self.Radius = radius


def functions():
    tree = ast.parse(ASSET.read_text(encoding="utf-8"))
    body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in {"measure_socket_section", "socket_observation_text"}]
    namespace = {"Part": SimpleNamespace(Circle=Circle), "math": math}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(ASSET), "exec"), namespace)
    return namespace["measure_socket_section"], namespace["socket_observation_text"]


def section(flat=-2.4, radius=3.2, other_flat=None):
    endpoints = [SimpleNamespace(Point=SimpleNamespace(x=x, y=y))
                 for x, y in [(flat, -1), (flat if other_flat is None else other_flat, 1)]]
    return SimpleNamespace(Edges=[SimpleNamespace(Curve=Circle(radius), Vertexes=endpoints),
                                 SimpleNamespace(Curve=object(), Vertexes=endpoints)])


@pytest.mark.parametrize("flat,radius", [(-2.4, 3.2), (-2.0, 3.2), (-2.4, 3.4)])
def test_observer_retains_measured_dimensions_instead_of_rejecting_nominal_mismatch(flat, radius):
    measure, describe = functions()
    observation = measure(section(flat, radius), 5.0)
    assert observation == {"z_mm": 5.0, "round_radius_mm": radius, "flat_x_mm": flat}
    text = describe([observation])
    assert f"x={flat:g}" in text and f"R{radius:g}" in text
    if flat == -2.0:
        assert "x=-2.4" not in text and "span=5.2 mm" in text


def test_missing_or_unmeasurable_socket_still_fails_explicitly():
    measure, _ = functions()
    with pytest.raises(AssertionError, match="one circular wall and one flat"):
        measure(SimpleNamespace(Edges=[]), 5.0)
    with pytest.raises(AssertionError, match="not parallel"):
        measure(section(other_flat=-2.0), 5.0)


def test_original_acceptance_target_is_unchanged():
    import json
    profile = json.loads(ASSET.with_name("native-inspection-profile.json").read_text())
    check = next(row for row in profile["checks"] if row["id"] == "socket-flat")
    assert check["selector"] == "/socket_sections/1/flat_x_mm"
    assert check["constraint"]["target"] == -2.4
    assert check["constraint"]["tolerance"] == 1e-6
