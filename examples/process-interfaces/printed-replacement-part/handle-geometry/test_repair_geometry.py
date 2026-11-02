"""Pure controls for the authored FreeCAD-to-Blender measurement migration.

Only named pure definitions are evaluated. No Blender, FreeCAD, providers,
workspace outputs, or engineering acceptance are involved.
"""

import ast
import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest

HERE = Path(__file__).parent
PURE = {
    "grip_y",
    "thumb_depth",
    "clip_polygon",
    "distance_to_segment",
    "polygon_contains",
    "polygon_radial_bounds",
    "slab_radial_bounds",
    "point_in_solid",
    "cylinder_occupancy",
    "section_segments",
    "section_graph",
    "inner_contour",
    "radial_section_hits",
    "mouth_radius",
    "bore_observation",
    "require_bore",
    "grip_section",
    "nominal_grip_mesh_fidelity",
    "require_grip",
    "root_mesh_fidelity",
    "root_arc_observation",
    "require_root",
    "root_sections",
    "require_pad",
    "geometric_triangle_area",
}


@pytest.fixture(scope="module")
def measured():
    code = json.loads((HERE / "repair.json").read_bytes())["code"]
    tree = ast.parse(code)
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in PURE
    ]
    assert {node.name for node in functions} == PURE
    scope = {"math": math}
    exec(
        compile(
            ast.Module(body=functions, type_ignores=[]),
            "<pure-repair-measurements>",
            "exec",
        ),
        scope,
    )
    return scope


def tube(rings, center_x=0.0, count=96, outer_radius=8.0):
    """Closed oriented annular solid, with authored inner wall at each height."""
    points = []
    for z, radius in rings + [
        (rings[0][0], outer_radius),
        (rings[-1][0], outer_radius),
    ]:
        points.extend(
            (
                center_x + radius * math.cos(2 * math.pi * i / count),
                radius * math.sin(2 * math.pi * i / count),
                z,
            )
            for i in range(count)
        )
    triangles = []

    def quad(a, b, c, d):
        triangles.extend(((a, b, c), (a, c, d)))

    for k in range(len(rings) - 1):
        for i in range(count):
            j = (i + 1) % count
            quad(k * count + i, (k + 1) * count + i, (k + 1) * count + j, k * count + j)
    bottom, top = len(rings) * count, (len(rings) + 1) * count
    for i in range(count):
        j = (i + 1) % count
        quad(bottom + i, bottom + j, top + j, top + i)
        quad(bottom + i, i, j, bottom + j)
        last = (len(rings) - 1) * count
        quad(top + i, top + j, last + j, last + i)
    return points, triangles


def box(lower, upper):
    points = [
        (x, y, z)
        for z in (lower[2], upper[2])
        for y in (lower[1], upper[1])
        for x in (lower[0], upper[0])
    ]
    quads = [
        (0, 2, 3, 1),
        (4, 5, 7, 6),
        (0, 1, 5, 4),
        (2, 6, 7, 3),
        (0, 4, 6, 2),
        (1, 3, 7, 5),
    ]
    return points, [
        triangle for a, b, c, d in quads for triangle in ((a, b, c), (a, c, d))
    ]


@pytest.mark.parametrize("center_x", [0.0, 96.0])
def test_complete_rounded_bore_preserves_barrel_and_translated_centers(
    measured, center_x
):
    heights = [0.0, 0.255, 0.51, 0.765, 1.02, 2.5, 3.98, 4.235, 4.49, 4.745, 5.0]
    mesh = tube([(z, measured["mouth_radius"](z)) for z in heights], center_x)
    observed = measured["bore_observation"](*mesh, center_x)
    measured["require_bore"](observed)
    assert observed["full_pad_slab"]["minimum_radius_mm"] * 2 == pytest.approx(
        4.5, abs=1e-10
    )
    assert observed["barrel_slab"]["maximum_radius_mm"] * 2 < 4.503
    assert (
        max(row["continuous_diameter_min_max_mm"][1] for row in observed["sections"])
        > 6.5
    )
    hits, distances, continuous = measured["radial_section_hits"](*mesh, 2.5, center_x)
    assert len(hits) == len(distances) == 128
    assert continuous[0] == pytest.approx(4.5, abs=1e-10)
    assert sum(
        (hits[i][0] + hits[i + 64][0]) / 2 for i in range(64)
    ) / 64 == pytest.approx(center_x, abs=1e-10)
    assert observed["axis_midpoint_inside_material"] is False


