from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_package_build_helper_dry_run_validates_initial_packages() -> None:
    result = subprocess.run(
        [
            str(ROOT / "scripts/build-python-distributions.sh"),
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
