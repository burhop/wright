import pytest

from workspace_service.adapters.runtime import (
    get_active_rivet_workflow,
    set_active_rivet_workflow,
)


def test_active_rivet_workflow_is_scoped_to_chat_session(tmp_path) -> None:
    database = str(tmp_path / "wright.db")

    set_active_rivet_workflow(database, "session-1", "untitled-workflow-2")
    set_active_rivet_workflow(database, "session-2", "other-workflow")

    assert get_active_rivet_workflow(database, "session-1") == "untitled-workflow-2"
    assert get_active_rivet_workflow(database, "session-2") == "other-workflow"

    set_active_rivet_workflow(database, "session-1", None)
    assert get_active_rivet_workflow(database, "session-1") is None
    assert get_active_rivet_workflow(database, "session-2") == "other-workflow"


@pytest.mark.parametrize("slug", ["../outside", "Uppercase", "", "a" * 64])
def test_active_rivet_workflow_rejects_invalid_nonempty_slugs(
    tmp_path, slug: str
) -> None:
    database = str(tmp_path / "wright.db")
    if not slug:
        set_active_rivet_workflow(database, "session-1", slug)
        assert get_active_rivet_workflow(database, "session-1") is None
        return

    with pytest.raises(ValueError, match="Invalid Rivet workflow slug"):
        set_active_rivet_workflow(database, "session-1", slug)
