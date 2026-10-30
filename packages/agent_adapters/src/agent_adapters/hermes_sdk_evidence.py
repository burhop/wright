"""Small standard-library evidence helper usable by the isolated SDK worker.

The qualified provider environment need not install Wright's core package. This
captures fixed SDK arguments only, never runtime credentials, headers or env.
The parent applies the shared core redactor again before durable persistence.
"""

from copy import deepcopy
import hashlib
import json
import re


def sdk_model_observation(response_model):
    """An SDK adapter result may echo an alias; it cannot attest upstream identity.

    Keep the caller's legacy model fields unchanged. Even a different returned
    alias is not proof of a provider revision at this observable boundary.
    """
    return {
        "adapter_returned_model": response_model
        if isinstance(response_model, str)
        and response_model.strip()
        and len(response_model) <= 160
        else None,
        "model_observation_scope": "hermes_model_sdk_adapter_result",
        "upstream_reported_model": None,
    }


def sdk_failure_evidence(error, category):
    """Retain finite exception metadata, never exception text or response bodies."""
    categories = {
        "SCOPED_MODEL_TIMEOUT",
        "SCOPED_MODEL_AUTH_REQUIRED",
        "SCOPED_MODEL_RATE_LIMITED",
        "WORKFLOW_MODEL_CHANGED",
        "SCOPED_INVOCATION_UNAVAILABLE",
    }
    exception_types = {
        "APIError",
        "APIStatusError",
        "APIConnectionError",
        "APITimeoutError",
        "BadRequestError",
        "AuthenticationError",
        "PermissionDeniedError",
        "NotFoundError",
        "ConflictError",
        "UnprocessableEntityError",
        "RateLimitError",
        "InternalServerError",
        "APIResponseValidationError",
        "_StreamErrorEvent",
        "TimeoutError",
        "TimeoutException",
        "ConnectionError",
        "ValueError",
        "TypeError",
        "KeyError",
        "AttributeError",
        "IndexError",
        "RuntimeError",
        "ImportError",
        "ModuleNotFoundError",
        "OSError",
        "WorkflowSdkConfigurationChangedError",
    }
    provider_codes = {
        "invalid_request_error",
        "model_not_found",
        "invalid_api_key",
        "insufficient_quota",
        "rate_limit_exceeded",
        "context_length_exceeded",
        "unsupported_parameter",
        "unsupported_value",
        "invalid_value",
        "invalid_image",
        "server_error",
    }
    name = type(error).__name__
    result = {
        "schema_version": "wright.scoped-sdk-failure/1",
        "capture_scope": "worker_exception_after_sdk_capture",
        "category": category
        if isinstance(category, str) and category in categories
        else "SCOPED_INVOCATION_UNAVAILABLE",
        "exception_type": name if name in exception_types else "unclassified_error",
    }
    # SDK attributes can be missing or implemented as raising properties.
    # Do not inspect .body, .response, headers, args, causes or arbitrary strings.
    for attribute, output_key in (
        ("status_code", "http_status"),
        ("code", "provider_code"),
    ):
        try:
            value = getattr(error, attribute, None)
        except Exception:
            continue
        if attribute == "status_code" and type(value) is int and 100 <= value <= 599:
            result[output_key] = value
        elif attribute == "code" and type(value) is str and value in provider_codes:
            result[output_key] = value
    return result


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
