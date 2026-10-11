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


@pytest.mark.parametrize("mount", ["/workspace", "/mounted/engineering"])
def test_inspection_job_uses_the_explicit_provider_workspace_mount(tmp_path, mount):
    path, tools = fixture.make_binding(tmp_path / "configuration", "fixture-01", PROCESS)
    value = json.loads(path.read_text())
    value["inspection"]["workspace_mount"] = mount
    path.write_text(json.dumps(value), encoding="utf-8")
    prepared = binding.preflight(path, "fixture-01", tools, PROCESS)
    step = {"kind": "task", "id": "inspect", "fields": {"inputs": [], "outputs": [], "settings": {}}}
    sections = [step]
    binding.bind(sections, step, "geometry.actual_mesh", workspace=tmp_path / "workspace",
                 input_root="campaign/fixture/inputs", output_root="campaign/fixture/artifacts",
                 source="campaign/fixture/artifacts/source.stl", prepared=prepared, staged=[],
                 operation_label="qualified_fixture_inspection")
    arguments = json.loads(step["fields"]["settings"]["mcp_arguments"])
    assert arguments["job_name"] == mount + "/campaign/fixture/artifacts/package-inspection"
    assert str(mount + "/campaign/fixture/inputs/inspect_manufacturing_package.py") in arguments["input_content"]


def test_package_is_owned_by_slicer_and_inspection_only_produces_new_evidence(tmp_path):
    path, tools = fixture.make_binding(tmp_path / "configuration", "fixture-01", PROCESS)
    prepared = binding.preflight(path, "fixture-01", tools, PROCESS)
    step = {"kind": "task", "id": "inspect", "fields": {"inputs": [], "outputs": [], "settings": {}}}
    consumer = {"kind": "connection", "id": "package_consumer", "fields": {
        "type": "item", "from": "inspect.slice_package", "to": "review.package",
        "label": "actual package", "when": None}}
    sections = [step, consumer]
    evidence = binding.bind(sections, step, "geometry.actual_mesh", workspace=tmp_path / "workspace",
                            input_root="campaign/fixture/inputs", output_root="campaign/fixture/artifacts",
                            source="campaign/fixture/artifacts/source.stl", prepared=prepared, staged=[],
                            operation_label="qualified_fixture_inspection")
    native = next(item for item in sections if item["id"] == "invoke_external_slice_inspect")
    package = "campaign/fixture/artifacts/slice_package.gcode.3mf"
    assert native["fields"]["settings"]["expected_file_ports"]["external_slice_package"] == package
    assert package not in step["fields"]["settings"]["expected_files"].splitlines()
    assert "slice_package" not in step["fields"]["settings"]["expected_file_ports"]
    assert evidence["package_reference"] == "invoke_external_slice_inspect.external_slice_package"
    assert consumer["fields"]["from"] == evidence["package_reference"]
