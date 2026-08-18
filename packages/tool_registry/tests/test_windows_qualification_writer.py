from __future__ import annotations

import json
import hashlib
from datetime import UTC, datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tool_registry.canonical_catalog import load_catalog_document
from tool_registry.catalog_models import CatalogEntry
from tool_registry.windows_qualification_models import (
    EMPTY_DIGEST,
    QUALIFICATION_STAGES,
    WINDOWS_MCP_ALLOWLIST,
    SafetyPreflight,
    ServerQualificationEvidence,
    StageEvidence,
)
from tool_registry.windows_qualification_recipes import (
    load_windows_qualification_recipes,
    recipe_digest,
)
from tool_registry.windows_qualification_writer import (
    build_catalog_summary,
    write_run_artifacts,
    write_server_evidence,
)


def _evidence(private_root: Path) -> ServerQualificationEvidence:
    stages = []
    for stage in QUALIFICATION_STAGES:
        stages.append(
            StageEvidence(
                stage=stage,
                result="passed",
                reason_code=f"{stage}_passed",
                summary="Bounded fixture passed.",
                observations=(
                    {
                        "api_token": "SUPERSECRET",
                        "private_path": str(private_root / "package"),
                    }
                    if stage == "windows_install_passed"
                    else {}
                ),
            )
        )
    return ServerQualificationEvidence(
        evidence_id="brep-mcp-windows-fixture",
        server_id="brep-mcp",
        policy_version="windows-allowlist-v1",
        recipe_digest=EMPTY_DIGEST,
        machine_digest=EMPTY_DIGEST,
        credential_binding_digest=EMPTY_DIGEST,
        observed_at=datetime(2026, 8, 13, tzinfo=UTC),
        safety_preflight=SafetyPreflight(
            decision="approved",
            reason_code="fixture_reviewed",
            reviewed_at=datetime(2026, 8, 13, tzinfo=UTC),
        ),
        stages=stages,
        installed_items=["brepjs-cad@0.103.0"],
        cleanup_events=["removed_disposable_server_root"],
        attempted_server_ids=["brep-mcp"],
        non_allowlist_actions=[],
        terminal_classification="passed",
    )


def test_writer_is_atomic_schema_valid_bounded_and_redacted(tmp_path: Path) -> None:
    private_root = tmp_path / "windows-mcp-qualification"
    evidence_dir = tmp_path / "evidence"

    result = write_server_evidence(
        _evidence(private_root), evidence_dir, private_roots=[private_root]
    )

    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    serialized = result.json_path.read_text(encoding="utf-8")
    assert payload["server_id"] == "brep-mcp"
    assert len(payload["stages"]) == 8
    assert "SUPERSECRET" not in serialized
    assert str(private_root) not in serialized
    assert "[REDACTED]" in serialized
    assert result.json_path.stat().st_size <= 1024 * 1024
    assert len(result.digest) == 64
    assert not list(evidence_dir.glob("*.tmp"))

    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "| Source | passed |" in markdown
    assert "| Cleanup | passed |" in markdown
    assert "SUPERSECRET" not in markdown


def test_consolidated_artifacts_have_complete_matrix_and_empty_denial_proof(
    tmp_path: Path,
) -> None:
    evidence = _evidence(tmp_path / "windows-mcp-qualification")

    paths = write_run_artifacts([evidence], tmp_path / "evidence")

    matrix = paths["matrix"].read_text(encoding="utf-8")
    assert "Package or registration" in matrix
    assert "Wright gateway" in matrix
    assert "brep-mcp" in matrix
    assert json.loads(paths["installed_items"].read_text())[0]["item"] == (
        "brepjs-cad@0.103.0"
    )
    assert json.loads(paths["cleanup_ledger"].read_text())[0]["event"] == (
        "removed_disposable_server_root"
    )
    assert json.loads(paths["non_allowlist_proof"].read_text()) == {
        "actions": [],
        "count": 0,
    }


def test_catalog_summary_uses_independent_results_and_bounded_labels(
    tmp_path: Path,
) -> None:
    evidence = _evidence(tmp_path / "windows-mcp-qualification")
    stages = list(evidence.stages)
    stages[4] = stages[4].model_copy(
        update={
            "result": "failed",
            "reason_code": "safe_probe_output_schema_mismatch",
        }
    )
    evidence = evidence.model_copy(
        update={"stages": stages, "terminal_classification": "failed"}
    )

    summary = build_catalog_summary(
        evidence,
        evidence_path="docs/mcp-catalog/evidence/solid-edge.json",
        evidence_digest="b" * 64,
    )

    assert summary.package_or_registration.result == "passed"
    assert summary.host_or_backend.result == "failed"
    assert summary.host_or_backend.label == "Status result violates MCP schema"
    assert summary.claim is None


def test_saved_evidence_and_catalog_summaries_are_exactly_bound() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    evidence_dir = (
        repo_root
        / "docs"
        / "mcp-catalog"
        / "evidence"
        / "windows-qualification-2026-08-13"
    )
    schema = json.loads(
        (
            repo_root
            / "packages"
            / "tool_registry"
            / "src"
            / "tool_registry"
            / "catalog"
            / "windows-qualification-evidence.schema.json"
        ).read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    recipes = load_windows_qualification_recipes()
    catalog_entries = {
        raw["id"]: CatalogEntry.model_validate(raw)
        for raw in load_catalog_document()["servers"]
        if raw["id"] in WINDOWS_MCP_ALLOWLIST
    }

    assert tuple(recipes) == WINDOWS_MCP_ALLOWLIST
    assert set(catalog_entries) == set(WINDOWS_MCP_ALLOWLIST)
    for server_id in WINDOWS_MCP_ALLOWLIST:
        evidence_path = evidence_dir / f"{server_id}-windows-qualification.json"
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        validator.validate(payload)
        evidence = ServerQualificationEvidence.model_validate(payload)
        digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        relative_path = evidence_path.relative_to(repo_root).as_posix()
        expected = build_catalog_summary(
            evidence,
            evidence_path=relative_path,
            evidence_digest=digest,
        )
        actual = catalog_entries[server_id].windows_qualification

        assert evidence.server_id == server_id
        assert evidence.recipe_digest == recipe_digest(recipes[server_id])
        assert actual == expected