@pytest.mark.parametrize("radius", [2.2, 2.3])
def test_bore_rejects_wrong_size_without_relaxing_nominal_bounds(measured, radius):
    mesh = tube([(0.0, radius), (5.0, radius)])
    observed = measured["bore_observation"](*mesh, 0.0)
    with pytest.raises(RuntimeError, match="clearance|barrel"):
        measured["require_bore"](observed)


def test_full_height_clearance_catches_thin_intrusion_between_all_section_planes(
    measured,
):
    radius = measured["mouth_radius"](2.5)
    mesh = tube(
        [(0.0, radius), (2.122, radius), (2.123, 2.2), (2.124, radius), (5.0, radius)]
    )
    observed = measured["bore_observation"](*mesh, 0.0)
    assert all(
        row["continuous_diameter_min_max_mm"][0] >= 4.5 - 0.00005
        for row in observed["sections"]
    )
    assert observed["full_pad_slab"]["minimum_radius_mm"] < 2.2
    with pytest.raises(RuntimeError, match="Complete through-bore"):
        measured["require_bore"](observed)


def test_mouth_expansion_does_not_excuse_an_oversize_barrel_or_unbounded_mouth(
    measured,
):
    radius = measured["mouth_radius"](2.5)
    mesh = tube([(0.0, 3.6), (1.02, radius), (3.98, radius), (5.0, 3.6)])
    observed = measured["bore_observation"](*mesh, 0.0)
    assert observed["barrel_slab"]["maximum_radius_mm"] * 2 < 4.503
    with pytest.raises(RuntimeError, match="maximum outer diameter"):
        measured["require_bore"](observed)


def test_contour_rejects_open_and_branched_paths_and_removes_coplanar_diagonal(
    measured,
):
    square = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    closed = list(zip(square, square[1:] + square[:1]))
    for invalid in (closed[:-1], closed + [(square[0], (2.0, 2.0))]):
        with pytest.raises(RuntimeError, match="open or branching"):
            measured["section_graph"](invalid, True)
    points = [(*point, 0.0) for point in square]
    segments = measured["section_segments"](
        points, [(0, 1, 2), (0, 2, 3)], (0, 0, 0), (0, 0, 1), (1, 0, 0), (0, 1, 0)
    )
    assert len(segments) == 4
    assert len(measured["section_graph"](segments, True)) == 1


def test_bore_complete_contour_detects_notch_between_radial_observations(measured):
    points, triangles = tube([(0.0, 2.2501), (5.0, 2.2501)], count=512)
    for index in (2, 514):
        angle = 2 * math.pi * 2 / 512
        points[index] = (2.2 * math.cos(angle), 2.2 * math.sin(angle), points[index][2])
    _, distances, continuous = measured["radial_section_hits"](
        points, triangles, 2.5, 0.0
    )
    assert min(distances) * 2 >= 4.5 - 0.00005
    assert continuous[0] == pytest.approx(4.4)


@pytest.mark.parametrize("center_x", [0.0, 96.0])
def test_whole_washer_volume_detects_a_small_obstruction_between_prior_rays(
    measured, center_x
):
    angle = math.pi / 64
    x, y = center_x + 4.99 * math.cos(angle), 4.99 * math.sin(angle)
    mesh = box((x - 0.001, y - 0.001, 8.0), (x + 0.001, y + 0.001, 8.002))
    assert all(
        not (
            x - 0.001 <= center_x + 5 * math.cos(2 * math.pi * i / 64) <= x + 0.001
            and y - 0.001 <= 5 * math.sin(2 * math.pi * i / 64) <= y + 0.001
        )
        for i in range(64)
    )
    observed = measured["cylinder_occupancy"](*mesh, (center_x, 0.0), 5.0, 5.0, 34.0)
    assert observed["occupied"] is True
    assert observed["surface_triangle_penetrations"] > 0


