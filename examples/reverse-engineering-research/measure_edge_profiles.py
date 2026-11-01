import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
import cv2
import numpy as np

VERSION = "wright-profile-proposal/1.1"
CAPS = dict(image_bytes=64000000, pixels=12000000, profiles_per_feature=300, features=2)
POLARITIES = dict(either=0, brightening=1, darkening=-1)
POLARITY_SEMANTICS = "For xy=guide+t*normal, normal=(-tangent_y,tangent_x): sign is d(gray DN)/dt. Brightening selects +1; darkening selects -1; either selects both. No sign is inferred from feature names."


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def candidates(t, gradient, origin, normal):
    mag = np.abs(gradient)
    result = []
    for j in range(2, len(t) - 2):
        if not (mag[j] > 0 and mag[j] >= mag[j - 1] and mag[j] > mag[j + 1]):
            continue
        aa = float((mag[j - 1] + mag[j + 1]) / 2 - mag[j])
        bb = float((mag[j + 1] - mag[j - 1]) / 2)
        shift = -bb / (2 * aa) if aa < -1e-9 else 0.0
        valid = aa < -1e-9 and abs(shift) <= 0.5
        offset = float(t[j] + (shift if valid else 0) * (t[1] - t[0]))
        z = np.arange(-2, 3)
        prediction = aa * z * z + bb * z + mag[j]
        result.append(
            dict(
                index=j,
                xy_px=(origin + offset * normal).tolist(),
                offset_from_guide_px=offset,
                strength=float(mag[j]),
                sign=int(np.sign(gradient[j])),
                refinement_ok=bool(valid),
                quadratic_rmse=float(
                    np.sqrt(np.mean((prediction - mag[j - 2 : j + 3]) ** 2))
                ),
                status="rejected",
            )
        )
    return result


