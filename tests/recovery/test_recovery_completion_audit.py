from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


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


def test_frozen_task_comparison_ignores_only_checkbox_marker_case() -> None:
    original = "- [X] T001 Complete\n- [ ] T002 Open\n"
    normalized = "- [x] T001 Complete\r\n- [ ] T002 Open\r\n"
    changed = "- [x] T001 Different\n- [ ] T002 Open\n"

    assert AUDIT._canonical_frozen_task_document(original) == (
        AUDIT._canonical_frozen_task_document(normalized)
    )
    assert AUDIT._canonical_frozen_task_document(original) != (
        AUDIT._canonical_frozen_task_document(changed)
    )


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


@pytest.mark.parametrize("delivery", [None, {"status": "verified"}])
def test_dashboard_verification_falls_back_only_when_no_current_path_is_supplied(
    tmp_path: Path, monkeypatch, delivery
) -> None:
    feature = tmp_path / "specs/080-canonical-workflow-recovery"
    (feature / "evidence").mkdir(parents=True)
    monkeypatch.setattr(AUDIT, "ROOT", tmp_path)
    monkeypatch.setattr(AUDIT, "FEATURE", feature)
    if delivery is not None:
        (feature / "evidence/image-redesign-delivery.json").write_text(
            json.dumps(delivery)
        )
    assert (
        AUDIT._dashboard_verification_path()
        == tmp_path
        / "artifacts/dashboard-recovery-verification/dashboard-verification.json"
    )


def test_dashboard_verification_uses_current_repo_contained_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    feature = tmp_path / "specs/080-canonical-workflow-recovery"
    (feature / "evidence").mkdir(parents=True)
    relative = "artifacts/dashboard-image-redesign-verification/fresh/dashboard-verification.json"
    (feature / "evidence/image-redesign-delivery.json").write_text(
        json.dumps({"dashboardVerificationPath": relative})
    )
    monkeypatch.setattr(AUDIT, "ROOT", tmp_path)
    monkeypatch.setattr(AUDIT, "FEATURE", feature)
    assert AUDIT._dashboard_verification_path() == tmp_path / relative


@pytest.mark.parametrize(
    "relative",
    [
        "../outside.json",
        "/outside.json",
        "C:/outside.json",
        "\\\\server\\outside.json",
        "artifacts/../outside.json",
        "artifacts\\outside.json",
        "https://example.com/evidence.json",
        "",
        None,
        42,
    ],
)
def test_current_dashboard_path_must_be_safe_and_never_silently_falls_back(
    tmp_path: Path, monkeypatch, relative
) -> None:
    feature = tmp_path / "specs/080-canonical-workflow-recovery"
    (feature / "evidence").mkdir(parents=True)
    (feature / "evidence/image-redesign-delivery.json").write_text(
        json.dumps({"dashboardVerificationPath": relative})
    )
    monkeypatch.setattr(AUDIT, "ROOT", tmp_path)
    monkeypatch.setattr(AUDIT, "FEATURE", feature)
    with pytest.raises(ValueError, match="repository-contained"):
        AUDIT._dashboard_verification_path()


def test_dashboard_path_checks_resolved_containment_before_reading(
    tmp_path: Path, monkeypatch
) -> None:
    feature = tmp_path / "specs/080-canonical-workflow-recovery"
    (feature / "evidence").mkdir(parents=True)
    relative = "artifacts/linked/dashboard-verification.json"
    (feature / "evidence/image-redesign-delivery.json").write_text(
        json.dumps({"dashboardVerificationPath": relative})
    )
    monkeypatch.setattr(AUDIT, "ROOT", tmp_path)
    monkeypatch.setattr(AUDIT, "FEATURE", feature)
    original_resolve = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == tmp_path / relative:
            return tmp_path.parent / "outside/dashboard-verification.json"
        return original_resolve(path, *args, **kwargs)

    # Exercise the resolved-path guard without requiring Windows symlink
    # privilege; this is not evidence of native symlink creation or a race test.
    monkeypatch.setattr(Path, "resolve", resolve)
    with pytest.raises(ValueError, match="repository-contained"):
        AUDIT._dashboard_verification_path()


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
        == "38b409bf149a1241cc87cdedd48f83fed16b5050"
    )
    assert (
        result["usability_correction_walkthrough"]["tree"]
        == "452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6"
    )
    assert (
        result["usability_correction_walkthrough"]["manifest_sha256"]
        == "b8764a02ef83dfc52b65714de0cdbb05071feb9c0ebf4f5fde4995a2870cf335"
    )
    assert result["usability_correction_walkthrough"]["steps_passed"] == 24
    assert result["usability_correction_walkthrough"]["steps_total"] == 24
    assert result["usability_correction_walkthrough"]["raw_screenshots"] == 26
    assert result["usability_correction_walkthrough"]["annotated_screenshots"] == 26
    assert result["usability_correction_walkthrough"]["manifest_files"] == 59
    assert result["usability_correction_walkthrough"]["browser_diagnostics"] == 0
    # The current image-led authoring mapping adds nine rows to the historical
    # 881-row correction map; require the live ledger and coverage to agree.
    assert result["capability_coverage"]["mapped"] == capability_map["row_count"] == 890
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
