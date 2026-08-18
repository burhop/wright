from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from tool_registry.capability_views import build_capability_views
from tool_registry.catalog_models import CatalogEntry
from tool_registry.compatibility import observe_machine
from tool_registry.windows_qualification_models import EMPTY_DIGEST


def _observation():
    return observe_machine(
        clock=lambda: datetime(2026, 8, 13, tzinfo=UTC),
        which=lambda name: None,
        version_reader=lambda path: None,
        system_reader=lambda: "Windows",
        version_system_reader=lambda: "11",
        architecture_reader=lambda: "AMD64",
        network_policy="allowed",
    )


def _status(result: str, label: str, reason_code: str) -> dict[str, str]:
    return {"result": result, "label": label, "reason_code": reason_code}


def _summary(*, current: bool = True, claim: str | None = None) -> dict:
    return {
        "observed_at": "2026-08-13T12:00:00Z",
        "evidence_path": (
            "docs/mcp-catalog/evidence/windows-qualification-2026-08-13/"
            "brep-mcp-windows-qualification.json"
        ),
        "evidence_digest": EMPTY_DIGEST,
        "current": current,
        "stale_reasons": [] if current else ["qualification_source_changed"],
        "source": _status("passed", "Source verified", "source_pinned"),
        "package_or_registration": _status(
            "passed", "MCP server installed", "package_installed"
        ),
        "startup": _status("passed", "MCP server started", "startup_passed"),
        "protocol": _status("passed", "MCP protocol passed", "protocol_passed"),
        "host_or_backend": _status(
            "partial", "Host app needed", "commercial_host_not_configured"
        ),
        "wright_setup": _status("passed", "Added to Wright", "wright_registered"),
        "gateway": _status("partial", "Gateway check pending", "gateway_not_tested"),
        "cleanup": _status("passed", "Cleanup passed", "cleanup_passed"),
        "claim": claim,
    }


def _entry(summary: dict | None) -> CatalogEntry:
    data = {
        "id": "brep-mcp",
        "name": "BREP MCP",
        "vendor": "andymai",
        "description": "Deterministic BREP geometry tools.",
        "domains": ["cad"],
        "transport": "stdio",
        "command": ["brep-mcp"],
        "locality": "local",
        "weight": "light",
        "platform_support": {"windows_11_x64": {"status": "yes", "tested": True}},
    }
    if summary is not None:
        data["windows_qualification"] = summary
    return CatalogEntry.model_validate(data)


def test_catalog_accepts_bounded_windows_qualification_summary() -> None:
    entry = _entry(_summary())

    assert entry.windows_qualification is not None
    assert entry.windows_qualification.host_or_backend.label == "Host app needed"


def test_catalog_rejects_unsubstantiated_no_problems_claim() -> None:
    summary = _summary(claim="Installs on Windows with no problems")
    summary["startup"] = _status("failed", "Startup failed", "startup_failed")

    with pytest.raises(ValidationError, match="no-problems claim"):
        _entry(summary)


def test_capability_projection_preserves_independent_windows_boundaries() -> None:
    view = build_capability_views([_entry(_summary())], [], _observation())[0]

    assert view.windows_qualification is not None
    assert view.windows_qualification.package_or_registration.result == "passed"
    assert view.windows_qualification.host_or_backend.result == "partial"
    assert view.windows_qualification.host_or_backend.label == "Host app needed"
    assert view.windows_qualification.evidence_digest == EMPTY_DIGEST


def test_capability_projection_preserves_staleness_and_absence() -> None:
    stale = build_capability_views(
        [_entry(_summary(current=False))], [], _observation()
    )[0]
    absent = build_capability_views([_entry(None)], [], _observation())[0]

    assert stale.windows_qualification is not None
    assert stale.windows_qualification.current is False
    assert stale.windows_qualification.stale_reasons == ["qualification_source_changed"]
    assert absent.windows_qualification is None
