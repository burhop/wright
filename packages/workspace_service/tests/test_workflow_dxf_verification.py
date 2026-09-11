import asyncio
import hashlib
import json
import math
from pathlib import Path

import pytest

from workspace_service.workflow_dxf_verification import verify_flat_dxf
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError
from packages.workspace_service.tests.test_workflow_cad import runner, settings


def entity(name, layer, fields):
    return [(0, name), (8, layer), *fields]


def line(a, b, layer="OUTER_LOOP"):
    return entity("LINE", layer, [(10, a[0]), (20, a[1]), (11, b[0]), (21, b[1])])


def rectangle(width=80, height=100, layer="OUTER_LOOP"):
    points = [(0, 0), (width, 0), (width, height), (0, height)]
    return sum([line(points[i], points[(i + 1) % 4], layer) for i in range(4)], [])


def circle(x=20, y=20, radius=3, layer="INTERIOR_LOOPS"):
    return entity("CIRCLE", layer, [(10, x), (20, y), (40, radius)])


def dxf(geometry=None, units=4, measurement=1):
    header = [(0, "SECTION"), (2, "HEADER"), (9, "$ACADVER"), (1, "AC1014")]
    if units is not None:
        header += [(9, "$INSUNITS"), (70, units)]
    if measurement is not None:
        header += [(9, "$MEASUREMENT"), (70, measurement)]
    pairs = [
        *header,
        (0, "ENDSEC"),
        (0, "SECTION"),
        (2, "ENTITIES"),
        *(geometry if geometry is not None else rectangle() + circle()),
        (0, "ENDSEC"),
        (0, "EOF"),
    ]
    return "".join(f"{code}\n{value}\n" for code, value in pairs).encode()


def verify(tmp_path, data):
    path = tmp_path / "flat.dxf"
    path.write_bytes(data)
    return verify_flat_dxf(path, relative_path="flat.dxf")


def codes(report, key):
    return {issue["code"] for issue in report[key]}


def test_verified_mm_contour_holes_and_bends_have_exact_file_identity(tmp_path):
    data = dxf(
        rectangle()
        + circle()
        + circle(60, 80)
        + line((0, 50), (80, 50), "UP_CENTERLINES")
    )
    report = verify(tmp_path, data)
    assert report["status"] == "pass"
    assert report["file"]["sha256"] == hashlib.sha256(data).hexdigest()
    assert report["file"]["path"] == "flat.dxf"
    assert report["units"]["source"] == "$INSUNITS"
    assert report["bounds_mm"]["size"] == [80, 100]
    assert report["contours"]["closed_components"] == 1
    assert report["holes"]["diameters_mm"] == [6, 6]
    assert report["bends"]["centerline_count"] == 1
    assert report["bends"]["lengths_mm"] == [80]
    assert "Supplier acceptance and manufacturing suitability" in report["not_checked"]


@pytest.mark.parametrize("units", [None, 0, 999])
def test_measurement_metric_flag_does_not_establish_mm(tmp_path, units):
    report = verify(tmp_path, dxf(units=units, measurement=1))
    assert report["status"] == "inconclusive"
    assert "units_unverified" in codes(report, "unverified")
    assert report["units"]["measurement"] == 1
    assert report["bounds_raw"]["size"] == [80, 100]
    assert report["bounds_mm"] is None


def test_explicit_inches_are_scaled_without_changing_file(tmp_path):
    data = dxf(rectangle(2, 3) + circle(0.5, 0.5, 0.1), units=1)
    report = verify(tmp_path, data)
    assert report["status"] == "pass"
    assert report["bounds_mm"]["size"] == pytest.approx([50.8, 76.2])
    assert (tmp_path / "flat.dxf").read_bytes() == data


@pytest.mark.parametrize(
    "geometry, expected",
    [
        (rectangle()[:-6], "open_contour"),
        (rectangle() + circle(radius=-1), "invalid_geometry"),
        (rectangle() + circle(x=float("nan")), "invalid_geometry"),
        (rectangle() + circle(x=float("inf")), "invalid_geometry"),
        (line((0, 0), (10, 0)), "open_contour"),
        (rectangle() + line((80, 0), (0, 0)), "overlapping_cuts"),
        (
            line((0, 0), (10, 10))
            + line((10, 10), (0, 10))
            + line((0, 10), (10, 0))
            + line((10, 0), (0, 0)),
            "intersecting_cuts",
        ),
        (rectangle() + circle(1, 20, 3), "intersecting_hole"),
        (rectangle() + circle(100, 20, 3), "cut_outside_outer"),
        (rectangle() + circle() + circle(24, 20, 3), "intersecting_holes"),
    ],
)
def test_invalid_cut_geometry_cannot_pass(tmp_path, geometry, expected):
    report = verify(tmp_path, dxf(geometry))
    assert report["status"] == "fail"
    assert expected in codes(report, "errors")


