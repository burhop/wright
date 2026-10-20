from __future__ import annotations

import argparse
import sys


class HermesDependencyReconciliationError(ValueError):
    """Raised when uv reports anything outside the reviewed Hermes exceptions."""


EXPECTED_CONFLICTS = {
    "The package `hermes-agent` requires `certifi==2026.5.20`, "
    "but `2026.10.19` is installed",
    "The package `hermes-agent` requires `cryptography==46.0.7`, "
    "but `50.0.0` is installed",
    "The package `hermes-agent` requires `pillow==12.2.0`, but `12.3.0` is installed",
    "The package `hermes-agent` requires `pyjwt[crypto]==2.13.0`, "
    "but `2.15.1` is installed",
}


def reconcile_pip_check(output: str, exit_code: int) -> None:
    """Accept a clean check or exactly the reviewed Hermes 0.19 conflicts."""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    conflict_lines = [line for line in lines if line.startswith("The package `")]

    if exit_code == 0:
        if conflict_lines:
            raise HermesDependencyReconciliationError(
                "uv pip check exited successfully but reported incompatibilities"
            )
        return

    if exit_code != 1:
        raise HermesDependencyReconciliationError(
            f"uv pip check exited with unexpected status {exit_code}"
        )

    expected_count = len(EXPECTED_CONFLICTS)
    if f"Found {expected_count} incompatibilities" not in lines:
        raise HermesDependencyReconciliationError(
            f"uv pip check did not report exactly {expected_count} incompatibilities"
        )

    if (
        len(conflict_lines) != expected_count
        or set(conflict_lines) != EXPECTED_CONFLICTS
    ):
        unexpected = sorted(set(conflict_lines) - EXPECTED_CONFLICTS)
        missing = sorted(EXPECTED_CONFLICTS - set(conflict_lines))
        raise HermesDependencyReconciliationError(
            f"unexpected Hermes dependency conflicts; missing={missing}, "
            f"unexpected={unexpected}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Strictly reconcile reviewed Hermes 0.19 uv pip conflicts."
    )
    parser.add_argument("--exit-code", required=True, type=int)
    args = parser.parse_args()

    try:
        reconcile_pip_check(sys.stdin.read(), args.exit_code)
    except HermesDependencyReconciliationError as exc:
        print(f"Hermes dependency reconciliation failed: {exc}", file=sys.stderr)
        return 1

    if args.exit_code == 0:
        print("uv pip check passed without reconciliation.")
    else:
        print(
            "Accepted only the reviewed Hermes 0.19 certifi/cryptography/Pillow/PyJWT "
            "security overrides."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
