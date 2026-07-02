from __future__ import annotations

import json
from pathlib import Path

from core.tracing import traced

from .validation_evidence import ValidationEvidence


def _safe_name(server_id: str) -> str:
    return (
        "".join(
            char if char.isalnum() or char in {"-", "_"} else "-" for char in server_id
        ).strip("-")
        or "validation"
    )


@traced("mcp.validation.evidence.write")
def write_validation_evidence(
    evidence: ValidationEvidence,
    evidence_dir: str | Path,
    *,
    secrets: list[str] | None = None,
) -> tuple[Path, Path]:
    target_dir = Path(evidence_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    basename = f"{_safe_name(evidence.server_id)}-validation"
    json_path = target_dir / f"{basename}.json"
    markdown_path = target_dir / f"{basename}.md"
    redacted = evidence.redacted_model_dump(secrets)
    json_path.write_text(
        json.dumps(redacted, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_markdown_summary(redacted), encoding="utf-8")
    return json_path, markdown_path


def _markdown_summary(data: dict) -> str:
    lines = [
        f"# MCP Validation Evidence: {data['server_id']}",
        "",
        f"- Result: {data.get('result') or data.get('status')}",
        f"- Environment: {data.get('environment')}",
        f"- Container: {data.get('container_image') or 'not recorded'}",
        f"- Follow-up required: {data.get('follow_up_required')}",
        "",
        "## Diagnostics",
        "",
        str(data.get("diagnostics") or ""),
        "",
        "## Steps",
        "",
    ]
    for step in data.get("steps", []):
        lines.append(f"- {step.get('name')}: {step.get('status')}")
    if not data.get("steps"):
        lines.append("- No runtime probes were executed.")
    lines.extend(["", "## Redactions", ""])
    for redaction in data.get("redactions", []):
        lines.append(f"- {redaction}")
    if not data.get("redactions"):
        lines.append("- Default redaction rules applied.")
    return "\n".join(lines) + "\n"