@pytest.mark.parametrize("data", [b"0\nSECTION\n2", dxf()[:-6], b"not a dxf\nfile\n"])
def test_malformed_file_is_evidenced_failure(tmp_path, data):
    report = verify(tmp_path, data)
    assert report["status"] == "fail"
    assert report["file"]["sha256"] == hashlib.sha256(data).hexdigest()


def test_overflowing_derived_bend_length_fails_with_writable_report(tmp_path):
    report = verify(
        tmp_path, dxf(rectangle() + line((-1e308, 0), (1e308, 0), "UP_CENTERLINES"))
    )
    assert report["status"] == "fail"
    json.dumps(report, allow_nan=False)


@pytest.mark.parametrize(
    "geometry, expected",
    [
        (
            rectangle() + entity("SPLINE", "INTERIOR_LOOPS", [(10, 1), (20, 2)]),
            "unsupported_geometry",
        ),
        (rectangle(layer="0"), "unknown_cut_layer"),
        (rectangle() + circle() + circle(20, 20, 1), "nested_circular_cuts"),
    ],
)
def test_unverified_geometry_never_silently_dropped(tmp_path, geometry, expected):
    report = verify(tmp_path, dxf(geometry))
    assert report["status"] == "inconclusive"
    assert expected in codes(report, "unverified")


@pytest.mark.parametrize("legacy", [False, True])
def test_straight_polyline_contour_supported(tmp_path, legacy):
    points = [(0, 0), (80, 0), (80, 100), (0, 100)]
    if legacy:
        geometry = entity("POLYLINE", "OUTER_LOOP", [(70, 1)])
        for x, y in points:
            geometry += entity("VERTEX", "OUTER_LOOP", [(10, x), (20, y)])
        geometry += [(0, "SEQEND")]
    else:
        fields = [(70, 1), (90, 4)]
        for x, y in points:
            fields += [(10, x), (20, y), (40, 0), (41, 0)]
        geometry = entity("LWPOLYLINE", "OUTER_LOOP", fields)
    report = verify(tmp_path, dxf(geometry + circle()))
    assert report["status"] == "pass"
    assert report["bounds_mm"]["size"] == [80, 100]


def test_arc_metrics_are_retained_but_curve_intersections_are_inconclusive(tmp_path):
    arcs = entity("ARC", "OUTER_LOOP", [(10, 0), (20, 0), (40, 10), (50, 0), (51, 180)])
    arcs += entity(
        "ARC", "OUTER_LOOP", [(10, 0), (20, 0), (40, 10), (50, 180), (51, 360)]
    )
    report = verify(tmp_path, dxf(arcs))
    assert report["status"] == "inconclusive"
    assert report["bounds_mm"]["size"] == pytest.approx([20, 20])
    assert "curved_contour_intersections" in codes(report, "unverified")


