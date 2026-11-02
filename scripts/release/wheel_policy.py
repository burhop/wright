"""Apply the pinned wheel checker with exact Wright resource classifications."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from check_wheel_contents.checker import WheelChecker
from check_wheel_contents.checks import FailedCheck
from check_wheel_contents.contents import WheelContents

from .python_artifacts import validate_native_distribution


POLICY_VERSION = "wright-native-wheel-v1"
TEMPLATE_ROOT = "workspace_service/engineering_workflow_templates"

# These are data copies with distinct runtime lookup identities. Removing or
# renaming them would break the existing template/validator/editor bindings.
DUPLICATE_RESOURCE_GROUPS = (
    frozenset(
        {
            f"{TEMPLATE_ROOT}/inputs/replacement-drawer-handle/validation-profile.json",
            "workspace_service/process_validation/profiles/printed-replacement-part-02.json",
        }
    ),
    frozenset(
        f"{TEMPLATE_ROOT}/layouts/{name}.json"
        for name in (
            "heat-spreader-sizing",
            "lightweight-equipment-bracket",
            "parametric-drill-jig",
            "printed-replacement-part",
            "raspberry-pi-enclosure",
            "replacement-drawer-handle",
            "robot-tracking-diagnosis",
            "sensor-fan-harness",
            "sensor-interface-pcb",
            "sheet-metal-supplier-handoff",
            "water-heater-sizing",
        )
    ),
    frozenset(
        {
            "workspace_service/_rivet/editor/dist/favicon.png",
            "workspace_service/_rivet/editor/dist/rivet-icon-macos.png",
        }
    ),
)

# These files are existing path-addressed setup resources, not importable
# modules. The hyphenated resource directory is part of their accepted binding.
PATH_ADDRESSED_SCRIPTS = frozenset(
    f"{TEMPLATE_ROOT}/setup_resources/printed-replacement-part/{name}"
    for name in (
        "native_inspection.py",
        "orca-preparation.py",
        "orca_binding.py",
        "orca_stages.py",
        "orientation_stages.py",
        "prepare.py",
        "provider_inputs.py",
        "repair_gate.py",
        "retained_source.py",
        "run_disclosure.py",
        "scenario_inputs.py",
    )
)
NATIVE_PACKAGE_ROOTS = frozenset(
    f"{name}/"
    for name in (
        "wright",
        "wright_engineering",
        "api",
        "agent_adapters",
        "core",
        "data_vault",
        "model_registry",
        "tool_registry",
        "workspace_service",
    )
)


class WheelPolicyError(ValueError):
    """An artifact has an unreviewed wheel-layout finding."""


def reviewed_resource(finding: FailedCheck) -> bool:
    paths = frozenset(finding.args)
    if finding.check.name == "W002":
        return len(paths) > 1 and any(
            paths <= group for group in DUPLICATE_RESOURCE_GROUPS
        )
    if finding.check.name == "W004":
        return bool(paths) and paths <= PATH_ADDRESSED_SCRIPTS
    if finding.check.name == "W009":
        return paths == NATIVE_PACKAGE_ROOTS
    return False


def inspect_findings(contents: WheelContents) -> list[FailedCheck]:
    # Do not load cwd-dependent ignores: every check runs, including W009.
    findings = WheelChecker().check_contents(contents)
    blocked = [finding for finding in findings if not reviewed_resource(finding)]
    if blocked:
        raise WheelPolicyError("\n".join(finding.show() for finding in blocked))
    return findings


def validate_wheel(path: Path) -> list[FailedCheck]:
    validate_native_distribution(path)
    return inspect_findings(WheelContents.from_wheel(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheels", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for wheel in args.wheels:
        try:
            findings = validate_wheel(wheel)
        except ValueError as error:
            print(f"{wheel.name}: {error}", file=sys.stderr)
            return 1
        print(
            json.dumps(
                {
                    "policy": POLICY_VERSION,
                    "wheel": wheel.name,
                    "reviewed_resources": [
                        {"code": finding.check.name, "paths": finding.args}
                        for finding in findings
                    ],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
