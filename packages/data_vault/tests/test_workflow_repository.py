from data_vault.workflow_repository import WorkflowIndexRecord, WorkflowRepository


def test_workflow_index_is_metadata_only_and_scoped_to_workspace(tmp_path):
    repository = WorkflowRepository(str(tmp_path / "state.db"))
    record = WorkflowIndexRecord("left", "id-1", "first", 2, "digest", "active", 1)
    repository.upsert(record)
    repository.upsert(
        WorkflowIndexRecord("right", "id-1", "first", 1, "other", "active", 1)
    )
    assert repository.list("left") == [record]
    repository.mark_deleted("left", "id-1")
    assert repository.list("left") == []
    assert repository.list("left", include_deleted=True)[0].state == "deleted"


def test_workflow_index_replaces_stale_slug_with_authoritative_workflow(tmp_path):
    repository = WorkflowRepository(str(tmp_path / "state.db"))
    repository.upsert(
        WorkflowIndexRecord("workspace", "old-id", "flow", 1, "old", "active", 1)
    )
    repository.mark_deleted("workspace", "old-id")

    replacement = WorkflowIndexRecord(
        "workspace", "new-id", "flow", 1, "new", "active", 3
    )
    repository.upsert(replacement)

    assert repository.list("workspace", include_deleted=True) == [replacement]
