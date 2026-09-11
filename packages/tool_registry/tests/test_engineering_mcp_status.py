from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "packages" / "tool_registry" / "src"))

from engineering_mcp_status import (  # noqa: E402
    PORTFOLIO_CATEGORY_IDS,
    _portfolio_category,
    build_engineering_status,
    history_snapshot,
    load_assessments,
    public_projection,
    qa_projection,
    record_history,
)
from tool_registry.canonical_catalog import load_canonical_entries  # noqa: E402
from tool_registry.catalog_models import CatalogEntry  # noqa: E402

STATUS_ROOT = ROOT / "docs" / "mcp-catalog" / "status"


def sample_entry(**updates) -> CatalogEntry:
    values = {
        "id": "sample",
        "name": "Sample",
        "vendor": "Vendor",
        "description": "Sample engineering integration",
        "domains": ["cad"],
        "engineering_stages": ["design"],
        "transport": "stdio",
        "command": ["sample"],
        "source_url": "https://example.com/sample",
        "locality": "local",
        "weight": "light",
    }
    values.update(updates)
    return CatalogEntry.model_validate(values)


def build_current(as_of: date = date(2026, 9, 10)):
    entries = load_canonical_entries()
    assessments = load_assessments(
        STATUS_ROOT / "assessments.yaml",
        catalog_ids={entry.id for entry in entries},
        schema_path=STATUS_ROOT / "assessments.schema.json",
    )
    return build_engineering_status(
        entries,
        as_of=as_of,
        repository_root=ROOT,
        process_chains_path=None,
        assessments=assessments,
    )


def test_combined_baseline_has_one_category_per_canonical_integration():
    status = build_current()
    ids = [record["server_id"] for record in status["records"]]
    assert len(ids) == len(set(ids)) == status["total"] == 78
    assert status["category_counts"] == {
        "works": 11,
        "preview": 6,
        "requires_login": 15,
        "in_progress": 0,
        "abandoned": 46,
        "vendor_blocked": 0,
    }
    assert sum(status["category_counts"].values()) == len(ids)
    by_category = {
        category: {
            record["server_id"]
            for record in status["records"]
            if record["portfolio_category"] == category
        }
        for category in PORTFOLIO_CATEGORY_IDS
    }
    assert "kernelcad-mcp" in by_category["abandoned"]
    assert {"web3d-mcp", "grafana-official-mcp", "nvidia-elements-mcp"} <= (
        by_category["preview"]
    )
    assert {
        "ansys-mcp-server-community",
        "easy-mcp-autocad",
        "freecad-mcp-contextform",
        "freecad-mcp-proximile",
        "freecad-mcp-sergiudanstan",
        "kicad-mcp-lamaalrajih",
        "openfoam-mcp-webworn",
        "solidworks-mcp-python",
    } <= by_category["abandoned"]
    assert {
        "autocad-mcp-u-c4n",
        "rhino-mcp-easehee",
        "solid-edge-mcp-burhop",
    } <= by_category["works"]
    assert {
        "ansys-fluent-mcp",
        "fusion360-mcp-server",
        "matlab-mcp-server",
        "rhino-mcp",
        "solidworks-mcp-ts",
    } <= by_category["requires_login"]
    assert {
        "autodesk-fusion-desktop-mcp",
        "blender-mcp-harveyxiacn",
        "cad-mcp-daobataotie",
        "comsol-multiphysics-mcp-wjc9011",
        "creo-mcp",
        "multicad-mcp",
        "nvidia-omniverse-isaac-sim-mcp",
        "nvidia-omniverse-kit-mcp",
        "nvidia-omniverse-omniui-mcp",
        "nvidia-omniverse-usd-code-mcp",
        "simscale-edge-mcp-getanirao",
        "simulink-agentic-toolkit",
        "sketchup-mcp",
        "thingworx-mcp",
        "webmcp-openscad",
        "wincc-unified-mcp",
    } <= by_category["abandoned"]
    assert not by_category["in_progress"]
    assert set().union(*by_category.values()) == set(ids)
    assert {record["protocol_family"] for record in status["records"]} == {
        "mcp",
        "webmcp",
        "hardware_mcp",
    }
    assert status["chain_diagnostic"]["status"] == "not_supplied"


