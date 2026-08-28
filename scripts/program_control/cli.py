"""Deterministic command-line rendering and bounded failure handling."""

from __future__ import annotations

import argparse
import copy
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Never

from .dashboard import DashboardError, atomic_replace_json, make_dashboard
from .git_subject import (
    GitReader,
    GitSubjectError,
    ensure_safe_checkout_target,
    normalize_repo_path,
)
from .json_contracts import ContractError, deterministic_json_bytes, strict_loads
from .validation import validate_program


EXIT_USAGE = 2
EXIT_SCHEMA = 3
EXIT_SEMANTIC = 4
EXIT_DELIVERY = 5
EXIT_COMPATIBILITY = 6
EXIT_INTERNAL = 70

_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_-]{2,99}$")
_SAFE_REPO_PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
_SENSITIVE_VALUE = re.compile(
    r"(?i)(?:password|passwd|secret|token|credential|authorization|bearer|api[_-]?key)\s*[:=]"
)


class BoundedArgumentParser(argparse.ArgumentParser):
    """Argparse variant that never echoes attacker-controlled argument values."""

    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, "error: invalid command arguments\n")


def build_parser() -> argparse.ArgumentParser:
    parser = BoundedArgumentParser(prog="validate-engineering-process-program")
    commands = parser.add_subparsers(
        dest="command", required=True, parser_class=BoundedArgumentParser
    )
    validate = commands.add_parser("validate", help="validate one committed source")
    validate.add_argument("--source", default="HEAD")
    validate.add_argument(
        "--container",
        help="explicit dashboard-only successor commit C (otherwise only HEAD may be inferred)",
    )
    validate.add_argument(
        "--delivery",
        help="explicit delivery-evidence successor commit D; never discovered implicitly",
    )
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


def _safe_code(value: Any, fallback: str) -> str:
    text = str(value)
    return text if _SAFE_CODE.fullmatch(text) else fallback


def _safe_repo_path(value: Any) -> str:
    text = str(value).replace("\\", "/")
    if _SAFE_REPO_PATH.fullmatch(text) and not text.startswith(("/", "../")):
        return text
    return "[redacted]"


def _safe_message(value: Any, fallback: str) -> str:
    text = str(value)
    if (
        len(text) > 500
        or "\n" in text
        or "\r" in text
        or _SENSITIVE_VALUE.search(text)
        or re.search(r"(?:[A-Za-z]:[\\/]|\\\\|/(?:home|Users|tmp|var)/)", text)
    ):
        return fallback
    return text


