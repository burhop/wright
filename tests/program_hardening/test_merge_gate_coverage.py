from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_dev_gate_names_every_deterministic_program_finding() -> None:
    gate = (ROOT / "scripts" / "check-dev-merge.sh").read_text(encoding="utf-8")
    findings = {
        "contract-schema-drift": "tests/program_hardening",
        "native-schema-and-quarantine": "test_program_state_compatibility.py",
        "diagnostic-redaction-and-grants": "test_support_diagnostic_service.py",
        "diagnostic-api": "test_support_diagnostics_api.py",
        "offline-retained-state": "test_engineering_program_offline.py",
        "artifact-platform-evidence": "test_program_compatibility_evidence.py",
        "packaged-program-boundary": "test_program_hardening_contents.py",
        "capability-next-action": "CapabilityLibrary",
        "rivet-evidence-and-recovery": "RivetScenarioReport",
        "local-support-export": "SupportDiagnosticsPanel",
        "bounded-browser-journeys": "PLAYWRIGHT_INCLUDE_LIVE=1",
        "full-python-regression": "python -m pytest",
        "full-web-regression": "npm run test --workspace=apps/web",
        "strict-documentation": "mkdocs build --strict",
    }
    missing = {name: token for name, token in findings.items() if token not in gate}
    assert missing == {}


def test_gate_e_scan_is_part_of_the_program_tranche() -> None:
    gate = (ROOT / "scripts" / "check-dev-merge.sh").read_text(encoding="utf-8")
    assert "tests/program_hardening" in gate
    leak_test = (
        ROOT / "tests" / "program_hardening" / "test_diagnostic_leaks.py"
    ).read_text(encoding="utf-8")
    for prohibited_fixture in ("M3 S12000", "G28", "reusable-authority"):
        assert prohibited_fixture in leak_test
