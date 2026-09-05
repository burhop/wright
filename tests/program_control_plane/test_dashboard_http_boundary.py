"""Exercise the standalone dashboard's HTTP boundary without starting Wright."""

from __future__ import annotations

import importlib.util
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def dashboard(tmp_path, monkeypatch):
    path = ROOT / "scripts/program_status/implementation-dashboard/server.py"
    spec = importlib.util.spec_from_file_location("dashboard_routing_regression", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("dashboard", encoding="utf-8")
    (site / "server.py").write_text("private implementation", encoding="utf-8")
    (site / "lane-status.json").write_text(
        "private operational sidecar", encoding="utf-8"
    )
    monkeypatch.setattr(module, "ROOT", site)
    handler = object.__new__(module.Handler)
    handler.cache = SimpleNamespace(repo=tmp_path)
    handler.wfile = BytesIO()
    handler.result = {"status": None, "headers": {}}
    handler.send_response = lambda status: handler.result.update(status=status)
    handler.send_error = handler.send_response
    handler.send_header = lambda key, value: handler.result["headers"].update(
        {key: value}
    )
    handler.end_headers = lambda: None
    return module, handler


@pytest.mark.parametrize("route", ["/", "/index.html", "/?refresh=1"])
def test_only_shipped_dashboard_page_is_available(dashboard, route):
    _, handler = dashboard
    handler.path = route
    handler.do_GET()
    assert handler.result["status"] == 200
    assert handler.wfile.getvalue() == b"dashboard"
    assert handler.result["headers"]["Content-Type"] == "text/html; charset=utf-8"


@pytest.mark.parametrize(
    "route",
    [
        "/server.py",
        "/lane-status.json",
        "/agent-activity.json",
        "/../server.py",
        "/%2e%2e/server.py",
        "/%2fserver.py",
        "/index.html/../server.py",
        "/index.html%00",
        "/C:/private/file",
        "/%5c..%5cserver.py",
    ],
)
def test_arbitrary_urls_cannot_read_dashboard_files(dashboard, route):
    _, handler = dashboard
    handler.path = route
    handler.do_GET()
    assert handler.result["status"] == 404
    assert handler.wfile.getvalue() == b""


def test_evidence_mount_preserves_files_and_rejects_escape(dashboard):
    module, handler = dashboard
    evidence = handler.cache.repo / module.FROZEN_WALKTHROUGH
    evidence.mkdir(parents=True)
    (evidence / "report.html").write_text("retained evidence", encoding="utf-8")
    handler.path = "/evidence/frozen/report.html"
    handler.do_GET()
    assert handler.result["status"] == 200
    assert handler.wfile.getvalue() == b"retained evidence"
    assert handler.evidence_target("/evidence/frozen/%2e%2e/secret") is None
    assert handler.evidence_target("/evidence/unknown/report.html") is None


def test_mime_headers_ignore_host_mime_registry(dashboard, monkeypatch):
    import mimetypes

    module, handler = dashboard
    monkeypatch.setattr(
        mimetypes, "guess_type", lambda *args: ("text/html\r\nX-Injected: yes", None)
    )
    handler.send_file(module.ROOT / "index.html")
    assert handler.result["headers"]["Content-Type"] == "text/html; charset=utf-8"
    assert all(
        "\r" not in value and "\n" not in value
        for value in handler.result["headers"].values()
    )
