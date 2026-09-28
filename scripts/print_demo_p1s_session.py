"""Keep P1S telemetry separate from command replies and track actual receipt age."""

from __future__ import annotations

import json
import secrets
import threading
import time
from datetime import datetime, timezone

from bambu_p1s_mcp.printer import PrinterSession


class MonitoredPrinterSession(PrinterSession):
    def __init__(self, settings):
        super().__init__(settings)
        # Replies are broadcast on the printer report topic. Avoid reusing the
        # small counter values of another Studio/Handy/MCP client.
        self._seq = 1_000_000_000 + secrets.randbelow(1_000_000_000)
        self._reports = threading.Condition()
        self._received_at = None
        self._received_monotonic = None
        self._responses = {}
        self._last_refresh = 0.0

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return super()._on_message(client, userdata, msg)
        report = payload.get("print") if isinstance(payload, dict) else None
        if isinstance(report, dict) and report.get("command") == "project_file":
            # A reply's result/error/sequence must not overwrite job telemetry.
            sequence = str(report.get("sequence_id", ""))
            with self._reports:
                self._responses[sequence] = {
                    key: report[key] for key in ("sequence_id", "result", "reason", "error_code", "print_error")
                    if key in report and isinstance(report[key], (str, int, float, bool))
                }
                while len(self._responses) > 32:
                    self._responses.pop(next(iter(self._responses)))
                self._reports.notify_all()
            return
        super()._on_message(client, userdata, msg)
        if isinstance(report, dict) and report.get("command") == "push_status":
            with self._reports:
                self._received_monotonic = time.monotonic()
                self._received_at = datetime.now(timezone.utc).isoformat()
                self._reports.notify_all()

    def snapshot(self, *, fresh=False):
        with self._reports:
            age = None if self._received_monotonic is None else time.monotonic() - self._received_monotonic
        # Polling serves streamed telemetry. Request a bounded refresh if the
        # stream stops, rather than treating an open MQTT socket as fresh data.
        refresh = fresh or ((age is None or age > 15) and time.monotonic() - self._last_refresh > 15)
        if refresh:
            self._last_refresh = time.monotonic()
        value = super().snapshot(fresh=refresh)
        raw = self.raw_state().get("print", {})
        with self._reports:
            age = None if self._received_monotonic is None else time.monotonic() - self._received_monotonic
            value.update(telemetry_at=self._received_at, telemetry_age_seconds=age, telemetry_stale=age is None or age > 30)
        # The upstream summary defaults missing faults to zero. Readiness must
        # distinguish absent telemetry from an explicit all-clear.
        value.update(print_error=raw.get("print_error"), hms=raw.get("hms"), stage=raw.get("stg_cur"))
        return value

    def wait_for_project_response(self, sequence: str, timeout=15):
        with self._reports:
            self._reports.wait_for(lambda: sequence in self._responses, timeout=timeout)
            return self._responses.pop(sequence, None)
