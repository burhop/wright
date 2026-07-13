from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_codex_compatibility_harness_is_ephemeral_and_explicit() -> None:
    source = (
        Path(__file__).parents[2] / "scripts" / "run_codex_mcp_compatibility.py"
    ).read_text("utf-8")
    assert "--ephemeral" in source
    assert "--ignore-user-config" in source
    assert "--session-id" in source
    assert "--workspace-id" in source
    assert "wright__workspace_status" in source


@pytest.mark.skipif(
    os.getenv("WRIGHT_RUN_CODEX_COMPAT") != "1",
    reason="requires installed authenticated Codex CLI",
)
def test_live_codex_compatibility(tmp_path) -> None:
    from scripts.run_codex_mcp_compatibility import run

    assert run(model="gpt-5.6-sol", output=tmp_path) == 0
