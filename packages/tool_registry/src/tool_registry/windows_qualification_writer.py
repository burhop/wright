from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from core.redaction import redact_mapping, redact_text
from jsonschema import Draft202012Validator, FormatChecker

from .windows_qualification_models import (
    MAX_EVIDENCE_BYTES,
    ServerQualificationEvidence,
    WindowsQualificationStatus,
    WindowsQualificationSummary,
)

_STAGE_LABELS = {
    "source_current": "Source",
    "windows_install_passed": "Package or registration",
    "mcp_started": "Startup",
    "protocol_passed": "Protocol",
    "safe_probe_passed": "Host or backend",
    "wright_install_passed": "Wright setup",
    "wright_gateway_passed": "Wright gateway",
    "cleanup_passed": "Cleanup",
}

_PASSED_LABELS = {
    "source_current": "Source reviewed",
    "windows_install_passed": "MCP package installed",
    "mcp_started": "MCP server started",
    "protocol_passed": "MCP protocol passed",
    "safe_probe_passed": "Approved probe passed",
    "wright_install_passed": "Added to Wright",
    "wright_gateway_passed": "Available through Wright gateway",
    "cleanup_passed": "Cleanup complete",
}

_REASON_LABELS = {
    "safe_probe_upstream_entrypoint_defect": "Upstream tool startup bug",
    "safe_probe_output_schema_mismatch": "Status result violates MCP schema",
    "wright_external_license_incomplete": "Publisher terms not recorded",
    "official_repository_archived_and_credentials_required": "Official source archived",
    "no_preconfigured_clean_fusion_mcp_session": "Clean Fusion session unavailable",
    "oauth_and_exact_credential_free_endpoint_unavailable": "OAuth safety boundary",
    "official_labs_page_still_marks_mcp_coming_soon": "Preview not generally available",
    "no_local_package": "No local package required",
}

_FALLBACK_RESULT_LABELS = {
    "partial": "Partially validated",
    "failed": "Validation failed",
    "safety_blocked": "Not run - safety blocked",
    "obsolete_or_unavailable": "Not available",
    "not_applicable": "Not applicable",
    "not_tested": "Not tested",
}

_SUMMARY_FIELDS = {
    "source_current": "source",
    "windows_install_passed": "package_or_registration",
    "mcp_started": "startup",
    "protocol_passed": "protocol",
    "safe_probe_passed": "host_or_backend",
    "wright_install_passed": "wright_setup",
    "wright_gateway_passed": "gateway",
    "cleanup_passed": "cleanup",
}


@dataclass(frozen=True, slots=True)
class EvidenceWriteResult:
    json_path: Path
    markdown_path: Path
    digest: str


def build_catalog_summary(
    evidence: ServerQualificationEvidence,
    *,
    evidence_path: str,
    evidence_digest: str,
) -> WindowsQualificationSummary:
    """Project bounded evidence into the catalog without inventing a pass claim."""

    statuses: dict[str, WindowsQualificationStatus] = {}
    stage_results = {stage.stage: stage.result for stage in evidence.stages}
    for stage in evidence.stages:
        label = _REASON_LABELS.get(stage.reason_code)
        if label is None and stage.result == "passed":
            label = _PASSED_LABELS[stage.stage]
        if label is None:
            label = _FALLBACK_RESULT_LABELS[stage.result]
        statuses[_SUMMARY_FIELDS[stage.stage]] = WindowsQualificationStatus(
            result=stage.result,
            label=label,
            reason_code=stage.reason_code,
        )

    return WindowsQualificationSummary(
        observed_at=evidence.observed_at,
        evidence_path=evidence_path,
        evidence_digest=evidence_digest,
        current=not evidence.stale_reasons,
        stale_reasons=evidence.stale_reasons,
        claim=(
            "Installs on Windows with no problems"
            if all(
                stage_results[stage] == "passed"
                for stage in (
                    "windows_install_passed",
                    "mcp_started",
                    "protocol_passed",
                    "safe_probe_passed",
                    "wright_install_passed",
                    "cleanup_passed",
                )
            )
            else None
        ),
        **statuses,
    )


def _replace_private_values(value: Any, private_roots: Iterable[Path]) -> Any:
    roots = sorted(
        {str(Path(root).resolve()) for root in private_roots},
        key=len,
        reverse=True,
    )
    if isinstance(value, dict):
        return {
            str(key): _replace_private_values(item, private_roots)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_private_values(item, private_roots) for item in value]
    if isinstance(value, str):
        redacted = redact_text(value)
        for root in roots:
            redacted = redacted.replace(root, "[REDACTED_PATH]")
            redacted = redacted.replace(root.replace("\\", "/"), "[REDACTED_PATH]")
        return redacted
    return value


def _redacted_payload(
    evidence: ServerQualificationEvidence,
    *,
    private_roots: Iterable[Path],
    secrets: Iterable[str],
) -> dict[str, Any]:
    raw = evidence.model_dump(mode="json")
    payload = redact_mapping(raw)
    # This is a one-way binding hash used for staleness, not a credential.
    payload["credential_binding_digest"] = raw["credential_binding_digest"]
    payload = _replace_private_values(payload, private_roots)
    serialized = json.dumps(payload, sort_keys=True)
    for secret in secrets:
        if secret:
            serialized = serialized.replace(str(secret), "[REDACTED]")
    return json.loads(serialized)


