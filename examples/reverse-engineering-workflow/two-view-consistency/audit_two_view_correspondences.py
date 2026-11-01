import argparse
import hashlib
import json
import platform
from pathlib import Path
import sys
import cv2
import numpy as np

METHOD = {
    "schema": "wright.two-view-audit/1",
    "fit": "Unweighted Hartley-normalized eight-point F / normalized DLT H; all common observations retained",
    "F_convention": "b_h.T @ F @ a_h = 0; rank two explicitly enforced after design diagnostics",
    "uncertainty_assumption": "Independent isotropic coordinate scales within and between observations; supplied uncertainty is not measured sigma",
    "F_normalization": "abs(e)/sqrt(sa^2*||(F.T b)[:2]||^2 + sb^2*||(F a)[:2]||^2); first-order propagation of scalar constraint, holding fitted F fixed",
    "directional_scales": "Propagated scalar-constraint scale divided by each line normal; not full off-constraint derivatives of directional distances",
    "H_errors": "Separate original-pixel forward-to-b and backward-to-a Euclidean distances; no uncertainty normalization",
    "rank_tolerance": "max(design.shape)*float64_epsilon*largest_singular_value",
    "diagnostic_effective_rank_relative_cutoff": 1e-6,
    "diagnostic_cutoff_scope": "Assumed numerical warning only, not an engineering acceptance tolerance",
    "validation": "Leave one identity out; refit normalization and model on remaining identities only",
    "interpretation": "No pass decision, metric recovery, outlier rejection, bounds expansion, or F-versus-H objective ranking; noisy full rank does not establish camera identifiability",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    if isinstance(value, dict):
        for x in value.values():
            finite(x)
    elif isinstance(value, (list, tuple)):
        for x in value:
            finite(x)
    elif isinstance(value, float):
        require(np.isfinite(value), "nonfinite number")
    return value


def unique_object(items):
    out = {}
    for key, value in items:
        require(key not in out, "duplicate JSON key: " + key)
        out[key] = value
    return out


def reject_constant(value):
    raise ValueError("nonfinite JSON constant: " + value)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check_hash(actual, expected):
    require(
        isinstance(expected, str)
        and len(expected) == 64
        and all(c in "0123456789abcdefABCDEF" for c in expected),
        "invalid SHA256",
    )
    require(actual == expected.lower(), "SHA256 mismatch")


def identifier(value):
    require(isinstance(value, str) and bool(value), "invalid identifier")
    return value


def verify(data, base, report):
    require(data["schema"] == "wright.two-view-correspondences/1", "unsupported schema")
    images, tracks = {}, {}
    for spec in data["images"]:
        key = identifier(spec["id"])
        require(key not in images, "duplicate image identity")
        images[key] = spec
        for dim in ("width_px", "height_px"):
            require(
                type(spec[dim]) is int and spec[dim] > 0, "invalid image dimensions"
            )
        path = Path(spec["path"])
        path = path if path.is_absolute() else base / path
        record = {
            "declared": spec,
            "resolved_path": str(path.resolve()),
            "verified": False,
        }
        report["image_identities"].append(record)
        raw = path.read_bytes()
        record.update(actual_sha256=sha(raw), byte_count=len(raw))
        check_hash(record["actual_sha256"], spec["sha256"])
        image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_UNCHANGED)
        require(image is not None, "image decode failed")
        h, w = image.shape[:2]
        record.update(actual_width_px=w, actual_height_px=h)
        require(
            (w, h) == (spec["width_px"], spec["height_px"]), "image dimension mismatch"
        )
        record["verified"] = True
    for track in data["tracks"]:
        key = identifier(track["id"])
        require(key not in tracks, "duplicate track identity")
        observations = {}
        for obs in track["observations"]:
            image_id = obs["image_id"]
            require(
                image_id in images and image_id not in observations,
                "unknown/duplicate observation image",
            )
            uv = obs["uv_px"]
            if uv is not None:
                require(
                    isinstance(uv, list)
                    and len(uv) == 2
                    and all(type(v) in (int, float) for v in uv),
                    "malformed coordinates",
                )
                scale = obs["uncertainty_px"]
                require(
                    type(scale) in (int, float) and scale > 0,
                    "invalid uncertainty scale",
                )
                spec = images[image_id]
                require(
                    0 <= uv[0] < spec["width_px"] and 0 <= uv[1] < spec["height_px"],
                    "coordinates outside original image",
                )
            observations[image_id] = obs
        tracks[key] = observations
    for exclusion in data.get("host_review", {}).get("excluded_observations", []):
        for key in exclusion["tracks"]:
            obs = tracks.get(key, {}).get(exclusion["image"])
            require(
                obs is None or obs["uv_px"] is None,
                "explicitly excluded observation is present",
            )
    seen = set()
    for pair in data["pairs"]:
        require(
            isinstance(pair, list)
            and len(pair) == 2
            and all(isinstance(k, str) for k in pair),
            "malformed pair",
        )
        require(
            pair[0] != pair[1] and all(k in images for k in pair), "invalid pair images"
        )
        require(tuple(pair) not in seen, "duplicate configured pair")
        seen.add(tuple(pair))
    return tracks


