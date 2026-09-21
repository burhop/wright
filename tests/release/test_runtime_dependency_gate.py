import json
from pathlib import Path
import subprocess

import pytest

from scripts.release import audit_runtime_dependencies as gate
from scripts.release.dependency_audit import DependencyAuditError


@pytest.mark.parametrize(
    ("report", "code", "passes"),
    [
        ({"dependencies": [{"name": "example", "vulns": []}]}, 0, True),
        (
            {"dependencies": [{"name": "example", "vulns": [{"id": "CVE-test"}]}]},
            1,
            False,
        ),
        ({"dependencies": [{"name": "example", "vulns": []}]}, 1, False),
        ({"dependencies": []}, 0, False),
        ({}, 0, False),
        (None, 2, False),
    ],
)
def test_runtime_audit_fails_closed(tmp_path, monkeypatch, report, code, passes):
    policy = tmp_path / ".github/dependency-audit-policy.json"
    policy.parent.mkdir()
    policy.write_text('{"exceptions": []}', encoding="utf-8")

    def run(command, *, cwd, check):
        assert command[:7] == [
            "uv",
            "run",
            "--locked",
            "--extra",
            "runtime",
            "--with",
            "pip-audit",
        ]
        assert cwd == tmp_path
        assert check is False
        if report is not None:
            Path(command[-1]).write_text(json.dumps(report), encoding="utf-8")
        return subprocess.CompletedProcess(command, code)

    monkeypatch.setattr(gate.subprocess, "run", run)
    if passes:
        gate.audit(tmp_path)
    else:
        with pytest.raises(DependencyAuditError):
            gate.audit(tmp_path)


def test_both_local_gates_run_runtime_dependency_audit():
    root = Path(__file__).resolve().parents[2]
    for name in ("push", "merge"):
        script = (root / f"scripts/check-dev-{name}.sh").read_text(encoding="utf-8")
        assert (
            'run "$GATE_PYTHON" -m scripts.release.audit_runtime_dependencies' in script
        )
