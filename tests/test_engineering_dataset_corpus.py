"""The committed corpus must contain 10 × 3 complete human input packs."""

import json
import re
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


def test_engineering_guide_covers_existing_cases_without_replacing_inputs():
    guide_path = DEFAULT_INPUTS / "ENGINEERING-GUIDE.md"
    guide = guide_path.read_text(encoding="utf-8")
    assert "[engineering example guide](ENGINEERING-GUIDE.md)" in (
        DEFAULT_INPUTS / "README.md"
    ).read_text(encoding="utf-8")

    sections = dict(re.findall(r'<a id="([^"]+)"></a>\s*(.*?)(?=<a id=|\Z)', guide, re.S))
    scenario_sections = {key for key in sections if re.search(r"-\d{2}$", key)}
    expected_ids = set()
    for manifest in MANIFESTS:
        scenario = json.loads(manifest.read_text(encoding="utf-8-sig"))
        scenario_id = scenario["scenario_id"]
        expected_ids.add(scenario_id)
        assert guide.count(f'<a id="{scenario_id}"></a>') == 1
        section = sections[scenario_id]
        for label in ("Purpose", "Work", "Useful result"):
            assert f"**{label}:**" in section, scenario_id
        source_dir = manifest.parent.relative_to(DEFAULT_INPUTS).as_posix()
        assert f"]({source_dir}/{scenario['files']['prompt']})" in section
        assert f"]({source_dir}/context.md)" in section
        # Presentation copy is not another uploaded requirement or hashed input.
        assert guide_path.name not in json.dumps(scenario["files"])

    assert scenario_sections == expected_ids
    for target in re.findall(r"\]\(([^)]+)\)", guide):
        if target.startswith("#"):
            assert target[1:] in sections, target
        else:
            assert (DEFAULT_INPUTS / target).is_file(), target


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
