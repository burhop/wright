from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_package_build_helper_dry_run_validates_initial_packages() -> None:
    script = ROOT / "scripts/build-python-distributions.sh"
    command = [str(script)]
    if sys.platform == "win32":
        command = ["bash", str(script)]

    result = subprocess.run(
        command
        + [
            "--dry-run",
            "packages/core",
            "packages/tool_registry",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert "metadata ok: wright-core" in result.stdout
    assert "metadata ok: wright-tool-registry" in result.stdout
    assert "Dry run completed" in result.stdout
