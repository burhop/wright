"""The installed qualification must retain failed cleanup evidence in CI."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("doctor_unavailable", [False, True])
def test_failed_lifecycle_keeps_command_and_read_only_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, doctor_unavailable: bool
) -> None:
    wheel = tmp_path / "candidate.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("api/desktop/native-editor.html", "<html></html>")
    evidence = tmp_path / "evidence"
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setattr(tempfile, "mkdtemp", lambda **kwargs: str(home))
    monkeypatch.setattr(importlib.metadata, "version", lambda name: "0.1.9")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qualify-desktop-native.py",
            "--wheel",
            str(wheel),
            "--wheelhouse",
            str(tmp_path),
            "--evidence-dir",
            str(evidence),
        ],
    )
    commands: list[str] = []

    def command_result(command, **kwargs):
        operation = command[-1]
        commands.append(operation)
        assert kwargs["env"]["WRIGHT_HOME"] == str(home)
        if operation == "doctor" and doctor_unavailable:
            raise TimeoutError("Synthetic diagnostic failure")
        result = {
            "ok": False,
            "command": operation,
            "code": "doctor_findings"
            if operation == "doctor"
            else "process_identity_failed",
            "details": {"process_identity_code": "process_start_mismatch"},
        }
        return subprocess.CompletedProcess(command, 1, json.dumps(result), "")

    monkeypatch.setattr(subprocess, "run", command_result)
    with pytest.raises(AssertionError, match="stop failed"):
        runpy.run_path(
            str(ROOT / "scripts/qualification/qualify-desktop-native.py"),
            run_name="__main__",
        )

    receipt = json.loads((evidence / "receipt.json").read_text())
    assert receipt["result"] == "FAIL"
    assert commands == ["start", "doctor", "stop", "doctor"]
    assert receipt["first-start"]["code"] == "process_identity_failed"
    assert receipt["final-stop"]["code"] == "process_identity_failed"
    if doctor_unavailable:
        assert receipt["final-stop-doctor"] == {
            "code": "diagnostic_unavailable",
            "error_type": "TimeoutError",
        }
        assert receipt["lifecycle_exit_codes"] == {"first-start": 1, "final-stop": 1}
    else:
        assert (
            receipt["final-stop-doctor"]["details"]["process_identity_code"]
            == "process_start_mismatch"
        )
        assert receipt["lifecycle_exit_codes"] == {
            "first-start": 1,
            "first-start-doctor": 1,
            "final-stop": 1,
            "final-stop-doctor": 1,
        }
    assert "workspace" not in receipt
    assert receipt["engineering_runs"] == 0