def _validate_payload(payload: dict[str, Any]) -> bytes:
    schema_path = Path(
        str(
            files("tool_registry").joinpath(
                "catalog", "windows-qualification-evidence.schema.json"
            )
        )
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "evidence"
        raise ValueError(f"{location}: {first.message}")
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > MAX_EVIDENCE_BYTES:
        raise ValueError("qualification evidence exceeds the 1 MiB limit")
    return encoded


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_bytes(content)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Windows MCP Qualification: {payload['server_id']}",
        "",
        f"- Result: **{payload['terminal_classification']}**",
        f"- Observed: {payload['observed_at']}",
        f"- Safety decision: {payload['safety_preflight']['decision']}",
        f"- Evidence ID: `{payload['evidence_id']}`",
        "",
        "## Qualification boundaries",
        "",
        "| Boundary | Result | What was established | Recovery |",
        "|---|---|---|---|",
    ]
    for stage in payload["stages"]:
        label = _STAGE_LABELS[stage["stage"]]
        summary = str(stage.get("summary") or "").replace("|", "\\|")
        recovery = str(stage.get("recovery") or "").replace("|", "\\|")
        lines.append(f"| {label} | {stage['result']} | {summary} | {recovery} |")
    lines.extend(
        [
            "",
            "## Audit proof",
            "",
            f"- Attempted identity: `{payload['server_id']}`",
            f"- Non-allowlist actions: {len(payload['non_allowlist_actions'])}",
            f"- Installed items recorded: {len(payload['installed_items'])}",
            f"- Cleanup events recorded: {len(payload['cleanup_events'])}",
            "",
        ]
    )
    return "\n".join(lines)


def write_server_evidence(
    evidence: ServerQualificationEvidence,
    evidence_dir: str | Path,
    *,
    private_roots: Iterable[Path] = (),
    secrets: Iterable[str] = (),
) -> EvidenceWriteResult:
    target = Path(evidence_dir)
    basename = f"{evidence.server_id}-windows-qualification"
    payload = _redacted_payload(
        evidence,
        private_roots=private_roots,
        secrets=secrets,
    )
    encoded = _validate_payload(payload)
    json_path = target / f"{basename}.json"
    markdown_path = target / f"{basename}.md"
    _atomic_write(json_path, encoded)
    _atomic_write(markdown_path, _markdown(payload).encode("utf-8"))
    return EvidenceWriteResult(
        json_path=json_path,
        markdown_path=markdown_path,
        digest=hashlib.sha256(encoded).hexdigest(),
    )


def write_run_artifacts(
    evidence_items: Iterable[ServerQualificationEvidence], evidence_dir: str | Path
) -> dict[str, Path]:
    items = list(evidence_items)
    target = Path(evidence_dir)
    target.mkdir(parents=True, exist_ok=True)
    matrix_lines = [
        "# Native Windows MCP Qualification Matrix",
        "",
        "| MCP server | Source | Package or registration | Startup | Protocol | Host/backend | Wright setup | Wright gateway | Cleanup | Overall |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for evidence in items:
        results = [stage.result for stage in evidence.stages]
        matrix_lines.append(
            "| "
            + " | ".join(
                [evidence.server_id, *results, evidence.terminal_classification]
            )
            + " |"
        )
    matrix_lines.append("")

    installed = [
        {"server_id": evidence.server_id, "item": item}
        for evidence in items
        for item in evidence.installed_items
    ]
    cleanup = [
        {"server_id": evidence.server_id, "event": event}
        for evidence in items
        for event in evidence.cleanup_events
    ]
    denied = [action for evidence in items for action in evidence.non_allowlist_actions]
    progress_lines = ["# Windows MCP Qualification Progress", ""]
    progress_lines.extend(
        f"- {evidence.observed_at.isoformat()}: `{evidence.server_id}` -> "
        f"**{evidence.terminal_classification}**"
        for evidence in items
    )
    progress_lines.append("")

    paths = {
        "matrix": target / "qualification-matrix.md",
        "progress": target / "progress-log.md",
        "installed_items": target / "installed-items.json",
        "cleanup_ledger": target / "cleanup-ledger.json",
        "non_allowlist_proof": target / "non-allowlist-proof.json",
    }
    _atomic_write(paths["matrix"], "\n".join(matrix_lines).encode("utf-8"))
    _atomic_write(paths["progress"], "\n".join(progress_lines).encode("utf-8"))
    _atomic_write(
        paths["installed_items"],
        (json.dumps(installed, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _atomic_write(
        paths["cleanup_ledger"],
        (json.dumps(cleanup, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _atomic_write(
        paths["non_allowlist_proof"],
        (json.dumps({"actions": denied, "count": len(denied)}, indent=2) + "\n").encode(
            "utf-8"
        ),
    )
    return paths
