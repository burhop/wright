from core.telemetry import (
    REMOTE_TELEMETRY_ENABLED_ENV,
    WRIGHT_CORRELATION_ID,
    is_remote_telemetry_enabled,
    bind_correlation_id,
    clear_correlation_id,
)
from api.logging_config import configure_logging
from core.logging import get_logger
import json


def test_remote_telemetry_export_is_disabled_by_default():
    assert is_remote_telemetry_enabled({}) is False


def test_remote_telemetry_export_requires_explicit_opt_in():
    assert is_remote_telemetry_enabled({REMOTE_TELEMETRY_ENABLED_ENV: "true"}) is True
    assert (
        is_remote_telemetry_enabled({"OTEL_EXPORTER_OTLP_ENDPOINT": "https://example"})
        is False
    )


def test_wright_correlation_field_name_is_stable():
    assert WRIGHT_CORRELATION_ID == "wright.correlation_id"


def test_json_logs_include_correlation_and_otel_trace_fields(capsys):
    configure_logging()
    bind_correlation_id("corr-123")
    try:
        get_logger("test.telemetry").info("shape_check")
    finally:
        clear_correlation_id()

    entry = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert entry["event"] == "shape_check"
    assert entry["trace_id"] == "no-active-span"
    assert entry[WRIGHT_CORRELATION_ID] == "corr-123"
