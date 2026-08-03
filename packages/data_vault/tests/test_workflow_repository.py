from data_vault.workflow_repository import WorkflowIndexRecord, WorkflowRepository


def test_workflow_index_is_metadata_only_and_scoped_to_workspace(tmp_path):
    repository = WorkflowRepository(str(tmp_path / "state.db"))
    record = WorkflowIndexRecord("left", "id-1", "first", 2, "digest", "active", 1)
    repository.upsert(record)
    repository.upsert(WorkflowIndexRecord("right", "id-1", "first", 1, "other", "active", 1))
    assert repository.list("left") == [record]
    repository.mark_deleted("left", "id-1")
    assert repository.list("left") == []
    assert repository.list("left", include_deleted=True)[0].state == "deleted"