@pytest.mark.parametrize("units, succeeds", [(4, True), (None, False)])
def test_cad_export_gate_preserves_report_and_stops_later_export(
    tmp_path, units, succeeds
):
    cfg = settings()
    cfg.update(
        save_native=False,
        exports=[
            {"format": "flat_dxf", "path": "flat.dxf", "port": "flat"},
            {"format": "step", "path": "later.step", "port": "step"},
        ],
    )
    gateway, run = runner(tmp_path, cfg)
    original_call = gateway.call_tool
    events = []

    async def emit(kind, **event):
        events.append({"kind": kind, **event})

    run.emit = emit

    async def call(session, request, name, arguments, **kwargs):
        result = await original_call(session, request, name, arguments, **kwargs)
        if name == "cad.list_providers":
            result.structured_content["result"][0]["capabilities"]["exports"].append(
                "flat_dxf"
            )
        if name == "cad.export_document" and arguments["format"] == "flat_dxf":
            Path(arguments["outputPath"]).write_bytes(dxf(units=units))
        return result

    gateway.call_tool = call

    async def scenario():
        await run.start()
        if succeeds:
            _, files = await run.finish()
            descriptor = next(
                file for file in files if file["output_path"] == "flat.dxf"
            )
            assert descriptor["verification"]["status"] == "pass"
            assert descriptor["verification_report"]["sha256"]
        else:
            with pytest.raises(WorkflowSourceExecutionError) as error:
                await run.finish()
            assert error.value.code == "CAD_EXPORT_VERIFICATION_FAILED"
            assert "millimeters" in str(error.value)
            assert not (tmp_path / "later.step").exists()
            assert not run.outputs

    asyncio.run(scenario())
    report = json.loads((tmp_path / "flat.dxf.verification.json").read_text())
    assert report["status"] == ("pass" if succeeds else "inconclusive")
    assert (
        report["file"]["sha256"]
        == hashlib.sha256((tmp_path / "flat.dxf").read_bytes()).hexdigest()
    )
    assert any(event.get("export_verification") for event in events)


def native_evidence(path, *, width=80, height=100, radius=3, scale=1):
    """Independent physical measurements for a rectangle with one round hole."""
    return {
        "evidenceStatus": {"provenance": "observed", "disposition": "not_evaluated"},
        "nativeFlatUpToDate": True,
        "unit": "mm",
        "providerId": "solid_edge",
        "documentId": "original",
        "outputPath": str(path),
        "outputSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "netAreaMm2": (width * height - math.pi * radius**2) * scale**2,
        "outerPerimeterMm": 2 * (width + height) * scale,
        "innerPerimeterMm": 2 * math.pi * radius * scale,
        "innerLoopCount": 1,
        "selectedFaceIds": ["face-1", "face-2"],
        "nativeMethods": ["Face.Area", "Loop.Edges"],
    }


def verify_with_native(tmp_path, *, units=None, scale=1, patch=None, geometry=None):
    path = tmp_path / "flat.dxf"
    path.write_bytes(dxf(geometry, units=units))
    evidence = native_evidence(path, scale=scale)
    evidence.update(patch or {})
    report = verify_flat_dxf(
        path, native_evidence=evidence, provider_id="solid_edge", document_id="original"
    )
    json.dumps(
        report, allow_nan=False
    )  # Evidence remains writable even for bad provider values.
    return report


@pytest.mark.parametrize(
    "units, scale", [(None, 1), (None, 25.4), (0, 1), (4, 1), (1, 25.4), (5, 10)]
)
def test_native_flat_metrics_establish_unique_scale_without_rewriting_dxf(
    tmp_path, units, scale
):
    data = dxf(units=units)
    report = verify_with_native(tmp_path, units=units, scale=scale)
    assert report["status"] == "pass"
    assert report["native_geometry"]["status"] == "pass"
    assert report["native_geometry"]["scale_to_mm"] == scale
    assert report["native_geometry"]["tolerances"] == {
        "length_abs_mm": 1e-4,
        "area_abs_mm2": 1e-3,
        "relative": 1e-6,
    }
    assert report["bounds_mm"]["size"] == pytest.approx([80 * scale, 100 * scale])
    assert report["units"]["source"] == (
        "hash_bound_native_flat_geometry" if units in (None, 0) else "$INSUNITS"
    )
    assert (tmp_path / "flat.dxf").read_bytes() == data
    assert "Native flat-model geometry equivalence" not in report["not_checked"]
    assert "Design-dependent dimensions and feature counts" in report["not_checked"]
    assert "Supplier acceptance and manufacturing suitability" in report["not_checked"]


@pytest.mark.parametrize(
    "patch, expected",
    [
        ({"providerId": "another_provider"}, "native_document_mismatch"),
        ({"documentId": "other"}, "native_document_mismatch"),
        ({"outputPath": "unrelated.dxf"}, "native_export_mismatch"),
        ({"outputSha256": "0" * 64}, "native_export_mismatch"),
        ({"innerLoopCount": 2}, "native_loop_mismatch"),
        ({"netAreaMm2": 9000}, "native_geometry_mismatch"),
        ({"outerPerimeterMm": 400}, "native_geometry_mismatch"),
        ({"innerPerimeterMm": 1}, "native_geometry_mismatch"),
    ],
)
def test_native_evidence_must_match_bound_export_and_all_geometry_metrics(
    tmp_path, patch, expected
):
    report = verify_with_native(tmp_path, patch=patch)
    assert report["status"] == "fail"
    assert expected in codes(report, "errors")
    assert report["units"]["scale_to_mm"] is None


