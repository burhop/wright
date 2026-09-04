from __future__ import annotations

import asyncio

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from core import native_tracing


@pytest.fixture
def spans(monkeypatch):
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(native_tracing, "_tracer", provider.get_tracer("native-test"))
    yield exporter
    provider.shutdown()


@pytest.mark.parametrize("asynchronous", [False, True])
def test_native_spans_preserve_results_and_parent_context(spans, asynchronous):
    result = object()

    @native_tracing.traced_native("native.child")
    def child():
        return result

    def operation():
        return child()

    async def async_operation():
        await asyncio.sleep(0)
        return child()

    wrapped = native_tracing.traced_native("native.parent")(
        async_operation if asynchronous else operation
    )
    assert (asyncio.run(wrapped()) if asynchronous else wrapped()) is result
    child_span, parent_span = spans.get_finished_spans()
    assert child_span.parent.span_id == parent_span.context.span_id
    assert child_span.context.trace_id == parent_span.context.trace_id
    assert all(s.status.status_code == StatusCode.OK for s in (child_span, parent_span))


@pytest.mark.parametrize("asynchronous", [False, True])
def test_native_spans_do_not_export_exception_content_or_chains(spans, asynchronous):
    sentinel = "NATIVE_TRACE_TEST_PRIVATE_PAYLOAD"
    cause = ValueError("api_key=" + sentinel)
    failure = RuntimeError("C:/private/" + sentinel)

    def operation():
        raise failure from cause

    async def async_operation():
        await asyncio.sleep(0)
        raise failure from cause

    wrapped = native_tracing.traced_native("native.failure")(
        async_operation if asynchronous else operation
    )
    with pytest.raises(RuntimeError) as raised:
        if asynchronous:
            asyncio.run(wrapped())
        else:
            wrapped()
    assert raised.value is failure and raised.value.__cause__ is cause
    (span,) = spans.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes["error.type"] == "RuntimeError"
    assert sentinel not in span.to_json()
    assert span.status.description is None
    assert not span.events


def test_native_async_cancellation_preserves_cancellation_without_exporting_reason(
    spans,
):
    cancellation = asyncio.CancelledError("NATIVE_TRACE_TEST_PRIVATE_REASON")

    @native_tracing.traced_native("native.cancelled")
    async def operation():
        raise cancellation

    with pytest.raises(asyncio.CancelledError) as raised:
        asyncio.run(operation())
    assert raised.value is cancellation
    (span,) = spans.get_finished_spans()
    assert span.status.status_code == StatusCode.ERROR
    assert span.attributes["error.type"] == "CancelledError"
    assert "NATIVE_TRACE_TEST_PRIVATE_REASON" not in span.to_json()
    assert not span.events
