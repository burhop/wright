import json
from pathlib import Path
import subprocess

import pytest

from scripts.release import audit_node_dependencies as gate
from scripts.release.dependency_audit import DependencyAuditError


def report(findings=None, *, total=1, high=0):
    return {
        "vulnerabilities": findings or {},
        "metadata": {
            "dependencies": {"total": total},
            "vulnerabilities": {"high": high, "critical": 0},
        },
    }


@pytest.mark.parametrize(
    ("data", "code", "passes"),
    [
        (report(), 0, True),
        (report({"example": {"via": [{"severity": "moderate"}]}}), 0, True),
        (
            report(
                {"example": {"via": [{"severity": "high", "source": "test"}]}},
                high=1,
            ),
            1,
            False,
        ),
        (report(high=1), 0, False),
        (report(), 1, False),
        (report(total=0), 0, False),
        (report(total=True), 0, False),
        ({"error": {"code": "ENOAUDIT"}}, 1, False),
        ({}, 0, False),
        (None, 0, False),
        (report(), 2, False),
    ],
)
def test_node_audit_fails_closed(tmp_path, monkeypatch, data, code, passes):
    policy = tmp_path / ".github/dependency-audit-policy.json"
    policy.parent.mkdir()
    policy.write_text('{"exceptions": []}', encoding="utf-8")
    monkeypatch.setattr(gate.shutil, "which", lambda name: "npm")

    def run(command, **kwargs):
        assert command == ["npm", "audit", "--json", "--audit-level=high"]
        assert kwargs["cwd"] == tmp_path
        assert kwargs["check"] is False
        kwargs["stdout"].write(json.dumps(data) if data is not None else "not JSON")
        return subprocess.CompletedProcess(command, code)

    monkeypatch.setattr(gate.subprocess, "run", run)
    if passes:
        gate.audit(tmp_path)
    else:
        with pytest.raises(DependencyAuditError):
            gate.audit(tmp_path)


def test_node_audit_requires_npm(tmp_path, monkeypatch):
    monkeypatch.setattr(gate.shutil, "which", lambda name: None)
    with pytest.raises(DependencyAuditError, match="requires npm"):
        gate.audit(tmp_path)


def test_local_gates_include_ci_node_audit():
    root = Path(__file__).resolve().parents[2]
    for name in ("push", "merge"):
        source = (root / f"scripts/check-dev-{name}.sh").read_text(encoding="utf-8")
        command = 'run "$GATE_PYTHON" -m scripts.release.audit_node_dependencies'
        assert command in source
        assert source.index(command) < source.index("npm run build")
