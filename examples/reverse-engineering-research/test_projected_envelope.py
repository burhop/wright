import numpy as np
from projected_envelope import upper_envelope


def camera():
    return dict(
        projection="orthographic",
        R_world_to_camera=np.eye(3).tolist(),
        t_world_to_camera_mm=[0.0, 0.0, 0.0],
        fx=1.0,
        fy=1.0,
        cx_px=50.0,
        cy_px=50.0,
        width_px=100,
        height_px=100,
        near_mm=0.1,
        distortion="none_assumed",
        provenance="Analytic controlled fixture;not real-camera qualification.",
    )


def test_full_assembly_detects_protrusion_hidden_by_regional_fit():
    roof = dict(
        id="roof",
        points=[[-10, 0, 10], [10, 0, 10], [0, 10, 10]],
        triangles=[[0, 1, 2]],
    )
    body = dict(
        id="body_protrusion",
        points=[[-5, -5, 10], [5, -5, 10], [0, 5, 10]],
        triangles=[[0, 1, 2]],
    )
    assert upper_envelope([roof], camera(), [50])[0]["upper_y_px"] == 50
    full = upper_envelope([roof, body], camera(), [50])[0]
    assert full["upper_y_px"] == 45 and full["owner"] == "body_protrusion"


def test_vertical_edge_and_missing_coverage_are_retained():
    triangle = dict(
        id="part", points=[[0, -5, 10], [0, 5, 10], [5, 0, 10]], triangles=[[0, 1, 2]]
    )
    values = upper_envelope([triangle], camera(), [50, 90])
    assert values[0]["upper_y_px"] == 45
    assert values[1]["upper_y_px"] is None and values[1]["owner"] is None
