import hashlib
from importlib.resources import files
import json
from pathlib import Path

from core.process_validation import Baseline, canonical_json
from workspace_service.process_validation.baselines import load_baseline


REPOSITORY = Path(__file__).resolve().parents[3]
DEFINITIONS = (
    REPOSITORY / "packages/workspace_service/src/workspace_service/process_validation/"
    "baselines/definitions.json"
)


def definitions():
    return json.loads(DEFINITIONS.read_text(encoding="utf-8"))["scenarios"]


def test_definitions_cover_every_current_campaign_scenario_exactly_once():
    declared = [row["scenario_id"] for row in definitions()]
    current = [
        json.loads(path.read_text(encoding="utf-8"))["scenario_id"]
        for path in (
            REPOSITORY / "tests/datasets/engineering-workflows/scenarios"
        ).glob("*/*/scenario.json")
    ]
    assert len(declared) == len(set(declared)) == 30
    assert set(declared) == set(current)


def test_all_declared_baselines_are_packaged_closed_and_source_current():
    for definition in definitions():
        baseline = load_baseline(definition["scenario_id"])
        assert isinstance(baseline, Baseline)
        assert baseline.id == definition["scenario_id"] + "-basis"
        for requirement in baseline.requirements:
            for source in requirement.sources:
                path = REPOSITORY / source.artifact_ref
                assert path.is_file()
                assert hashlib.sha256(path.read_bytes()).hexdigest() == source.sha256


def test_generated_baselines_are_reproducible():
    import importlib.util

    script = REPOSITORY / "scripts/build_engineering_validation_baselines.py"
    spec = importlib.util.spec_from_file_location("baseline_builder", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for path, expected in module.render().items():
        assert path.read_bytes() == expected


def test_baseline_loader_pins_digest_and_rejects_traversal():
    baseline = load_baseline("heat-spreader-sizing-01")
    assert (
        load_baseline("heat-spreader-sizing-01", expected=baseline.reference())
        == baseline
    )
    assert canonical_json(baseline).startswith('{"amendments":')
    try:
        load_baseline("../heat-spreader-sizing-01")
    except ValueError as error:
        assert "stable resource name" in str(error)
    else:
        raise AssertionError("Traversal was accepted")


def test_resources_are_available_through_package_loader():
    resource = files("workspace_service.process_validation").joinpath(
        "baselines", "heat-spreader-sizing-03.json"
    )
    assert resource.is_file()
