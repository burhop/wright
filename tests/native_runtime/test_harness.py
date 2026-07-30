from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

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
    assert args.hermes_command == "hermes"
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
    assert environment["WRIGHT_MANAGER_ID"] == "hermes"
    assert environment["WRIGHT_MANAGER_PROTOCOL"] == "hermes-git-plugin-v1"
    assert environment["WRIGHT_HOME"] == str(tmp_path / "wright-home")
    assert environment["PATH"] == str(
        plugin / ("Scripts" if os.name == "nt" else "bin")
    )
    HARNESS.assert_forbidden_tools_inaccessible(environment)


def test_hermes_install_temp_stays_on_the_test_home_volume(tmp_path: Path) -> None:
    hermes_home = tmp_path / "hermes-home"
    test_root = tmp_path / ".hermes-home-acceptance"

    environment = HARNESS.hermes_install_environment(
        hermes_home=hermes_home,
        test_root=test_root,
        base_environment={
            "PYTHONPATH": "source-leak",
            "WRIGHT_REPO_DIR": "source-leak",
            "KEEP": "value",
        },
    )

    expected_temp = str(test_root / "manager-temp")
    assert environment["HERMES_HOME"] == str(hermes_home)
    assert {environment[name] for name in ("TEMP", "TMP", "TMPDIR")} == {
        expected_temp
    }
    assert environment["KEEP"] == "value"
    assert "PYTHONPATH" not in environment
    assert "WRIGHT_REPO_DIR" not in environment


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


def test_subprocess_audit_tolerates_parent_exit_during_child_sampling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ProcessGone(Exception):
        pass

    class ExitedProcess:
        pid = 42
        returncode = 0

        def __init__(self) -> None:
            self._polls = iter((None, 0))

        def poll(self) -> int | None:
            return next(self._polls)

        def communicate(self) -> tuple[str, str]:
            return "", ""

    fake_psutil = SimpleNamespace(
        Error=ProcessGone,
        Process=lambda _pid: (_ for _ in ()).throw(ProcessGone()),
    )
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    monkeypatch.setattr(subprocess, "Popen", lambda *_args, **_kwargs: ExitedProcess())
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    completed = HARNESS.CommandAudit().run(
        [sys.executable, "-c", "pass"],
        cwd=tmp_path,
        env={},
    )

    assert completed.returncode == 0


def test_wheel_version_is_exact_and_rejects_non_wright_artifact(tmp_path: Path) -> None:
    candidate = tmp_path / "wright_engineering-0.1.5-py3-none-any.whl"
    candidate.write_bytes(b"wheel")
    assert HARNESS.wheel_version(candidate) == "0.1.5"
    with pytest.raises(HARNESS.HarnessError, match="not a Wright wheel"):
        HARNESS.wheel_version(tmp_path / "other-0.1.5-py3-none-any.whl")


def test_json_result_accepts_pretty_manager_output() -> None:
    completed = subprocess.CompletedProcess(
        ["manager"],
        0,
        '{\n  "ok": true,\n  "profile": "wright"\n}\n',
        "",
    )

    assert HARNESS._json_result(completed) == {"ok": True, "profile": "wright"}