def sample(gray, origin, normal, roi, radius, p, polarity="either"):
    need(
        isinstance(polarity, str) and polarity in POLARITIES,
        "Invalid gradient_polarity",
    )
    step = p["profile_step_px"]
    sigmas = p["blur_sigmas_px"]
    thresholds = p["thresholds_dn_per_px"]
    pad = math.ceil(3 * max(sigmas) / step) * step + 2 * step
    t = np.arange(-radius - pad, radius + pad + step / 2, step)
    xy = origin[None, :] + t[:, None] * normal
    out = dict(
        guide_xy_px=origin.tolist(),
        normal=normal.tolist(),
        missing=True,
        gradient_polarity=polarity,
        ambiguous=False,
        provisional_edge_xy_px=None,
        variants=[],
    )
    if np.any(xy < roi[:2]) or np.any(xy > roi[2:]):
        out["reason"] = "profile_support_outside_search_region"
        return out
    h, w = gray.shape
    ix = np.floor(xy[:, 0]).astype(int)
    iy = np.floor(xy[:, 1]).astype(int)
    if np.any(ix < 0) or np.any(iy < 0) or np.any(ix + 1 >= w) or np.any(iy + 1 >= h):
        out["reason"] = "bilinear_support_outside_image"
        return out
    fx = xy[:, 0] - ix
    fy = xy[:, 1] - iy
    raw = (
        (1 - fx) * (1 - fy) * gray[iy, ix]
        + fx * (1 - fy) * gray[iy, ix + 1]
        + (1 - fx) * fy * gray[iy + 1, ix]
        + fx * fy * gray[iy + 1, ix + 1]
    )
    mask = np.abs(t) <= radius + 1e-8
    search_t = t[mask]
    out.update(
        profile_offsets_px=t.tolist(),
        raw_gray_dn=raw.tolist(),
        search_offsets_px=search_t.tolist(),
    )
    for sigma in sigmas:
        k = math.ceil(3 * sigma / step)
        u = np.arange(-k, k + 1) * step
        kernel = np.exp(-0.5 * (u / sigma) ** 2)
        kernel /= kernel.sum()
        gradient = np.gradient(np.convolve(raw, kernel, mode="same"), step)[mask]
        cs = candidates(search_t, gradient, origin, normal)
        decisions = []
        for c in cs:
            c["polarity_eligible"] = (
                polarity == "either" or c["sign"] == POLARITIES[polarity]
            )
            if not c["polarity_eligible"]:
                c["status"] = "excluded_polarity"
        for threshold in thresholds:
            ids = sorted(
                [
                    i
                    for i, c in enumerate(cs)
                    if c["polarity_eligible"]
                    and c["refinement_ok"]
                    and c["strength"] >= threshold
                ],
                key=lambda i: (-cs[i]["strength"], i),
            )
            best = ids[0] if ids else None
            ambiguous = False
            if best is not None:
                ambiguous = any(
                    cs[i]["strength"] >= p["ambiguity_ratio"] * cs[best]["strength"]
                    and abs(
                        cs[i]["offset_from_guide_px"] - cs[best]["offset_from_guide_px"]
                    )
                    >= p["peak_separation_px"]
                    for i in ids[1:]
                )
            decisions.append(
                dict(
                    threshold_dn_per_px=threshold,
                    eligible_indices=ids,
                    chosen_index=best,
                    ambiguous=ambiguous,
                )
            )
        out["variants"].append(
            dict(
                sigma_px=sigma,
                signed_gradient_dn_per_px=gradient.tolist(),
                candidates=cs,
                decisions=decisions,
            )
        )
    base = out["variants"][0]
    bi = base["decisions"][1]["chosen_index"]
    stable = bi is not None
    shifts = []
    for variant in out["variants"]:
        for decision in variant["decisions"]:
            i = decision["chosen_index"]
            delta = None
            if bi is not None and i is not None:
                c = variant["candidates"][i]
                b = base["candidates"][bi]
                delta = c["offset_from_guide_px"] - b["offset_from_guide_px"]
                shifts.append(delta)
                stable = (
                    stable
                    and abs(delta) <= p["stability_px"]
                    and c["sign"] == b["sign"]
                )
            else:
                stable = False
            stable = stable and not decision["ambiguous"]
            decision["offset_change_from_baseline_px"] = delta
        for c in variant["candidates"]:
            if (
                c["polarity_eligible"]
                and c["refinement_ok"]
                and c["strength"] >= thresholds[0]
            ):
                c["status"] = "tentative"
    out.update(
        missing=bi is None,
        ambiguous=any(d["ambiguous"] for v in out["variants"] for d in v["decisions"]),
        sensitivity_failed=not stable,
        sensitivity_max_abs_shift_px=max(map(abs, shifts)) if shifts else None,
    )
    if stable:
        base["candidates"][bi]["status"] = "accepted"
        out["provisional_edge_xy_px"] = base["candidates"][bi]["xy_px"]
    out["reason"] = (
        "algorithm_qualified_pending_visual_check"
        if stable
        else ("no_baseline_eligible_peak" if bi is None else "ambiguous_or_sensitive")
    )
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Bounded provisional pixel-edge observations; no physical scale."
    )
    for name in ("image", "config", "output"):
        ap.add_argument("--" + name, required=True)
    args = ap.parse_args()
    dst = Path(args.output)
    need(not dst.exists() and not dst.is_symlink(), "Output directory already exists")
    cfg_bytes = Path(args.config).read_bytes()
    cfg = json.loads(cfg_bytes)
    image_path = Path(args.image)
    need(image_path.stat().st_size <= CAPS["image_bytes"], "Image byte cap exceeded")
    image_bytes = image_path.read_bytes()
    digest = sha(image_bytes)
    matches = [
        (key, item)
        for key, item in cfg["images"].items()
        if item.get("sha256") == digest
    ]
    need(
        len(matches) == 1,
        "Need exactly one matching SHA256 from the verified manifest; null hashes are not executable",
    )
    image_id, spec = matches[0]
    w, h = spec["dimensions_wh"]
    need(
        isinstance(w, int)
        and isinstance(h, int)
        and 2 <= w <= 6000
        and 2 <= h <= 6000
        and w * h <= CAPS["pixels"],
        "Dimension cap exceeded",
    )
    need(
        cv2.__version__.startswith("4.12.") and np.__version__.startswith("2.2."),
        "Requires OpenCV 4.12.x and NumPy 2.2.x",
    )
    cv2.setNumThreads(1)
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_UNCHANGED)
    need(
        image is not None and image.dtype == np.uint8 and image.shape == (h, w, 3),
        "Expected original dimensions and 8-bit three-channel image",
    )
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    overlay = image.copy()
    p = cfg["parameters"]
    step = p["profile_step_px"]
    spacing = p["station_spacing_px"]
    need(step in (0.5, 1.0) and 4 <= spacing <= 40, "Sampling bounds invalid")
    th = p["thresholds_dn_per_px"]
    sig = p["blur_sigmas_px"]
    need(
        len(th) == 3 and 0 < th[0] < th[1] < th[2] <= 255,
        "Need three positive increasing thresholds",
    )
    need(
        len(sig) == 2 and 0.5 <= sig[0] < sig[1] <= 3,
        "Need two bounded increasing blur sigmas",
    )
    need(
        0 < p["ambiguity_ratio"] <= 1
        and 0 < p["stability_px"] <= 4
        and 1 <= p["peak_separation_px"] <= 4,
        "Decision bounds invalid",
    )
    features = spec["features"]
    need(1 <= len(features) <= CAPS["features"], "Feature count exceeds cap")
    need(
        len({f["id"] for f in features}) == len(features),
        "Duplicate feature identifier",
    )
    observations = []
    scale = np.array([w - 1, h - 1], dtype=float)
    colors = dict(
        accepted=(0, 255, 0),
        tentative=(0, 191, 255),
        rejected=(0, 0, 255),
        excluded_polarity=(255, 0, 255),
    )
    for feature in features:
        polarity = feature.get("gradient_polarity", "either")
        need(
            isinstance(polarity, str) and polarity in POLARITIES,
            "Invalid gradient_polarity",
        )
        guide = np.asarray(feature["guide_uv"], dtype=float)
        box = np.asarray(feature["search_box_uv"], dtype=float)
        need(
            guide.ndim == 2
            and guide.shape[1] == 2
            and 2 <= len(guide) <= 8
            and np.isfinite(guide).all()
            and np.all((guide >= 0) & (guide <= 1)),
            "Invalid guide",
        )
        need(
            box.shape == (4,)
            and np.isfinite(box).all()
            and np.all((box >= 0) & (box <= 1))
            and np.all(box[2:] > box[:2])
            and np.prod(box[2:] - box[:2]) <= 0.08,
            "Invalid or oversized search box",
        )
        need(
            np.all(guide >= box[:2]) and np.all(guide <= box[2:]),
            "Guide outside search box",
        )
        guide = guide * scale
        roi = box * np.tile(scale, 2)
        radius = feature["search_half_width_px"]
        need(
            isinstance(radius, int) and 2 <= radius <= 40,
            "Search radius must be an integer in [2,40]",
        )
        lengths = np.linalg.norm(np.diff(guide, axis=0), axis=1)
        need(
            np.all(lengths > 0)
            and sum(math.ceil(v / spacing) for v in lengths)
            <= CAPS["profiles_per_feature"],
            "Degenerate guide or station cap exceeded",
        )
        cv2.polylines(
            overlay, [np.rint(guide).astype(np.int32)], False, (255, 128, 0), 1
        )
        samples = []
        for segment, (a, b, length) in enumerate(zip(guide[:-1], guide[1:], lengths)):
            tangent = (b - a) / length
            normal = np.array([-tangent[1], tangent[0]])
            for fraction in np.linspace(
                0, 1, math.ceil(length / spacing), endpoint=False
            ):
                origin = a + fraction * (b - a)
                s = sample(gray, origin, normal, roi, radius, p, polarity)
                s.update(
                    station_index=len(samples),
                    segment_index=segment,
                    segment_fraction=float(fraction),
                )
                samples.append(s)
                cs = s["variants"][0]["candidates"] if s["variants"] else []
                for status in (
                    "excluded_polarity",
                    "rejected",
                    "tentative",
                    "accepted",
                ):
                    for c in cs:
                        if c["status"] == status:
                            cv2.circle(
                                overlay,
                                tuple(np.rint(c["xy_px"]).astype(int)),
                                2,
                                colors[status],
                                -1,
                            )
                if s["missing"]:
                    cv2.drawMarker(
                        overlay,
                        tuple(np.rint(origin).astype(int)),
                        (255, 255, 0),
                        cv2.MARKER_CROSS,
                        6,
                        1,
                    )
        observations.append(
            dict(
                id=feature["id"],
                proposal=feature,
                gradient_polarity=polarity,
                samples=samples,
            )
        )
    frame = dict(
        schema_version="wright.image-coordinate-frame/1",
        image_sha256=digest,
        width_px=w,
        height_px=h,
        origin="top-left",
        axes="x-right-y-down",
        pixel_reference="centers",
        units="original-image pixels",
        dimensions_wh=[w, h],
        integer_pixel_centers=True,
        normalized_mapping="x=u*(width-1); y=v*(height-1)",
        orientation="stored raster; IMREAD_UNCHANGED ignores EXIF orientation",
        resizing=False,
        distortion_correction=False,
    )
    report = dict(
        schema=VERSION,
        image_id=image_id,
        image_sha256=digest,
        config_sha256=sha(cfg_bytes),
        source_sha256=sha(Path(__file__).read_bytes()),
        runtime=dict(
            opencv=cv2.__version__,
            numpy=np.__version__,
            python=platform.python_version(),
        ),
        frame=frame,
        parameters=p,
        safety_caps=CAPS,
        configuration=cfg,
        observations=observations,
        polarity_semantics=POLARITY_SEMANTICS,
        semantics="Accepted means algorithm-qualified pixel candidate only; all component identifications and traces require visual checking. Polarity is a feature-association hypothesis, not confidence or accuracy. No joining or gap filling.",
        overlay_legend=dict(
            green="accepted baseline candidate",
            amber="tentative baseline candidate",
            red="rejected baseline candidate",
            magenta="baseline candidate excluded by polarity",
            blue="unverified guide",
            cyan="missing baseline at guide station",
        ),
    )
    text = json.dumps(report, indent=2, allow_nan=False)
    dst.mkdir(parents=False, exist_ok=False)
    need(
        cv2.imwrite(str(dst / "overlay.png"), overlay),
        "Overlay encoding failed; output is incomplete",
    )
    (dst / "observations.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
