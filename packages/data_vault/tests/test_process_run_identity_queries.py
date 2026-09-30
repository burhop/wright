"""Run projection queries keep durable input/validation identity scoped."""

import pytest

from core.process_interactions import ProcessRef
from data_vault.process_input_repository import ProcessInputRepository
from data_vault.process_validation_repository import ProcessValidationRepository
from packages.data_vault.tests.test_process_interface_migrations import inputs, receipt
from packages.data_vault.tests.test_process_validation_repository import request, passed


def test_run_receipt_query_recovers_frozen_inputs_without_using_status(tmp_path):
    repository = ProcessInputRepository(tmp_path / "state.db")
    snapshot = inputs()
    retained, _ = repository.reserve_start(snapshot, receipt(snapshot))
    assert (
        repository.receipt_for_run("workspace", snapshot.process.source_path, "run")
        == retained
    )
    assert repository.get_snapshot("workspace", retained.input_snapshot_id) == snapshot


@pytest.mark.parametrize(
    "workspace,path,run_id",
    [
        ("other", "workflows/analysis.wflow", "run"),
        ("workspace", "workflows/other.wflow", "run"),
        ("workspace", "workflows/analysis.wflow", "other"),
    ],
)
def test_receipt_lookup_cannot_cross_scope(tmp_path, workspace, path, run_id):
    repository = ProcessInputRepository(tmp_path / "state.db")
    snapshot = inputs()
    repository.reserve_start(snapshot, receipt(snapshot))
    assert repository.receipt_for_run(workspace, path, run_id) is None


def test_query_does_not_rebind_receipt_to_changed_source_digest(tmp_path):
    repository = ProcessInputRepository(tmp_path / "state.db")
    snapshot = inputs()
    repository.reserve_start(snapshot, receipt(snapshot))
    current = ProcessRef.model_validate(
        {**snapshot.process.model_dump(), "source_digest": "b" * 64}
    )
    retained = repository.receipt_for_run("workspace", current.source_path, "run")
    assert retained.process == snapshot.process and retained.process != current


def assessments(repository, *, legacy=False):
    ids = []
    for key in ("first", "second"):
        req, profile = request(key)
        if legacy:
            req = type(req).model_validate(
                {**req.model_dump(), "run_id": None, "check_step_id": None}
            )
        attempt, _ = repository.create(req)
        repository.start(req.workspace_id, attempt.id)
        assessment = passed(attempt, profile)
        repository.finalize(assessment)
        ids.append(assessment.id)
    return ids


@pytest.mark.parametrize("legacy", [False, True])
def test_assessment_identity_query_is_paged_and_scoped(tmp_path, legacy):
    repository = ProcessValidationRepository(tmp_path / "state.db")
    ids = assessments(repository, legacy=legacy)
    first = repository.assessment_ids_for_run("workspace-1", "run", limit=1)
    assert [item[1] for item in first] == ids[:1]
    second = repository.assessment_ids_for_run(
        "workspace-1", "run", cursor=first[0][0], limit=1
    )
    assert [item[1] for item in second] == ids[1:]
    assert repository.assessment_ids_for_run("other", "run") == ()
    assert repository.assessment_ids_for_run("workspace-1", "other") == ()


@pytest.mark.parametrize(
    "changes", [{"limit": 0}, {"limit": 257}, {"cursor": -1}, {"cursor": True}]
)
def test_assessment_query_rejects_unbounded_or_invalid_page(tmp_path, changes):
    repository = ProcessValidationRepository(tmp_path / "state.db")
    with pytest.raises(ValueError):
        repository.assessment_ids_for_run("workspace-1", "run", **changes)
