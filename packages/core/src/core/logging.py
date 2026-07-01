"""
Shared structured logging configuration for all Wright backend packages.

Constitution 7: All packages MUST implement structured JSON logging (structlog).
Traditional text logs are forbidden.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import structlog
from opentelemetry import trace

# Resolve the absolute path to apps/api/wright.log
_lib_dir = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.abspath(os.path.join(_lib_dir, "..", "..", "..", ".."))
LOG_FILE_PATH = os.path.join(_repo_root, "apps", "api", "wright.log")

# Setup standard rotating file handler (10MB limit per file, 5 backups)
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
_file_handler = RotatingFileHandler(
    LOG_FILE_PATH, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter("%(message)s"))


class WrightPrintLogger:
    def msg(self, message):
        # Write to stdout for developer console (uvicorn output)
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

        # Emit to rotating file handler
        try:
            record = logging.LogRecord(
                name="wright",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=message,
                args=(),
                exc_info=None,
            )
            _file_handler.emit(record)
        except Exception:
            pass

    log = msg
    debug = msg
    info = msg
    warning = msg
    warn = msg
    error = msg
    critical = msg
    exception = msg
    fatal = msg


class WrightLoggerFactory:
    def __call__(self, *args, **kwargs):
        return WrightPrintLogger()


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
        logger_factory=WrightLoggerFactory(),
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
