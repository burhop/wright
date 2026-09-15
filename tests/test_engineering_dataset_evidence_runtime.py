"""Real recorder/approval evidence must satisfy the campaign observer adapter."""

import importlib.util
from pathlib import Path

import pytest

from packages.workspace_service.tests.test_workflow_approval_execution import setup_case
from workspace_service.workflow_approval_execution import decide_workflow_approval, resume_workflow_approval


spec = importlib.util.spec_from_file_location(
    "runtime_dataset_evidence", Path(__file__).resolve().parents[1] / "scripts/engineering_dataset_evidence.py"
)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


@pytest.mark.asyncio
@pytest.mark.parametrize("handoff", [False, True])
async def test_actual_recorded_continuation_exports_without_fabricated_events(tmp_path, handoff):
    case = await setup_case(tmp_path, handoff=handoff)
    arguments = dict(workspace_root=tmp_path, export_root=tmp_path / "exported",
                     scenario_id=case.context["dataset_id"], attempt_id="attempt-01",
                     dataset_digest=case.context["dataset_digest"], template_digest="d" * 64,
                     definition_digest=case.context["source_digest"],
                     required_step_ids=["package", "approve", "after"], output_root=case.context["output_root"])
    first = evidence.export_run_evidence(case.result["run_log_path"], **arguments)
    assert first["accepted_by_runtime"] is True
    assert first["terminal_step_reached"] is False
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    _, result = await resume_workflow_approval(**case.args, request_id="test-resume",
                                              response_generator=case.generate)
    completed = evidence.export_run_evidence(result["run_log_path"], **arguments)
    assert completed["terminal_step_reached"] is True
    assert completed["all_required_steps_succeeded"] is True
    assert completed["external_effects"] == ("test_destinations" if handoff else "none")
    assert len(completed["produced_files"]) == (3 if handoff else 2)
    assert completed["content_validated"] is False
