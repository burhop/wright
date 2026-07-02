from __future__ import annotations

import re
import shlex
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"

SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|authorization|credential|private[_-]?key)"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?(?:key|token)|secret|token|password|authorization|credential)\b\s*[:=]\s*([^\s,;]+)"
)
BEARER_RE = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")


def redact_text(text: Any, secrets: Sequence[str] | None = None) -> str:
    value = "" if text is None else str(text)
    for secret in secrets or []:
        if secret:
            value = value.replace(str(secret), REDACTED)
    value = BEARER_RE.sub(f"Bearer {REDACTED}", value)
    return SECRET_ASSIGNMENT_RE.sub(lambda match: f"{match.group(1)}={REDACTED}", value)


def redact_mapping(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    if not mapping:
        return {}
    redacted: dict[str, Any] = {}
    for key, value in mapping.items():
        if SECRET_KEY_RE.search(str(key)):
            redacted[str(key)] = REDACTED
        elif isinstance(value, Mapping):
            redacted[str(key)] = redact_mapping(value)
        elif isinstance(value, list):
            redacted[str(key)] = [
                redact_mapping(item)
                if isinstance(item, Mapping)
                else redact_text(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        elif isinstance(value, str):
            redacted[str(key)] = redact_text(value)
        else:
            redacted[str(key)] = value
    return redacted


def redact_command(command: str | Sequence[str]) -> str:
    parts = (
        shlex.split(command)
        if isinstance(command, str)
        else [str(part) for part in command]
    )
    redacted: list[str] = []
    redact_next = False
    for part in parts:
        if redact_next:
            redacted.append(REDACTED)
            redact_next = False
            continue
        if SECRET_KEY_RE.search(part):
            if "=" in part:
                key = part.split("=", 1)[0]
                redacted.append(f"{key}={REDACTED}")
            else:
                redacted.append(part)
                redact_next = part.startswith("-")
        else:
            redacted.append(redact_text(part))
    return " ".join(redacted)


def redact_validation_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return redact_mapping(payload)