@pytest.mark.parametrize(
    "patch",
    [
        {
            "evidenceStatus": {
                "provenance": "ai_assertion",
                "disposition": "not_evaluated",
            }
        },
        {
            "evidenceStatus": {
                "provenance": "unavailable",
                "disposition": "not_evaluated",
            }
        },
        {"evidenceStatus": {"provenance": "observed", "disposition": "approved"}},
        {"nativeFlatUpToDate": False},
        {"nativeFlatUpToDate": "true"},
        {"unit": "m"},
    ],
)
def test_native_measurement_provenance_and_up_to_date_flat_are_required(
    tmp_path, patch
):
    report = verify_with_native(tmp_path, patch=patch)
    assert report["status"] == "inconclusive"
    assert "native_evidence_unavailable" in codes(report, "unverified")
    assert report["units"]["scale_to_mm"] is None


@pytest.mark.parametrize(
    "patch",
    [
        {"netAreaMm2": float("nan")},
        {"outerPerimeterMm": float("inf")},
        {"innerPerimeterMm": -1},
        {"netAreaMm2": None},
        {"netAreaMm2": True},
        {"netAreaMm2": 0},
        {"innerLoopCount": 1.0},
    ],
)
def test_invalid_native_numbers_fail_with_serializable_evidence(tmp_path, patch):
    report = verify_with_native(tmp_path, patch=patch)
    assert report["status"] == "fail"
    assert "invalid_native_measurement" in codes(report, "errors")


def test_explicit_units_cannot_contradict_native_scale(tmp_path):
    report = verify_with_native(tmp_path, units=1, scale=1)
    assert report["status"] == "fail"
    assert "native_unit_conflict" in codes(report, "errors")


def test_unknown_explicit_unit_is_not_overridden(tmp_path):
    report = verify_with_native(tmp_path, units=999)
    assert report["status"] == "inconclusive"
    assert "unsupported_explicit_units" in codes(report, "unverified")


def test_native_oracle_does_not_approve_unknown_geometry(tmp_path):
    report = verify_with_native(
        tmp_path,
        geometry=rectangle()
        + circle()
        + entity("SPLINE", "INTERIOR_LOOPS", [(10, 1), (20, 2)]),
    )
    assert report["status"] == "inconclusive"
    assert "native_comparison_unsupported" in codes(report, "unverified")
    assert report["units"]["scale_to_mm"] is None


def test_native_oracle_metrics_ignore_edge_order_direction_and_rotation(tmp_path):
    # An 80x100 rectangle, rotated 90 degrees and translated, with shuffled and
    # reversed edge directions. Its area and perimeter are still unchanged.
    geometry = line((1000, 1000), (1000, 1080)) + line((900, 1080), (900, 1000))
    geometry += line((1000, 1000), (900, 1000)) + line((900, 1080), (1000, 1080))
    geometry += circle(980, 1020)
    report = verify_with_native(tmp_path, geometry=geometry)
    assert report["status"] == "pass"
    assert report["bounds_mm"]["size"] == [100, 80]


def test_ambiguous_tiny_geometry_does_not_guess_units(tmp_path):
    path = tmp_path / "tiny.dxf"
    path.write_bytes(dxf(rectangle(1e-6, 1e-6), units=None))
    evidence = native_evidence(path, width=1e-6, height=1e-6, radius=0)
    evidence["innerLoopCount"] = 0
    report = verify_flat_dxf(
        path, native_evidence=evidence, provider_id="solid_edge", document_id="original"
    )
    assert report["status"] == "inconclusive"
    assert "native_geometry_mismatch" in codes(report, "unverified")


