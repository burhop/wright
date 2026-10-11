"""Synthetic handoff failures against the actual saved wheel acceptance profile.

The canonical runner owns the gate. These tests neither invoke CAD nor certify
native geometry: a recorded observation subset feeds the runner's producer
fixture, and each declared mutation must hold the dependent consumer.
"""

import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from core.process_validation import Assessment, ValidationProfile
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    execute_prompt_workflow,
)
from packages.workspace_service.tests.test_workflow_process_validation import (
    runtime_service,
    validator,
    workflow,
)
from packages.workspace_service.tests.test_workflow_source_execution import task
from packages.workspace_service.tests.test_workflow_mcp_execution import mcp, runtime

REPO = Path(__file__).resolve().parents[1]
PROFILE = (
    REPO
    / "examples/process-interfaces/printed-replacement-part/native-inspection-profile.json"
)
OBSERVATIONS = REPO / "tests/fixtures/workflow-validation/focus-wheel-measurements.json"
ROUTE_PROFILE = REPO / "tests/fixtures/workflow-validation/wall-dock-route-profile.json"


@pytest.mark.parametrize(
    "choice, passing",
    [
        ({"manufacturing_route": "Sheet-metal fabrication"}, True),
        ({"manufacturing_route": "Polymer material extrusion"}, False),
        ({"manufacturing_route": "Machining from solid stock"}, False),
        ({}, False),
    ],
    ids=[
        "requested-sheet-metal",
        "wrong-polymer-route",
        "wrong-machining-route",
        "missing-route",
    ],
)
def test_assignment_route_gate_holds_incompatible_declared_method(
    tmp_path, choice, passing
):
    """A scoped configured requirement, not a global restriction on workflows."""
    profile = ValidationProfile.model_validate_json(ROUTE_PROFILE.read_bytes())
    reference = profile.baseline.requirements[0].sources[0]
    assert (
        hashlib.sha256((REPO / reference.artifact_ref).read_bytes()).hexdigest()
        == reference.sha256
    )
    (tmp_path / "route-profile.json").write_bytes(ROUTE_PROFILE.read_bytes())
    config = {
        "profile": {
            "source": "workspace",
            "name": "route-profile.json",
            "reference": profile.reference().model_dump(),
        },
        "baseline": profile.baseline.reference().model_dump(),
        "subjects": {"route_choice": "inspect_subject"},
    }
    plan = compile_prompt_workflow(workflow(validator(config), consumer=True))
    app, calls, events = runtime_service(tmp_path), [], []

    async def fixture_response(prompt, fmt):
        calls.append(fmt)
        return json.dumps(choice) if fmt == "json" else "Fixture handoff permitted"

    async def retain(event):
        events.append(event)

    invocation = execute_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        plan=plan,
        input_values={},
        response_generator=fixture_response,
        on_event=retain,
        run_id="route-fixture",
    )
    if passing:
        result = asyncio.run(invocation)
        assert result["steps"][-1]["task_id"] == "consume"
        assert calls == ["json", "text"]
    else:
        with pytest.raises(WorkflowSourceExecutionError) as stopped:
            asyncio.run(invocation)
        assert stopped.value.code == "PROCESS_VALIDATION_REJECTED"
        assert calls == ["json"] and not (tmp_path / "consume.txt").exists()
    report = next(e["report"] for e in events if e["kind"] == "design_check")
    assessment = Assessment.model_validate_json(
        (tmp_path / report["assessment_path"]).read_bytes()
    )
    assert assessment.request.profile_ref == profile.reference()
    assert assessment.request.baseline_ref == profile.baseline.reference()
    assert assessment.request.subjects[0].value == json.dumps(choice)
    assert assessment.summary.release_eligible is passing
    assert assessment.checks[0].state == ("pass" if passing else "fail")
    if not passing:
        assert any(
            f.selector == "/manufacturing_route"
            and "DOCK-REQUESTED-MANUFACTURING-ROUTE" in f.requirement_ids
            for f in assessment.findings
        )
    assert next(
        e
        for e in events
        if e["kind"] == "result_ready" and e.get("task_id") == "inspect"
    )["artifact_role"] == ("verification" if passing else "diagnostic")


