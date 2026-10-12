"""Passive exact-STEP fastener alignment and planar bearing-contact audit."""

import hashlib
import importlib.metadata
import itertools
import json
from pathlib import Path
import sys
import time

import build123d as b
import numpy as np
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCP.GProp import GProp_GProps
from OCP.Precision import Precision

root, out = map(Path, sys.argv[1:3])
assert out.is_dir() and not (out / "fastener-audit.json").exists()
started = time.monotonic()
basis_path, step_path = root / "native-assembly-basis.json", root / "robot-rev7.step"
basis = json.loads(basis_path.read_bytes())
design = basis["design"]
instances = {x["name"]: x for x in design["instances"]}
assert basis["revision"] == 7
shape = b.import_step(step_path)
shapes, bounds = {}, {}
for child in shape.children:
    bb = child.bounding_box()
    extent = np.array(list(bb.min) + list(bb.max))
    candidates = []
    for name, instance in instances.items():
        if name in shapes:
            continue
        boxes = list(instance["bodies"].values())
        target = [min(v[k] for v in boxes) for k in range(3)] + [
            max(v[k] for v in boxes) for k in range(3, 6)
        ]
        volume = sum(
            v["volume"]
            for v in design["components"][instance["component"]]["bodies"].values()
        )
        if (
            max(abs(extent - np.array(target))) < 1e-5
            and abs(child.volume - volume) < 0.001
        ):
            candidates.append(name)
    assert len(candidates) == 1 and child.is_valid and len(child.solids()) == 1
    shapes[candidates[0]], bounds[candidates[0]] = child, extent.reshape(2, 3)
assert len(shapes) == 110
printed = sorted(n for n, i in instances.items() if i.get("print"))
bolts = sorted(n for n, i in instances.items() if i["component"].startswith("m3_bolt"))
nuts = sorted(n for n, i in instances.items() if i["component"].startswith("m3_nut"))
assert len(printed) == 28 and len(bolts) == len(nuts) == 25
metal_groups = [
    [
        prefix + "_shaft",
        prefix + "_washer_head",
        prefix + "_washer_rotating",
        prefix + "_nut",
    ]
    for prefix in ["yaw", "shoulder", "elbow", "wrist"]
]
hardware = sorted(set(bolts + nuts + [n for g in metal_groups for n in g]))
precision = Precision.Confusion_s()


def xyz(point):
    return np.array([point.X(), point.Y(), point.Z()])


def surfaces(name):
    cylinders, planes = [], []
    for face in shapes[name].faces():
        surface = BRepAdaptor_Surface(face.wrapped)
        if surface.GetType() == GeomAbs_Cylinder:
            cylinder = surface.Cylinder()
            axis, origin = xyz(cylinder.Axis().Direction()), xyz(cylinder.Location())
            heights = [
                float((np.array(tuple(v.center())) - origin) @ axis) for v in face.vertices()
            ]
            cylinders.append(
                {
                    "radius_mm": cylinder.Radius(),
                    "axis": axis.tolist(),
                    "origin_mm": origin.tolist(),
                    "axial_span_mm": [min(heights), max(heights)],
                    "length_mm": max(heights) - min(heights),
                }
            )
        elif surface.GetType() == GeomAbs_Plane:
            plane = surface.Plane()
            planes.append((face, xyz(plane.Axis().Direction()), xyz(plane.Location())))
    return cylinders, planes


geometry = {n: surfaces(n) for n in set(printed + hardware)}
stacks = []
for bolt in bolts + [g[0] for g in metal_groups]:
    nut = (
        bolt.replace("_bolt", "_nut")
        if bolt in bolts
        else bolt.replace("_shaft", "_nut")
    )
    shaft_radius = 1.5 if bolt in bolts else 2.5
    shaft = [
        c for c in geometry[bolt][0] if abs(c["radius_mm"] - shaft_radius) < precision
    ]
    assert len(shaft) == 1, (bolt, shaft)
    shaft = shaft[0]
    bore = min(geometry[nut][0], key=lambda c: c["radius_mm"])
    axis, origin = np.array(shaft["axis"]), np.array(shaft["origin_mm"])
    coaxial_error = float(
        np.linalg.norm(np.cross(np.array(bore["origin_mm"]) - origin, axis))
    )
    alignment = abs(float(axis @ np.array(bore["axis"])))
    nut_heights = [
        float((np.array(tuple(v.center())) - origin) @ axis) for v in shapes[nut].vertices()
    ]
    span = [min(nut_heights), max(nut_heights)]
    low, high = shaft["axial_span_mm"]
    nut_on_shaft = low - precision <= span[0] <= span[1] <= high + precision
    stacks.append(
        {
            "shaft": bolt,
            "nut": nut,
            "shaft_cylinder": shaft,
            "nut_bore": bore,
            "coaxial_error_mm": coaxial_error,
            "axis_parallel_dot_absolute": alignment,
            "nut_span_in_shaft_frame_mm": span,
            "nut_within_shaft_span": nut_on_shaft,
            "radial_profile_gap_mm": bore["radius_mm"] - shaft_radius,
            "alignment_pass": coaxial_error <= precision
            and alignment >= 1 - 1e-10
            and nut_on_shaft,
        }
    )