@pytest.mark.parametrize("spoof_document", [False, True])
def test_cad_gate_uses_actual_export_report_for_native_scale_and_publishes_evidence(
    tmp_path, spoof_document
):
    cfg = settings()
    cfg.update(
        save_native=False,
        exports=[{"format": "flat_dxf", "path": "flat.dxf", "port": "flat"}],
    )
    gateway, run = runner(tmp_path, cfg)
    original_call = gateway.call_tool

    async def call(session, request, name, arguments, **kwargs):
        result = await original_call(session, request, name, arguments, **kwargs)
        if name == "cad.list_providers":
            result.structured_content["result"][0]["capabilities"]["exports"].append(
                "flat_dxf"
            )
        if name == "cad.export_document":
            path = Path(arguments["outputPath"])
            path.write_bytes(dxf(units=None))
            evidence = native_evidence(path)
            if spoof_document:
                evidence["documentId"] = "other"
            result.structured_content["result"]["flatPatternEvidence"] = evidence
        return result

    gateway.call_tool = call

    async def scenario():
        await run.start()
        if spoof_document:
            with pytest.raises(WorkflowSourceExecutionError) as error:
                await run.finish()
            assert error.value.code == "CAD_EXPORT_VERIFICATION_FAILED"
            assert not run.outputs
        else:
            _, files = await run.finish()
            assert files[0]["verification"]["native_geometry"]["status"] == "pass"
            report_file = files[0]["verification_report"]
            saved = json.loads((tmp_path / report_file["output_path"]).read_text())
            assert saved["native_geometry"]["evidence"]["documentId"] == "original"
            assert saved["units"]["source"] == "hash_bound_native_flat_geometry"

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "expected_status, data",
    [
        ("inconclusive", dxf(units=None)),
        ("fail", dxf(rectangle() + circle(100, 20, 3))),
    ],
)
def test_failed_dxf_report_is_clickable_partial_result_without_releasing_export_or_quote(
    tmp_path, expected_status, data
):
    from dataclasses import replace
    from workspace_service.workflow_source_execution import (
        execute_prompt_workflow,
        PromptWorkflow,
    )
    from packages.workspace_service.tests.test_workflow_source_execution import service

    cfg = settings()
    cfg.update(
        save_native=False,
        exports=[{"format": "flat_dxf", "path": "flat.dxf", "port": "flat"}],
    )
    gateway, setup = runner(tmp_path, cfg)
    runtime, original_call = setup.runtime, gateway.call_tool
    events, executed = [], []

    async def on_event(event):
        events.append(event)

    async def run_task(step, *args, **kwargs):
        executed.append(step.id)
        return "Export the flat pattern.", []

    runtime.run_task = run_task

    async def call(session, request, name, arguments, **kwargs):
        result = await original_call(session, request, name, arguments, **kwargs)
        if name == "cad.list_providers":
            result.structured_content["result"][0]["capabilities"]["exports"].append(
                "flat_dxf"
            )
        if name == "cad.export_document":
            Path(arguments["outputPath"]).write_bytes(data)
        return result

    gateway.call_tool = call
    step = replace(setup.step, output_ports=(("flat", "workspace_file"),))
    quote = replace(
        step,
        id="quote",
        title="Request supplier quote",
        references=(("DXF", "edit.flat"),),
    )
    with pytest.raises(WorkflowSourceExecutionError) as error:
        asyncio.run(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=PromptWorkflow("DXF to quote", (step, quote), {}),
                input_values={},
                response_generator=None,
                on_event=on_event,
                tool_runtime=runtime,
                action_generator=object(),
            )
        )
    assert error.value.code == "CAD_EXPORT_VERIFICATION_FAILED"
    assert executed == ["edit"]
    assert not any(event["kind"] == "step_completed" for event in events)
    saved = [event for event in events if event["kind"] == "output_saved"]
    assert len(saved) == 1 and saved[0]["artifact_role"] == "diagnostic"
    assert saved[0]["output_path"] == "flat.dxf.verification.json"
    ready = [event for event in events if event["kind"] == "result_ready"]
    assert len(ready) == 1 and ready[0]["artifact_role"] == "diagnostic"
    result = ready[0]["engineering_result"]
    assert result["kind"] == "file"
    assert result["name"] == f"DXF verification report · {expected_status}"
    assert result["provenance"]["run_id"]
    assert (
        result["provenance"]["output_port"] == "diagnostic:flat.dxf.verification.json"
    )
    (representation,) = result["representations"]
    report_path = tmp_path / representation["location"]
    assert (
        representation["kind"] == "workspace_file"
        and representation["durability"] == "persistent"
    )
    assert (
        representation["sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    )
    assert representation["size_bytes"] == report_path.stat().st_size
    assert json.loads(report_path.read_text())["status"] == expected_status
