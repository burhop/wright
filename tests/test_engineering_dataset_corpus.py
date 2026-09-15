"""The committed corpus must contain 10 × 3 complete human input packs."""

import json
from collections import Counter

import pytest

from scripts.engineering_dataset_campaign import DEFAULT_INPUTS, TEMPLATES, load_dataset


MANIFESTS = sorted((DEFAULT_INPUTS / "scenarios").glob("*/*/scenario.json"))
CONFIG = json.loads((DEFAULT_INPUTS / "campaign.json").read_text())


def test_corpus_has_exact_three_scenarios_for_each_current_template():
    import yaml

    catalog = yaml.safe_load((TEMPLATES.parent / "catalog.yaml").read_text())
    catalog_ids = {entry["id"] for entry in catalog["templates"]}
    assert len(catalog_ids) == 10
    assert set(CONFIG["template_ids"]) == catalog_ids
    data = [json.loads(path.read_text(encoding="utf-8-sig")) for path in MANIFESTS]
    assert len(data) == CONFIG["target"] == 30
    assert len({row["scenario_id"] for row in data}) == 30
    assert Counter(row["template_id"] for row in data) == {key: 3 for key in catalog_ids}
    assert CONFIG["content_validation_enabled"] is False
    assert CONFIG["approval_mode"] == "auto"


@pytest.mark.parametrize("manifest", MANIFESTS, ids=[p.parent.name + "-" + p.parent.parent.name for p in MANIFESTS])
def test_each_input_pack_is_complete_original_and_uploadable(manifest):
    item = load_dataset(manifest, DEFAULT_INPUTS, CONFIG)
    files = item["files"]
    assert len((manifest.parent / files["prompt"]).read_text(encoding="utf-8").split()) >= 25
    assert len((manifest.parent / files["user_profile"]).read_text(encoding="utf-8").split()) >= 20
    assert any(path.endswith(".svg") for path in files["images"])
    rasters = [path for path in files["images"] if path.endswith(".png")]
    assert rasters, "Original SVG concepts need raster companions for the current image input"
    for raster in rasters:
        assert (manifest.parent / raster).read_bytes().startswith(bytes([137, 80, 78, 71, 13, 10, 26, 10]))
    assert item["provenance"]["kind"] == "synthetic"
    assert item["provenance"]["rights"]
    assert len({entry["role"] for entry in item["expected_outputs"]}) == len(item["expected_outputs"])
