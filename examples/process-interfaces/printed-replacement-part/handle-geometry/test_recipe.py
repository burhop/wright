"""Provider argument, source identity and analytic design checks; no native execution."""

import ast
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

HERE = Path(__file__).parent
REPO = HERE.parents[3]


def recipe(name):
    return json.loads((HERE / (name + ".json")).read_bytes())


@pytest.fixture(scope="module")
def analytic():
    names = {
        "multiply",
        "bump_power",
        "bernstein4",
        "axial_controls",
        "c1_conic_controls",
    }
    functions = [
        node
        for node in ast.parse(recipe("construction")["code"]).body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    assert {node.name for node in functions} == names
    scope = {"math": math}
    exec(
        compile(ast.Module(body=functions, type_ignores=[]), "<pure-grip>", "exec"),
        scope,
    )
    return scope


@pytest.mark.parametrize("name", ["construction", "repair"])
def test_arguments_are_bounded_and_require_an_explicit_run_binding(name):
    value = recipe(name)
    assert set(value) == {"code"}
    assert (HERE / (name + ".json")).stat().st_size <= 65536
    ast.parse(value["code"])
    assert "{{wright.run_id}}" in value["code"]
    assert "'WRIGHT_HANDLE_OUTPUTS' in OUTPUT_ROOT" in value["code"]
    assert value["code"].count("OUTPUT_ROOT = '/WRIGHT_HANDLE_OUTPUTS/' + RUN_ID") == 1


def test_repair_retains_the_pinned_blender_safe_mode_contract():
    policy = REPO / "tests/fixtures/blender_mcp_5f8ddaf6/src/blender_mcp/safe_mode.py"
    spec = importlib.util.spec_from_file_location("handle_provider_policy", policy)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    code = recipe("repair")["code"]
    module.validate_code(code)
    assert "bpy.ops.wm.stl_import" in code and "bpy.ops.wm.stl_export" in code
    assert code.count("print('W083_FINAL_REPORT'") == 1


def test_original_inputs_profile_and_supplied_dimensions_are_preserved():
    basis = recipe("basis")
    assert basis["scenario_id"] == "printed-replacement-part-02"
    assert basis["engineering_acceptance"] is basis["physical_acceptance"] is False
    for item in basis["original_inputs"] + [basis["original_validation_profile"]]:
        assert (
            hashlib.sha256((REPO / item["path"]).read_bytes()).hexdigest()
            == item["sha256"]
        )
    assert len(basis["original_inputs"]) == 6
    assert b"\r\n" in (REPO / basis["original_inputs"][3]["path"]).read_bytes()
    supplied = basis["supplied_requirements"]
    assert supplied["mounting"]["pad_xyz_mm"] == [18, 24, 5]
    assert supplied["mounting"]["bolt_centers_xy_mm"] == [[0, 0], [96, 0]]
    assert supplied["nominal_grip_yz_mm"] == [12, 9]
    assert supplied["finger_clearance"] == {"minimum_z_mm": 25, "central_span_mm": 65}
    assert supplied["envelope_max_xyz_mm"] == [118, 28, 34]


def bezier(poles, weights, t):
    n = len(poles) - 1
    terms = [
        math.comb(n, k) * t**k * (1 - t) ** (n - k) * weights[k] for k in range(n + 1)
    ]
    return tuple(
        sum(terms[k] * poles[k][axis] for k in range(n + 1)) / sum(terms)
        for axis in range(len(poles[0]))
    )


def test_axial_surface_preserves_nominal_ellipse_arch_recess_and_endpoint_tangency(
    analytic,
):
    controls = analytic["axial_controls"](10.5)
    for offset, (a, b) in zip((0, 4, 8), ((15.5, 28), (28, 68), (68, 80.5))):
        for i in range(101):
            t = i / 100
            x = a + (b - a) * t
            u, v = (x - 15.5) / 65, (x - 28) / 40
            depth = 24 * v * v * (1 - v) * (1 - v) if 0 < v < 1 else 0
            expected = (
                x,
                10.5 + 48 * u * u * (1 - u) * (1 - u) - depth / 2,
                6 - depth / 2,
            )
            assert bezier(controls[offset : offset + 5], [1] * 5, t) == pytest.approx(
                expected, abs=1e-12
            )
    for axis in (1, 2):
        assert controls[1][axis] == controls[0][axis]
        assert controls[-1][axis] == controls[-2][axis]
    # The construction keeps Z radius4.5 and center29.5: full65mm back25/front34.
    assert (29.5 - 4.5, 29.5 + 4.5) == (25, 34)
    assert 2 * controls[0][2] == 12
    assert bezier(controls[4:9], [1] * 5, 0.5)[2] * 2 == 10.5


def test_homogeneous_c1_conversion_preserves_exact_conic_and_all_join_derivatives(
    analytic,
):
    r = math.sqrt(3)
    original = [
        (0, 1, 0),
        (0, 1, r),
        (0, -0.5, r / 2),
        (0, -2, 0),
        (0, -0.5, -r / 2),
        (0, 1, -r),
    ]
    source_weights = [1, 0.5, 1, 0.5, 1, 0.5]
    poles, weights = analytic["c1_conic_controls"](original, source_weights)
    assert len(poles) == len(weights) == 13
    assert min(weights) > 0
    for arc in range(3):
        indices = [(2 * arc + k) % 6 for k in range(3)]
        for k in range(101):
            t = k / 100
            expected = bezier(
                [original[i] for i in indices], [source_weights[i] for i in indices], t
            )
            actual = bezier(
                poles[4 * arc : 4 * arc + 5], weights[4 * arc : 4 * arc + 5], t
            )
            assert actual == pytest.approx(expected, abs=1e-12)
            assert actual[1] ** 2 + actual[2] ** 2 == pytest.approx(1, abs=1e-12)
    homogeneous = [
        tuple(c * w for c in point) + (w,) for point, w in zip(poles, weights)
    ]
    for left, right in ((0, 4), (4, 8), (8, 0)):
        for axis in range(4):
            end = 4 * (homogeneous[left + 4][axis] - homogeneous[left + 3][axis])
            start = 4 * (homogeneous[right + 1][axis] - homogeneous[right][axis])
            assert end == pytest.approx(start, abs=1e-12)


def test_exact_constructor_publishes_expected_outputs_after_its_geometry_gates():
    code = recipe("construction")["code"]
    tree = ast.parse(code)
    publication = [
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "os"
        and n.func.attr == "link"
    ]
    assert len(publication) == 1
    geometry_guard = next(
        n.lineno
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and n.value == "Original full65mm finger-clearance bound failed"
    )
    assert publication[0] > geometry_guard
    assert "source-native.brep" in code and "native-geometry-observations.json" in code
    assert (
        "raise RuntimeError('Existing run output requires reconciliation; do not replay construction')"
        in code
    )
