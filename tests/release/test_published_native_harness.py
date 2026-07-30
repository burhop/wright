from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
import time
import types


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "test-published-native-hermes.py"
SPEC = importlib.util.spec_from_file_location("published_native_harness", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
_RELEASE_MODULES = ("release", "release.hermes_capability")
_PREVIOUS_RELEASE_MODULES = {
    name: sys.modules.pop(name, None) for name in _RELEASE_MODULES
}
_RELEASE_STUB = types.ModuleType("release")
_RELEASE_STUB.__path__ = []
_CAPABILITY_STUB = types.ModuleType("release.hermes_capability")
_CAPABILITY_STUB.require_released_git_plugin_interface = lambda: None
sys.modules["release"] = _RELEASE_STUB
sys.modules["release.hermes_capability"] = _CAPABILITY_STUB
try:
    SPEC.loader.exec_module(HARNESS)
finally:
    for name in reversed(_RELEASE_MODULES):
        sys.modules.pop(name, None)
    sys.modules.update(
        {
            name: module
            for name, module in _PREVIOUS_RELEASE_MODULES.items()
            if module is not None
        }
    )


def test_run_does_not_wait_for_descendant_inheriting_standard_handles(
    tmp_path: Path,
) -> None:
    child = "import time; time.sleep(2)"
    parent = (
        "import subprocess,sys;"
        f"subprocess.Popen([sys.executable,'-c',{child!r}]);"
        "print('parent-complete')"
    )

    started = time.monotonic()
    result = HARNESS._run(
        [sys.executable, "-c", parent],
        env=dict(os.environ),
        cwd=tmp_path,
        timeout=5,
    )

    assert time.monotonic() - started < 1.5
    assert result.stdout.strip() == "parent-complete"


def test_wait_for_doctor_retries_transient_health_findings(
    monkeypatch, tmp_path: Path
) -> None:
    results = iter(
        [
            {
                "ok": False,
                "code": "doctor_findings",
                "details": {"checks": {"api": {"ok": False}}},
            },
            {"ok": True, "code": "ok", "details": {"checks": {}}},
        ]
    )
    calls: list[str] = []

    def fake_lifecycle(*_args, **kwargs):
        calls.append(kwargs.get("require_ok"))
        return next(results)

    monkeypatch.setattr(HARNESS, "_adapter_lifecycle", fake_lifecycle)

    result = HARNESS._wait_for_doctor(
        tmp_path,
        env={},
        cwd=tmp_path,
        timeout=1,
        interval=0,
    )

    assert result["ok"] is True
    assert calls == [False, False]


def test_failed_doctor_checks_reports_only_unhealthy_core_checks() -> None:
    result = {
        "details": {
            "checks": {
                "api": {"ok": False},
                "manifest": {"ok": True},
                "manager": "invalid",
            }
        }
    }

    assert HARNESS._failed_doctor_checks(result) == ["api", "manager"]