def test_washer_volume_includes_containment_but_excludes_cap_contact_and_tangency(
    measured,
):
    enclosing = measured["cylinder_occupancy"](
        *box((-10, -10, 0), (10, 10, 40)), (0, 0), 5, 5, 34
    )
    assert enclosing["surface_triangle_penetrations"] == 0
    assert enclosing["axis_midpoint_inside_material"] is True
    assert enclosing["occupied"] is True
    for mesh in (box((5, -0.5, 8), (6, 0.5, 9)), box((-2, -2, 0), (2, 2, 5))):
        assert (
            measured["cylinder_occupancy"](*mesh, (0, 0), 5, 5, 34)["occupied"] is False
        )


def test_radial_distance_checks_triangle_interiors_and_rejects_nonfinite_geometry(
    measured,
):
    triangle = [(-4, -4, 2), (4, -4, 2), (0, 4, 2)]
    assert measured["polygon_radial_bounds"](triangle, (0, 0))[0] == 0
    with pytest.raises(RuntimeError, match="Non-finite"):
        measured["polygon_radial_bounds"]([(math.inf, 0, 0)], (0, 0))


@pytest.mark.parametrize("center_x", [0.0, 96.0])
def test_pad_position_changes_only_the_explicit_proposal_equalities(measured, center_x):
    pad = {
        "bounded_pad_region_min_mm": [center_x - 9, -6.2, 0],
        "bounded_pad_region_max_mm": [center_x + 9, 17.8, 5],
        "flat_z0_contact_area_mm2": 250,
    }
    measured["require_pad"](pad, center_x)
    for field, index, value in (
        ("bounded_pad_region_min_mm", 1, -12),
        ("bounded_pad_region_max_mm", 1, 12),
        ("bounded_pad_region_max_mm", 2, 4.9),
    ):
        changed = copy.deepcopy(pad)
        changed[field][index] = value
        with pytest.raises(RuntimeError, match="mounting pad"):
            measured["require_pad"](changed, center_x)


def grip_fixture(measured, x, cy_delta=0.0, radius_y_delta=0.0, radius_z_delta=0.0):
    cy = measured["grip_y"](x) + cy_delta
    ry = 6 - measured["thumb_depth"](x) / 2 + radius_y_delta
    rz = 4.5 + radius_z_delta
    count = 256
    points = [
        (
            station,
            cy + ry * math.cos(2 * math.pi * i / count),
            29.5 + rz * math.sin(2 * math.pi * i / count),
        )
        for station in (x - 0.01, x + 0.01)
        for i in range(count)
    ]
    triangles = []
    for i in range(count):
        j = (i + 1) % count
        triangles.extend(((i, j, count + j), (i, count + j, count + i)))
    return points, triangles


@pytest.mark.parametrize("x", [15.5, 22, 28, 38, 48, 58, 68, 74, 80.5])
def test_quartic_ellipse_sections_preserve_complete_profile_and_recess(measured, x):
    observed = measured["grip_section"](*grip_fixture(measured, x), x)
    measured["require_grip"](observed)
    assert observed["thickness_mm"] == pytest.approx(9)
    assert observed["height_mm"] == pytest.approx(12 - measured["thumb_depth"](x))
    assert observed["complete_contour_radial_deviation_bound_mm"] < 0.002
    assert measured["thumb_depth"](48) == 1.5
    assert measured["thumb_depth"](28) == measured["thumb_depth"](68) == 0
    assert measured["grip_y"](48) == 12.75
    assert observed["thickness_error_mm"] == pytest.approx(0, abs=1e-12)
    assert observed["height_error_mm"] == pytest.approx(0, abs=1e-12)
    assert observed["center_y_error_mm"] == pytest.approx(0, abs=1e-12)


@pytest.mark.parametrize(
    "quantity",
    [
        "thickness_mm",
        "height_mm",
        "center_y",
        "complete_contour_radial_deviation_bound_mm",
    ],
)
@pytest.mark.parametrize("sign", [-1, 1])
def test_nominal_grip_fidelity_is_explicit_and_rejects_just_beyond_bound(
    measured, quantity, sign
):
    policy = measured["nominal_grip_mesh_fidelity"]()
    assert policy["schema_version"] == "printed02-nominal-grip-mesh-fidelity/1"
    assert policy["tolerance_mm"] == 0.03
    assert "Changed proposal fidelity tolerance" in policy["scope"]
    assert (
        policy["reference_diagnostic_sha256"]
        == "f6347f6021378c83ee8c49cce7f8e92e1ea8f66695b77e719f4fc3ad38a32cfe"
    )
    baseline = measured["grip_section"](*grip_fixture(measured, 48), 48)
    for deviation, accepted in ((0.029999, True), (0.030001, False)):
        observed = copy.deepcopy(baseline)
        if quantity == "center_y":
            observed["y_min_max_mm"] = [
                value + sign * deviation for value in baseline["y_min_max_mm"]
            ]
        elif quantity == "complete_contour_radial_deviation_bound_mm":
            observed[quantity] = deviation  # This bound is nonnegative by construction.
        else:
            observed[quantity] += sign * deviation
        if accepted:
            measured["require_grip"](observed)
        else:
            with pytest.raises(
                RuntimeError, match="versioned nominal-grip mesh fidelity"
            ):
                measured["require_grip"](observed)