candidate_pairs = {tuple(sorted((a, z))) for a in hardware for z in printed}
candidate_pairs |= {
    tuple(sorted((a, z)))
    for group in metal_groups
    for a, z in itertools.combinations(group, 2)
}
candidate_pairs |= {tuple(sorted((r["shaft"], r["nut"]))) for r in stacks}
near_pairs, bearings = [], []
for a, z in sorted(candidate_pairs):
    boxgap = np.maximum(
        np.maximum(bounds[a][0] - bounds[z][1], bounds[z][0] - bounds[a][1]), 0
    )
    if np.linalg.norm(boxgap) > 0.5:
        continue
    query = BRepExtrema_DistShapeShape(shapes[a].wrapped, shapes[z].wrapped)
    assert query.IsDone()
    distance = query.Value()
    if distance > 0.5:
        continue
    area, overlap = 0.0, 0.0
    if distance <= precision:
        common = BRepAlgoAPI_Common(shapes[a].wrapped, shapes[z].wrapped)
        common.Build()
        assert common.IsDone()
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(common.Shape(), props)
        overlap = abs(props.Mass())
        for face_a, normal_a, origin_a in geometry[a][1]:
            for face_z, normal_z, origin_z in geometry[z][1]:
                if (
                    abs(float(normal_a @ normal_z)) < 1 - 1e-10
                    or abs(float((origin_z - origin_a) @ normal_a)) > precision
                ):
                    continue
                contact = BRepAlgoAPI_Common(face_a.wrapped, face_z.wrapped)
                contact.Build()
                assert contact.IsDone()
                props = GProp_GProps()
                BRepGProp.SurfaceProperties_s(contact.Shape(), props)
                area += abs(props.Mass())
    item = {
        "a": a,
        "b": z,
        "minimum_distance_mm": distance,
        "overlap_mm3": overlap,
        "coplanar_bearing_area_mm2": area,
    }
    near_pairs.append(item)
    if area > 1e-6 and overlap <= 1e-9:
        bearings.append(item)

for row in stacks:
    row["shaft_bearing_pairs"] = [
        r for r in bearings if row["shaft"] in (r["a"], r["b"])
    ]
    row["nut_bearing_pairs"] = [r for r in bearings if row["nut"] in (r["a"], r["b"])]
    row["both_ends_have_measured_planar_bearings"] = bool(
        row["shaft_bearing_pairs"] and row["nut_bearing_pairs"]
    )

report = {
    "scope": "Independent passive exact-STEP home-pose alignment, axial-stack and planar bearing-area observations. Simplified purchased references have no threads, driver geometry or physical engagement proof. No CAD edit or MCP invocation.",
    "document_id": basis["document_id"],
    "revision": 7,
    "build_id": basis["build_id"],
    "step_sha256": hashlib.sha256(step_path.read_bytes()).hexdigest(),
    "native_basis_sha256": hashlib.sha256(basis_path.read_bytes()).hexdigest(),
    "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "build123d_version": importlib.metadata.version("build123d"),
    "linear_kernel_precision_mm": precision,
    "mapped_instances": len(shapes),
    "m3_stacks": 25,
    "m5_stacks": 4,
    "all_stack_alignments_pass": all(r["alignment_pass"] for r in stacks),
    "all_stacks_have_both_bearings": all(
        r["both_ends_have_measured_planar_bearings"] for r in stacks
    ),
    "positive_overlap_pairs": [r for r in near_pairs if r["overlap_mm3"] > 1e-9],
    "stacks": stacks,
    "measured_planar_bearing_pairs": bearings,
    "near_pairs_within_half_mm": near_pairs,
    "elapsed_seconds": round(time.monotonic() - started, 3),
}
(out / "fastener-audit.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    json.dumps(
        {
            k: v
            for k, v in report.items()
            if k
            not in {
                "stacks",
                "measured_planar_bearing_pairs",
                "near_pairs_within_half_mm",
            }
        },
        indent=2,
    ),
    flush=True,
)
print(
    "Missing bearing stacks:",
    [r["shaft"] for r in stacks if not r["both_ends_have_measured_planar_bearings"]],
    flush=True,
)
print("Measured bearing pairs:", len(bearings), flush=True)
