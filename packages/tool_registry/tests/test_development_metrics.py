from concurrent.futures import ThreadPoolExecutor

import pytest

from tool_registry.development_metrics import DevelopmentMetrics, collect_tasks


def event(identity="one", **changes):
    return {
        "id": identity,
        "at": "2026-08-01T10:00:00Z",
        "kind": "task",
        "feature": "F01",
        "subject": "abc:working-tree",
        "data": {
            "task": "T001",
            "title": "Example",
            "state": "working",
            "evidence": "",
        },
        **changes,
    }


def test_missing_store_is_unknown_and_read_does_not_create(tmp_path):
    assert DevelopmentMetrics(tmp_path).read()["availability"] == "unavailable"
    assert not list(tmp_path.iterdir())


def test_concurrent_append_is_idempotent_and_rejects_conflicting_replay(tmp_path):
    store = DevelopmentMetrics(tmp_path)
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda _: store.append(event()), range(8)))
    assert sum(results) == 1
    with pytest.raises(ValueError, match="reused"):
        store.append(event(subject="different"))
    assert len(store.read()["events"]) == 1


def test_out_of_order_results_sort_by_observation_time(tmp_path):
    store = DevelopmentMetrics(tmp_path)
    store.append(event("late", at="2026-08-02T10:00:00Z"))
    store.append(event("early"))
    assert [e["id"] for e in store.read()["events"]] == ["early", "late"]


@pytest.mark.parametrize("state", ["verified", "integrated"])
def test_completion_needs_evidence(tmp_path, state):
    row = event()
    row["data"]["state"] = state
    with pytest.raises(ValueError, match="evidence"):
        DevelopmentMetrics(tmp_path).append(row)


def test_snapshot_preserves_checkbox_without_promoting_verification(tmp_path):
    (tmp_path / "tasks.md").write_text(
        "- [X] T001 Done\n- [ ] T002 Next\n", encoding="utf-8"
    )
    result = collect_tasks(tmp_path, [("F01", "tasks.md")])
    assert result[0]["tasks"] == [
        {"task": "T001", "title": "Done", "checked": True},
        {"task": "T002", "title": "Next", "checked": False},
    ]
    with pytest.raises(ValueError, match="inside"):
        collect_tasks(tmp_path, [("F01", "../tasks.md")])


def test_duplicate_tasks_invalid_and_boolean_not_a_token_count(tmp_path):
    store = DevelopmentMetrics(tmp_path)
    with pytest.raises(ValueError, match="count"):
        store.append(
            event(
                kind="usage",
                data={
                    "session": "s",
                    "task": "T001",
                    "input_tokens": True,
                    "output_tokens": 1,
                },
            )
        )
    task = {"task": "T001", "title": "Title", "checked": False}
    with pytest.raises(ValueError, match="Duplicate"):
        store.append(event(kind="snapshot", data={"tasks": [task, task]}))
