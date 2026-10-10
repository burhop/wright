"""Fixture-only checks of an authored passive completion reader; no CAD claims."""
import json
import runpy
from pathlib import Path

import pytest

OPERATION = Path(__file__).resolve().parents[1] / "examples/process-interfaces/printed-replacement-part/repair-completion-operation.py"


@pytest.fixture
def completion_fixture(tmp_path):
    config = {}
    for role, name in (("source_path", "source.stl"), ("repaired_path", "repaired.stl"), ("preview_path", "preview.png")):
        path = tmp_path / name
        path.write_bytes(b"fixture-only; independent mesh validation remains required")
        config[role] = str(path)
    config.update(response_path=str(tmp_path / "response.json"), output_path=str(tmp_path / "completion.json"))
    config.update(producer_path_style="windows", producer_output_paths={
        "repaired_mesh_stl": "C:/isolated-provider/current-run/repaired.stl",
        "geometry_only_preview_png": "C:/isolated-provider/current-run/preview.png",
    })
    topology = {"non_manifold_edges": 0, "boundary_edges": 0, "degenerate_faces": 0, "winding_conflicts": 0, "triangles": 12}
    record = {key: dict(topology) for key in ("source_actual", "post_transform_object", "exported_binary_stl_verified")}
    record.update(repair={"dimensions_preserved": True}, transform={},
                  outputs=dict(config["producer_output_paths"]),
                  support_consequences=[], remaining_review_limits=[])
    return config, record


def run_fixture(config, result):
    Path(config["response_path"]).write_text(json.dumps({"result": result}))
    runpy.run_path(str(OPERATION), init_globals={"__WRIGHT_REPAIR_COMPLETION_CONFIG__": config})


def test_typed_completion_receipt_keeps_measurement_and_acceptance_scopes_separate(completion_fixture):
    config, record = completion_fixture
    run_fixture(config, "W083_FINAL_REPORT " + repr(record))
    receipt = json.loads(Path(config["output_path"]).read_bytes())
    assert receipt["completed_program_record"] is True
    assert receipt["engineering_acceptance"] is False
    assert receipt["physical_acceptance"] is False
    assert set(receipt["files"]) == {"source_path", "repaired_path", "preview_path"}
    assert all(len(file["sha256"]) == 64 for file in receipt["files"].values())


@pytest.mark.parametrize("fault", ["partial_files", "duplicate_record", "invalid_topology", "boolean_count", "too_many_triangles", "dimensions_changed", "preview_missing", "preview_empty", "wrong_schema", "wrong_export", "wrong_run_same_filename", "unsupported_path_style", "malformed_record"])
def test_incomplete_or_invalid_program_cannot_create_receipt(completion_fixture, fault):
    config, record = completion_fixture
    if fault == "invalid_topology":
        record["post_transform_object"]["boundary_edges"] = 1
    elif fault == "boolean_count":
        record["source_actual"]["boundary_edges"] = False
    elif fault == "too_many_triangles":
        record["exported_binary_stl_verified"]["triangles"] = 80001
    elif fault == "dimensions_changed":
        record["repair"]["dimensions_preserved"] = False
    elif fault == "preview_missing":
        Path(config["preview_path"]).unlink()
    elif fault == "preview_empty":
        Path(config["preview_path"]).write_bytes(b"")
    elif fault == "wrong_schema":
        record["unexpected_authority"] = True
    elif fault == "wrong_export":
        record["outputs"]["repaired_mesh_stl"] = "other.stl"
    elif fault == "wrong_run_same_filename":
        record["outputs"]["repaired_mesh_stl"] = "C:/isolated-provider/previous-run/repaired.stl"
    elif fault == "unsupported_path_style":
        config["producer_path_style"] = "guess"
    result = "W083_FINAL_REPORT " + repr(record)
    if fault == "partial_files":
        result = "Code execution error: Repaired socket-up object unavailable for preview"
    elif fault == "duplicate_record":
        result += "\n" + result
    elif fault == "malformed_record":
        result = "W083_FINAL_REPORT not_a_record"
    with pytest.raises((AssertionError, ValueError)):
        run_fixture(config, result)
    assert not Path(config["output_path"]).exists()


@pytest.mark.parametrize("style,reported,declared", [
    ("windows", r"C:\isolated-provider\current-run\repaired.stl", "C:/isolated-provider/current-run/repaired.stl"),
    ("posix", "/provider/current-run/repaired.stl", "/provider/current-run/repaired.stl"),
])
def test_producer_path_convention_is_independent_of_inspector_host(completion_fixture, style, reported, declared):
    config, record = completion_fixture
    config["producer_path_style"] = style
    config["producer_output_paths"] = {"repaired_mesh_stl": declared, "geometry_only_preview_png": declared + ".png"}
    record["outputs"] = {"repaired_mesh_stl": reported, "geometry_only_preview_png": reported + ".png"}
    run_fixture(config, "W083_FINAL_REPORT " + repr(record))
    assert Path(config["output_path"]).exists()


def test_completion_inspection_never_overwrites_a_prior_receipt(completion_fixture):
    config, record = completion_fixture
    prior = Path(config["output_path"])
    prior.write_text("previous evidence")
    with pytest.raises(AssertionError, match="Preserve prior"):
        run_fixture(config, "W083_FINAL_REPORT " + repr(record))
    assert prior.read_text() == "previous evidence"
