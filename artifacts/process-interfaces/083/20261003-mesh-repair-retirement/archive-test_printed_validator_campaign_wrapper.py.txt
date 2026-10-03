"""Exercise printing wrapper decisions with mocked subprocesses, never native dispatch."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = "printed-replacement-part-01"
ATTEMPT = "attempt-017"


@pytest.fixture
def wrapper(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("printed_wrapper", ROOT / "scripts/run_printed_validator_campaign.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = tmp_path / "runtime"
    execution = base / "campaign-execution"
    execution.mkdir(parents=True)
    for key, value in {"ROOT": tmp_path, "BASE": base, "EXECUTION": execution}.items():
        monkeypatch.setattr(module, key, value)
    monkeypatch.setattr(module, "model", lambda: "openai-codex::gpt-5.6-sol")
    monkeypatch.setattr(sys, "argv", ["wrapper", "--scenario", SCENARIO])
    return module


@pytest.mark.parametrize("phase,runtime,cleanup,cleanup_problem", [
    ("completed", "completed", True, None),
    ("failed", "failed", True, None),
    ("awaiting_manual_approval", "awaiting_approval", False, None),
    ("outcome_unknown", "running", False, None),
    ("runner_blocked", "running", False, None),
    ("completed", "running", False, None),
    ("process_exception", "running", False, None),
    ("failed", "failed", True, {"status": "cleanup_blocked"}),
    ("failed", "failed", True, {"status": "cleaned", "post_cleanup_identity": {"pid": 123}}),
])
def test_wrapper_retains_nonterminal_resources(wrapper, monkeypatch, phase, runtime, cleanup, cleanup_problem):
    calls = []

    def fake_run(arguments, *, capture=False):
        calls.append(arguments)
        script = Path(arguments[1]).name
        output = {}
        if script == "manage-printing03-blender-runtime.py":
            if arguments[2] == "launch":
                lifecycle = wrapper.BASE / f"printing01-runtime-{ATTEMPT}/lifecycle.json"
                lifecycle.parent.mkdir(parents=True)
                lifecycle.write_text("{}")
                output = {"server_id": "owned", "repair_server_id": "repair", "session_id": "native", "pid": 123}
            else:
                output = cleanup_problem or {"status": "cleaned"}
        elif script == "audit-engineering-batch-preflight.py":
            Path(arguments[arguments.index("--output") + 1]).write_text(json.dumps({"summary": {"cases": 1, "passed": 1, "review": 0, "failed": 0}}))
        elif script == "run_engineering_dataset_campaign.py":
            assert "--retry-episode-ledger" in arguments
            assert arguments[arguments.index("--retry-episode-ledger") + 1] == str(wrapper.ROOT / "artifacts/engineering-workflow-datasets/reliability-episodes.json")
            if phase == "process_exception":
                raise subprocess.CalledProcessError(1, arguments)
            state_root = Path(arguments[arguments.index("--state-root") + 1])
            (state_root / SCENARIO).mkdir(parents=True)
            (state_root / "summary.json").write_text(json.dumps({"cases": [{"scenario_id": SCENARIO, "attempt_id": ATTEMPT, "phase": phase, "content_validated": False, "validations": []}]}))
            (state_root / SCENARIO / f"{ATTEMPT}.json").write_text(json.dumps({"phase": phase, "runtime_status": runtime, "active_operation": None, "run_id": "run"}))
        return subprocess.CompletedProcess(arguments, 0, json.dumps(output), "")

    monkeypatch.setattr(wrapper, "run", fake_run)
    if phase == "process_exception":
        with pytest.raises(subprocess.CalledProcessError):
            wrapper.main()
    elif cleanup_problem:
        with pytest.raises(RuntimeError, match="process exit was not verified"):
            wrapper.main()
    else:
        wrapper.main()
    cleanup_calls = [call for call in calls if Path(call[1]).name == "manage-printing03-blender-runtime.py" and call[2] == "cleanup"]
    assert bool(cleanup_calls) == cleanup
    receipt = json.loads((wrapper.EXECUTION / f"printing-01-{ATTEMPT}-validator082-managed.json").read_text())
    assert receipt["cleanup_required"] is (bool(cleanup_problem) or not cleanup)
    if cleanup_problem:
        assert receipt["status"] == "native_cleanup_blocked"
    elif phase == "completed" and runtime == "completed":
        assert receipt["status"] == "completed_and_cleaned"
        assert receipt["workflow_completed"] is True
    elif not cleanup:
        assert "retained" in receipt["status"]


def test_existing_attempt_is_never_replayed(wrapper):
    receipt = wrapper.EXECUTION / f"printing-01-{ATTEMPT}-validator082-managed.json"
    receipt.write_text('{"status":"workflow_nonterminal_native_retained"}')
    with pytest.raises(ValueError, match="instead of replaying"):
        wrapper.main()
