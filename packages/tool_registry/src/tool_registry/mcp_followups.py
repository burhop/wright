from __future__ import annotations

import re
from pathlib import Path

from .mcp_validation import ValidationResult

SECRET_PATTERN = re.compile(
    r"(?i)(token|secret|password|api[_-]?key)\s*[:=]\s*([^\s]+)"
)


def redact_secrets(text: str) -> str:
    return SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", text)


def followup_path(root: Path, server_id: str) -> Path:
    return root / f"{server_id}.md"


def write_followup_record(
    root: str | Path,
    result: ValidationResult,
    source_url: str | None = None,
    verification_state: str = "unknown",
) -> str:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    path = followup_path(root_path, result.server_id)
    if path.exists():
        return str(path)

    diagnostics = redact_secrets(result.diagnostics or result.message)
    source = source_url or "TBD"
    content = f"""# Investigate MCP Server: {result.server_id}

## Server ID

{result.server_id}

## Source URL

{source}

## Verification State

{verification_state}

## Current Installability Tier

{result.installability_tier}

## Environment

{result.environment}

## Observed Failure

{diagnostics}

## Expected Behavior

The server should either install and complete a safe MCP initialization/tools-list probe, or report a declared missing host dependency without an ambiguous failure.

## Reproduction Steps

1. Run catalog validation for `{result.server_id}` in `{result.environment}`.
2. Review the validation diagnostics above.

## Missing Context Or Dependencies

{", ".join(result.missing_dependencies) if result.missing_dependencies else "None recorded."}

## Suggested Next Action

Verify the upstream package/source and update the catalog metadata, install command, or blocked reason.

## GitHub PR/Issue URL

TBD
"""
    path.write_text(content, encoding="utf-8")
    return str(path)
