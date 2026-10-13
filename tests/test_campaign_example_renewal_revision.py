from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _module():
    path = ROOT / "scripts/build_campaign_example_renewal_revision.py"
    spec = importlib.util.spec_from_file_location("renewal_revision", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_revision_maps_exactly_30_without_reusing_historical_credit():
    document = json.loads(_module().render()[0])
    assert document["status"] == "prospective_prepared_not_dispatched"
    assert len(document["cases"]) == 30
    assert len({item["scenario_id"] for item in document["cases"]}) == 30
    assert document["history_policy"] == {
        "prior_attempts_mutated": False,
        "prior_approvals_reused": False,
        "retry_budgets_reset": False,
        "campaign_credit_carried_forward": False,
    }
    assert all(
        item["prospective_identity"]["profile_ref"]["sha256"]
        and item["prospective_identity"]["baseline_ref"]["sha256"]
        and item["prospective_identity"]["expected_output_roles"]
        for item in document["cases"]
    )


def test_checked_in_revision_is_reproducible():
    module = _module()
    json_bytes, markdown_bytes = module.render()
    assert module.JSON_DESTINATION.read_bytes() == json_bytes
    assert module.MARKDOWN_DESTINATION.read_bytes() == markdown_bytes


def test_revision_rejects_changed_historical_semantic_identity(monkeypatch):
    module = _module()
    identities = module._historical_identities()
    identities[next(iter(identities))]["semantic_manifest_sha256"] = "0" * 64
    monkeypatch.setattr(module, "_historical_identities", lambda: identities)

    with pytest.raises(ValueError, match="Historical scenario content changed"):
        module.render()
