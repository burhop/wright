from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/test-native-hermes-install.py"
SPEC = importlib.util.spec_from_file_location("native_hermes_harness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HARNESS
SPEC.loader.exec_module(HARNESS)


def test_harness_requires_exact_candidate_wheel_and_evidence_paths() -> None:
    parser = HARNESS.build_parser()
    args = parser.parse_args(
        [
            "--wheel",
            "candidate.whl",
            "--hermes-home",
            "hermes",
            "--wheelhouse",
            "wheelhouse",
            "--evidence",
            "evidence.json",
        ]
    )
    assert args.wheel == Path("candidate.whl")
    assert args.previous_wheel is None
    assert not args.base_only


def test_clean_child_environment_removes_source_and_forbidden_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTHONPATH", str(ROOT))
    monkeypatch.setenv("WRIGHT_REPO_DIR", str(ROOT))
    plugin = tmp_path / "plugin"
    (plugin / ("Scripts" if os.name == "nt" else "bin")).mkdir(parents=True)
    environment = HARNESS.clean_child_environment(
        plugin_environment=plugin,
        hermes_home=tmp_path / "hermes",
        port=8765,
    )
    assert "PYTHONPATH" not in environment
    assert "WRIGHT_REPO_DIR" not in environment
    assert environment["HERMES_PLUGIN_INSTALL_CAPABILITY"] == "python-distribution-v1"
    assert environment["PATH"] == str(
        plugin / ("Scripts" if os.name == "nt" else "bin")
    )
    HARNESS.assert_forbidden_tools_inaccessible(environment)


def test_source_checkout_leak_is_rejected(tmp_path: Path) -> None:
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    HARNESS.assert_source_isolation(
        cwd=isolated,
        sys_path=[str(tmp_path / "site-packages")],
        repository_root=ROOT,
    )
    with pytest.raises(HARNESS.HarnessError, match="source checkout"):
        HARNESS.assert_source_isolation(
            cwd=ROOT,
            sys_path=[],
            repository_root=ROOT,
        )
    with pytest.raises(HARNESS.HarnessError, match="leaked"):
        HARNESS.assert_source_isolation(
            cwd=isolated,
            sys_path=[str(ROOT / "src")],
            repository_root=ROOT,
        )


def test_subprocess_audit_fails_if_forbidden_executable_is_observed() -> None:
    audit = HARNESS.CommandAudit()
    audit._record("python")
    audit._record("git.exe")
    assert audit.forbidden == {"git.exe"}


def test_wheel_version_is_exact_and_rejects_non_wright_artifact(tmp_path: Path) -> None:
    candidate = tmp_path / "wright_engineering-0.1.5-py3-none-any.whl"
    candidate.write_bytes(b"wheel")
    assert HARNESS.wheel_version(candidate) == "0.1.5"
    with pytest.raises(HARNESS.HarnessError, match="not a Wright wheel"):
        HARNESS.wheel_version(tmp_path / "other-0.1.5-py3-none-any.whl")
