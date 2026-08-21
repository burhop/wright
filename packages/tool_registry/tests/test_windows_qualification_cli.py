from __future__ import annotations

import json
from pathlib import Path

from tool_registry import windows_qualification_cli as cli
from tool_registry.windows_qualification_models import WINDOWS_MCP_ALLOWLIST
from tool_registry.windows_qualification_recipes import (
    get_windows_qualification_recipe,
    recipe_digest,
)


def _decision(path: Path, server_id: str, value: str) -> None:
    recipe = get_windows_qualification_recipe(server_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "server_id": server_id,
                "recipe_digest": recipe_digest(recipe),
                "preflight": {
                    "decision": value,
                    "reason_code": f"fixture_{value}",
                    "reviewed_at": "2026-08-13T12:00:00Z",
                    "material_concerns": [],
                    "residual_risks": [],
                },
            }
        ),
        encoding="utf-8",
    )


def test_preview_is_pure_and_rejects_nonallowlisted_identity(
    tmp_path: Path, capsys
) -> None:
    evidence = tmp_path / "must-not-be-created"

    assert cli.main(["preview", "brep-mcp", "--evidence-dir", str(evidence)]) == 0
    assert not evidence.exists()
    preview = json.loads(capsys.readouterr().out)
    assert preview["server_id"] == "brep-mcp"
    assert "command" not in json.dumps(preview).lower()

    assert cli.main(["preview", "unreviewed-mcp", "--evidence-dir", str(evidence)]) == 2


def test_qualify_enforces_native_windows_before_any_run(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(cli.platform, "system", lambda: "Linux")

    assert (
        cli.main(
            [
                "qualify",
                "brep-mcp",
                "--evidence-dir",
                str(tmp_path / "evidence"),
                "--work-root",
                str(tmp_path / "windows-mcp-qualification"),
                "--safety-decision",
                str(tmp_path / "missing.json"),
            ]
        )
        == 2
    )


def test_qualify_rejects_unmarked_work_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli.platform, "system", lambda: "Windows")
    decision = tmp_path / "decision.json"
    _decision(decision, "brep-mcp", "safety_blocked")

    assert (
        cli.main(
            [
                "qualify",
                "brep-mcp",
                "--evidence-dir",
                str(tmp_path / "evidence"),
                "--work-root",
                str(tmp_path / "broad-root"),
                "--safety-decision",
                str(decision),
            ]
        )
        == 2
    )


def test_qualify_all_uses_only_the_fixed_order_and_completes_boundaries(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(cli.platform, "system", lambda: "Windows")
    decisions = tmp_path / "decisions"
    for server_id in WINDOWS_MCP_ALLOWLIST:
        _decision(decisions / f"{server_id}.json", server_id, "safety_blocked")
    evidence_dir = tmp_path / "evidence"
    work_root = tmp_path / "windows-mcp-qualification"

    assert (
        cli.main(
            [
                "qualify-all",
                "--evidence-dir",
                str(evidence_dir),
                "--work-root",
                str(work_root),
                "--decisions-dir",
                str(decisions),
            ]
        )
        == 0
    )

    progress = (evidence_dir / "progress-log.md").read_text(encoding="utf-8")
    positions = [
        progress.index(f"`{server_id}`") for server_id in WINDOWS_MCP_ALLOWLIST
    ]
    assert positions == sorted(positions)
    proof = json.loads((evidence_dir / "non-allowlist-proof.json").read_text())
    assert proof == {"actions": [], "count": 0}


def test_decision_must_be_bound_to_current_recipe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cli.platform, "system", lambda: "Windows")
    decision = tmp_path / "decision.json"
    _decision(decision, "brep-mcp", "safety_blocked")
    payload = json.loads(decision.read_text())
    payload["recipe_digest"] = "0" * 64
    decision.write_text(json.dumps(payload), encoding="utf-8")

    assert (
        cli.main(
            [
                "qualify",
                "brep-mcp",
                "--evidence-dir",
                str(tmp_path / "evidence"),
                "--work-root",
                str(tmp_path / "windows-mcp-qualification"),
                "--safety-decision",
                str(decision),
            ]
        )
        == 2
    )
