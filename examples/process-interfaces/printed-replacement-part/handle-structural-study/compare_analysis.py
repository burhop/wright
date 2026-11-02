"""Compare exact assessed baseline/candidate fields; never solve or approve work."""


def compare_analysis(config):
    import hashlib
    import json
    import math
    import os
    from pathlib import Path

    root = Path(config["workspace_root"])
    output = Path(config["output_dir"])
    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("Use the declared real workspace")
    if output.resolve() != output or not output.is_relative_to(root) or output == root or output.exists():
        raise ValueError("Preserve existing comparison outputs")
    assessments = {}
    identities = {}
    for key in ("baseline_coarse", "baseline_fine", "candidate_coarse", "candidate_fine"):
        item = config["assessments"][key]
        path = Path(item["path"])
        if path.resolve() != path or not path.is_relative_to(root):
            raise ValueError("Comparison inputs must remain in the workspace")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("An exact assessment changed: " + key)
        value = json.loads(raw)
        if value["original_brep_sha256"] != item["brep_sha256"]:
            raise ValueError("Assessment belongs to another CAD revision")
        if value["run_id"] != item["run_id"] or not value["checks"] or not all(c["passed"] for c in value["checks"]):
            raise ValueError("Numerical credibility or assessment identity is unavailable: " + key)
        assessments[key] = value
        identities[key] = {**item, "nodes": value["mesh"]["nodes"]}
    geometry_path = Path(config["geometry"]["path"])
    if geometry_path.resolve() != geometry_path or not geometry_path.is_relative_to(root):
        raise ValueError("Use the exact workspace CAD investigation")
    geometry_bytes = geometry_path.read_bytes()
    if hashlib.sha256(geometry_bytes).hexdigest() != config["geometry"]["sha256"]:
        raise ValueError("CAD investigation identity changed")
    geometry = json.loads(geometry_bytes)
    for prefix, key in [("baseline", "baseline_sha256"), ("candidate", "trial_brep_sha256")]:
        if any(assessments[prefix + "_" + mesh]["original_brep_sha256"] != geometry[key]
               for mesh in ("coarse", "fine")):
            raise ValueError("The comparison does not match the checked CAD revisions")
    radii = geometry["changes"]["root_blend_radius_mm"]
    output.mkdir(parents=True)
    definitions = [
        ("Loaded mean displacement", "mm", "displacement", "load_weighted_mean_Uz_mm", 5.0),
        ("Compliance", "N mm", "displacement", "compliance_Nmm", 5.0),
        *[(region + " P95 von Mises", "MPa", "regions", region, 10.0)
          for region in ("Left root", "Right root", "Central grip", "Pads")],
    ]

    def value(report, group, field):
        result = (report[group][field]["full"]["vm_p95_MPa"]
                  if group == "regions" else report[group][field])
        if not math.isfinite(result) or result <= 0:
            raise ValueError("A comparison quantity is missing, nonfinite or nonpositive")
        return result

    def sensitivity(a, b):
        return 100 * abs(b - a) / max(abs(a), abs(b))

    rows = []
    for name, unit, group, field, limit in definitions:
        measured = {key: value(report, group, field) for key, report in assessments.items()}
        base_mesh = sensitivity(measured["baseline_coarse"], measured["baseline_fine"])
        trial_mesh = sensitivity(measured["candidate_coarse"], measured["candidate_fine"])
        deltas = {mesh: 100 * (measured["candidate_" + mesh] - measured["baseline_" + mesh])
                  / measured["baseline_" + mesh] for mesh in ("coarse", "fine")}
        direction = ("Lower on both meshes" if all(x < 0 for x in deltas.values())
                     else "Higher on both meshes" if all(x > 0 for x in deltas.values())
                     else "Mixed or unchanged")
        rows.append({"quantity": name, "unit": unit, "values": measured,
                     "candidate_change_percent": deltas, "direction": direction,
                     "baseline_mesh_change_percent": base_mesh,
                     "candidate_mesh_change_percent": trial_mesh,
                     "declared_mesh_limit_percent": limit,
                     "mesh_checks_within_limits": base_mesh <= limit and trial_mesh <= limit})
    raw_peaks = {key: {"integration_point_MPa": report["stress"]["integration_point_peak_MPa"],
                       "location_mm": report["stress"]["peak_location_mm"]}
                 for key, report in assessments.items()}
    report = {"schema_version": "printed02.structural-comparison/1", "run_id": config["run_id"],
              "inputs": identities, "quantities": rows, "raw_peak_diagnostics": raw_peaks,
              "geometry": config["geometry"],
              "baseline_review_reference": config["baseline_review_reference"],
              "all_declared_mesh_checks_within_limits": all(r["mesh_checks_within_limits"] for r in rows),
              "engineering_acceptance": False, "physical_acceptance": False,
              "limits": ["Observed two-mesh changes are not rigorous error bounds or confidence intervals.",
                         "A lower scalar does not automatically establish a useful design improvement.",
                         "Raw fixed-bore peaks remain diagnostics; no printed PETG allowable is supplied.",
                         "Prior approval concerns only its exact original baseline, not this comparison or candidate."]}
    (output / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["all_declared_mesh_checks_within_limits"]:
        raise ValueError("A declared mesh-sensitivity check failed; retain data and investigate before review")
    lines = ["# Handle root blend: measured comparison", "",
             f"Same40 N S1/L1 assumptions; original R{radii['baseline']:g} and candidate R{radii['trial']:g}. No design or printed-strength approval.", "",
             "| Quantity | Original coarse | Original finer | Candidate coarse | Candidate finer | Fine change |",
             "|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        v = row["values"]
        lines.append(f"| {row['quantity']} ({row['unit']}) | {v['baseline_coarse']:.6f} | {v['baseline_fine']:.6f} | {v['candidate_coarse']:.6f} | {v['candidate_fine']:.6f} | {row['candidate_change_percent']['fine']:+.3f}% |")
    lines += ["", "| Quantity | Original mesh change | Candidate mesh change | Declared limit | Observation |",
              "|---|---:|---:|---:|---|"]
    for row in rows:
        lines.append(f"| {row['quantity']} | {row['baseline_mesh_change_percent']:.3f}% | {row['candidate_mesh_change_percent']:.3f}% | {row['declared_mesh_limit_percent']:g}% | {row['direction']} |")
    lines += ["", "All twelve declared sensitivity checks are within limits. All four assessments retain passing force, moment and load checks.", "",
              "Compare the measured design changes with the observed mesh changes. These two samples do not establish a rigorous error bound or an automatic ranking. Regional improvements and penalties must be judged with the unchanged geometry constraints and model limitations.", "",
              "## Raw peak diagnostic", "", "| Study | Integration-point peak (MPa) |", "|---|---:|"]
    for key, peak in raw_peaks.items():
        lines.append(f"| {key.replace('_', ' ')} | {peak['integration_point_MPa']:.6f} |")
    lines += ["", "Raw peaks remain restraint-edge diagnostics. Inspect their measured mesh response; they do not justify moving the fixed mounting holes or claiming a stronger printed handle.", "",
              f"The retained CAD investigation records the prior rejection: {geometry['previous_rejection']}. The checked R{radii['trial']:g} candidate has a measured volume change of{geometry['volume_change_percent']:+.4f}%. The original design remains available. Engineering review must decide whether any supported change is worthwhile.", "",
              "The chart displays the actual coarse/finer observations, not confidence intervals or physical-test results. No solver was repeated to make this comparison.", ""]
    (output / "comparison.md").write_text("\n".join(lines))
    os.environ.setdefault("MPLCONFIGDIR", str(output / ".mplconfig"))
    import matplotlib
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    with matplotlib.rc_context({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False}):
        fig = Figure(figsize=(13, 7), constrained_layout=True)
        FigureCanvasAgg(fig)
        axes = fig.subplots(2, 3)
        for ax, row in zip(axes.flat, rows):
            v = row["values"]
            for prefix, label, color, marker in [("baseline", f"Original R{radii['baseline']:g}", "#376489", "o"),
                                                  ("candidate", f"Candidate R{radii['trial']:g}", "#bd742b", "s")]:
                ys = [v[prefix + "_coarse"], v[prefix + "_fine"]]
                ax.plot([0, 1], ys, marker=marker, color=color, label=label)
                for x, y in enumerate(ys):
                    ax.annotate(f"{y:.5g}", (x, y), xytext=(5, 7 if prefix == 'baseline' else -13), textcoords="offset points", fontsize=8)
            ax.set_xticks([0, 1], ["Coarse", "Finer"])
            ax.set_ylabel(row["unit"])
            ax.set_title(row["quantity"])
            ax.grid(alpha=.2)
            ax.margins(x=.25, y=.35)
        axes.flat[0].legend(loc="best", fontsize=8)
        fig.suptitle("Handle root blend: actual two-mesh observations\nSame illustrative material/support assumptions and40 N load; no strength or design approval", fontsize=12)
        fig.savefig(output / "comparison.png", dpi=160)
        fig.clear()
    print("Retained measured structural comparison:", str(output))
    return report
