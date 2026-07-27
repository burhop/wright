from __future__ import annotations

from pathlib import Path
import re


ACTION_RE = re.compile(r"^\s*uses:\s*([^#\s]+)", re.MULTILINE)
FULL_SHA_RE = re.compile(r"^[^@]+@[0-9a-f]{40}$")


class WorkflowPolicyError(ValueError):
    """Raised when a release workflow violates supply-chain policy."""


def validate_action_pins(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    bad = [
        value
        for value in ACTION_RE.findall(text)
        if not value.startswith("./") and not FULL_SHA_RE.fullmatch(value)
    ]
    if bad:
        raise WorkflowPolicyError(
            f"{path}: third-party actions must use full commit SHAs: {', '.join(bad)}"
        )


def validate_scoped_workflows(root: Path) -> None:
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        validate_action_pins(path)
