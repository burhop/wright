import hashlib
import json

SOURCE_PATH = r"C:\Users\markb\.codex\visualizations\2026\09\24\01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056\t047-heat-repeat-013\process-proofs\heat-spreader-sizing\repeatable-default-013\outputs\63b639c7a8f446cd90a9285921ab9072\plate-source.py"
OUTPUT_DIR = r"C:\Users\markb\.codex\visualizations\2026\09\24\01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056\t047-heat-repeat-013\process-proofs\heat-spreader-sizing\repeatable-default-013\outputs\63b639c7a8f446cd90a9285921ab9072"
MEASUREMENTS_PATH = r"C:\Users\markb\.codex\visualizations\2026\09\24\01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056\t047-heat-repeat-013\process-proofs\heat-spreader-sizing\repeatable-default-013\outputs\63b639c7a8f446cd90a9285921ab9072\geometry-measurements.json"

if not callable(globals().get("show_object")):
    raise RuntimeError("AgentCAD injected show_object is required")


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def measured_dimensions(shape):
    bounds = shape.bounding_box()
    return {
        "x": float(bounds.max.X - bounds.min.X),
        "y": float(bounds.max.Y - bounds.min.Y),
        "z": float(bounds.max.Z - bounds.min.Z),
    }


def main():
    specifications = (
        ("baseline_40", 100.0, 40.0, 2.0),
        ("revision_60", 100.0, 60.0, 2.0),
    )
    measurements = {"cases": {}}

    for case_id, length, width, thickness in specifications:
        actual_shape = Box(
            length,
            width,
            thickness,
            align=(Align.MIN, Align.MIN, Align.MIN),
        )
        if not actual_shape.is_valid:
            raise RuntimeError(f"Invalid generated shape for {case_id}")

        show_object(actual_shape)

        step_path = OUTPUT_DIR + "\\" + case_id + ".step"
        export_step(actual_shape, step_path)

        reopened_shape = import_step(step_path)
        reopened_shape = Compound(reopened_shape) if isinstance(reopened_shape, list) else reopened_shape
        if reopened_shape is None or not reopened_shape.is_valid:
            raise RuntimeError(f"Invalid reopened STEP shape for {case_id}")

        measurements["cases"][case_id] = {
            "dimensions_mm": measured_dimensions(reopened_shape),
            "step_sha256": file_sha256(step_path),
        }

    with open(MEASUREMENTS_PATH, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(measurements, stream, indent=2, sort_keys=True)
        stream.write("\n")


main()
