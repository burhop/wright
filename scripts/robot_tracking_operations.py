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
import textwrap

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


def exceeds_interval_limit(start, end, maximum):
    """Compare sampled times without treating float representation noise as a gap."""
    interval = end - start
    return interval > maximum and not math.isclose(
        interval, maximum, rel_tol=1e-12, abs_tol=1e-12
    )


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


def plot_segments(samples, maximum_gap):
    """Never draw a measured line across an unobserved time interval."""
    segments = []
    for sample in samples:
        if not segments or exceeds_interval_limit(
            segments[-1][-1]["time_s"], sample["time_s"], maximum_gap
        ):
            segments.append([])
        segments[-1].append(sample)
    return segments


def render_tracking_plots(output, timeline, planned, odometry, metrics):
    """Present the recorded comparison; no smoothing, acceptance limit or diagnosis."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    output = Path(output)
    contract = metrics["alignment"]
    maximum_gap = float(contract["max_interpolation_gap_s"])
    external_segments = plot_segments(timeline, maximum_gap)
    wheel_segments = plot_segments(odometry, maximum_gap)
    peak = max(timeline, key=lambda row: abs(row["lateral_error_m"]))
    peak_wheel = max(odometry, key=lambda row: abs(row["lateral_error_m"]))
    start, end = planned[0]["time_s"], planned[-1]["time_s"]
    gaps = list(metrics["external_gaps_not_interpolated"])
    if timeline[0]["time_s"] > start:
        gaps.insert(0, [start, timeline[0]["time_s"]])
    if timeline[-1]["time_s"] < end:
        gaps.append([timeline[-1]["time_s"], end])
    colors = {"planned": "#475569", "external": "#0072B2", "wheel": "#D55E00"}
    legend = [
        Line2D([], [], color=colors["planned"], lw=2, ls=":", label="Intended route"),
        Line2D([], [], color=colors["external"], lw=2, marker="o", ms=4,
               label="External position measurement"),
        Line2D([], [], color=colors["wheel"], lw=2, ls="--",
               label="Wheel-based estimate (odometry)"),
    ]

    def series(ax, segments, x_key, y_key, color, style, y_scale=1):
        for segment in segments:
            ax.plot([row[x_key] for row in segment],
                    [row[y_key] * y_scale for row in segment],
                    style, color=color, lw=2, ms=3.5)

    def decorate(ax):
        ax.grid(True, color="#e2e8f0", lw=0.8)
        ax.set_axisbelow(True)
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.margins(x=0.025, y=0.18)

    def path_plot(ax, prefix="aligned"):
        series(ax, plot_segments(planned, maximum_gap), "x_m", "y_m",
               colors["planned"], ":", 1000)
        series(ax, wheel_segments, "x_m", "y_m", colors["wheel"], "--", 1000)
        series(ax, external_segments, prefix + "_x_m", prefix + "_y_m",
               colors["external"], "o-", 1000)
        ax.set(xlabel="Map X position (m)", ylabel="Map Y position (mm)", aspect="auto")
        decorate(ax)

    def save(fig, name, description):
        # SVG text remains text for accessibility, searching and crisp enlargement.
        try:
            fig.savefig(output / (name + ".svg"), metadata={
                "Title": "Robot tracking — intended and recorded motion",
                "Description": description,
            })
            fig.savefig(output / (name + ".png"), dpi=150)
        finally:
            plt.close(fig)

    event_notes = [
        f"Operator note at {event['bag_elapsed_s']:g} s: {event.get('operator_note', 'Event recorded')}"
        for event in metrics["events"]
    ]
    alignment_note = (
        f"External alignment: X shift {float(contract['translation_x_m']):g} m; "
        f"Y shift {float(contract['translation_y_m']):g} m; "
        f"rotation {math.degrees(float(contract['rotation_rad'])):g} degrees; "
        f"subtract {1000 * float(contract['header_offset_s']):g} ms from its clock."
    )
    no_correction = all(float(contract[key]) == 0 for key in (
        "translation_x_m", "translation_y_m", "rotation_rad", "header_offset_s"
    ))
    limitations = ("Shaded bands: no comparable external measurements. " if gaps else "") + (
        "Lines connect recorded samples; missing external measurements are not filled. "
        "Tracker repeatability is unknown. No acceptance limit is drawn. "
        "An event occurring at the same time does not prove a cause or wheel slip."
    )
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.titlesize": 14, "axes.labelsize": 11,
                         "svg.fonttype": "none", "figure.facecolor": "white"}):
        fig = plt.figure(figsize=(12, 10.5))
        fig.suptitle("How closely did the cart follow its intended path?",
                     x=0.08, y=0.975, ha="left", fontsize=21, weight="bold", color="#0f172a")
        fig.text(0.08, 0.938,
                 f"Synthetic example • Recorded interval {start:g}–{end:g} s • "
                 f"Common coordinate frame: {contract['map_frame']}", color="#475569")
        for x, value, label in [
            (0.08, f"{abs(peak['lateral_error_m']) * 1000:.1f} mm",
             f"Largest external sideways error · {peak['time_s']:g} s"),
            (0.40, f"{abs(peak_wheel['lateral_error_m']) * 1000:.1f} mm",
             f"Largest wheel-estimated error · {peak_wheel['time_s']:g} s"),
            (0.73, f"{metrics['lateral_rmse_m'] * 1000:.1f} mm",
             "External sideways error · RMS"),
        ]:
            fig.text(x, 0.889, value, fontsize=22, weight="bold", color="#0f172a")
            fig.text(x, 0.864, label, fontsize=9.5, color="#475569")
        fig.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.073, 0.841),
                   ncol=3, frameon=False, fontsize=10.5)
        grid = fig.add_gridspec(2, 1, left=0.10, right=0.97, top=0.77,
                               bottom=0.24, hspace=0.60, height_ratios=[1, 1.05])
        path_ax = fig.add_subplot(grid[0])
        path_plot(path_ax)
        path_ax.set_title("1  |  Where did the cart go?", loc="left", pad=12, weight="bold")
        path_ax.text(0, -0.31,
                     "Path-view axes are scaled independently to reveal small deviations; this is not a scale drawing.",
                     transform=path_ax.transAxes, fontsize=10, color="#475569")

        error_ax = fig.add_subplot(grid[1])
        error_ax.set_title("2  |  How far sideways, and when?", loc="left", pad=12, weight="bold")
        error_ax.axhline(0, color=colors["planned"], ls=":", lw=2)
        series(error_ax, wheel_segments, "time_s", "lateral_error_m", colors["wheel"], "--", 1000)
        series(error_ax, external_segments, "time_s", "lateral_error_m", colors["external"], "o-", 1000)
        for a, b in gaps:
            error_ax.axvspan(a, b, color="#cbd5e1", alpha=0.65)
        for index, event in enumerate(metrics["events"]):
            t = event["bag_elapsed_s"]
            error_ax.axvline(t, color="#64748b", lw=1, ls="-.")
            error_ax.text(t, 1.02 + 0.06 * index, f"Operator note · {t:g} s",
                          transform=error_ax.get_xaxis_transform(), ha="center", fontsize=9.5)
        error_ax.scatter([peak["time_s"]], [1000 * peak["lateral_error_m"]],
                         s=75, facecolors="white", edgecolors=colors["external"], lw=2, zorder=5)
        error_ax.set(xlabel="Elapsed time from run start (s)",
                     ylabel="Sideways error (mm)\nrelative to intended route", xlim=(start, end))
        decorate(error_ax)
        error_ax.text(0, -0.32,
                      "Zero = on the intended route. Positive = left of the intended heading; negative = right.",
                      transform=error_ax.transAxes, fontsize=10, color="#475569")
        fig.text(0.08, 0.153, "\n".join(textwrap.fill(note, 124) for note in event_notes),
                 fontsize=10.5, color="#0f172a", va="top")
        fig.text(0.08, 0.110,
                 "RMS is a whole-interval error measure, not the peak. "
                 f"External comparison uses {len(timeline)} recorded samples.", fontsize=10, color="#475569")
        fig.text(0.08, 0.079, textwrap.fill(limitations, 132), fontsize=10,
                 color="#475569", va="top", linespacing=1.5)
        save(fig, "trajectory-overlay", limitations)

        # Keep the raw/aligned evidence separate so an unchanged alignment does
        # not consume the main engineering comparison with two identical panels.
        fig, axes = plt.subplots(1, 2, figsize=(12, 6.5))
        fig.subplots_adjust(left=0.08, right=0.97, top=0.71, bottom=0.31, wspace=0.29)
        fig.suptitle("Alignment check: put the measurements on the same basis",
                     x=0.08, y=0.97, ha="left", fontsize=18, weight="bold")
        fig.text(0.08, 0.89, textwrap.fill(alignment_note, 118), fontsize=11)
        fig.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.073, 0.82),
                   ncol=3, frameon=False, fontsize=10)
        for ax, prefix, title in zip(axes, ["raw", "aligned"],
                                     ["Before: source coordinates", "After: common map coordinates"]):
            path_plot(ax, prefix)
            ax.set_title(title, loc="left", fontsize=13, pad=12)
        axes[0].set(xlabel="Source X coordinate (m)", ylabel="Source Y coordinate (mm)")
        fig.text(0.08, 0.20,
                 "The panels match: no position or clock correction was specified." if no_correction else
                 "Before: external coordinates may use a different origin. Only the aligned comparison supports diagnosis.",
                 fontsize=11)
        fig.text(0.08, 0.14,
                 "Axes are independently scaled, not a physical scale drawing. "
                 "See the main plot for time-linked sideways error.", fontsize=10)
        fig.text(0.08, 0.09, "Synthetic example • Missing measurements remain missing • No engineering approval", fontsize=10)
        save(fig, "alignment-comparison", alignment_note + " " + limitations)

    guide = [
        "# Reading the robot tracking plots", "",
        "## Start with the path and sideways-error comparison", "",
        "![Path and sideways-error comparison](trajectory-overlay.svg)", "",
        "- Dotted gray: the intended route, not a measurement.",
        "- Blue circles and line: the external tracker's position measurements, not assumed ground truth.",
        "- Dashed orange: the wheel-based position estimate (odometry), not an independent measurement of ground motion.",
        "- Top panel: map position. The axes use different scales to expose small deviations; do not infer angles from it.",
        "- Bottom panel: sideways error in millimetres at each recorded time. Zero is on the intended route; positive is left of the intended heading.",
        "- The outlined blue point marks the largest absolute external sideways error. RMS summarizes error over the retained samples; it is not a maximum or a confidence bound.",
        "- Gray time bands, when present, mark intervals without comparable external measurements. No external line bridges them.", "",
        "## Observations to inspect", "",
        f"- Largest absolute external sideways error: {abs(peak['lateral_error_m'])*1000:.3f} mm at {peak['time_s']:g} s.",
        f"- Largest absolute wheel-estimated sideways error: {abs(peak_wheel['lateral_error_m'])*1000:.3f} mm at {peak_wheel['time_s']:g} s.",
        f"- External lateral RMS error: {metrics['lateral_rmse_m']*1000:.3f} mm over {len(timeline)} samples.",
        *["- " + note for note in event_notes], "",
        "These are observations in synthetic input data, not a proven physical cause. " + limitations, "",
        "## Check the alignment", "", alignment_note, "",
        "![Before and after alignment](alignment-comparison.svg)", "",
        "Original values and calculated external residuals remain in [timeline.csv](timeline.csv); "
        "the calculation record is [tracking-metrics.json](tracking-metrics.json). "
        "Wheel poses are read from the same recorded bag in the declared map frame; "
        "their sideways residuals use the intended heading at each wheel sample time.", "",
        "These plots do not set an acceptable tracking limit, certify performance, or authorize robot operation.", "",
    ]
    (output / "plot-guide.md").write_text("\n".join(guide), encoding="utf-8")


def analyze_tracking_bag(bag, alignment, output_dir):
    """Read actual CDR messages, apply explicit survey/time contract and compare."""
    import numpy as np

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
    if any(msg.header.frame_id != contract["map_frame"] for _, msg in planned):
        raise ValueError("Planned path frame disagrees with the declared map frame")
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
    odometry = []
    for _, msg in data["/wright_test/odom"]:
        if msg.header.frame_id != contract["map_frame"]:
            raise ValueError("Wheel odometry frame disagrees with the declared map frame")
        t = time(msg.header.stamp)
        p = interpolate(t)
        if p is not None:
            x, y, _ = pose_values(msg)
            odometry.append({"time_s": t, "x_m": x, "y_m": y,
                             "lateral_error_m": -math.sin(p[2]) * (x-p[0]) + math.cos(p[2]) * (y-p[1])})
        if cmd_t[0] <= t <= cmd_t[-1]:
            velocity.append(float(msg.twist.twist.linear.x - np.interp(t, cmd_t, cmd_v)))
    if not odometry:
        raise ValueError("No wheel odometry samples in planned-path coverage")
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
    gaps = [
        [a, b]
        for a, b in zip(external_times, external_times[1:])
        if exceeds_interval_limit(a, b, max_gap)
    ]
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
    render_tracking_plots(output, timeline,
                          [{"time_s": float(t), "x_m": float(p[0]), "y_m": float(p[1])}
                           for t, p in zip(planned_t, planned_xy)], odometry, metrics)
    metrics["plot_files"] = ["trajectory-overlay.svg", "alignment-comparison.svg", "plot-guide.md"]
    write_json(output / "tracking-metrics.json", metrics)
    shutil.copyfile(__file__, output / "analysis-operation.py")
    return metrics
