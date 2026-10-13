from __future__ import annotations

import json
import re
import shlex
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"

SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|authorization|cookie|credential|private[_-]?key|x[_-](?:upload|download)[_-]ticket)"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?(?:key|token)|secret|token|password|authorization|cookie|credential)\b\s*[:=]\s*([^\s,;]+)"
)
BEARER_RE = re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")
# One-use HTTP transfer credentials also occur inside returned command strings
# and JSON encoded in a text block. Preserve surrounding quoting/JSON syntax.
TRANSFER_TICKET_RE = re.compile(
    r"""(?i)(\bx[_-](?:upload|download)[_-]ticket\b)((?:\\*["'])?\s*[:=]\s*)((?:\\*["'])?)([^\s"'\\,;}]+)"""
)
# Evidence also contains public identities such as credential_binding_digest and
# token counts. Match credential fields, not those longer metadata names.
EVIDENCE_SECRET_KEY_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|cookie|credential|private[_-]?key|x[_-](?:upload|download)[_-]ticket)$"
)


def redact_text(text: Any, secrets: Sequence[str] | None = None) -> str:
    value = "" if text is None else str(text)
    for secret in secrets or []:
        if secret:
            value = value.replace(str(secret), REDACTED)
    value = BEARER_RE.sub(f"Bearer {REDACTED}", value)
    value = TRANSFER_TICKET_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{match.group(3)}{REDACTED}",
        value,
    )
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


def redact_evidence(value: Any) -> Any:
    """Copy evidence without credentials, preserving public provenance and types.

    Raw values stay in the current execution for connected tool arguments. This
    projection is for persistence/observation, never for reconstructing authority
    or silently replacing execution inputs. Decode embedded JSON before redacting
    its fields so surrounding syntax and nonsecret values remain usable.
    """
    if isinstance(value, Mapping):
        return {
            key: REDACTED
            if EVIDENCE_SECRET_KEY_RE.search(str(key))
            else redact_evidence(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_evidence(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_evidence(item) for item in value)
    if isinstance(value, str):
        if value.lstrip().startswith(("{", "[", '"')):
            try:
                decoded = json.loads(value)
            except (ValueError, RecursionError):
                pass
            else:
                clean = redact_evidence(decoded)
                if clean != decoded:
                    return json.dumps(clean, ensure_ascii=False)
        return redact_text(value)
    return value


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
        if TRANSFER_TICKET_RE.search(part):
            redacted.append(redact_text(part))
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
