from __future__ import annotations

import sys
from typing import TextIO

import structlog

from core.telemetry import current_trace_fields


class _StreamLogger:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def msg(self, message: str) -> None:
        self.stream.write(message + "\n")
        self.stream.flush()

    log = msg
    debug = msg
    info = msg
    warning = msg
    warn = msg
    error = msg
    critical = msg
    exception = msg
    fatal = msg


class _StreamLoggerFactory:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def __call__(self, *args, **kwargs):
        return _StreamLogger(self.stream)


def _add_trace_fields(logger, method_name, event_dict):
    event_dict.update(current_trace_fields())
    return event_dict


def configure_logging(*, stream: TextIO | None = None) -> None:
    """Configure JSON logging without import-time filesystem effects.

    HTTP processes use stdout. Stdio protocol servers must pass stderr so
    diagnostics never corrupt their JSON-RPC stdout channel.
    """
    output = stream or sys.stdout
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
        logger_factory=_StreamLoggerFactory(output),
        cache_logger_on_first_use=True,
    )
