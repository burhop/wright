"""
Shared OpenTelemetry tracer factory and instrumentation utilities.

Constitution §7: Every user request MUST generate a trace_id. This ID must be passed
down to every sub-agent, tool execution, and database query.

Span naming follows the semantic hierarchy defined in spec.md:
  - workspace.create, workspace.files.list, agent.chat.start
  - db.sqlite.query, db.sqlite.execute (child spans of operations)
"""

import functools
import sqlite3
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import StatusCode

# Single tracer instance for the Wright API backend service
_tracer = trace.get_tracer("wright.api")


def get_tracer(component: str = "wright.api") -> trace.Tracer:
    """Return a named OTel tracer. Defaults to the wright.api service tracer."""
    return trace.get_tracer(component)


def traced(span_name: str, attributes: dict[str, Any] | None = None):
    """Decorator that wraps a function in an OTel span with automatic error recording.

    Usage:
        @traced("workspace.create")
        async def create_workspace(...):
            ...

    On exception, the span records the exception and sets status to ERROR.
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with _tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v))
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_status(StatusCode.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with _tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for k, v in attributes.items():
                        span.set_attribute(k, str(v))
                try:
                    result = func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as exc:
                    span.set_status(StatusCode.ERROR, str(exc))
                    span.record_exception(exc)
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@contextmanager
def traced_db(span_name: str, db_path: str, statement: str | None = None):
    """Context manager that creates a db.sqlite child span for database operations.

    Usage:
        with traced_db("db.sqlite.query", db_path, "SELECT * FROM workspaces") as span:
            conn = sqlite3.connect(db_path)
            rows = conn.execute(query, params).fetchall()
            span.set_attribute("db.rows_affected", len(rows))

    The span is a child of the current active span (e.g., workspace.create).
    """
    with _tracer.start_as_current_span(span_name) as span:
        span.set_attribute("db.system", "sqlite")
        span.set_attribute("db.path", db_path)
        if statement:
            # Record parameterized statement (no user data)
            span.set_attribute("db.statement", statement)
        try:
            yield span
            span.set_status(StatusCode.OK)
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


def traced_query(db_path: str, query: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Execute a SELECT query with automatic OTel tracing.

    Returns list of sqlite3.Row objects.
    """
    with traced_db("db.sqlite.query", db_path, query) as span:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(query, params).fetchall()
            span.set_attribute("db.rows_affected", len(rows))
            return rows
        finally:
            conn.close()


def traced_execute(db_path: str, statement: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE with automatic OTel tracing.

    Returns number of rows affected.
    """
    with traced_db("db.sqlite.execute", db_path, statement) as span:
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.execute(statement, params)
            conn.commit()
            span.set_attribute("db.rows_affected", cursor.rowcount)
            return cursor.rowcount
        finally:
            conn.close()
