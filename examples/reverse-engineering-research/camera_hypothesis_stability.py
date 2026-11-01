"""Measure image-prediction spread among calibration-feasible camera hypotheses.

No fitting, pose selection, geometry mutation, executor or acceptance authority.
All predictions must refer to one exact artifact and original image frame.
"""

import math
import re

from core.image_coordinates import ImageCoordinateFrame


def prediction_spread(hypotheses, *, frame, artifact_sha256, calibration_band_px):
    frame = ImageCoordinateFrame.model_validate(frame)
    if not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
        raise ValueError("An exact geometry artifact hash is required")

    def number(value):
        return type(value) in (int, float) and math.isfinite(value)

    if not number(calibration_band_px) or calibration_band_px <= 0:
        raise ValueError("Retain the explicit positive calibration reading band")
    if not 1 <= len(hypotheses) <= 64:
        raise ValueError("Supply one to 64 explicitly attributed hypotheses")
    ids = set()
    feasible = []
    excluded = []
    all_observations = set()
    for hypothesis in hypotheses:
        identity = hypothesis["id"]
        if not isinstance(identity, str) or not identity or identity in ids:
            raise ValueError("Hypothesis identities must be unique nonempty strings")
        ids.add(identity)
        if (
            hypothesis["artifact_sha256"] != artifact_sha256
            or hypothesis["frame_id"] != frame.identifier()
        ):
            raise ValueError(
                "Camera sensitivity must use the same exact geometry and image frame"
            )
        maximum = hypothesis["calibration_maximum_px"]
        if not number(maximum) or maximum < 0:
            raise ValueError("Calibration residual must be finite and nonnegative")
        predictions = hypothesis["predictions"]
        if not isinstance(predictions, dict) or len(predictions) > 4096:
            raise ValueError("Supply a bounded mapping of named image observations")
        for key, point in predictions.items():
            if (
                not isinstance(key, str)
                or not key
                or len(point) != 2
                or not all(number(p) for p in point)
            ):
                raise ValueError(
                    "Each prediction needs an explicit identity and finite original-frame XY"
                )
            if not (0 <= point[0] < frame.width_px and 0 <= point[1] < frame.height_px):
                raise ValueError("Prediction is outside the declared original raster")
        all_observations.update(predictions)
        if maximum <= calibration_band_px:
            feasible.append(hypothesis)
        else:
            excluded.append(dict(id=identity, calibration_maximum_px=maximum))
    rows = []
    for key in sorted(all_observations):
        witnesses = [
            dict(id=h["id"], xy=h["predictions"][key])
            for h in feasible
            if key in h["predictions"]
        ]
        pairs = [
            (math.dist(a["xy"], b["xy"]), a["id"], b["id"])
            for i, a in enumerate(witnesses)
            for b in witnesses[i + 1 :]
        ]
        maximum = max(pairs) if pairs else None
        rows.append(
            dict(
                observation_id=key,
                witnesses=witnesses,
                missing_feasible_hypotheses=[
                    h["id"] for h in feasible if key not in h["predictions"]
                ],
                prediction_diameter_px=maximum[0] if maximum else None,
                diameter_witness_ids=list(maximum[1:]) if maximum else [],
            )
        )
    spreads = [
        r["prediction_diameter_px"]
        for r in rows
        if r["prediction_diameter_px"] is not None
    ]
    return dict(
        image_frame=frame.model_dump(mode="json"),
        frame_id=frame.identifier(),
        artifact_sha256=artifact_sha256,
        calibration_band_px=calibration_band_px,
        feasible_hypothesis_ids=[h["id"] for h in feasible],
        excluded_hypotheses=excluded,
        observations=rows,
        maximum_prediction_diameter_px=max(spreads) if spreads else None,
        scope="Finite camera-hypothesis witnesses only; not exhaustive uncertainty, physical calibration or engineering acceptance.",
    )
