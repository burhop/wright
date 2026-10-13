"""Passive standard-STEP distance audit; no CAD edits or workflow execution."""

import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import sys
import time

import build123d as b
import numpy as np
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.gp import gp_Trsf
from OCP.Precision import Precision

root, out = map(Path, sys.argv[1:3])
assert out.is_dir() and not (out / "sampled-clearance.json").exists()
started = time.monotonic()
basis_path = root / "native-assembly-basis.json"
step_path = root / "robot-rev7.step"
basis = json.loads(basis_path.read_bytes())
assert basis["revision"] == 7
design = basis["design"]
kin = design["kinematics"]
instances = {i["name"]: i for i in design["instances"]}
printed = sorted(n for n, i in instances.items() if i.get("print"))
assert len(printed) == 28
contacts = {tuple(sorted((c["a"], c["b"]))) for c in kin["fits"][0]["contacts"]}
assert len(contacts) == 25
assert all(c["max_overlap_mm3"] == 0 for c in kin["fits"][0]["contacts"])
assert all(set(p) <= set(printed) for p in contacts)
incoming = {j["child"]: j for j in kin["joints"]}
assert len(incoming) == len(kin["joints"])

# Imported children are already located in the native home-world frame.
shapes = {}
assembly = b.import_step(step_path)
for child in assembly.children:
    box = child.bounding_box()
    extent = list(box.min) + list(box.max)
    candidates = []
    for name, instance in instances.items():
        if name in shapes:
            continue
        bounds = list(instance["bodies"].values())
        target = [min(v[k] for v in bounds) for k in range(3)] + [
            max(v[k] for v in bounds) for k in range(3, 6)
        ]
        volume = sum(
            v["volume"]
            for v in design["components"][instance["component"]]["bodies"].values()
        )
        if (
            max(abs(x - y) for x, y in zip(extent, target)) < 1e-5
            and abs(child.volume - volume) < 0.001
        ):
            candidates.append(name)
    assert len(candidates) == 1, (child.label, candidates)
    assert child.is_valid and len(child.solids()) == 1
    shapes[candidates[0]] = child.wrapped
assert set(shapes) == set(instances) and len(shapes) == 110


def transforms(values):
    q = dict(values)
    for coupling in kin["couplings"]:
        for name, ratio in coupling["gears"].items():
            q[name] = values.get(coupling["name"], coupling["value"]) * ratio
    done, active = {}, set()

    def visit(name):
        if name in done:
            return done[name]
        assert name not in active
        active.add(name)
        matrix = np.eye(4)
        joint = incoming.get(name)
        if joint:
            matrix = visit(joint["parent"]).copy()
            axis = np.array(joint["axis"], dtype=float)
            axis /= np.linalg.norm(axis)
            delta = np.eye(4)
            value = q.get(joint["name"], joint["value"]) - joint["value"]
            if joint["type"] == "revolute":
                x, y, z = axis
                cross = np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])
                angle = math.radians(value)
                rotation = (
                    np.eye(3) * math.cos(angle)
                    + (1 - math.cos(angle)) * np.outer(axis, axis)
                    + math.sin(angle) * cross
                )
                origin = np.array(joint["origin"])
                delta[:3, :3] = rotation
                delta[:3, 3] = origin - rotation @ origin
                assert np.allclose(
                    delta @ np.r_[origin, 1.0], np.r_[origin, 1.0], atol=1e-10
                )
            elif joint["type"] == "slider":
                delta[:3, 3] = axis * value
            else:
                assert joint["type"] == "rigid"
            matrix = matrix @ delta
        else:
            assert name in kin["ground"]
        assert np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=1e-10)
        assert abs(np.linalg.det(matrix[:3, :3]) - 1) < 1e-10
        done[name] = matrix
        active.remove(name)
        return matrix

    return {name: visit(name) for name in instances}


