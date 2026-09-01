from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "recovery" / "audit_recovery_completion.py"
SPEC = importlib.util.spec_from_file_location("audit_recovery_completion", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_recovery_completion_audit_is_truthful_and_complete() -> None:
    result = AUDIT.collect()

    assert result["audit_status"] == "PASS"
    assert result["goal_status"] == "blocked_external"
    assert result["goal_complete"] is False
    assert result["recovery_ledger"] == {
        "completed": 57,
        "total": 60,
        "open_tasks": ["T056", "T058", "T060"],
    }
    assert result["frozen_checkpoint"]["unchanged"] is True
    assert result["approved_walkthrough"]["steps_passed"] == 50
    assert result["approved_walkthrough"]["steps_total"] == 50
    assert result["approved_walkthrough"]["browser_diagnostics"] == 0
    assert result["capability_coverage"]["mapped"] == 859
    assert result["capability_coverage"]["capabilities"] == 33
    assert all(item["status"] == "passed" for item in result["requirements"])
    assert [item["task"] for item in result["blockers"]] == ["T056", "T058", "T060"]
    assert result["prohibited_actions_performed"] == []
    assert result["customer_ready"] is False
