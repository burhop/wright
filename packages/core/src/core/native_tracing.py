"""Native operation spans that never export exception messages or stack traces."""

from __future__ import annotations

import functools
import inspect
import re
from collections.abc import Iterator
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.trace import Span, StatusCode

_tracer = trace.get_tracer("wright.native")
_ERROR_TYPE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}")


@contextmanager
def _native_span(name: str) -> Iterator[Span]:
    # OTel's context manager also records escaping exceptions by default. Both
    # automatic behaviors must be disabled, including for chained exceptions.
    with _tracer.start_as_current_span(
        name, record_exception=False, set_status_on_exception=False
    ) as span:
        try:
            yield span
        except BaseException as error:
            error_type = type(error).__name__
            span.set_attribute(
                "error.type",
                error_type if _ERROR_TYPE.fullmatch(error_type) else "Exception",
            )
            span.set_status(StatusCode.ERROR)
            raise
        else:
            span.set_status(StatusCode.OK)


def traced_native(span_name: str):
    """Trace a native operation without copying arguments or exception content.

    Span names are static operation identifiers. Failures retain their original
    exception behavior, while telemetry contains only a bounded exception type.
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with _native_span(span_name):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with _native_span(span_name):
                return func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
