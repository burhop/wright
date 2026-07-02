from __future__ import annotations

from collections.abc import Mapping

from opentelemetry import trace
from structlog import contextvars

WRIGHT_CORRELATION_ID = "wright.correlation_id"
WRIGHT_WORKSPACE_ID = "wright.workspace_id"
WRIGHT_SESSION_ID = "wright.session_id"
WRIGHT_AGENT_ID = "wright.agent_id"
WRIGHT_PROVIDER_ID = "wright.provider_id"
WRIGHT_SERVER_ID = "wright.server_id"
WRIGHT_TOOL_NAME = "wright.tool_name"
WRIGHT_VALIDATION_ID = "wright.validation_id"
WRIGHT_CATALOG_VERSION = "wright.catalog_version"
WRIGHT_POLICY_DECISION = "wright.policy_decision"

REMOTE_TELEMETRY_ENABLED_ENV = "WRIGHT_REMOTE_TELEMETRY_ENABLED"

TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}


def is_remote_telemetry_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = env or {}
    return source.get(REMOTE_TELEMETRY_ENABLED_ENV, "").strip().lower() in TRUE_VALUES


def current_trace_fields() -> dict[str, str]:
    span = trace.get_current_span()
    context = span.get_span_context() if span else None
    if context and context.is_valid:
        return {
            "trace_id": f"{context.trace_id:032x}",
            "span_id": f"{context.span_id:016x}",
        }
    return {"trace_id": "no-active-span"}


def bind_correlation_id(correlation_id: str | None) -> None:
    if correlation_id:
        contextvars.bind_contextvars(**{WRIGHT_CORRELATION_ID: correlation_id})


def clear_correlation_id() -> None:
    contextvars.unbind_contextvars(WRIGHT_CORRELATION_ID)
