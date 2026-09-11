import importlib.util
import json
from types import SimpleNamespace
from pathlib import Path

from tool_registry.development_metrics import DevelopmentMetrics

spec = importlib.util.spec_from_file_location(
    "metrics_collector",
    Path(__file__).parents[3] / "scripts/track-development-metrics.py",
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def usage(total, recent, at="2026-08-01T10:00:00Z"):
    return (
        json.dumps(
            {
                "timestamp": at,
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": total,
                            "output_tokens": 0,
                        },
                        "last_token_usage": {
                            "input_tokens": recent,
                            "output_tokens": 0,
                        },
                    },
                },
            }
        )
        + "\n"
    )


def test_usage_deduplicates_notifications_resets_and_reimport(tmp_path):
    path = tmp_path / "session.jsonl"
    path.write_text(
        usage(100, 100)
        + usage(100, 100)
        + usage(150, 50)
        + usage(10, 10)
        + usage(30, 20)
        + '{"unfinished":',
        encoding="utf-8",
    )
    store = DevelopmentMetrics(tmp_path / "data")
    collector.import_usage(store, "F01", path)
    collector.import_usage(store, "F01", path)
    events = store.read()["events"]
    assert len(events) == 3
    assert sum(e["data"]["input_tokens"] for e in events) == 170
    assert all(e["data"]["task"] == "unassigned" for e in events)


def test_collection_records_only_changed_snapshots_and_stable_ledger_runs(
    tmp_path, monkeypatch
):
    program = tmp_path / collector.PROGRAM
    program.mkdir(parents=True)
    (program / "work-registry.json").write_text(
        json.dumps({"task_sources": [{"feature_id": "F01", "tasks_path": "tasks.md"}]}),
        encoding="utf-8",
    )
    (program / "test-run-ledger.json").write_text('{"runs":[]}', encoding="utf-8")
    (tmp_path / "tasks.md").write_text("- [ ] T001 Start", encoding="utf-8")
    monkeypatch.setattr(collector.subprocess, "check_output", lambda *a, **kw: "commit")
    store = DevelopmentMetrics(tmp_path / "data")
    collector.collect(store, tmp_path, [])
    collector.collect(store, tmp_path, [])
    (tmp_path / "tasks.md").write_text("- [x] T001 Start", encoding="utf-8")
    collector.collect(store, tmp_path, [])
    events = store.read()["events"]
    assert len([e for e in events if e["kind"] == "snapshot"]) == 2
    assert len([e for e in events if e["kind"] == "heartbeat"]) == 3


def test_history_preserves_commit_dates_and_deduplicates(tmp_path, monkeypatch):
    program = tmp_path / collector.PROGRAM
    program.mkdir(parents=True)
    (program / "work-registry.json").write_text(
        json.dumps({"task_sources": [{"feature_id": "F01", "tasks_path": "tasks.md"}]}),
        encoding="utf-8",
    )

    def history(command, **kwargs):
        assert "--first-parent" not in command
        assert command[-1] == "tasks.md"
        return "first\t2026-08-28T10:00:00Z\nsecond\t2026-08-30T10:00:00Z\n"

    monkeypatch.setattr(collector.subprocess, "check_output", history)
    monkeypatch.setattr(
        collector.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="- [x] T001 Work\n"
            if "second:" in command[-1]
            else "- [ ] T001 Work\n",
        ),
    )
    store = DevelopmentMetrics(tmp_path / "data")
    assert collector.import_history(store, tmp_path) == 2
    assert collector.import_history(store, tmp_path) == 0
    events = store.read()["events"]
    assert [e["at"][:10] for e in events] == ["2026-08-28", "2026-08-30"]
    assert [e["data"]["tasks"][0]["checked"] for e in events] == [False, True]
    assert all(e["id"].startswith("git:") for e in events)


def test_history_recovers_merged_branch_progress(tmp_path):
    import os
    import subprocess

    def git(*args, day=1):
        env = {
            **os.environ,
            "GIT_AUTHOR_DATE": f"2026-08-{day:02d}T12:00:00Z",
            "GIT_COMMITTER_DATE": f"2026-08-{day:02d}T12:00:00Z",
        }
        return subprocess.check_output(["git", "-C", str(tmp_path), *args], env=env)

    git("init", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    program = tmp_path / collector.PROGRAM
    program.mkdir(parents=True)
    (program / "work-registry.json").write_text(
        json.dumps(
            {
                "task_sources": [
                    {"feature_id": "F01", "tasks_path": "tasks.md"},
                    {"feature_id": "F02", "tasks_path": "other.md"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "other.md").write_text("- [ ] T001 Other", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "baseline")
    git("checkout", "-b", "feature")
    (tmp_path / "tasks.md").write_text("- [ ] T001 Work", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "plan", day=2)
    (tmp_path / "tasks.md").write_text("- [x] T001 Work", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "implement", day=3)
    git("checkout", "main")
    git("merge", "--no-ff", "feature", "-m", "integrate", day=4)
    store = DevelopmentMetrics(tmp_path / "data")
    assert collector.import_history(store, tmp_path) == 3
    assert collector.import_history(store, tmp_path) == 0
    events = store.read()["events"]
    feature = [e for e in events if e["feature"] == "F01"]
    assert [e["at"][:10] for e in feature] == ["2026-08-02", "2026-08-03"]
    assert [e["data"]["tasks"][0]["checked"] for e in feature] == [False, True]
    assert len([e for e in events if e["feature"] == "F02"]) == 1


def test_explicit_sources_do_not_replay_archived_registry(tmp_path, monkeypatch):
    program = tmp_path / collector.PROGRAM
    program.mkdir(parents=True)
    (program / "work-registry.json").write_text(
        json.dumps(
            {
                "task_sources": [
                    {"feature_id": "OLD", "tasks_path": "missing-archived.md"}
                ]
            }
        ),
        encoding="utf-8",
    )
    (program / "test-run-ledger.json").write_text('{"runs":[]}', encoding="utf-8")
    (tmp_path / "current.md").write_text("- [ ] T001 Current", encoding="utf-8")
    monkeypatch.setattr(collector.subprocess, "check_output", lambda *a, **kw: "commit")
    store = DevelopmentMetrics(tmp_path / "data")
    collector.collect(store, tmp_path, ["CURRENT=current.md"], only_tasks=True)
    snapshots = [e for e in store.read()["events"] if e["kind"] == "snapshot"]
    assert [e["feature"] for e in snapshots] == ["CURRENT"]
