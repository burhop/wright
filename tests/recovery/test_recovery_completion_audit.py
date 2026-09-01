from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "recovery" / "audit_recovery_completion.py"
SPEC = importlib.util.spec_from_file_location("audit_recovery_completion", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def test_task_ledger_derives_counts_and_rejects_gaps_or_duplicates(
    tmp_path: Path,
) -> None:
    task_file = tmp_path / "tasks.md"
    task_file.write_text(
        "- [x] T001 First\n- [x] T002 Second\n- [ ] T003 External gate\n",
        encoding="utf-8",
    )

    ledger = AUDIT._task_ledger(task_file)

    assert ledger == {
        "completed": {"T001", "T002"},
        "open_tasks": {"T003"},
        "total": 3,
        "well_formed": True,
    }

    task_file.write_text(
        "- [x] T001 First\n- [x] T001 Duplicate\n- [ ] T003 Gap\n",
        encoding="utf-8",
    )
    assert AUDIT._task_ledger(task_file)["well_formed"] is False


def test_capability_map_summary_uses_the_current_source_map(tmp_path: Path) -> None:
    source_map = tmp_path / "capability-source-map.csv"
    source_map.write_text(
        "source_key,capability_id\nsource:a,CAP-001\nsource:b,CAP-001\nsource:c,CAP-002\n",
        encoding="utf-8",
    )

    assert AUDIT._capability_map_summary(source_map) == {
        "row_count": 3,
        "unique_source_key_count": 3,
        "capabilities_represented": 2,
    }


def test_recovery_completion_audit_reports_current_evidence_truthfully() -> None:
    result = AUDIT.collect()
    task_ledger = AUDIT._task_ledger(AUDIT.FEATURE / "tasks.md")
    capability_map = AUDIT._capability_map_summary(
        AUDIT.FEATURE / "capability-source-map.csv"
    )

    assert result["goal_complete"] is False
    assert result["recovery_ledger"] == {
        "completed": len(task_ledger["completed"]),
        "total": task_ledger["total"],
        "open_tasks": sorted(task_ledger["open_tasks"]),
    }
    assert result["frozen_checkpoint"]["unchanged"] is True
    assert result["approved_walkthrough"]["steps_passed"] == 50
    assert result["approved_walkthrough"]["steps_total"] == 50
    assert result["approved_walkthrough"]["browser_diagnostics"] == 0
    assert (
        result["usability_correction_walkthrough"]["commit"]
        == "c5fb7d8e4a722f84956ebe22085e7fdf38b1b1d5"
    )
    assert (
        result["usability_correction_walkthrough"]["tree"]
        == "148a935edd38e9abe91b9ed284cd04882acf59c6"
    )
    assert (
        result["usability_correction_walkthrough"]["manifest_sha256"]
        == "e661bf45ff1449abc87399b928156fc336f367f260368a2966645a0026afd96e"
    )
    assert result["usability_correction_walkthrough"]["steps_passed"] == 12
    assert result["usability_correction_walkthrough"]["steps_total"] == 12
    assert result["usability_correction_walkthrough"]["raw_screenshots"] == 12
    assert result["usability_correction_walkthrough"]["annotated_screenshots"] == 12
    assert result["usability_correction_walkthrough"]["manifest_files"] == 30
    assert result["usability_correction_walkthrough"]["browser_diagnostics"] == 0
    assert result["capability_coverage"]["mapped"] == capability_map["row_count"] == 879
    assert (
        result["capability_coverage"]["unique"]
        == capability_map["unique_source_key_count"]
    )
    assert (
        result["capability_coverage"]["capabilities"]
        == capability_map["capabilities_represented"]
    )
    assert AUDIT.EXPECTED_SYNTAX_TREATMENTS == {
        "json",
        "yaml",
        "engineering_source",
    }
    assert [item["task"] for item in result["blockers"]] == sorted(
        AUDIT.ALLOWED_OPEN_TASKS
    )
    failed_requirements = {
        item["id"] for item in result["requirements"] if item["status"] == "failed"
    }
    assert result["audit_status"] == ("FAIL" if failed_requirements else "PASS")
    assert result["goal_status"] == (
        "blocked_external"
        if not failed_requirements
        and task_ledger["open_tasks"] == AUDIT.ALLOWED_OPEN_TASKS
        else "incomplete"
    )
    if task_ledger["open_tasks"] != AUDIT.ALLOWED_OPEN_TASKS:
        assert "OBJ-006" in failed_requirements
    assert result["prohibited_actions_performed"] == []
    assert result["customer_ready"] is False