def homogeneous(points):
    return np.column_stack((points, np.ones(len(points))))


def normalize(points):
    center = points.mean(axis=0)
    radius = np.linalg.norm(points - center, axis=1).mean()
    require(np.isfinite(radius) and radius > 0, "zero/invalid point spread")
    scale = np.sqrt(2.0) / radius
    transform = np.array(
        [[scale, 0, -scale * center[0]], [0, scale, -scale * center[1]], [0, 0, 1.0]]
    )
    return homogeneous(points) @ transform.T, transform


def ratio(a, b):
    if b <= 0:
        return None
    value = float(a / b)
    return value if np.isfinite(value) else None


def fit(kind, a, b):
    out = {"status": "unavailable", "n": len(a)}
    if len(a) < (8 if kind == "F" else 4):
        return dict(out, reason="insufficient_correspondences")
    try:
        x, ta = normalize(a)
        y, tb = normalize(b)
        if kind == "F":
            design = np.einsum("ni,nj->nij", y, x).reshape(-1, 9)
        else:
            zero = np.zeros_like(x)
            design = np.stack(
                (
                    np.hstack((-x, zero, y[:, 0:1] * x)),
                    np.hstack((zero, -x, y[:, 1:2] * x)),
                ),
                axis=1,
            ).reshape(-1, 9)
        _, s, vt = np.linalg.svd(design, full_matrices=design.shape[0] < 9)
        tol = max(design.shape) * np.finfo(float).eps * s[0]
        rank = int(np.sum(s > tol))
        effective = int(np.sum(s > s[0] * 1e-6))
        ninth = float(s[8]) if len(s) == 9 else 0.0
        out["design_before_enforcement"] = {
            "shape": list(design.shape),
            "singular_values": s.tolist(),
            "rank": rank,
            "rank_tolerance": float(tol),
            "nullity": 9 - rank,
            "effective_rank_diagnostic": effective,
            "condition_first_eight": ratio(s[0], s[7]),
            "eighth_over_first": ratio(s[7], s[0]),
            "eighth_over_ninth": ratio(s[7], ninth),
            "ninth_is_implicit_zero": len(s) == 8,
            "weak_eight_row_support_warning": effective < 8,
            "camera_identifiability": "not_established_by_numerical_rank",
        }
        require(rank >= 8, "fewer_than_eight_independent_design_rows")
        matrix = vt[-1].reshape(3, 3)
        if kind == "F":
            u, values, v = np.linalg.svd(matrix)
            out["pre_rank2_matrix_singular_values"] = values.tolist()
            values[-1] = 0.0
            matrix = tb.T @ (u @ np.diag(values) @ v) @ ta
            require(np.linalg.matrix_rank(matrix) == 2, "rank-two F not recoverable")
        else:
            require(np.linalg.matrix_rank(matrix) == 3, "singular homography")
            out["normalized_H_condition"] = float(np.linalg.cond(matrix))
            matrix = np.linalg.solve(tb, matrix @ ta)
            np.linalg.inv(matrix)
        matrix /= np.linalg.norm(matrix)
        finite(matrix.tolist())
        out.update(status="fitted_image_model", matrix=matrix.tolist())
        finite(out)
    except (ValueError, np.linalg.LinAlgError, FloatingPointError) as exc:
        out.update(status="non_identifiable", reason=str(exc))
        out.pop("matrix", None)
    return out


def evaluate(kind, model, key, a, b, sa, sb):
    out = {"id": key, "status": "unavailable"}
    if model["status"] != "fitted_image_model":
        return dict(out, reason="fit_" + model["status"])
    try:
        matrix = np.asarray(model["matrix"])
        x, y = np.r_[a, 1.0], np.r_[b, 1.0]
        if kind == "F":
            lb, la = matrix @ x, matrix.T @ y
            na, nb = np.linalg.norm(la[:2]), np.linalg.norm(lb[:2])
            require(na > 0 and nb > 0, "undefined epipolar line")
            e = abs(float(y @ lb))
            scale = float(np.hypot(sa * na, sb * nb))
            metrics = {
                "to_image_a_px": float(e / na),
                "to_image_b_px": float(e / nb),
                "constraint_normalized": float(e / scale),
                "constraint_scale_over_line_a_px": float(scale / na),
                "constraint_scale_over_line_b_px": float(scale / nb),
            }
        else:
            forward, backward = matrix @ x, np.linalg.solve(matrix, y)
            require(
                forward[2] != 0 and backward[2] != 0, "homography transfer at infinity"
            )
            metrics = {
                "forward_to_b_px": float(np.linalg.norm(forward[:2] / forward[2] - b)),
                "backward_to_a_px": float(
                    np.linalg.norm(backward[:2] / backward[2] - a)
                ),
            }
        finite(metrics)
        out.update(status="evaluated", metrics=metrics)
    except (ValueError, np.linalg.LinAlgError, FloatingPointError) as exc:
        out["reason"] = str(exc)
    return out


