from __future__ import annotations

import sys

import structlog

from core.telemetry import current_trace_fields


class _StdoutLogger:
    def msg(self, message: str) -> None:
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    log = msg
    debug = msg
    info = msg
    warning = msg
    warn = msg
    error = msg
    critical = msg
    exception = msg
    fatal = msg


class _StdoutLoggerFactory:
    def __call__(self, *args, **kwargs):
        return _StdoutLogger()


def _add_trace_fields(logger, method_name, event_dict):
    event_dict.update(current_trace_fields())
    return event_dict


def configure_logging() -> None:
    """Configure JSON stdout logging without import-time filesystem effects."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            _add_trace_fields,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=_StdoutLoggerFactory(),
        cache_logger_on_first_use=True,
    )
