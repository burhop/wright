"""Build and inspect the two declared heat-spreader plate candidates."""

import hashlib
import json
from pathlib import Path

SOURCE_PATH = Path(r"C:\Users\markb\.codex\visualizations\2026\09\24\01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056\t047-heat-live-005\process-proofs\heat-spreader-sizing\live-default-model-002\outputs\plate-source.py")
OUTPUT_DIRECTORY = Path(r"C:\Users\markb\.codex\visualizations\2026\09\24\01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056\t047-heat-live-005\process-proofs\heat-spreader-sizing\live-default-model-002\outputs")
MEASUREMENTS_PATH = Path(r"C:\Users\markb\.codex\visualizations\2026\09\24\01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056\t047-heat-live-005\process-proofs\heat-spreader-sizing\live-default-model-002\outputs\geometry-measurements.json")

CASES = (
    ("baseline_40", 40.0),
    ("revision_60", 60.0),
)


def build_plate(width_mm):
    shape = Box(
        100.0,
        width_mm,
        2.0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    if not shape.is_valid:
        raise RuntimeError(f"Invalid plate geometry for width {width_mm} mm")
    return shape


def inspect_export(case_id, actual_shape):
    step_path = OUTPUT_DIRECTORY / f"{case_id}.step"
    export_step(actual_shape, str(step_path))
    if not step_path.is_file():
        raise RuntimeError(f"STEP export was not created: {step_path}")

    reopened_shape = import_step(str(step_path))
    if not reopened_shape.is_valid:
        raise RuntimeError(f"Reopened STEP is invalid: {step_path}")

    bounds = reopened_shape.bounding_box()
    step_bytes = step_path.read_bytes()
    return {
        "dimensions_mm": {
            "x": float(bounds.size.X),
            "y": float(bounds.size.Y),
            "z": float(bounds.size.Z),
        },
        "step_sha256": hashlib.sha256(step_bytes).hexdigest(),
    }


def main():
    if not callable(globals().get("show_object")):
        raise RuntimeError("AgentCAD injected show_object is required")

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    measurements = {"cases": {}}

    for case_id, width_mm in CASES:
        actual_shape = build_plate(width_mm)
        show_object(actual_shape)
        measurements["cases"][case_id] = inspect_export(case_id, actual_shape)

    MEASUREMENTS_PATH.write_text(
        json.dumps(measurements, indent=2) + "\n",
        encoding="utf-8",
    )


main()
