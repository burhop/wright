from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Release shell scripts require a POSIX shell; Windows CI validates them through Linux jobs.",
)


def test_package_build_helper_dry_run_validates_alpha_package() -> None:
    script = ROOT / "scripts/build-python-distributions.sh"
    command = [str(script)]
    if sys.platform == "win32":
        command = ["bash", str(script)]

    result = subprocess.run(
        command + ["--dry-run", "."],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert "metadata ok: wright-engineering" in result.stdout
    assert "Dry run completed" in result.stdout
