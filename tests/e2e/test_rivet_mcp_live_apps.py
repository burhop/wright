"""Explicitly opted-in live lifecycle probes; never part of normal gates."""

from __future__ import annotations

import os

import httpx
import pytest


def _enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes"}


def _live_inputs() -> tuple[str, str, dict[str, str]]:
    base_url = os.environ["WRIGHT_LIVE_API_URL"].rstrip("/")
    session_id = os.environ["WRIGHT_LIVE_SESSION_ID"]
    token = os.getenv("WRIGHT_LIVE_API_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return base_url, session_id, headers


@pytest.mark.rivet_live_brep
@pytest.mark.skipif(
    not _enabled("WRIGHT_RIVET_LIVE_BREP"),
    reason="live BREP evidence requires explicit WRIGHT_RIVET_LIVE_BREP=1 opt-in",
)
def test_live_brep_panel_probe_records_visible_application_evidence() -> None:
    base_url, session_id, headers = _live_inputs()
    response = httpx.post(
        f"{base_url}/api/workspace/brep/panel",
        json={"session_id": session_id},
        headers=headers,
        timeout=180,
    )
    response.raise_for_status()
    evidence = response.json()
    assert evidence["module_url"].startswith("http://127.0.0.1:")
    assert evidence["control_url"].startswith("http://127.0.0.1:")


@pytest.mark.rivet_live_host
@pytest.mark.skipif(
    not _enabled("WRIGHT_RIVET_LIVE_HOST"),
    reason="live host evidence requires explicit WRIGHT_RIVET_LIVE_HOST=1 opt-in",
)
def test_live_available_host_bridge_probe_uses_workspace_gateway() -> None:
    base_url, session_id, headers = _live_inputs()
    server_id = os.environ["WRIGHT_LIVE_HOST_SERVER_ID"]
    response = httpx.get(
        f"{base_url}/api/mcp/servers/{server_id}",
        headers={**headers, "X-Wright-Session": session_id},
        timeout=30,
    )
    response.raise_for_status()
    evidence = response.json()
    assert evidence["server_id"] == server_id
    assert evidence["status"] in {"active", "inactive", "error"}
