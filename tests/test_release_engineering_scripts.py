from pathlib import Path
import os
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def run_help(script: str) -> str:
    script_path = ROOT / script
    command = [str(script_path)]
    if sys.platform == "win32":
        command = ["bash", str(script_path)]

    result = subprocess.run(
        command + ["--help"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout + result.stderr


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Release shell scripts require a POSIX shell; Windows CI validates them through Linux jobs.",
)
def test_release_engineering_scripts_are_executable_and_documented() -> None:
    scripts = [
        "scripts/build-python-distributions.sh",
        "scripts/sync-hermes-plugin-mirror.sh",
        "scripts/validate-hermes-plugin-mirror.sh",
    ]

    readme = (ROOT / "scripts/README.md").read_text(encoding="utf-8")
    for script in scripts:
        path = ROOT / script
        assert path.exists(), script
        if os.name != "nt":
            assert path.stat().st_mode & 0o111, script
        help_text = run_help(script)
        assert "Usage:" in help_text
        assert Path(script).name in readme


def test_makefile_exposes_mirror_and_package_validation_targets() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")

    for target in [
        "python-package-build-check:",
        "hermes-plugin-mirror-validate:",
        "hermes-plugin-mirror-sync-dry-run:",
        "hermes-plugin-root-lifecycle-test:",
    ]:
        assert target in makefile

    mirror_target = makefile.split("hermes-plugin-mirror-validate:", 1)[1].split(
        "hermes-plugin-root-lifecycle-test:", 1
    )[0]
    assert "set -e;" in mirror_target


def test_mirror_scripts_respect_explicit_python_interpreter() -> None:
    for script_name, expected_uses in [
        ("sync-hermes-plugin-mirror.sh", 4),
        ("validate-hermes-plugin-mirror.sh", 1),
    ]:
        script = (ROOT / "scripts" / script_name).read_text(encoding="utf-8")

        assert 'PYTHON_CMD=("$PYTHON")' in script
        assert script.count('"${PYTHON_CMD[@]}" -') == expected_uses
        assert "python3 - " not in script


def test_dev_merge_gate_reproducibly_bootstraps_package_build_frontend() -> None:
    gate = (ROOT / "scripts" / "check-dev-merge.sh").read_text(encoding="utf-8")

    assert "uv sync --all-packages --all-groups --reinstall-package wright-engineering" in gate
    assert "uv run --with mypy mypy" in gate
    assert "scripts/build-python-distributions.sh --dist-root" in gate
    assert "WRIGHT_API_MCP_AUTOSTART=1" in gate


def test_package_builder_emits_shell_values_without_windows_carriage_returns() -> None:
    script = (ROOT / "scripts" / "build-python-distributions.sh").read_text(
        encoding="utf-8"
    )

    assert "data['project']['name']), end=\"\")" in script
