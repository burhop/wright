"""Reusable offline CSV/ROS2 tracking operations; no robot or network access.

Selected dependency environment: rosbags==0.11.5, numpy==2.5.3,
matplotlib==3.11.1. The caller provides the human data and alignment contract.
"""
from __future__ import annotations

import csv
from decimal import Decimal
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import shutil

EPOCH_NS = 1767225600000000000
TOPICS = {
    "planned-path.csv": ("/wright_test/planned_pose", "geometry_msgs/msg/PoseStamped"),
    "external-pose.csv": ("/wright_test/external_pose", "geometry_msgs/msg/PoseStamped"),
    "odometry.csv": ("/wright_test/odom", "nav_msgs/msg/Odometry"),
    "velocity-command.csv": ("/wright_test/cmd_vel", "geometry_msgs/msg/TwistStamped"),
    "events.csv": ("/wright_test/operator_event", "std_msgs/msg/String"),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ns(value):
    return EPOCH_NS + int(Decimal(str(value)) * Decimal(1000000000))


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def fresh(path):
    path = Path(path)
    if path.exists():
        raise ValueError(f"Output already exists: {path}")
    path.mkdir(parents=True)
    return path


def convert_csv_to_bag(input_dir, output_dir):
    """Preserve frames/header clocks; acquisition timestamps order the real bag."""
    import numpy as np
    from rosbags.rosbag2 import Writer
    from rosbags.typesys import Stores, get_typestore

    source, output = Path(input_dir), fresh(output_dir)
    store = get_typestore(Stores.ROS2_HUMBLE)
    types = store.types
    def message(name, *args):
        return types[name](*args)
    def header(time, frame):
        stamp = ns(time)
        return message("std_msgs/msg/Header", message("builtin_interfaces/msg/Time", stamp // 10**9, stamp % 10**9), frame)
    def pose(row):
        yaw = float(row["yaw_rad"])
        return message("geometry_msgs/msg/Pose", message("geometry_msgs/msg/Point", float(row["x_m"]), float(row["y_m"]), 0.0),
                       message("geometry_msgs/msg/Quaternion", 0.0, 0.0, math.sin(yaw / 2), math.cos(yaw / 2)))
    def twist(row):
        return message("geometry_msgs/msg/Twist", message("geometry_msgs/msg/Vector3", float(row["linear_mps"]), 0.0, 0.0),
                       message("geometry_msgs/msg/Vector3", 0.0, 0.0, float(row["angular_radps"])))
    pending, skipped, inputs, counts = [], [], [], {}
    for name, (topic, schema) in TOPICS.items():
        path = source / name
        data = rows(path)
        inputs.append({"name": name, "sha256": sha(path), "rows": len(data)})
        counts[topic] = 0
        previous = None
        for index, row in enumerate(data):
            timestamp = ns(row["time_s"])
            if previous is not None and timestamp <= previous:
                raise ValueError(f"Non-increasing acquisition timestamps: {name} row {index + 2}")
            previous = timestamp
            if name == "external-pose.csv" and row["valid"] != "1":
                skipped.append({"source": name, "row": index + 2, "time_s": row["time_s"], "reason": "invalid external pose; no ROS message"})
                continue
            if name == "events.csv":
                payload = message(schema, json.dumps(row, ensure_ascii=False, sort_keys=True))
            elif name == "odometry.csv":
                payload = message(schema, header(row["time_s"], row["frame_id"]), row["child_frame_id"],
                                  message("geometry_msgs/msg/PoseWithCovariance", pose(row), np.full(36, np.nan)),
                                  message("geometry_msgs/msg/TwistWithCovariance", twist(row), np.full(36, np.nan)))
            elif name == "velocity-command.csv":
                payload = message(schema, header(row["time_s"], "base_link"), twist(row))
            else:
                payload = message(schema, header(row.get("timestamp_s", row["time_s"]), row["frame_id"]), pose(row))
            pending.append((timestamp, topic, schema, payload))
            counts[topic] += 1
    bag = output / "recording"
    with Writer(bag, version=9) as writer:
        connections = {topic: writer.add_connection(topic, schema, typestore=store) for topic, schema in TOPICS.values()}
        for timestamp, topic, schema, payload in sorted(pending, key=lambda value: (value[0], value[1])):
            writer.write(connections[topic], timestamp, store.serialize_cdr(payload, schema))
    shutil.copyfile(__file__, output / "conversion-operation.py")
    manifest = {"format": "ROS2 sqlite3 CDR", "epoch": "2026-01-01T00:00:00Z", "epoch_ns": EPOCH_NS,
                "rosbags_version": importlib.metadata.version("rosbags"), "typestore": "ROS2_HUMBLE",
                "source_inputs": inputs, "topics": [{"topic": topic, "schema": schema, "count": counts[topic]} for topic, schema in TOPICS.values()],
                "omitted_rows": skipped, "frame_transform_applied": False, "header_clock_corrected": False,
                "covariance": "Unknown: IEEE NaN entries; never zero or measured confidence", "operation_sha256": sha(__file__),
                "bag_files": [{"path": p.relative_to(output).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(bag.iterdir())]}
    write_json(output / "conversion-manifest.json", manifest)
    return manifest


def load_bag(bag):
    from rosbags.highlevel import AnyReader
    result = {topic: [] for topic, _ in TOPICS.values()}
    with AnyReader([Path(bag)]) as reader:
        actual = {connection.topic: connection.msgtype for connection in reader.connections}
        if actual != dict(TOPICS.values()):
            raise ValueError("Bag topics/message types differ from the uploaded mapping")
        for connection, timestamp, raw in reader.messages():
            result[connection.topic].append((timestamp, reader.deserialize(raw, connection.msgtype)))
    if any(not values for values in result.values()):
        raise ValueError("A required bag topic contains no messages")
    return result


def analyze_tracking_bag(bag, alignment, output_dir):
    """Read actual CDR messages, apply explicit survey/time contract and compare."""
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = fresh(output_dir)
    contract = json.loads(Path(alignment).read_text(encoding="utf-8"))
    required = {"external_frame", "map_frame", "translation_x_m", "translation_y_m", "rotation_rad", "header_offset_s", "max_interpolation_gap_s", "event_tolerance_s"}
    if set(contract) != required:
        raise ValueError("Alignment contract keys missing or unknown")
    data = load_bag(bag)
    def time(stamp):
        return (stamp.sec * 10**9 + stamp.nanosec - EPOCH_NS) / 1e9
    def pose_values(msg):
        pose = msg.pose.pose if hasattr(msg.pose, "pose") else msg.pose
        q = pose.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        return [pose.position.x, pose.position.y, yaw]
    planned = data["/wright_test/planned_pose"]
    planned_t = np.array([time(msg.header.stamp) for _, msg in planned])
    planned_xy = np.array([pose_values(msg) for _, msg in planned])
    yaw_unwrapped = np.unwrap(planned_xy[:, 2])
    max_gap = float(contract["max_interpolation_gap_s"])
    def interpolate(t):
        if t < planned_t[0] or t > planned_t[-1]:
            return None
        hi = int(np.searchsorted(planned_t, t))
        if hi < len(planned_t) and abs(planned_t[hi] - t) < 1e-9:
            return planned_xy[hi]
        lo = hi - 1
        if hi >= len(planned_t) or planned_t[hi] - planned_t[lo] > max_gap:
            return None
        weight = (t - planned_t[lo]) / (planned_t[hi] - planned_t[lo])
        return np.array([*(planned_xy[lo, :2] * (1-weight) + planned_xy[hi, :2] * weight), yaw_unwrapped[lo] * (1-weight) + yaw_unwrapped[hi] * weight])
    theta = float(contract["rotation_rad"])
    c, s = math.cos(theta), math.sin(theta)
    timeline, excluded = [], []
    for record_ns, msg in data["/wright_test/external_pose"]:
        if msg.header.frame_id != contract["external_frame"]:
            raise ValueError("External frame disagrees with supplied survey contract")
        acquisition = (record_ns - EPOCH_NS) / 1e9
        original_header = time(msg.header.stamp)
        aligned_time = original_header - float(contract["header_offset_s"])
        if abs(aligned_time - acquisition) > 1e-8:
            raise ValueError("Header correction does not match acquisition clock; do not double-correct")
        p = interpolate(aligned_time)
        if p is None:
            excluded.append({"time_s": aligned_time, "reason": "outside planned coverage or excessive interpolation gap"})
            continue
        x, y, yaw = pose_values(msg)
        ax = c*x - s*y + float(contract["translation_x_m"])
        ay = s*x + c*y + float(contract["translation_y_m"])
        dx, dy = ax - p[0], ay - p[1]
        lateral = -math.sin(p[2])*dx + math.cos(p[2])*dy
        timeline.append(dict(time_s=aligned_time, acquisition_time_s=acquisition, original_header_time_s=original_header,
                             raw_x_m=x, raw_y_m=y, aligned_x_m=ax, aligned_y_m=ay, planned_x_m=float(p[0]), planned_y_m=float(p[1]),
                             dx_m=dx, dy_m=dy, lateral_error_m=lateral, yaw_error_rad=math.atan2(math.sin(yaw+theta-p[2]), math.cos(yaw+theta-p[2]))))
    if not timeline:
        raise ValueError("No common valid comparison samples")
    # Both implementations independently reduce individual residuals; do not compare rounded values.
    squared = np.array([[r["dx_m"]**2+r["dy_m"]**2, r["lateral_error_m"]**2] for r in timeline])
    numpy_rmse = np.sqrt(np.mean(squared, axis=0)).tolist()
    scalar_rmse = [math.sqrt(math.fsum(r["dx_m"]**2+r["dy_m"]**2 for r in timeline)/len(timeline)),
                   math.sqrt(math.fsum(r["lateral_error_m"]**2 for r in timeline)/len(timeline))]
    disagreement = [abs(a-b)/max(abs(a), abs(b), 1e-12) for a, b in zip(numpy_rmse, scalar_rmse)]
    if max(disagreement) > 0.01:
        raise ValueError("Independent metric comparison exceeds original one-percent gate")
    commands = data["/wright_test/cmd_vel"]
    cmd_t = np.array([time(msg.header.stamp) for _, msg in commands])
    cmd_v = np.array([msg.twist.linear.x for _, msg in commands])
    velocity = []
    for _, msg in data["/wright_test/odom"]:
        t = time(msg.header.stamp)
        if cmd_t[0] <= t <= cmd_t[-1]:
            velocity.append(float(msg.twist.twist.linear.x - np.interp(t, cmd_t, cmd_v)))
    events = []
    for timestamp, msg in data["/wright_test/operator_event"]:
        elapsed = (timestamp-EPOCH_NS)/1e9
        raw = json.loads(msg.data)
        if abs(float(raw["time_s"]) - elapsed) > 1e-9:
            raise ValueError("Event content and bag recording timestamp disagree")
        # Use continuous odometry timeline for occluded external pose intervals.
        nearest = min((time(m.header.stamp) for _, m in data["/wright_test/odom"]), key=lambda t: abs(t-elapsed))
        difference = abs(nearest-elapsed)
        if difference > float(contract["event_tolerance_s"]):
            raise ValueError("Event correlation exceeds original one-sample gate")
        events.append({**raw, "bag_elapsed_s": elapsed, "nearest_odometry_time_s": nearest, "difference_s": difference})
    external_times = [r["time_s"] for r in timeline]
    gaps = [[a, b] for a, b in zip(external_times, external_times[1:]) if b-a > max_gap]
    metrics = {"position_rmse_m": numpy_rmse[0], "lateral_rmse_m": numpy_rmse[1],
               "independent_scalar_rmse_m": scalar_rmse, "independent_relative_difference": disagreement,
               "independent_tolerance": 0.01, "velocity_disagreement_rmse_mps": math.sqrt(math.fsum(v*v for v in velocity)/len(velocity)),
               "velocity_samples": len(velocity), "retained_samples": len(timeline), "common_valid_time_range_s": [external_times[0], external_times[-1]],
               "external_gaps_not_interpolated": gaps, "excluded": excluded, "events": events, "alignment": contract,
               "method": "Evaluate planned linear interpolation at corrected measured external sample times; no external interpolation/extrapolation across occlusion; unwrap planned yaw, wrap yaw residuals.",
               "causal_limit": "Command/odometry disagreement does not establish wheel slip", "operation_sha256": sha(__file__),
               "alignment_sha256": sha(alignment), "bag_files": [{"name": p.name, "sha256": sha(p)} for p in sorted(Path(bag).iterdir())]}
    with (output / "timeline.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(timeline[0]))
        writer.writeheader()
        writer.writerows(timeline)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, prefix, title in zip(axes, ["raw", "aligned"], ["Supplied frame (unaligned)", "Survey/time aligned, valid samples only"]):
        ax.plot(planned_xy[:, 0], planned_xy[:, 1], label="planned")
        ax.scatter([r[prefix+"_x_m"] for r in timeline], [r[prefix+"_y_m"] for r in timeline], s=8, label="external")
        ax.set(xlabel="x [m]", ylabel="y [m]", title=title, aspect="equal")
        ax.legend()
    fig.tight_layout()
    fig.savefig(output / "trajectory-overlay.svg")
    plt.close(fig)
    write_json(output / "tracking-metrics.json", metrics)
    shutil.copyfile(__file__, output / "analysis-operation.py")
    return metrics