@pytest.mark.parametrize(
    "fault, failed_check, selector",
    [
        ("none", None, None),
        ("millimetre_value_in_metres", "height18", "/measured_height_mm"),
        ("wrong_socket_flat", "socket-flat", "/socket_sections/1/flat_x_mm"),
        (
            "drawing_from_failed_revision",
            "drawing-SocketAcrossFlat",
            "/drawing/dimension_values_mm/SocketAcrossFlat",
        ),
        (
            "missing_drawing_dimension",
            "drawing-SocketDepth",
            "/drawing/dimension_values_mm/SocketDepth",
        ),
        ("open_mesh", "mesh-closed", "/mesh/all_edges_two_facets"),
        (
            "different_neutral_geometry",
            "native-step-agreement",
            "/native_step_symmetric_volume_difference_mm3",
        ),
        ("invalid_json", "all", None),
        ("empty_file", "missing_artifact", None),
    ],
)
def test_wheel_handoff_defect_is_recorded_and_holds_consumer(
    tmp_path, fault, failed_check, selector
):
    raw = PROFILE.read_bytes()
    profile = ValidationProfile.model_validate_json(raw)
    assert profile.id == "focus-wheel-native-correspondence-001"
    assert profile.version == "2" and len(profile.checks) == 20
    (tmp_path / "wheel-profile.json").write_bytes(raw)
    fixture = json.loads(OBSERVATIONS.read_bytes())
    observed = fixture["observations"]
    if fault == "millimetre_value_in_metres":
        observed["measured_height_mm"] /= 1000
    elif fault == "wrong_socket_flat":
        observed["socket_sections"][1]["flat_x_mm"] = -2.0
    elif fault == "drawing_from_failed_revision":
        # The corrected geometry is retained, but its drawing still represents
        # the earlier 5.2 mm across-flat value instead of the required 5.6 mm.
        observed["drawing"]["dimension_values_mm"]["SocketAcrossFlat"] = 5.2
    elif fault == "missing_drawing_dimension":
        del observed["drawing"]["dimension_values_mm"]["SocketDepth"]
    elif fault == "open_mesh":
        observed["mesh"]["all_edges_two_facets"] = False
    elif fault == "different_neutral_geometry":
        observed["native_step_symmetric_volume_difference_mm3"] = 100.0
    config = {
        "profile": {
            "source": "workspace",
            "name": "wheel-profile.json",
            "reference": profile.reference().model_dump(),
        },
        "baseline": profile.baseline.reference().model_dump(),
        "subjects": {"inspection": "inspect_subject"},
    }
    producer = mcp(
        mcp_arguments=json.dumps(
            {"query": "Return the declared synthetic inspection fixture"}
        ),
        mcp_argument_ports="{}",
        expected_files="inspection.json",
        expected_file_ports={"search_result": "inspection.json"},
    ).replace('"kind":"structured_result"', '"kind":"workspace_file"')
    # Preserve the profile's file-only contract. A value response cannot stand
    # in for the measured file that the real engineering process must provide.
    text = workflow(validator(config), consumer=True)
    text = text.replace(task("produce", fmt="json"), producer)
    text = text.replace("produce.produce_response", "search.search_result")
    plan = compile_prompt_workflow(text)
    app, calls, events = runtime_service(tmp_path), [], []
    gateway, tool_runtime = runtime()
    original_call = gateway.call_tool

    async def write_fixture(*args, **kwargs):
        content = (
            '{"valid_solid":'
            if fault == "invalid_json"
            else ""
            if fault == "empty_file"
            else json.dumps(observed)
        )
        (tmp_path / "inspection.json").write_text(content, encoding="utf-8")
        return await original_call(*args, **kwargs)

    gateway.call_tool = write_fixture
    tool_runtime.preflight(plan.steps[0])

    async def read_reference(workspace_dir, path):
        return (tmp_path / path).read_bytes()

    app.files.read_reference = read_reference

    async def produce(prompt, fmt):
        calls.append(fmt)
        return "Fixture handoff released"

    async def retain(event):
        events.append(event)

    invocation = execute_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        plan=plan,
        input_values={},
        response_generator=produce,
        tool_runtime=tool_runtime,
        on_event=retain,
        run_id="wheel-fixture-" + fault,
    )
    if failed_check is None:
        result = asyncio.run(invocation)
        assert result["steps"][-1]["task_id"] == "consume"
        assert calls == ["text"]
    else:
        with pytest.raises(WorkflowSourceExecutionError) as stopped:
            asyncio.run(invocation)
        expected_code = (
            "WORKFLOW_OUTPUT_INVALID"
            if fault == "empty_file"
            else "PROCESS_VALIDATION_REJECTED"
        )
        assert stopped.value.code == expected_code
        assert calls == [] and not (tmp_path / "consume.txt").exists()
    assert len(gateway.calls) == 1
    if fault == "empty_file":
        assert not any(e["kind"] == "design_check" for e in events)
        return
    recorded = next(e["report"] for e in events if e["kind"] == "design_check")
    assessment = Assessment.model_validate_json(
        (tmp_path / recorded["assessment_path"]).read_bytes()
    )
    assert assessment.summary.release_eligible is (failed_check is None)
    assert len(assessment.checks) == 20
    assert assessment.request.profile_ref == profile.reference()
    assert assessment.request.baseline_ref == profile.baseline.reference()
    assert assessment.request.subjects[0].producer.run_id == "wheel-fixture-" + fault
    if failed_check == "all":
        assert all(c.state == "fail" for c in assessment.checks)
        assert assessment.findings and all(
            f.category == "output_defect" and f.code == "output.invalid_json"
            for f in assessment.findings
        )
        # One unreadable file affects every check; its correction is useful once
        # in the run diagnostic, while the exact assessment retains each finding.
        assert len(assessment.findings) == 20
        assert recorded["corrections"] == [assessment.findings[0].explanation]
    elif failed_check:
        check = next(c for c in assessment.checks if c.check_id == failed_check)
        assert check.state == "fail"
        assert any(
            f.selector == selector and f.requirement_ids for f in assessment.findings
        )
        assert all(
            c.state == "pass" for c in assessment.checks if c.check_id != failed_check
        )
    else:
        assert all(c.state == "pass" for c in assessment.checks)
