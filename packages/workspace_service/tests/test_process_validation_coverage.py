"""Integrity and honesty checks for the 30-pack validator support map."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from workspace_service.process_validation.profiles import load_profile


REPOSITORY = Path(__file__).parents[3]
COVERAGE_PATH = (
    REPOSITORY
    / "packages/workspace_service/src/workspace_service/process_validation/"
    "profiles/coverage.json"
)


def _builder():
    path = REPOSITORY / "scripts/build_process_validation_coverage.py"
    spec = importlib.util.spec_from_file_location("process_validation_coverage", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _coverage() -> dict:
    return json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))


def test_coverage_is_reproducible_and_accounts_for_exactly_30_source_packs():
    coverage = _coverage()
    assert coverage == _builder().build(REPOSITORY)
    assert coverage["schema_version"] == "wright.process-validation-coverage/2"
    assert coverage["kind"] == "capability_support_map"

    scenarios = coverage["scenarios"]
    ids = [item["scenario_id"] for item in scenarios]
    assert len(ids) == len(set(ids)) == 30
    assert {item["family"] for item in scenarios} == {
        "printed-replacement-part",
        "raspberry-pi-enclosure",
        "sheet-metal-supplier-handoff",
        "lightweight-equipment-bracket",
        "parametric-drill-jig",
        "robot-tracking-diagnosis",
        "heat-spreader-sizing",
        "sensor-fan-harness",
        "sensor-interface-pcb",
        "water-heater-sizing",
    }
    for family in {item["family"] for item in scenarios}:
        assert sum(item["family"] == family for item in scenarios) == 3
    assert all(item["sources"] for item in scenarios)
    assert all(item["source_requirements_seed"] for item in scenarios)
    assert all(item["targeted_defect_seed"] for item in scenarios)


def test_only_the_two_bounded_initial_slices_are_qualified():
    coverage = _coverage()
    scenarios = {item["scenario_id"]: item for item in coverage["scenarios"]}
    qualified = {
        scenario_id
        for scenario_id, item in scenarios.items()
        if item["support_status"] == "qualified"
    }
    assert qualified == {
        "parametric-drill-jig-01",
        "heat-spreader-sizing-01",
    }
    assert qualified == set(coverage["qualified_scenarios"])

    for scenario_id, item in scenarios.items():
        if scenario_id in qualified:
            assert item["requirements_frozen"] and item["initial_slice"]
            assert item["profile"]
            assert {capability["support"] for capability in item["capabilities"]} == {
                "qualified"
            }
        else:
            assert item["support_status"] in {"implemented", "unsupported"}
            assert item["requirements_frozen"]
            assert not item["initial_slice"]
            if item["profile"]:
                assert item["support_status"] == "implemented"
            else:
                assert item["profile"] is None
            assert not any(
                capability["support"] == "qualified"
                for capability in item["capabilities"]
            )


def test_qualified_entries_pin_loadable_profiles_readers_and_evidence():
    coverage = _coverage()
    for item in coverage["scenarios"]:
        metadata = item["profile"]
        if metadata is None:
            continue
        profile = load_profile(metadata["profile_resource"])
        assert profile.reference().model_dump(mode="json") == metadata["profile_ref"]
        assert profile.baseline.reference().model_dump(mode="json") == metadata[
            "baseline_ref"
        ]
        assert {f"{check.reader}@1" for check in profile.checks} == set(
            metadata["reader_ids"]
        )
        assert metadata["scope"] and metadata["limitations"]
        for evidence_path in metadata["evidence"]:
            assert (REPOSITORY / evidence_path).is_file()

    for item in coverage["scenarios"]:
        metadata = item["full_profile"]
        if metadata is None:
            continue
        profile = load_profile(metadata["profile_resource"])
        assert profile.reference().model_dump(mode="json") == metadata["profile_ref"]
        assert profile.baseline.reference().model_dump(mode="json") == metadata["baseline_ref"]
        assert {f"{check.reader}@1" for check in profile.checks} == set(metadata["reader_ids"])
        review_ids = {
            requirement_id
            for check in profile.checks
            if check.constraint.operator == "review"
            for requirement_id in check.requirement_ids
        }
        assert review_ids == {
            requirement.id
            for requirement in profile.baseline.requirements
            if requirement.review_required
        }


def test_every_unqualified_capability_has_an_explicit_extension_path():
    coverage = _coverage()
    recipes = coverage["extension_recipes"]
    supports = set()
    capabilities = set()
    for scenario in coverage["scenarios"]:
        for capability in scenario["capabilities"]:
            supports.add(capability["support"])
            capabilities.add(capability["id"])
            assert capability["support"] in coverage["support_definitions"]
            assert capability["limitation"]
            assert capability["extension_recipe"] in recipes
            recipe = recipes[capability["extension_recipe"]]
            assert recipe["prerequisites"] and recipe["steps"]

    assert capabilities == set(recipes)
    assert supports == {"qualified", "implemented"}
    assert all(item["full_profile"] for item in coverage["scenarios"])
