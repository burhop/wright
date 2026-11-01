"""Measure candidate crop/view dependence; never establish camera or CAD accuracy.

Read two images, preserve their identities, fit image transforms to descriptor
matches, and retain inspectable correspondences. No tool dispatch or workflow
state is owned here. Requires separately installed OpenCV and NumPy.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def read_image(path, max_dimension):
    data = path.read_bytes()
    original = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if original is None:
        raise ValueError(f"Unable to decode {path.name}")
    height, width = original.shape[:2]
    scale = min(1.0, max_dimension / max(height, width))
    image = cv2.resize(
        original,
        (round(width * scale), round(height * scale)),
        interpolation=cv2.INTER_AREA,
    )
    # Actual rounded resize factors, not the nominal scalar.
    factors = np.array([image.shape[1] / width, image.shape[0] / height])
    return (
        image,
        factors,
        {
            "path": str(path.resolve()),
            "sha256": hashlib.sha256(data).hexdigest(),
            "original_size_px": [width, height],
            "analysis_size_px": [image.shape[1], image.shape[0]],
            "original_to_analysis_scale_xy": factors.tolist(),
        },
    )


def measure(first, second, output, max_dimension=1600):
    output.mkdir(parents=True, exist_ok=False)
    cv2.setRNGSeed(78237)
    a, scale_a, identity_a = read_image(first, max_dimension)
    b, scale_b, identity_b = read_image(second, max_dimension)
    detector = cv2.SIFT_create(nfeatures=5000)
    ka, da = detector.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), None)
    kb, db = detector.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None)
    matcher = cv2.BFMatcher(cv2.NORM_L2)

    def ratio_matches(x, y):
        if x is None or y is None or len(y) < 2:
            return {}
        return {
            m.queryIdx: m
            for pair in matcher.knnMatch(x, y, k=2)
            if len(pair) == 2
            for m, n in [pair]
            if m.distance < 0.7 * n.distance
        }

    forward, reverse = ratio_matches(da, db), ratio_matches(db, da)
    matches = [
        m
        for m in forward.values()
        if m.trainIdx in reverse and reverse[m.trainIdx].trainIdx == m.queryIdx
    ]
    src = np.float32([ka[m.queryIdx].pt for m in matches]).reshape(-1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in matches]).reshape(-1, 2)
    report = {
        "scope": "Image-dependence diagnostic, not geometric or calibration acceptance",
        "sources": [identity_a, identity_b],
        "implementation": {"opencv": cv2.__version__, "numpy": np.__version__},
        "method": {
            "features": "SIFT",
            "max_features": 5000,
            "matching": "mutual nearest ratio 0.7",
            "ransac_threshold_analysis_px": 2.0,
            "seed": 78237,
            "max_dimension": max_dimension,
        },
        "keypoints": [len(ka), len(kb)],
        "mutual_matches": len(matches),
        "fits": {},
        "limits": [
            "A fitted image transform is not a calibrated camera or a three-dimensional reconstruction.",
            "Shared backgrounds, planar regions and similar rendered geometry can match despite different views.",
            "Few matches do not establish independence; specular and textureless surfaces can fail matching.",
            "Review correspondence locations and source provenance before assigning validation groups.",
        ],
    }
    visual_mask = None
    if len(matches) >= 4:
        affine, amask = cv2.estimateAffinePartial2D(
            src,
            dst,
            method=cv2.RANSAC,
            ransacReprojThreshold=2.0,
            maxIters=10000,
            confidence=0.999,
            refineIters=10,
        )
        homography, hmask = cv2.findHomography(
            src, dst, cv2.RANSAC, 2.0, maxIters=10000, confidence=0.999
        )
        for name, matrix, mask in [
            ("similarity", affine, amask),
            ("homography", homography, hmask),
        ]:
            if matrix is None or mask is None:
                report["fits"][name] = {"status": "unavailable"}
                continue
            h = np.vstack([matrix, [0, 0, 1]]) if matrix.shape == (2, 3) else matrix
            predicted = cv2.perspectiveTransform(src.reshape(-1, 1, 2), h).reshape(
                -1, 2
            )
            inliers = mask.ravel().astype(bool)
            residuals = np.linalg.norm((predicted - dst) / scale_b, axis=1)
            report["fits"][name] = {
                "status": "measured",
                "matrix_analysis_pixels": h.tolist(),
                "inliers": int(inliers.sum()),
                "inlier_fraction": float(inliers.mean()),
                "inlier_residual_target_original_px": {
                    "median": float(np.median(residuals[inliers])),
                    "p95": float(np.percentile(residuals[inliers], 95)),
                    "max": float(np.max(residuals[inliers])),
                },
                "source_inlier_bbox_original_px": [
                    src[inliers].min(axis=0).tolist(),
                    src[inliers].max(axis=0).tolist(),
                ],
            }
            report["fits"][name]["source_inlier_bbox_original_px"] = (
                np.array(report["fits"][name]["source_inlier_bbox_original_px"])
                / scale_a
            ).tolist()
            if name == "similarity":
                visual_mask = inliers.tolist()
    report["correspondences"] = [
        {
            "source_original_px": (p / scale_a).tolist(),
            "target_original_px": (q / scale_b).tolist(),
            "descriptor_distance": float(m.distance),
        }
        for p, q, m in zip(src, dst, matches)
    ]
    report["source_bytes_unchanged"] = all(
        hashlib.sha256(Path(x["path"]).read_bytes()).hexdigest() == x["sha256"]
        for x in report["sources"]
    )
    assert report["source_bytes_unchanged"]
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Diagnostic figure only. Original images remain untouched.
    chosen = [
        m for i, m in enumerate(matches) if visual_mask is None or visual_mask[i]
    ][:60]
    figure = cv2.drawMatches(
        a, ka, b, kb, chosen, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
    )
    ok, encoded = cv2.imencode(".png", figure)
    if not ok:
        raise RuntimeError("Unable to encode diagnostic figure")
    (output / "correspondences.png").write_bytes(encoded.tobytes())
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = measure(args.first, args.second, args.output)
    print(
        json.dumps(
            {
                "mutual_matches": result["mutual_matches"],
                "fits": result["fits"],
                "source_bytes_unchanged": result["source_bytes_unchanged"],
            }
        )
    )
