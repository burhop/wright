from __future__ import annotations

import hashlib
import json
import re
import threading
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

from .catalog_signing import canonical_json

MAX_IMPORT_BYTES = 256 * 1024
MAX_IMPORT_SERVERS = 100
IMPORT_PREVIEW_TTL = timedelta(minutes=15)
_COMMAND = re.compile(r"^[A-Za-z0-9_.+\\/:-]{1,500}$")
_SHELL_META = re.compile(r"[\r\n;|&`] |\$\(|\$\{|>|<", re.VERBOSE)
_SECRET_NAME = re.compile(
    r"(?:token|secret|password|passwd|api[_-]?key|authorization|credential)", re.I
)


class ConfigurationImportError(ValueError):
    def __init__(self, code: str, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class _DuplicateKey(ValueError):
    pass


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _diagnostic(path: str, code: str, message: str) -> dict[str, str]:
    return {"path": path, "code": code, "message": message}


def _parse(configuration: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(configuration, dict):
        encoded = json.dumps(configuration, ensure_ascii=False).encode("utf-8")
        if len(encoded) > MAX_IMPORT_BYTES:
            raise ConfigurationImportError(
                "import_too_large",
                "Configuration exceeds the 256 KiB limit.",
                status_code=413,
            )
        return deepcopy(configuration)
    if not isinstance(configuration, str):
        raise ConfigurationImportError(
            "import_type_invalid", "Configuration must be a JSON object or JSON text."
        )
    encoded = configuration.encode("utf-8")
    if len(encoded) > MAX_IMPORT_BYTES:
        raise ConfigurationImportError(
            "import_too_large",
            "Configuration exceeds the 256 KiB limit.",
            status_code=413,
        )
    try:
        parsed = json.loads(configuration, object_pairs_hook=_object_pairs)
    except _DuplicateKey as error:
        raise ConfigurationImportError(
            "import_duplicate_key",
            f"Duplicate JSON key '{error.args[0]}' is not allowed.",
        ) from error
    except json.JSONDecodeError as error:
        raise ConfigurationImportError(
            "import_json_invalid", "Configuration is not valid JSON."
        ) from error
    if not isinstance(parsed, dict):
        raise ConfigurationImportError(
            "import_document_invalid", "Configuration must contain one JSON object."
        )
    return parsed


def _detect(document: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if "mcpServers" in document:
        servers = document.get("mcpServers")
        return "claude_mcp_servers", servers if isinstance(servers, dict) else {}
    if "servers" in document:
        servers = document.get("servers")
        return "vscode_servers", servers if isinstance(servers, dict) else {}
    if any(key in document for key in ("command", "url", "endpoint", "type")):
        name = (
            document.get("name")
            if isinstance(document.get("name"), str)
            else "Imported MCP"
        )
        return "plain_server", {name: document}
    return "unknown", {}


def _safe_endpoint(value: Any, path: str, errors: list[dict[str, str]]) -> str | None:
    if not isinstance(value, str) or not value:
        errors.append(
            _diagnostic(path, "endpoint_required", "A remote MCP requires a URL.")
        )
        return None
    parsed = urlsplit(value)
    loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
        errors.append(
            _diagnostic(
                path,
                "endpoint_scheme_unsafe",
                "Remote MCP URLs must use HTTPS; HTTP is limited to loopback fixtures.",
            )
        )
        return None
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        errors.append(
            _diagnostic(path, "endpoint_invalid", "The remote MCP URL is not allowed.")
        )
        return None
    return value


def _requirement(name: str, value: Any, *, credential: bool) -> dict[str, Any]:
    return {
        "name": name,
        "credential_required": credential,
        "value_supplied": value not in (None, ""),
    }


def _normalize_server(
    name: str,
    raw: Any,
    source_format: str,
    *,
    input_ids: set[str],
) -> dict[str, Any]:
    path = f"servers.{name}"
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        raw = {}
        errors.append(
            _diagnostic(path, "server_invalid", "Server definition must be an object.")
        )

    raw_type = raw.get("type")
    url = raw.get("url", raw.get("endpoint"))
    remote = url is not None or raw_type in {"http", "streamable_http", "sse", "webmcp"}
    transport = "stdio"
    if remote:
        transport = {
            "http": "streamable_http",
            "streamable_http": "streamable_http",
            "sse": "sse",
            "webmcp": "webmcp",
        }.get(raw_type, "streamable_http")
    elif raw_type not in (None, "stdio"):
        errors.append(
            _diagnostic(
                f"{path}.type",
                "transport_unknown",
                "The MCP transport is not supported.",
            )
        )

    command = raw.get("command")
    if not remote:
        if (
            not isinstance(command, str)
            or not _COMMAND.fullmatch(command)
            or _SHELL_META.search(command)
        ):
            errors.append(
                _diagnostic(
                    f"{path}.command",
                    "command_unsafe",
                    "The command must be one literal executable token, not a shell expression.",
                )
            )
            command = None

    raw_args = raw.get("args", raw.get("arguments", []))
    arguments: list[str] = []
    if not isinstance(raw_args, list) or not all(
        isinstance(item, str) for item in raw_args
    ):
        errors.append(
            _diagnostic(
                f"{path}.args", "arguments_invalid", "Arguments must be strings."
            )
        )
    else:
        arguments = list(raw_args)
        for index, argument in enumerate(arguments):
            if _SHELL_META.search(argument):
                errors.append(
                    _diagnostic(
                        f"{path}.args.{index}",
                        "argument_shell_expression",
                        "Shell expansion and control operators are not allowed.",
                    )
                )

    endpoint = _safe_endpoint(url, f"{path}.url", errors) if remote else None
    env = raw.get("env", {})
    if not isinstance(env, dict):
        errors.append(
            _diagnostic(
                f"{path}.env", "environment_invalid", "Environment must be an object."
            )
        )
        env = {}
    environment_requirements = [
        _requirement(str(key), value, credential=bool(_SECRET_NAME.search(str(key))))
        for key, value in sorted(env.items())
    ]

    headers = raw.get("headers", {})
    if not isinstance(headers, dict):
        errors.append(
            _diagnostic(
                f"{path}.headers", "headers_invalid", "Headers must be an object."
            )
        )
        headers = {}
    header_requirements: list[dict[str, Any]] = []
    for key, value in sorted(headers.items()):
        placeholders = (
            re.findall(r"\$\{input:([^}]+)\}", value) if isinstance(value, str) else []
        )
        unknown = sorted(set(placeholders) - input_ids)
        if unknown:
            errors.append(
                _diagnostic(
                    f"{path}.headers.{key}",
                    "input_reference_unknown",
                    f"Header references unknown input '{unknown[0]}'.",
                )
            )
        credential = bool(_SECRET_NAME.search(str(key))) or bool(placeholders)
        header_requirements.append(_requirement(str(key), value, credential=credential))

    allowed = {
        "name",
        "type",
        "command",
        "args",
        "arguments",
        "url",
        "endpoint",
        "env",
        "headers",
    }
    for key in sorted(set(raw) - allowed):
        warnings.append(
            _diagnostic(
                f"{path}.{key}",
                "field_ignored",
                "This field is not used by the import preview.",
            )
        )

    material = {
        "name": name[:200],
        "source_format": source_format,
        "transport": transport,
        "command": command,
        "arguments": arguments,
        "endpoint": endpoint,
        "environment_requirements": environment_requirements,
        "header_requirements": header_requirements,
        "warnings": warnings,
        "errors": errors,
        "redacted_preview": {
            "name": name[:200],
            "transport": transport,
            "command": command,
            "arguments": arguments,
            "endpoint": endpoint,
            "environment": {str(key): "<redacted>" for key in sorted(env)},
            "headers": {str(key): "<redacted>" for key in sorted(headers)},
        },
    }
    digest = hashlib.sha256(canonical_json(material)).hexdigest()
    return {
        "draft_id": f"draft-{digest[:20]}",
        **material,
        "draft_digest": digest,
    }


def preview_configuration(
    configuration: str | dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    document = _parse(configuration)
    detected_format, servers = _detect(document)
    document_errors: list[dict[str, str]] = []
    if detected_format == "unknown":
        document_errors.append(
            _diagnostic(
                "$", "format_unknown", "No supported MCP configuration form was found."
            )
        )
    if len(servers) > MAX_IMPORT_SERVERS:
        raise ConfigurationImportError(
            "import_server_limit",
            "Configuration exceeds the 100-server limit.",
            status_code=413,
        )
    inputs = document.get("inputs", []) if detected_format == "vscode_servers" else []
    input_ids = (
        {
            item["id"]
            for item in inputs
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        if isinstance(inputs, list)
        else set()
    )
    drafts = [
        _normalize_server(str(name), raw, detected_format, input_ids=input_ids)
        for name, raw in sorted(
            servers.items(), key=lambda item: str(item[0]).casefold()
        )
    ]
    created_at = (now or datetime.now(UTC)).astimezone(UTC)
    preview_material = {
        "detected_format": detected_format,
        "drafts": drafts,
        "document_errors": document_errors,
        "created_at": created_at.isoformat(),
    }
    digest = hashlib.sha256(canonical_json(preview_material)).hexdigest()
    return {
        "preview_id": f"import-{digest[:20]}",
        **preview_material,
        "expires_at": (created_at + IMPORT_PREVIEW_TTL).isoformat(),
        "source_discarded": True,
    }


class ImportPreviewRepository:
    """Short-lived normalized previews; raw configuration is never retained."""

    def __init__(self) -> None:
        self._previews: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(
        self, configuration: str | dict[str, Any], *, now: datetime
    ) -> dict[str, Any]:
        preview = preview_configuration(configuration, now=now)
        with self._lock:
            self._previews[preview["preview_id"]] = deepcopy(preview)
        return preview

    def get(self, preview_id: str, *, now: datetime) -> dict[str, Any]:
        with self._lock:
            preview = deepcopy(self._previews.get(preview_id))
        if preview is None:
            raise ConfigurationImportError(
                "import_preview_not_found",
                "Import preview was not found.",
                status_code=404,
            )
        if datetime.fromisoformat(preview["expires_at"]) <= now.astimezone(UTC):
            raise ConfigurationImportError(
                "import_preview_expired", "Import preview has expired.", status_code=409
            )
        return preview

    def discard(self, preview_id: str) -> None:
        with self._lock:
            self._previews.pop(preview_id, None)
