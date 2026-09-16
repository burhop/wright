"""Confined native geometry and retained-field producer for validator demos."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil

from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode, export_step
from mcp.server.fastmcp import FastMCP


WORKSPACE = Path(os.environ["WRIGHT_PROCESS_VALIDATION_WORKSPACE"]).resolve(strict=True)
SERVER = FastMCP("wright-process-validation-engineering-demo")


def _path(relative: str) -> Path:
    if not isinstance(relative, str) or not relative or len(relative) > 256:
        raise ValueError("A bounded workspace-relative path is required")
    value = PurePosixPath(relative)
    if value.is_absolute() or any(part in {".", ".."} or part.startswith(".") for part in value.parts):
        raise ValueError("Hidden, absolute and parent paths are unavailable")
    target = (WORKSPACE / Path(*value.parts)).resolve()
    if target == WORKSPACE or not target.is_relative_to(WORKSPACE):
        raise ValueError("Path escapes the isolated workspace")
    return target


def _receipt(path: Path) -> dict:
    content = path.read_bytes()
    return {
        "path": path.relative_to(WORKSPACE).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


@SERVER.tool()
def create_jig_step(
    h1_x_mm: float,
    h2_x_mm: float,
    output_path: str = "jig.step",
) -> dict:
    """Create a new 200x60x12 mm plate STEP with 10.2 mm seats at y=30 mm.

    This isolated demonstration operation accepts only finite H1/H2 x locations
    within the plate and writes one exact workspace file. It has no application,
    device, network, supplier, or campaign effects.
    """

    import math

    if type(h1_x_mm) not in {int, float} or type(h2_x_mm) not in {int, float}:
        raise ValueError("Seat locations must be numeric")
    h1_x_mm, h2_x_mm = float(h1_x_mm), float(h2_x_mm)
    if not all(math.isfinite(value) and 10 <= value <= 190 for value in (h1_x_mm, h2_x_mm)):
        raise ValueError("Seat locations must be finite and remain within the plate")
    if h2_x_mm - h1_x_mm < 20:
        raise ValueError("Seat locations must remain distinct")
    output = _path(output_path)
    if output.name != "jig.step" or output.parent != WORKSPACE:
        raise ValueError("The demonstration output must be jig.step at workspace root")

    with BuildPart() as jig:
        Box(200, 60, 12, align=(Align.MIN, Align.MIN, Align.MIN))
        with Locations((h1_x_mm, 30, 0), (h2_x_mm, 30, 0)):
            Cylinder(
                5.1,
                12,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )
    temporary = output.with_name(output.stem + ".tmp" + output.suffix)
    temporary.unlink(missing_ok=True)
    export_step(jig.part, temporary)
    temporary.replace(output)
    return {
        "operation": "create_jig_step",
        "seat_centers_mm": [[h1_x_mm, 30.0], [h2_x_mm, 30.0]],
        "seat_diameter_mm": 10.2,
        "output": _receipt(output),
    }


@SERVER.tool()
def stage_heat_outputs() -> dict:
    """Copy five hash-pinned retained heat outputs into the isolated process."""

    names = {
        "baseline-coarse-temperature.csv": "baseline-coarse.csv",
        "baseline-fine-temperature.csv": "baseline-fine.csv",
        "revision-coarse-temperature.csv": "revision-coarse.csv",
        "revision-fine-temperature.csv": "revision-fine.csv",
        "sizing-decision.json": "sizing-decision.json",
    }
    receipts = []
    for source_name, output_name in names.items():
        source = _path("inputs/" + source_name)
        output = _path(output_name)
        if not source.is_file() or source.parent != WORKSPACE / "inputs":
            raise ValueError("The required isolated heat input is missing")
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.unlink(missing_ok=True)
        shutil.copyfile(source, temporary)
        temporary.replace(output)
        receipts.append(_receipt(output))
    return {"operation": "stage_heat_outputs", "outputs": receipts}


if __name__ == "__main__":
    SERVER.run(transport="stdio")