def summarize(rows):
    valid = [r["metrics"] for r in rows if r["status"] == "evaluated"]
    out = {
        "evaluated": len(valid),
        "unavailable": len(rows) - len(valid),
        "metrics": {},
    }
    for key in valid[0] if valid else []:
        v = np.array([r[key] for r in valid])
        maximum = float(v.max())
        rms = maximum * float(np.sqrt(np.mean((v / maximum) ** 2))) if maximum else 0.0
        out["metrics"][key] = {
            "mean": float(v.mean()),
            "median": float(np.median(v)),
            "rms": rms,
            "max": maximum,
        }
    return finite(out)


def audit_pair(pair, tracks):
    ids, omitted, a, b, sa, sb = [], [], [], [], [], []
    for key, obs in tracks.items():
        missing = [
            image for image in pair if image not in obs or obs[image]["uv_px"] is None
        ]
        if missing:
            omitted.append({"id": key, "missing_or_null_images": missing})
            continue
        oa, ob = (obs[image] for image in pair)
        ids.append(key)
        a.append(oa["uv_px"])
        b.append(ob["uv_px"])
        sa.append(oa["uncertainty_px"])
        sb.append(ob["uncertainty_px"])
    a, b = np.asarray(a, float).reshape(-1, 2), np.asarray(b, float).reshape(-1, 2)
    out = {
        "images": pair,
        "common_ids": ids,
        "omitted": omitted,
        "models": {},
        "interpretation": "Within-set consistency and internal leave-out checks only; not independent image validation or geometry acceptance",
    }
    for kind in ("F", "H"):
        model = fit(kind, a, b)
        within, leave = [], []
        for i, key in enumerate(ids):
            within.append(evaluate(kind, model, key, a[i], b[i], sa[i], sb[i]))
            keep = np.arange(len(ids)) != i
            refit = fit(kind, a[keep], b[keep])
            leave.append(
                {
                    "held_out_id": key,
                    "training_ids": [k for j, k in enumerate(ids) if j != i],
                    "fit": refit,
                    "evaluation": evaluate(kind, refit, key, a[i], b[i], sa[i], sb[i]),
                }
            )
        out["models"][kind] = {
            "training_ids": ids,
            "fit": model,
            "within_set": within,
            "within_summary": summarize(within),
            "leave_one_out": leave,
            "leave_out_summary": summarize([r["evaluation"] for r in leave]),
        }
    return out


def run(input_path, expected_sha256, output_dir):
    output = Path(output_dir)
    output.mkdir(
        parents=False, exist_ok=False
    )  # Never touch an existing output directory.
    report = {
        "method": METHOD,
        "status": "error",
        "image_identities": [],
        "pairs": [],
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "opencv": cv2.__version__,
        },
        "input_identity": {
            "path": str(Path(input_path).resolve()),
            "expected_sha256": expected_sha256,
        },
    }
    code = 2
    try:
        raw = Path(input_path).read_bytes()
        report["input_identity"].update(actual_sha256=sha(raw), byte_count=len(raw))
        report["input_text"] = raw.decode("utf-8")
        check_hash(sha(raw), expected_sha256)
        data = finite(
            json.loads(
                report["input_text"],
                object_pairs_hook=unique_object,
                parse_constant=reject_constant,
            )
        )
        report["supplied_input"] = data
        tracks = verify(data, Path(input_path).resolve().parent, report)
        for pair in data["pairs"]:
            report["pairs"].append(audit_pair(pair, tracks))
        report["status"] = "reported_image_consistency_only"
        report["geometry_acceptance"] = "not_assessed_or_authorized"
        code = 0  # Report production, NOT a fit/geometry pass.
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    with (output / "report.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, allow_nan=False, indent=2)
        stream.write("\n")
    return code


def main():
    parser = argparse.ArgumentParser(
        description="Original-pixel two-view correspondence audit; no geometry acceptance"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        return run(args.input, args.expected_sha256, args.output)
    except Exception as exc:
        print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
