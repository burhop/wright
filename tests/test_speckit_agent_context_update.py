from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / ".specify"
    / "extensions"
    / "agent-context"
    / "scripts"
    / "powershell"
    / "update-agent-context.ps1"
)


@pytest.mark.skipif(os.name != "nt", reason="Windows interpreter-alias regression")
def test_context_updater_falls_back_after_broken_python3_alias(
    tmp_path: Path,
) -> None:
    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        pytest.skip("PowerShell is not installed")
    if shutil.which("python") is None:
        pytest.skip("A working Python fallback is not installed")

    script = (
        tmp_path
        / ".specify"
        / "extensions"
        / "agent-context"
        / "scripts"
        / "powershell"
        / "update-agent-context.ps1"
    )
    script.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT, script)

    config = script.parents[2] / "agent-context-config.yml"
    config.write_text(
        "context_file: AGENTS.md\n"
        "context_markers:\n"
        "  start: '<!-- SPECKIT START -->'\n"
        "  end: '<!-- SPECKIT END -->'\n",
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text(
        "<!-- SPECKIT START -->\nold\n<!-- SPECKIT END -->\n",
        encoding="utf-8",
    )

    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    (shim_dir / "python3.cmd").write_text(
        "@echo Python was not found 1>&2\r\n@exit /b 9009\r\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join((str(shim_dir), env.get("PATH", "")))

    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "specs/050-native-hermes-install/plan.md",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "at specs/050-native-hermes-install/plan.md" in content, (
        result.stdout + result.stderr
    )
