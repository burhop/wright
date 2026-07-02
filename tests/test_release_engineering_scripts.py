from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run_help(script: str) -> str:
    result = subprocess.run(
        [str(ROOT / script), "--help"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout + result.stderr


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
