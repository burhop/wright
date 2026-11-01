"""Read-only full-assembly upper silhouette observations at declared columns.

Reports measurements only. The caller supplies exact geometry, frame identities,
source observations and its existing acceptance profile. Every supplied part is
included; callers must disclose completeness separately from a regional fit.
"""

import numpy as np
from project_mesh_to_photo import validate_camera


def upper_envelope(parts, camera, columns):
    validate_camera(camera)
    columns = np.asarray(columns, dtype=float)
    if columns.ndim != 1 or not np.isfinite(columns).all():
        raise ValueError("Expected finite original-frame image columns.")
    if ((columns < 0) | (columns > camera["width_px"] - 1)).any():
        raise ValueError("Column outside the declared image frame.")
    R, t = (
        np.asarray(camera["R_world_to_camera"]),
        np.asarray(camera["t_world_to_camera_mm"]),
    )
    best = np.full(len(columns), np.inf)
    owners = [None] * len(columns)
    for part in parts:
        points, faces = (
            np.asarray(part["points"], dtype=float),
            np.asarray(part["triangles"]),
        )
        if (
            points.ndim != 2
            or points.shape[1] != 3
            or faces.ndim != 2
            or faces.shape[1] != 3
            or faces.dtype.kind not in "iu"
            or not np.isfinite(points).all()
            or (faces < 0).any()
            or (faces >= len(points)).any()
        ):
            raise ValueError("Invalid part geometry.")
        q = points @ R.T + t
        z = q[:, 2]
        near = z[faces] >= camera["near_mm"]
        if (near.any(1) & ~near.all(1)).any():
            raise ValueError("Near-plane-crossing triangles require explicit clipping.")
        faces = faces[near.all(1)]
        if not len(faces):
            continue
        xy = (
            q[:, :2] / z[:, None] if camera["projection"] == "perspective" else q[:, :2]
        )
        xy = xy * [camera["fx"], camera["fy"]] + [camera["cx_px"], camera["cy_px"]]
        tri = xy[faces]
        lo, hi = tri[:, :, 0].min(1), tri[:, :, 0].max(1)
        for i, x in enumerate(columns):
            selected = tri[(lo <= x) & (hi >= x)]
            if not len(selected):
                continue
            ys = []
            for a, b in [(0, 1), (1, 2), (2, 0)]:
                first, second = selected[:, a], selected[:, b]
                dx = second[:, 0] - first[:, 0]
                ordinary = dx != 0
                fraction = (x - first[ordinary, 0]) / dx[ordinary]
                valid = (fraction >= 0) & (fraction <= 1)
                ys.extend(
                    (
                        first[ordinary, 1]
                        + fraction * (second[ordinary, 1] - first[ordinary, 1])
                    )[valid]
                )
                vertical = ~ordinary & (first[:, 0] == x)
                ys.extend(first[vertical, 1])
                ys.extend(second[vertical, 1])
            if ys and min(ys) < best[i]:
                best[i] = min(ys)
                owners[i] = part["id"]
    return [
        dict(
            column_px=float(x),
            upper_y_px=float(y) if np.isfinite(y) else None,
            owner=owner,
        )
        for x, y, owner in zip(columns, best, owners)
    ]
