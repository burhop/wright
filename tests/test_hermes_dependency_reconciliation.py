import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location(
    "wright_hermes_pip_reconciliation",
    ROOT / "scripts" / "reconcile_hermes_pip_check.py",
)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
RECONCILIATION = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(RECONCILIATION)


EXPECTED_OUTPUT = """Using Python 3.13.13 environment at: /opt/hermes/.venv
Checked 83 packages in 3ms
Found 2 incompatibilities
The package `hermes-agent` requires `cryptography==46.0.7`, but `49.0.0` is installed
The package `hermes-agent` requires `pillow==12.2.0`, but `12.3.0` is installed
"""


def test_accepts_only_reviewed_hermes_security_overrides() -> None:
    RECONCILIATION.reconcile_pip_check(EXPECTED_OUTPUT, 1)


def test_accepts_clean_uv_pip_check() -> None:
    RECONCILIATION.reconcile_pip_check("All installed packages are compatible\n", 0)


@pytest.mark.parametrize(
    ("output", "exit_code"),
    [
        (EXPECTED_OUTPUT.replace("Found 2", "Found 3"), 1),
        (EXPECTED_OUTPUT.replace("49.0.0", "50.0.0"), 1),
        (
            EXPECTED_OUTPUT
            + "The package `other` requires `safe==1`, but `2` is installed\n",
            1,
        ),
        (EXPECTED_OUTPUT, 2),
    ],
)
def test_rejects_any_unreviewed_or_changed_conflict(
    output: str, exit_code: int
) -> None:
    with pytest.raises(RECONCILIATION.HermesDependencyReconciliationError):
        RECONCILIATION.reconcile_pip_check(output, exit_code)
