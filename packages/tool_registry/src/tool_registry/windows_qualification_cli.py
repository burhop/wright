from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path
from typing import Sequence

from .windows_qualification_executor import validate_isolated_root
from .windows_qualification_models import (
    WINDOWS_MCP_ALLOWLIST,
    SafetyPreflight,
)
from .windows_qualification_recipes import (
    assert_allowlisted,
    get_windows_qualification_recipe,
    recipe_digest,
)
from .windows_qualification_service import WindowsQualificationService
from .windows_qualification_writer import (
    write_run_artifacts,
    write_server_evidence,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wright-windows-mcp-qualification")
    commands = parser.add_subparsers(dest="action", required=True)

    preview = commands.add_parser("preview")
    preview.add_argument("server_id")
    preview.add_argument("--evidence-dir", type=Path, required=True)

    qualify = commands.add_parser("qualify")
    qualify.add_argument("server_id")
    qualify.add_argument("--evidence-dir", type=Path, required=True)
    qualify.add_argument("--work-root", type=Path, required=True)
    qualify.add_argument("--safety-decision", type=Path, required=True)

    qualify_all = commands.add_parser("qualify-all")
    qualify_all.add_argument("--evidence-dir", type=Path, required=True)
    qualify_all.add_argument("--work-root", type=Path, required=True)
    qualify_all.add_argument("--decisions-dir", type=Path, required=True)
    return parser


def _require_native_windows() -> None:
    if platform.system() != "Windows":
        raise RuntimeError("native_windows_required")
    if platform.machine().casefold() not in {"amd64", "x86_64"}:
        raise RuntimeError("windows_x64_required")


def _load_decision(path: Path, server_id: str) -> SafetyPreflight:
    recipe = get_windows_qualification_recipe(server_id)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("server_id") != server_id:
        raise ValueError("safety_decision_identity_changed")
    if payload.get("recipe_digest") != recipe_digest(recipe):
        raise ValueError("safety_decision_recipe_changed")
    return SafetyPreflight.model_validate(payload.get("preflight"))


def _preview(server_id: str) -> dict:
    assert_allowlisted(server_id)
    recipe = get_windows_qualification_recipe(server_id)
    return {
        "server_id": recipe.server_id,
        "recipe_digest": recipe_digest(recipe),
        "publisher": recipe.publisher,
        "source": {
            "kind": recipe.source.kind,
            "url": recipe.source.url,
            "revision": recipe.source.immutable_revision,
            "package": recipe.source.package_name,
            "version": recipe.source.package_version,
            "maintenance": recipe.source.maintenance_expectation,
        },
        "locality": recipe.locality,
        "transport": recipe.transport,
        "host_requirements": recipe.host_requirements,
        "credential_requirements": recipe.credential_requirements,
        "risks": [
            {
                "capability": risk.capability,
                "severity": risk.severity,
                "boundary": risk.boundary,
            }
            for risk in recipe.risk_findings
        ],
        "planned_operations": [
            {"stage": operation.stage, "kind": operation.kind}
            for operation in [*recipe.operations, *recipe.cleanup]
        ],
    }


def _qualify_one(
    server_id: str,
    *,
    evidence_dir: Path,
    work_root: Path,
    decision_path: Path,
):
    assert_allowlisted(server_id)
    validated_root = validate_isolated_root(work_root)
    decision = _load_decision(decision_path, server_id)

    def checkpoint(evidence) -> None:
        write_server_evidence(
            evidence,
            evidence_dir,
            private_roots=[validated_root],
        )

    service = WindowsQualificationService(checkpoint=checkpoint)
    evidence = service.qualify(server_id, decision, validated_root)
    write_server_evidence(
        evidence,
        evidence_dir,
        private_roots=[validated_root],
    )
    return evidence


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.action == "preview":
            print(json.dumps(_preview(arguments.server_id), indent=2, sort_keys=True))
            return 0

        _require_native_windows()
        if arguments.action == "qualify":
            evidence = _qualify_one(
                arguments.server_id,
                evidence_dir=arguments.evidence_dir,
                work_root=arguments.work_root,
                decision_path=arguments.safety_decision,
            )
            write_run_artifacts([evidence], arguments.evidence_dir)
            print(
                json.dumps(
                    {
                        "server_id": evidence.server_id,
                        "result": evidence.terminal_classification,
                    }
                )
            )
            return 0

        validate_isolated_root(arguments.work_root)
        evidence_items = []
        for server_id in WINDOWS_MCP_ALLOWLIST:
            evidence_items.append(
                _qualify_one(
                    server_id,
                    evidence_dir=arguments.evidence_dir,
                    work_root=arguments.work_root,
                    decision_path=arguments.decisions_dir / f"{server_id}.json",
                )
            )
            write_run_artifacts(evidence_items, arguments.evidence_dir)
        print(json.dumps({"qualified_in_order": list(WINDOWS_MCP_ALLOWLIST)}))
        return 0
    except Exception as error:
        print(
            f"Qualification did not run ({type(error).__name__}).",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