def test_retained_native_grip_sections_distinguish_new_fidelity_from_old_failure(
    measured,
):
    # Raw subset of diagnosis-002, SHA256
    # f6347f6021378c83ee8c49cce7f8e92e1ea8f66695b77e719f4fc3ad38a32cfe.
    # This re-evaluates recorded observations, not a new native qualification.
    rows = [
        (
            15.5,
            [4.5006327629089355, 16.5],
            11.999367237091064,
            8.998687744140625,
            0.003376372891535251,
        ),
        (
            22.0,
            [4.891470373641314, 16.893620954548684],
            12.002150580907369,
            8.995082396275013,
            0.014777890613226985,
        ),
        (
            27.5,
            [5.601726245880127, 17.588513068013015],
            11.986786822132888,
            8.993121337890624,
            0.023985566980299966,
        ),
        (
            28.0,
            [5.667176723480225, 17.653042790570503],
            11.985866067090278,
            8.992975870768227,
            0.023506303873725765,
        ),
        (
            38.0,
            [6.957780116009319, 18.111085802239995],
            11.153305686230675,
            8.99865916323689,
            0.01802735647858231,
        ),
        (
            48.0,
            [7.500653843004895, 18.00835083442401],
            10.507696991419117,
            8.98998080363221,
            0.019538183785347024,
        ),
        (
            58.0,
            [6.95840196215324, 18.112372138588377],
            11.153970176435138,
            8.987062463609423,
            0.022485742916988155,
        ),
        (
            68.0,
            [5.658071824985642, 17.653373966277186],
            11.995302141291544,
            8.995135184377432,
            0.02741715496404562,
        ),
        (
            68.5,
            [5.588911973092415, 17.58515406120258],
            11.996242088110165,
            8.995153570780701,
            0.017127155110475023,
        ),
        (
            74.0,
            [4.891470426602741, 16.897055642382295],
            12.005585215779554,
            8.994621510809292,
            0.015244335067971848,
        ),
        (
            80.5,
            [4.50063419342041, 16.5],
            11.99936580657959,
            8.998689651489258,
            0.003376425235310565,
        ),
    ]
    maxima = [0.0] * 4
    for x, bounds, height, thickness, radial in rows:
        observed = {
            "x_mm": x,
            "y_min_max_mm": bounds,
            "height_mm": height,
            "thickness_mm": thickness,
            "complete_contour_radial_deviation_bound_mm": radial,
        }
        errors = [
            abs(thickness - 9),
            abs(height - (12 - measured["thumb_depth"](x))),
            abs(sum(bounds) / 2 - measured["grip_y"](x)),
            radial,
        ]
        # Preserve the distinction from the actual rejected v2 measurements.
        assert errors[0] > 0.00005
        assert errors[3] > 0.002
        measured["require_grip"](observed)
        maxima = [max(old, new) for old, new in zip(maxima, errors)]
    assert maxima == pytest.approx(
        [
            0.012937536390577264,
            0.014133932909722091,
            0.007437404924582225,
            0.02741715496404562,
        ],
        abs=1e-12,
    )


@pytest.mark.parametrize(
    "changes", [{"cy_delta": -4.5}, {"radius_y_delta": 0.2}, {"radius_z_delta": -0.1}]
)
def test_grip_rejects_old_arch_and_changed_section(measured, changes):
    observed = measured["grip_section"](*grip_fixture(measured, 48, **changes), 48)
    with pytest.raises(RuntimeError, match="oval/recess|nominal-grip"):
        measured["require_grip"](observed)