assert all(
    np.allclose(m, np.eye(4), atol=1e-10)
    for m in transforms(kin["poses"]["home"]).values()
)
poses = list(kin["poses"].items())
animation = kin["animations"][0]
assert animation["duration"] == 8 and animation["easing"] == "linear"
for sample in range(33):
    t = 8 * sample / 32
    keys = animation["keys"]
    left, right = next(
        (a, z) for a, z in zip(keys, keys[1:]) if a["time"] <= t <= z["time"]
    )
    fraction = (t - left["time"]) / (right["time"] - left["time"])
    values = {
        name: value + fraction * (right["values"][name] - value)
        for name, value in left["values"].items()
    }
    poses.append((f"path_{sample:02d}_t{t:g}", values))

linear_precision = Precision.Confusion_s()
results, violations = [], []
for label, values in poses:
    moved = {}
    for name, matrix in transforms(values).items():
        if name not in printed:
            continue
        trsf = gp_Trsf()
        trsf.SetValues(*[float(v) for v in matrix[:3, :].flat])
        moved[name] = BRepBuilderAPI_Transform(shapes[name], trsf, True).Shape()
    distances = []
    for a, z in itertools.combinations(printed, 2):
        query = BRepExtrema_DistShapeShape(moved[a], moved[z])
        assert query.IsDone() and query.NbSolution() > 0, (label, a, z)
        distance = query.Value()
        seated = (a, z) in contacts
        overlap = 0.0
        if distance <= linear_precision:
            common = BRepAlgoAPI_Common(moved[a], moved[z])
            common.Build()
            assert common.IsDone()
            props = GProp_GProps()
            BRepGProp.VolumeProperties_s(common.Shape(), props)
            overlap = abs(props.Mass())
        item = {
            "a": a,
            "b": z,
            "distance_mm": distance,
            "overlap_mm3": overlap,
            "declared_seat": seated,
        }
        if overlap > 1e-9 or (not seated and distance < 0.4 - linear_precision):
            violations.append({"pose": label, **item})
        distances.append(item)
    minimum = min(x["distance_mm"] for x in distances if not x["declared_seat"])
    results.append(
        {
            "pose": label,
            "joint_values": values,
            "minimum_nonseat_distance_mm": minimum,
            "pairs": distances,
        }
    )
    print(
        json.dumps(
            {
                "pose": label,
                "pairs": len(distances),
                "minimum_nonseat_distance_mm": minimum,
                "violations_so_far": len(violations),
            }
        ),
        flush=True,
    )

report = {
    "scope": "Independent passive exact-STEP distances at five poses and 33 linearly interpolated native-kinematic samples. No CAD edits, no new workflow executor, no continuous-motion or physical certification. This is a selected-library audit, not an AgentCAD MCP invocation.",
    "document_id": basis["document_id"],
    "revision": 7,
    "build_id": basis["build_id"],
    "step_sha256": hashlib.sha256(step_path.read_bytes()).hexdigest(),
    "native_basis_sha256": hashlib.sha256(basis_path.read_bytes()).hexdigest(),
    "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "build123d_version": importlib.metadata.version("build123d"),
    "mapped_native_instances": len(shapes),
    "printed_instances": printed,
    "declared_seat_pairs": sorted(contacts),
    "required_nonseat_gap_mm": 0.4,
    "linear_kernel_precision_mm": linear_precision,
    "numeric_zero_volume_threshold_mm3": 1e-9,
    "named_poses": 5,
    "path_samples": 33,
    "evaluated_pair_samples": sum(len(r["pairs"]) for r in results),
    "passed": not violations,
    "violations": violations,
    "results": results,
    "elapsed_seconds": round(time.monotonic() - started, 3),
}
(out / "sampled-clearance.json").write_text(json.dumps(report, indent=2) + "\n")
print(
    json.dumps(
        {
            k: v
            for k, v in report.items()
            if k
            not in {"results", "printed_instances", "declared_seat_pairs", "violations"}
        },
        indent=2,
    ),
    flush=True,
)
