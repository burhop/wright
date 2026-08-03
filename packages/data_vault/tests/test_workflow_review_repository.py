from data_vault.workflow_review_repository import (
    WorkflowReview,
    WorkflowReviewRepository,
)


def test_review_approval_is_exact_workspace_workflow_and_revision(tmp_path):
    repo = WorkflowReviewRepository(str(tmp_path / "state.db"))
    repo.set(WorkflowReview("workspace", "workflow", 2, "approved", "reviewer", 1))
    assert repo.approved("workspace", "workflow", 2)
    assert not repo.approved("workspace", "workflow", 1)
    assert not repo.approved("other", "workflow", 2)


def test_review_state_is_constrained_and_readable(tmp_path):
    repo = WorkflowReviewRepository(str(tmp_path / "state.db"))
    repo.set(WorkflowReview("workspace", "workflow", 1, "rejected", "reviewer", 2))
    assert repo.get("workspace", "workflow").state == "rejected"  # type: ignore[union-attr]
