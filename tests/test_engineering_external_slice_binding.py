"""Readiness/declaration coverage only; no native tools or campaign dispatch."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


binding = load("external_slice_declarations_test", "scripts/engineering_external_slice_binding.py")
fixture = load("external_slice_inputs_test", "tests/fixtures/external_slice_binding.py")
PROCESS = {"base": "historical-provider-owned-base", "layer_height": "0.20",
           "wall_loops": "5", "sparse_infill_density": "40%", "enable_support": "1"}


def test_missing_configuration_fails_before_any_staging(tmp_path):
    for filename, family in (("prepare-printed-dataset-campaign.py", "printed-replacement-part"),
                             ("prepare-drill-jig-dataset-campaign.py", "parametric-drill-jig")):
        module = load("preflight_" + family, "scripts/" + filename)
        directory = next((ROOT / "tests/datasets/engineering-workflows/scenarios" / family).glob("01-*"))
        args = SimpleNamespace(workspace_root=tmp_path / "workspace", draft_root=tmp_path / "draft",
                               attempt="preflight", initialize_agentcad=True)
        with pytest.raises(ValueError, match="Supply --slicer-binding"):
            module.prepare(args, directory, {})
    assert not list(tmp_path.iterdir())


def test_profile_bytes_and_exact_registered_schemas_are_retained(tmp_path):
    path, tools = fixture.make_binding(tmp_path, "fixture-01", PROCESS)
    value, selected, profiles, digest = binding.preflight(path, "fixture-01", tools, PROCESS)
    assert len(digest) == 64
    assert set(selected) == {"slicer", "files", "inspection"}
    for role, raw in profiles.items():
        assert raw == Path(value["profiles"][role]["path"]).read_bytes()


@pytest.mark.parametrize("change", [
    "scenario", "schema", "missing", "ambiguous", "legacy", "profile_digest", "process",
    "source", "receipt", "partial_path", "mount", "backend", "section", "success_contract",
])
def test_predictable_missing_changed_or_incompatible_choices_reject(tmp_path, change):
    path, tools = fixture.make_binding(tmp_path, "fixture-01", PROCESS)
    value = json.loads(path.read_text())
    if change == "scenario":
        value["scenario_id"] = "fixture-02"
    elif change == "schema":
        tools[0]["schema_digest"] = "changed"
    elif change == "missing":
        tools.pop()
    elif change == "ambiguous":
        tools.append(tools[0])
    elif change == "legacy":
        value["slicer"]["server"] = tools[0]["server_id"] = "wright-printed-part-slicer"
    elif change == "profile_digest":
        Path(value["profiles"]["filament"]["path"]).write_bytes(b"changed")
    elif change == "process":
        PROCESS_CHANGED = {**PROCESS, "enable_support": "0"}
        path, tools = fixture.make_binding(tmp_path, "fixture-01", PROCESS_CHANGED)
        value = json.loads(path.read_text())
    elif change == "source":
        del value["slicer"]["arguments"]["source"]
    elif change == "receipt":
        del value["expected_response_fields"]["output"]
    elif change == "partial_path":
        value["slicer"]["arguments"]["extra"] = "prefix{source}"
    elif change == "mount":
        value["inspection"]["workspace_mount"] = "/workspace/../outside"
    elif change == "backend":
        del value["inspection"]["backend"]
    elif change == "section":
        value["nominal_layer_section"] = {"start_marker": "guess"}
    elif change == "success_contract":
        value["success_contract"] = ""
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        binding.preflight(path, "fixture-01", tools, PROCESS)


def test_historical_binding_documents_and_wrappers_are_not_executed_by_preparers():
    for filename in ("prepare-printed-dataset-campaign.py", "prepare-drill-jig-dataset-campaign.py"):
        source = (ROOT / "scripts" / filename).read_text(encoding="utf-8")
        assert "engineering_dataset_slice" not in source
        assert "engineering_jig_slice_mcp" not in source
        assert "external_slice.preflight" in source and "external_slice.bind" in source
