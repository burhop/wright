from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPIKE = ROOT / "integrations" / "rivet" / "spike"


def test_spike_assets_are_synthetic_and_excluded_from_production_packages() -> None:
    assert (SPIKE / "README.md").is_file()
    fixture = (SPIKE / "fixture" / "mock-workflow.rivet-project").read_text(encoding="utf-8")
    assert "wright_mock_operation" in fixture
    lowered = fixture.lower()
    for forbidden in ("bearer", "api_key", "password", "workspace_id", "session_id"):
        assert forbidden not in lowered

    production_roots = (
        ROOT / "packages" / "core",
        ROOT / "packages" / "workspace_service",
        ROOT / "packages" / "tool_registry",
        ROOT / "apps" / "api",
        ROOT / "apps" / "web",
    )
    for root in production_roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".json"}:
                assert "integrations/rivet/spike" not in path.read_text(encoding="utf-8", errors="ignore")
