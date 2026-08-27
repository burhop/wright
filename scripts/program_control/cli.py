"""Deterministic command-line rendering and bounded failure handling."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .dashboard import DashboardError, atomic_replace_json, make_dashboard
from .git_subject import (
    GitReader,
    GitSubjectError,
    ensure_safe_checkout_target,
    normalize_repo_path,
)
from .json_contracts import ContractError, deterministic_json_bytes, strict_load
from .validation import validate_program


EXIT_USAGE = 2
EXIT_SCHEMA = 3
EXIT_SEMANTIC = 4
EXIT_DELIVERY = 5
EXIT_COMPATIBILITY = 6
EXIT_INTERNAL = 70


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="validate-engineering-process-program")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one committed source")
    validate.add_argument("--source", default="HEAD")
    validate.add_argument(
        "--program-root", default="docs/programs/engineering-process-platform"
    )
    validate.add_argument("--format", choices=("text", "json"), default="text")
    generate = commands.add_parser(
        "generate-dashboard", help="generate one local dashboard candidate"
    )
    generate.add_argument("--source", required=True)
    generate.add_argument(
        "--program-root", default="docs/programs/engineering-process-platform"
    )
    generate.add_argument("--output", required=True)
    generate.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def render_text(report: Mapping[str, Any]) -> str:
    subject = report["subject"]
    lines = [
        f"verdict: {report['verdict']}",
        f"source: {subject['source_commit'] or 'unresolved'}",
        f"tree: {subject['source_tree'] or 'unresolved'}",
        f"program_tree: {subject['program_tree'] or 'unresolved'}",
        f"worktree_clean: {str(subject['worktree_clean']).lower()}",
    ]
    for area in (
        "product_readiness",
        "benchmark_readiness",
        "commercial_readiness",
        "program_health",
    ):
        value = report["areas"][area]
        lines.append(
            f"{area}: {value['status']} ({value['passed_gates']}/{value['required_gates']})"
        )
    lines.append(f"release_eligible: {str(report['release_eligible']).lower()}")
    for finding in report["findings"][:20]:
        lines.append(
            f"{finding['severity']} {finding['code']} {finding['artifact']}: {finding['recovery']}"
        )
    action = report.get("next_action")
    lines.append(f"next_action: {action['action'] if action else 'none'}")
    return "\n".join(lines) + "\n"


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        sys.stdout.buffer.write(deterministic_json_bytes(report))
    else:
        sys.stdout.write(render_text(report))


def _bounded_failure(code: str, output_format: str, exit_code: int) -> int:
    payload = {
        "schema_version": "1.0",
        "verdict": "failed",
        "code": code,
        "recovery": "Inspect repository-relative evidence and retry after the named invariant is repaired.",
    }
    if output_format == "json":
        sys.stdout.buffer.write(deterministic_json_bytes(payload))
    else:
        sys.stderr.write(f"failed {code}: {payload['recovery']}\n")
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_format = str(args.format)
    try:
        program_root = normalize_repo_path(str(args.program_root))
        reader = GitReader.discover(Path.cwd())
        result = validate_program(reader, str(args.source), program_root)
        report = result.report
        if args.command == "validate":
            _emit(report, output_format)
            return result.exit_code
        if result.exit_code != 0:
            report["delivery"] = {
                "mode": "generate_dashboard",
                "status": "failed",
                "target_changed": False,
                "prior_snapshot_preserved": True,
            }
            _emit(report, output_format)
            return result.exit_code
        expected = f"{program_root}/dashboard.json"
        output = normalize_repo_path(str(args.output))
        if output != expected:
            return _bounded_failure(
                "OUTPUT_TARGET_UNDECLARED", output_format, EXIT_USAGE
            )
        target = ensure_safe_checkout_target(reader.repo_root, output)
        schema_path = (
            reader.repo_root / program_root / "schemas" / "dashboard.schema.json"
        )
        schema = strict_load(schema_path)
        dashboard = make_dashboard(report)
        atomic_replace_json(target, dashboard, schema)
        report["delivery"] = {
            "mode": "generate_dashboard",
            "status": "candidate_not_evidence",
            "target_changed": True,
            "prior_snapshot_preserved": False,
        }
        _emit(report, output_format)
        return 0
    except (GitSubjectError, ContractError):
        return _bounded_failure("INPUT_CONTRACT_INVALID", output_format, EXIT_SCHEMA)
    except DashboardError as exc:
        return _bounded_failure(exc.code, output_format, EXIT_DELIVERY)
    except Exception:
        return _bounded_failure(
            "INTERNAL_VALIDATION_FAILURE", output_format, EXIT_INTERNAL
        )