def test_former_in_progress_batch_has_fresh_review_metadata():
    reviewed_ids = {
        "ansys-fluent-mcp",
        "ansys-mcp-server-community",
        "autodesk-fusion-data-mcp",
        "autodesk-fusion-desktop-mcp",
        "autodesk-fusion-mcp-python",
        "blender-mcp-harveyxiacn",
        "cad-mcp-daobataotie",
        "comsol-multiphysics-mcp-suzysa",
        "comsol-multiphysics-mcp-wjc9011",
        "creo-mcp",
        "easy-mcp-autocad",
        "freecad-mcp-contextform",
        "freecad-mcp-proximile",
        "freecad-mcp-sandraschi",
        "freecad-mcp-sergiudanstan",
        "fusion360-mcp-server",
        "grafana-official-mcp",
        "kernelcad-mcp",
        "kicad-mcp-lamaalrajih",
        "matlab-mcp-server",
        "multicad-mcp",
        "nvidia-elements-mcp",
        "nvidia-omniverse-isaac-sim-mcp",
        "nvidia-omniverse-kit-mcp",
        "nvidia-omniverse-omniui-mcp",
        "nvidia-omniverse-usd-code-mcp",
        "openfoam-mcp-webworn",
        "rhino-mcp",
        "simulink-agentic-toolkit",
        "sketchup-mcp",
        "solidworks-mcp-alisamsam",
        "solidworks-mcp-python",
        "solidworks-mcp-ts",
        "thingworx-mcp",
        "webmcp-openscad",
        "wincc-unified-mcp",
    }
    records = {record["server_id"]: record for record in build_current()["records"]}
    assert len(reviewed_ids) == 36
    assert all(
        records[item]["assessment_reviewed_at"] == "2026-09-10" for item in reviewed_ids
    )
    assert all(records[item]["tests_completed"] for item in reviewed_ids)
    assert all(
        records[item]["priority"] in {"low", "normal", "high", "urgent"}
        for item in reviewed_ids
    )


def test_precedence_separates_vendor_restriction_abandonment_and_repair():
    failed = sample_entry(
        validation_result={"status": "failed", "message": "startup failed"}
    )
    assert (
        _portfolio_category(
            failed, disposition="follow_up", qualification_status="failing"
        )[0]
        == "in_progress"
    )
    assert (
        _portfolio_category(
            failed, disposition="removed", qualification_status="failing"
        )[0]
        == "abandoned"
    )
    vendor = {
        "category": "vendor_blocked",
        "substatus": "restricted",
        "reason": "The vendor explicitly requested that this integration use stop.",
        "restriction_reference": "restricted-reference-1",
    }
    assert (
        _portfolio_category(
            failed,
            disposition="removed",
            qualification_status="failing",
            assessment=vendor,
        )[0]
        == "vendor_blocked"
    )


def test_authentication_requires_an_observed_blocked_result():
    credential_only = sample_entry(credentials_required=["API_TOKEN"])
    assert (
        _portfolio_category(
            credential_only, disposition="follow_up", qualification_status="untested"
        )[0]
        == "in_progress"
    )
    observed = credential_only.model_copy(
        update={
            "validation_result": credential_only.validation_result.model_copy(
                update={
                    "status": "blocked",
                    "message": "Authentication challenge observed",
                }
            )
        }
    )
    assert (
        _portfolio_category(
            observed, disposition="follow_up", qualification_status="blocked"
        )[0]
        == "requires_login"
    )


def test_expired_works_become_review_needed_without_erasing_past_success():
    status = build_current(date(2026, 10, 10))
    autocad = next(
        record
        for record in status["records"]
        if record["server_id"] == "autocad-mcp-u-c4n"
    )
    assert autocad["portfolio_category"] == "in_progress"
    assert autocad["progress_substatus"] == "renewal_due"
    assert autocad["latest_result"] == "passed"