def root_segments(radius=3.05, count=32):
    points = [
        (
            5.55 - radius * math.sin(math.pi * i / (2 * count)),
            8.05 - radius * math.cos(math.pi * i / (2 * count)),
        )
        for i in range(count + 1)
    ]
    return list(zip(points, points[1:]))


def test_root_complete_segments_measure_r3_and_coverage(measured):
    observed = measured["root_arc_observation"](root_segments())
    measured["require_root"](observed)
    assert observed["segments"] == 32
    assert observed["continuous_radius_min_max_mm"][0] > 3
    assert observed["continuous_radius_min_max_mm"][1] == pytest.approx(3.05)
    assert observed["endpoint_coverage_error_mm"] == pytest.approx(0)
    assert observed["upper_nominal_radius_excess_mm"] == pytest.approx(0)


def test_root_fidelity_declares_mesh_allowances_separately_from_original_minimum(
    measured,
):
    policy = measured["root_mesh_fidelity"]()
    assert policy["schema_version"] == "printed02-root-mesh-fidelity/1"
    assert policy["measurement_window_q_mm"] == [2.48, 5.57]
    assert policy["measurement_window_z_mm"] == [5.0, 8.05]
    assert policy["endpoint_coverage_tolerance_mm"] == 0.03
    assert policy["nominal_radius_mm"] == 3.05
    assert policy["upper_nominal_radius_excess_mm"] == 0.02
    assert policy["original_minimum_radius_mm"] == 3.0
    assert policy["original_minimum_radius_numeric_epsilon_mm"] == 0.00005
    assert "not actual local curvature" in policy["scope"]


@pytest.mark.parametrize(
    "endpoint_error,accepted", [(0.029999, True), (0.030001, False)]
)
def test_root_complete_arc_rejects_just_beyond_endpoint_fidelity(
    measured, endpoint_error, accepted
):
    segments = root_segments()
    segments[0] = ((5.55 - endpoint_error, 5.0), segments[0][1])
    observed = measured["root_arc_observation"](segments)
    assert observed["endpoint_coverage_error_mm"] == pytest.approx(endpoint_error)
    assert observed["continuous_radius_min_max_mm"][0] >= 3.0 - 0.00005
    if accepted:
        measured["require_root"](observed)
    else:
        with pytest.raises(RuntimeError, match="root mesh fidelity"):
            measured["require_root"](observed)


@pytest.mark.parametrize("radius,accepted", [(3.069999, True), (3.070001, False)])
def test_root_complete_arc_rejects_just_beyond_upper_nominal_fidelity(
    measured, radius, accepted
):
    segments = root_segments()
    displaced = (5.55 - radius / math.sqrt(2), 8.05 - radius / math.sqrt(2))
    segments[15] = (segments[15][0], displaced)
    segments[16] = (displaced, segments[16][1])
    observed = measured["root_arc_observation"](segments)
    assert observed["continuous_radius_min_max_mm"][1] == pytest.approx(radius)
    assert observed["endpoint_coverage_error_mm"] == pytest.approx(0)
    assert observed["continuous_radius_min_max_mm"][0] >= 3.0 - 0.00005
    if accepted:
        measured["require_root"](observed)
    else:
        with pytest.raises(RuntimeError, match="root mesh fidelity"):
            measured["require_root"](observed)


@pytest.mark.parametrize("minimum,accepted", [(2.999951, True), (2.999949, False)])
def test_root_original_minimum_predicate_retains_its_numeric_epsilon(
    measured, minimum, accepted
):
    observed = measured["root_arc_observation"](root_segments())
    observed["continuous_radius_min_max_mm"][0] = minimum
    if accepted:
        measured["require_root"](observed)
    else:
        with pytest.raises(RuntimeError, match="original minimum R3"):
            measured["require_root"](observed)


def root_patch_mesh(offset=0.0, azimuth_offset=0.0):
    points, triangles = [], []
    azimuths, arc_points = 64, 33
    for center_x in (2.0 + offset, 94.0 + offset):
        start = len(points)
        for i in range(azimuths):
            angle = 2 * math.pi * i / azimuths + azimuth_offset
            for j in range(arc_points):
                phi = math.pi * j / (2 * (arc_points - 1))
                radius = 5.55 - 3.05 * math.sin(phi)
                points.append(
                    (
                        center_x + radius * math.cos(angle),
                        10.5 + radius * math.sin(angle),
                        8.05 - 3.05 * math.cos(phi),
                    )
                )
        for i in range(azimuths):
            k = (i + 1) % azimuths
            for j in range(arc_points - 1):
                a, b = start + i * arc_points + j, start + k * arc_points + j
                triangles.extend(((a, b, b + 1), (a, b + 1, a + 1)))
    return points, triangles


