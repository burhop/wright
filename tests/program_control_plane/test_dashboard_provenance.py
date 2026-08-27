"""Dashboard provenance, deterministic projection, and bounded corruption cases."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from program_control.dashboard import (
    DashboardError,
    default_benchmark_summary,
    derive_areas,
    make_dashboard,
)
from program_control.git_subject import GitReader
from program_control.json_contracts import deterministic_json_bytes, validate_schema


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
OBSERVED = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def _load(root: Path, relative: str) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _report(repository_root: Path) -> tuple[dict, str]:
    reader = GitReader(repository_root)
    identity = reader.resolve_identity("HEAD", PROGRAM_ROOT)
    policy = _load(repository_root, f"{PROGRAM_ROOT}/lifecycle-policy.json")
    input_manifest, input_digest = reader.authoritative_manifest(
        identity.source_commit, PROGRAM_ROOT, policy
    )
    bundle, bundle_digest = reader.source_bundle(identity.source_commit)
    catalog = _load(repository_root, f"{PROGRAM_ROOT}/gate-catalog.json")
    evidence = _load(repository_root, f"{PROGRAM_ROOT}/gate-evidence.json")
    areas = derive_areas(catalog, evidence, OBSERVED)
    observed = OBSERVED.isoformat().replace("+00:00", "Z")
    return (
        {
            "observed_at": observed,
            "validator": {
                "version": "1.0.0",
                "bundle_manifest_digest": bundle_digest,
                "bundle_manifest": bundle,
            },
            "subject": {
                "source_commit": identity.source_commit,
                "source_tree": identity.source_tree,
                "program_tree": identity.program_tree,
                "input_manifest_digest": input_digest,
                "input_manifest": input_manifest,
                "release_candidate": {
                    "kind": evidence["subject"]["kind"],
                    "git_commit": evidence["subject"]["git_commit"],
                    "git_tree": evidence["subject"]["git_tree"],
                    "artifact_digests": [],
                },
            },
            "areas": areas,
            "benchmark_summary": default_benchmark_summary(),
            "release_approval": {
                "status": "absent",
                "approval_id": None,
                "subject_matches": False,
            },
            "release_eligible": False,
            "next_action": {"action": "EXECUTE_EPP_F01_TASKS"},
        },
        evidence["data_cutoff"],
    )


def test_dashboard_candidate_matches_v2_schema_and_embeds_no_delivery_claim(
    repository_root: Path,
) -> None:
    report, cutoff = _report(repository_root)
    dashboard = make_dashboard(report, data_cutoff=cutoff)
    schema = _load(repository_root, f"{PROGRAM_ROOT}/schemas/dashboard.schema.json")
    assert validate_schema(schema, dashboard) == []
    assert dashboard["generation_status"] == "candidate_not_evidence"
    assert dashboard["data_cutoff"] == cutoff
    assert dashboard["container_relation"] == {
        "first_parent_must_equal_source": True,
        "allowed_generated_outputs": [f"{PROGRAM_ROOT}/dashboard.json"],
        "container_commit_embedded": False,
        "delivery_evidence_embedded": False,
    }
    assert dashboard["release_eligible"] is False


def test_dashboard_generation_is_byte_identical_for_fixed_observations(
    repository_root: Path,
) -> None:
    report, cutoff = _report(repository_root)
    first = deterministic_json_bytes(make_dashboard(report, data_cutoff=cutoff))
    second = deterministic_json_bytes(
        make_dashboard(copy.deepcopy(report), data_cutoff=cutoff)
    )
    assert first == second
    assert sha256(first).hexdigest() == sha256(second).hexdigest()


def test_isolated_evidence_corruption_is_bounded_and_does_not_mutate_source(
    repository_root: Path,
) -> None:
    catalog_path = repository_root / PROGRAM_ROOT / "gate-catalog.json"
    evidence_path = repository_root / PROGRAM_ROOT / "gate-evidence.json"
    before = {
        catalog_path: sha256(catalog_path.read_bytes()).hexdigest(),
        evidence_path: sha256(evidence_path.read_bytes()).hexdigest(),
    }
    catalog = _load(repository_root, f"{PROGRAM_ROOT}/gate-catalog.json")
    corrupted = _load(repository_root, f"{PROGRAM_ROOT}/gate-evidence.json")
    corrupted["assertions"][0]["status"] = "passed"
    with pytest.raises(DashboardError) as caught:
        derive_areas(catalog, corrupted, OBSERVED)
    assert caught.value.code == "GATE_AGGREGATE_MISMATCH"
    assert "aggregate" in str(caught.value).lower()
    assert before == {
        catalog_path: sha256(catalog_path.read_bytes()).hexdigest(),
        evidence_path: sha256(evidence_path.read_bytes()).hexdigest(),
    }