def test_assessments_reject_unknown_catalog_ids(tmp_path):
    assessment = tmp_path / "assessments.yaml"
    assessment.write_text(
        "schema_version: 1\npolicy_version: engineering-integrations-v2\nassessments:\n  unknown-server:\n    category: in_progress\n    substatus: planned\n    reason: This record has no matching canonical catalog identity.\n    reviewed_at: '2026-09-10'\n    priority: normal\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not in the canonical catalog"):
        load_assessments(
            assessment,
            catalog_ids={"sample"},
            schema_path=STATUS_ROOT / "assessments.schema.json",
        )


def test_assessments_reject_duplicate_ids(tmp_path):
    assessment = tmp_path / "duplicates.yaml"
    repeated = "    category: in_progress\n    substatus: planned\n    reason: This reviewed item still needs a clean execution check.\n    reviewed_at: '2026-09-10'\n    priority: normal\n"
    assessment.write_text(
        "schema_version: 1\npolicy_version: engineering-integrations-v2\nassessments:\n"
        f"  sample:\n{repeated}  sample:\n{repeated}",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate YAML key: sample"):
        load_assessments(
            assessment,
            catalog_ids={"sample"},
            schema_path=STATUS_ROOT / "assessments.schema.json",
        )


def test_public_projection_is_an_allowlist_with_matching_membership_and_counts():
    status = build_current()
    status["records"][0]["source_url"] = "file:///private/evidence.json"
    status["records"][0]["owner"] = "Private reviewer"
    qa = qa_projection(status)
    public = public_projection(status)
    assert public["category_counts"] == qa["category_counts"]
    assert [row["server_id"] for row in public["records"]] == [
        row["server_id"] for row in qa["records"]
    ]
    assert all(
        "owner" not in row and "evidence_href" not in row for row in public["records"]
    )
    assert all(
        not row.get("source_url") or row["source_url"].startswith("https://")
        for row in public["records"]
    )
    public_schema = json.loads((STATUS_ROOT / "status.schema.json").read_text("utf-8"))
    assert not list(Draft202012Validator(public_schema).iter_errors(public))


def test_history_is_idempotent_supports_corrections_and_declines():
    status = qa_projection(build_current())
    first = history_snapshot(status, observed_at="2026-09-10T12:00:00Z")
    history, added = record_history(None, first)
    assert added
    rerun = dict(first, observed_at="2026-09-10T13:00:00Z")
    same, added = record_history(history, rerun)
    assert not added and same == history

    declined = dict(first)
    declined["snapshot_id"] = "2026-09-11-deadbeef1234"
    declined["observed_at"] = "2026-09-11T12:00:00Z"
    declined["assessed_as_of"] = "2026-09-11"
    declined["green_count"] -= 1
    declined["green_components"] = dict(
        declined["green_components"],
        preview=declined["green_components"]["preview"] - 1,
    )
    corrected, added = record_history(
        history,
        declined,
        correction_for=first["snapshot_id"],
        correction_reason="Correct a superseded preview assessment after evidence review.",
    )
    assert added
    assert corrected["snapshots"][-1]["green_count"] == first["green_count"] - 1
    assert corrected["snapshots"][-1]["corrects"] == first["snapshot_id"]


def test_invalid_input_preserves_last_good_output(tmp_path):
    destination = tmp_path / "published"
    destination.mkdir()
    sentinel = destination / "status.json"
    sentinel.write_text('{"last_good": true}\n', encoding="utf-8")
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(
        "schema_version: 1\npolicy_version: wrong\nassessments: {}\n", encoding="utf-8"
    )
    process = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate-engineering-mcp-status.py"),
            "--assessments",
            str(invalid),
            "--qa-output",
            str(destination),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert process.returncode != 0
    assert sentinel.read_text("utf-8") == '{"last_good": true}\n'