def test_root_meridian_extraction_covers_both_actual_mesh_patches(measured):
    observations = measured["root_sections"](*root_patch_mesh())
    assert len(observations) == 32
    assert {tuple(item["center_xy_mm"]) for item in observations} == {
        (2.0, 10.5),
        (94.0, 10.5),
    }
    for item in observations:
        measured["require_root"](item)


def test_root_window_keeps_inscribed_facet_endpoints_below_nominal_leg_radius(measured):
    observations = measured["root_sections"](
        *root_patch_mesh(azimuth_offset=math.pi / 64)
    )
    assert len(observations) == 32
    for item in observations:
        upper_endpoint = max(item["endpoints_qz_mm"], key=lambda value: value[1])
        assert 2.48 < upper_endpoint[0] < 2.5
        assert upper_endpoint[1] == pytest.approx(8.05)
        measured["require_root"](item)


def test_root_meridian_extraction_rejects_a_shifted_root_mesh(measured):
    with pytest.raises(RuntimeError, match="root|Root|section"):
        for item in measured["root_sections"](*root_patch_mesh(offset=0.1)):
            measured["require_root"](item)


@pytest.mark.parametrize(
    "bad", ["sharp", "undersized", "missing", "branch", "disconnected"]
)
def test_root_rejects_missing_blend_wrong_radius_and_incomplete_coverage(measured, bad):
    segments = root_segments()
    if bad == "sharp":
        segments = [((5.55, 5), (2.5, 5)), ((2.5, 5), (2.5, 8.05))]
    elif bad == "undersized":
        segments = root_segments(2.9)
    elif bad == "missing":
        segments = segments[2:]
    elif bad == "branch":
        segments.append((segments[8][0], (4.5, 6.5)))
    else:
        segments = segments[:8] + segments[10:]
    with pytest.raises(RuntimeError, match="root|Root|section"):
        measured["require_root"](measured["root_arc_observation"](segments))


def test_authored_operation_retains_all_resource_topology_and_exact_output_gates():
    path = HERE / "repair.json"
    value = json.loads(path.read_bytes())
    assert set(value) == {"code"}
    assert path.stat().st_size <= 65536
    tree = ast.parse(value["code"])
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    inspection = ast.unparse(functions["inspect_geometry"])
    assert (
        inspection.index("80000")
        < inspection.index("bmesh.new")
        < inspection.index("tree.overlap")
    )
    gate = ast.unparse(functions["require_geometry"])
    for marker in (
        "80000",
        "degenerate_faces",
        "degenerate_triangles",
        "nonadjacent_triangle_overlap_pairs",
        "winding_conflicts",
        "euler_characteristic",
        "118.0",
        "28.0",
        "34.0",
        "25.0",
        "require_pad",
        "require_bore",
        "require_grip",
        "require_root",
    ):
        assert marker in gate
    code = value["code"]
    assert "printed02-freecad-repair/4" in inspection
    assert "nominal_grip_mesh_fidelity()" in inspection
    assert "root_mesh_fidelity()" in inspection
    for marker in (
        "dist=0.001",
        "dist=0.000001",
        "geometric_triangle_area",
        "<= 1e-10",
        "require_geometry(after)",
        "require_geometry(verified)",
        "maximum_bound_change_mm",
        "original X drawer width/Y vertical/Z outward",
        "bpy.ops.wm.stl_import",
        "bpy.ops.wm.stl_export",
    ):
        assert marker in code
    assert code.count("print('W083_FINAL_REPORT'") == 1
    assert "{{wright.run_id}}" in code
    assert "'WRIGHT_HANDLE_OUTPUTS' in OUTPUT_ROOT" in code
    policy = (
        HERE.parents[3]
        / "tests/fixtures/blender_mcp_5f8ddaf6/src/blender_mcp/safe_mode.py"
    )
    spec = importlib.util.spec_from_file_location(
        "repair_pinned_provider_policy", policy
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate_code(code)
