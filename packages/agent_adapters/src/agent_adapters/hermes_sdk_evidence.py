"""Small standard-library evidence helper usable by the isolated SDK worker.

The qualified provider environment need not install Wright's core package. This
captures fixed SDK arguments only, never runtime credentials, headers or env.
The parent applies the shared core redactor again before durable persistence.
"""

from copy import deepcopy
import hashlib
import json
import re


def sdk_invocation_evidence(payload, resolution):
    original = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    snapshot = deepcopy(payload)
    for message in snapshot.get("input", snapshot.get("messages", [])):
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for index, part in enumerate(content):
            if isinstance(part, dict) and part.get("type") in {
                "input_image",
                "image_url",
            }:
                image = part.get("image_url")
                url = image.get("url", "") if isinstance(image, dict) else image or ""
                content[index] = {
                    "type": "image_reference",
                    "sha256": hashlib.sha256(url.encode()).hexdigest(),
                    "encoded_size_bytes": len(url.encode()),
                    "media_type": url.split(";", 1)[0].removeprefix("data:"),
                }

    def redact(value):
        if isinstance(value, dict):
            return {
                key: "[REDACTED]"
                if re.search(
                    r"(?i)(api[_-]?key|secret|token|password|authorization|cookie|credential|private[_-]?key)",
                    key,
                )
                else redact(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, str):
            text = re.sub(
                r"(?i)\bbearer\s+[a-z0-9._~+/=-]+", "Bearer [REDACTED]", value
            )
            return re.sub(
                r"(?i)\b(api[_-]?(?:key|token)|secret|token|password|authorization|cookie|credential)\b\s*[:=]\s*([^\s,;]+)",
                lambda match: match[1] + "=[REDACTED]",
                text,
            )
        return value

    messages = snapshot.get("messages", snapshot.get("input", []))
    if "instructions" in snapshot:
        messages = [{"role": "system", "content": snapshot["instructions"]}, *messages]
    return redact(
        {
            "schema_version": "wright.workflow-invocation/1",
            "operation": "hermes-provider-sdk",
            "capture_scope": "provider_sdk_request",
            "request_digest": hashlib.sha256(original.encode()).hexdigest(),
            "request_fields": snapshot,
            "messages": messages,
            "tool_schemas": snapshot.get("tools", []),
            "tool_schemas_digest": hashlib.sha256(
                json.dumps(
                    payload.get("tools", []),
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode()
            ).hexdigest(),
            "resolution": resolution,
        }
    )
