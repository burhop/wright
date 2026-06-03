"""
Shared structured logging configuration for all Wright backend packages.

Constitution §7: All packages MUST implement structured JSON logging (structlog).
Traditional text logs are forbidden.
"""
import structlog
from opentelemetry import trace


def _add_trace_id(logger, method_name, event_dict):
    """Processor that binds trace_id from the active OTel span to every log entry."""
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        event_dict["trace_id"] = f"{span.get_span_context().trace_id:032x}"
        event_dict["span_id"] = f"{span.get_span_context().span_id:016x}"
    elif "trace_id" not in event_dict:
        event_dict["trace_id"] = "no-active-span"
    return event_dict


def configure_logging():
    """One-time structlog configuration with JSON renderer and trace_id processor.

    Call once at application startup (e.g., in main.py lifespan).
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            _add_trace_id,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Return a bound structlog logger with the component name.

    Usage:
        from core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("workspace_created", workspace_id="abc-123")
    """
    return structlog.get_logger(name)
