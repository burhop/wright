import subprocess
import sys


def test_generated_frontend_contracts_are_current():
    result = subprocess.run(
        [sys.executable, "scripts/generate-frontend-contracts.py", "--check"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