def _support_safe_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Copy a report and constrain free-form finding metadata at the output edge."""

    safe = copy.deepcopy(dict(report))
    for finding in safe.get("findings", []):
        finding["code"] = _safe_code(finding.get("code"), "VALIDATION_FAILURE")
        finding["invariant"] = _safe_code(
            finding.get("invariant"), "VALIDATION_INVARIANT"
        )
        finding["artifact"] = _safe_repo_path(finding.get("artifact", ""))
        pointer = finding.get("json_pointer")
        if pointer is not None:
            finding["json_pointer"] = _safe_message(pointer, "/redacted")
        finding["evidence"] = [
            _safe_message(item, "[redacted]")
            for item in list(finding.get("evidence", []))[:20]
        ]
        finding["consequence"] = _safe_message(
            finding.get("consequence"), "Validation invariant was not satisfied."
        )
        finding["recovery"] = _safe_message(
            finding.get("recovery"),
            "Inspect repository-relative evidence and repair the named invariant.",
        )
        correction = finding.get("correction_ref")
        if correction is not None:
            finding["correction_ref"] = _safe_repo_path(correction)
    return safe


def render_text(report: Mapping[str, Any]) -> str:
    subject = report["subject"]
    lines = [
        f"verdict: {report['verdict']}",
        f"source: {subject['source_commit'] or 'unresolved'}",
        f"tree: {subject['source_tree'] or 'unresolved'}",
        f"program_tree: {subject['program_tree'] or 'unresolved'}",
        f"container: {subject['container_commit'] or subject['container_resolution']}",
        f"delivery: {subject['delivery_commit'] or subject['delivery_resolution']}",
        f"worktree_clean: {str(subject['worktree_clean']).lower()}",
    ]
    validator = report.get("validator", {})
    if validator:
        lines.append(
            f"validator_bundle: {validator.get('bundle_manifest_digest', 'unresolved')}"
        )
    if "input_manifest_digest" in subject:
        lines.append(
            f"input_manifest: {subject.get('input_manifest_digest') or 'unresolved'}"
        )
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
    benchmark = report.get("benchmark_summary")
    if isinstance(benchmark, Mapping):
        lines.append(
            f"benchmark_progress: {benchmark.get('counted', 0)}/{benchmark.get('target', 100)}"
        )
    approval = report.get("release_approval")
    if isinstance(approval, Mapping):
        lines.append(f"release_approval: {approval.get('status', 'absent')}")
    eligibility = report.get("eligibility")
    if isinstance(eligibility, Mapping):
        lines.append(f"validation_blockers: {len(eligibility.get('blockers', []))}")
    for finding in report["findings"][:20]:
        disposition = _safe_code(
            finding.get("resolution_status", "unresolved").upper(), "UNRESOLVED"
        ).lower()
        pointer = _safe_message(finding.get("json_pointer") or "-", "[redacted]")
        correction_value = finding.get("correction_ref")
        correction = _safe_repo_path(correction_value) if correction_value else "-"
        lines.append(
            f"{_safe_code(finding.get('severity', '').upper(), 'ERROR').lower()} "
            f"{_safe_code(finding.get('code'), 'VALIDATION_FAILURE')} "
            f"{_safe_repo_path(finding.get('artifact', ''))} "
            f"{pointer} [{disposition}] correction={correction}: "
            f"{_safe_message(finding.get('recovery'), 'Inspect repository-relative evidence.')}"
        )
    action = report.get("next_action")
    omitted = max(0, len(report["findings"]) - 20)
    if omitted:
        lines.append(f"findings_omitted: {omitted}")
    lines.append(f"next_action: {action['action'] if action else 'none'}")
    return "\n".join(lines) + "\n"


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    report = _support_safe_report(report)
    if output_format == "json":
        sys.stdout.buffer.write(deterministic_json_bytes(report))
    else:
        sys.stdout.write(render_text(report))


def _bounded_failure(code: str, output_format: str, exit_code: int) -> int:
    safe_code = _safe_code(code, "INTERNAL_VALIDATION_FAILURE")
    payload = {
        "schema_version": "1.0",
        "verdict": "failed",
        "code": safe_code,
        "recovery": "Inspect repository-relative evidence and retry after the named invariant is repaired.",
    }
    if output_format == "json":
        sys.stdout.buffer.write(deterministic_json_bytes(payload))
    else:
        sys.stderr.write(f"failed {safe_code}: {payload['recovery']}\n")
    return exit_code


def _set_delivery(
    report: dict[str, Any],
    *,
    status: str,
    target_changed: bool,
    prior_snapshot_preserved: bool,
) -> None:
    """Update generation facts without discarding the validation envelope."""

    delivery = dict(report["delivery"])
    delivery.update(
        {
            "mode": "generate_dashboard",
            "status": status,
            "target_changed": target_changed,
            "prior_snapshot_preserved": prior_snapshot_preserved,
        }
    )
    report["delivery"] = delivery


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    output_format = str(args.format)
    try:
        program_root = normalize_repo_path(str(args.program_root))
        reader = GitReader.discover(Path.cwd())
        result = validate_program(
            reader,
            str(args.source),
            program_root,
            container=getattr(args, "container", None),
            delivery=getattr(args, "delivery", None),
        )
        report = result.report
        if args.command == "validate":
            _emit(report, output_format)
            return result.exit_code
        if result.exit_code != 0:
            _set_delivery(
                report,
                status="failed",
                target_changed=False,
                prior_snapshot_preserved=True,
            )
            _emit(report, output_format)
            return result.exit_code
        expected = f"{program_root}/dashboard.json"
        output = normalize_repo_path(str(args.output))
        if output != expected:
            return _bounded_failure(
                "OUTPUT_TARGET_UNDECLARED", output_format, EXIT_USAGE
            )
        target = ensure_safe_checkout_target(reader.repo_root, output)
        schema = strict_loads(
            reader.blob(
                str(report["subject"]["source_commit"]),
                f"{program_root}/schemas/dashboard.schema.json",
            )
        )
        dashboard = make_dashboard(report, data_cutoff=result.dashboard_data_cutoff)
        try:
            atomic_replace_json(target, dashboard, schema)
        except DashboardError:
            _set_delivery(
                report,
                status="failed",
                target_changed=False,
                prior_snapshot_preserved=True,
            )
            _emit(report, output_format)
            return EXIT_DELIVERY
        _set_delivery(
            report,
            status="candidate_not_evidence",
            target_changed=True,
            prior_snapshot_preserved=False,
        )
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
