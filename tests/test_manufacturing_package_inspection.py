"""Digital fixtures qualify passive inspection, not native manufacturing."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import pytest

from workspace_service.process_interfaces.representations import read_3mf_toolpaths

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "manufacturing_inspection",
    REPO / "scripts/engineering/inspect_manufacturing_package.py",
)
operation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operation)


@pytest.fixture
def handoff(tmp_path):
    inputs = tmp_path / "inputs"
    outputs = tmp_path / "outputs"
    inputs.mkdir()
    outputs.mkdir()
    (inputs / "mesh.stl").write_bytes(
        b"Synthetic mesh identity; geometry is not qualified here"
    )
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr(
            "Metadata/plate_1.gcode",
            "G90\nG21\nM83\nG1 X0 Y0 Z0.2\n;CHANGE_LAYER\n;Z_HEIGHT:0.2\n;FEATURE:Inner wall\nG1 X10 Y0 E1\n;FEATURE:Support\nG1 X10 Y5 E1\n",
        )
    (inputs / "package.3mf").write_bytes(archive.getvalue())
    response = {
        "ok": True,
        "source": "configured-host/mesh.stl",
        "output": "configured-host/package.3mf",
        "plate": 1,
    }
    (inputs / "response.json").write_text(
        json.dumps({"content": [{"type": "text", "text": json.dumps(response)}]})
    )
    profiles = {}
    for role in ("machine", "process", "filament"):
        relative = "inputs/" + role + ".json"
        (tmp_path / relative).write_text(json.dumps({"fixture_role": role}))
        profiles[role] = relative
    config = {
        "workspace_root": str(tmp_path),
        "source_mesh": "inputs/mesh.stl",
        "slice_package": "inputs/package.3mf",
        "provider_response": "inputs/response.json",
        "output_root": "outputs",
        "profiles": profiles,
        "gcode_entry": "Metadata/plate_1.gcode",
        "success_field": "ok",
        "expected_response_fields": {
            key: response[key] for key in ("source", "output", "plate")
        },
        "success_contract": "Fixture declaration only; no native slicer was executed",
        "operation_label": "fixture_offline_slice",
    }
    return tmp_path, config, response


@pytest.mark.parametrize("enveloped", [True, False])
def test_actual_recorded_paths_and_hashes_are_retained(handoff, enveloped):
    root, config, response = handoff
    if not enveloped:
        (root / config["provider_response"]).write_text(json.dumps(response))
    result = operation.run(config, read_3mf_toolpaths)
    assert result["engineering_acceptance"] is False
    evidence = json.loads((root / result["slice_evidence"]["path"]).read_bytes())
    for field, path in [
        ("source_sha256", "source_mesh"),
        ("package_sha256", "slice_package"),
        ("provider_response_sha256", "provider_response"),
    ]:
        assert (
            evidence[field]
            == hashlib.sha256((root / config[path]).read_bytes()).hexdigest()
        )
    assert evidence["exit_code_basis"] == config["success_contract"]
    view = json.loads((root / result["support_preview"]["path"]).read_bytes())
    summary_raw = (root / result["toolpath_summary"]["path"]).read_bytes()
    summary = json.loads(summary_raw)
    assert len(summary_raw) < 65536
    assert summary["source_view"] == result["support_preview"]
    assert summary["package_sha256"] == evidence["package_sha256"]
    assert summary["layer_count"] == len(view["layers"])
    assert summary["path_segments"] == {
        kind: sum(len(layer[kind]) for layer in view["layers"])
        for kind in ("model", "support", "unclassified")
    }
    assert "layers" not in summary
    assert summary["engineering_acceptance"] is False
    assert summary["provenance"] == view["provenance"]
    assert len(view["layers"]) == 1
    assert view["package_sha256"] == evidence["package_sha256"]
    with zipfile.ZipFile(root / config["slice_package"]) as archive:
        assert (
            view["provenance"]["source_sha256"]
            == hashlib.sha256(archive.read(config["gcode_entry"])).hexdigest()
        )
    assert view["layers"][0]["model"] and view["layers"][0]["support"]
    for role, record in evidence["profiles"].items():
        assert (root / record["path"]).read_bytes() == (
            root / config["profiles"][role]
        ).read_bytes()


@pytest.mark.parametrize(
    "field,value",
    [
        ("ok", False),
        ("ok", 1),
        ("source", "different-mesh"),
        ("output", "different-package"),
        ("plate", 2),
    ],
)
def test_unsuccessful_or_mismatched_response_cannot_publish(handoff, field, value):
    root, config, response = handoff
    response[field] = value
    (root / config["provider_response"]).write_text(json.dumps(response))
    with pytest.raises(ValueError):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())


@pytest.mark.parametrize(
    "content",
    [[], [{"type": "image", "data": "inert"}], [{"type": "text", "text": "{}"}] * 2],
)
def test_unsupported_envelope_is_explicit(handoff, content):
    root, config, _ = handoff
    (root / config["provider_response"]).write_text(json.dumps({"content": content}))
    with pytest.raises(ValueError, match="unsupported MCP envelope"):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())


def test_mcp_error_is_not_treated_as_success(handoff):
    root, config, response = handoff
    (root / config["provider_response"]).write_text(
        json.dumps(
            {
                "isError": True,
                "content": [{"type": "text", "text": json.dumps(response)}],
            }
        )
    )
    with pytest.raises(ValueError, match="unsupported MCP envelope"):
        operation.run(config, read_3mf_toolpaths)


@pytest.mark.parametrize("filename", ["support-preview.json", "toolpath-summary.json"])
def test_existing_output_is_preserved_without_partial_profile_writes(handoff, filename):
    root, config, _ = handoff
    (root / "outputs" / filename).write_bytes(b"prior-evidence")
    with pytest.raises(ValueError, match="fresh inspection output"):
        operation.run(config, read_3mf_toolpaths)
    assert {path.name: path.read_bytes() for path in (root / "outputs").iterdir()} == {
        filename: b"prior-evidence"
    }


def test_escape_is_rejected_before_output(handoff):
    root, config, _ = handoff
    outside = root.parent / "outside-inspection-mesh.stl"
    outside.write_bytes(b"outside")
    config["source_mesh"] = "../" + outside.name
    with pytest.raises(ValueError, match="declared workspace"):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())


def test_missing_profile_does_not_partially_publish(handoff):
    root, config, _ = handoff
    (root / config["profiles"]["filament"]).unlink()
    with pytest.raises(FileNotFoundError):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())


def test_explicit_nominal_layer_section_retains_full_package_identity(handoff):
    root, config, _ = handoff
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        package.writestr(
            "Metadata/plate_1.gcode",
            "G999 X1\n; BODY START\nG90\nG21\nM83\nG1 X0 Y0 Z0.2\n;CHANGE_LAYER\n;Z_HEIGHT:0.2\n;FEATURE:Support\nG1 X10 Y0 E1\n; BODY END\nG999 X2\n",
        )
    (root / config["slice_package"]).write_bytes(archive.getvalue())
    config["nominal_layer_section"] = {
        "start_marker": "; BODY START",
        "end_marker": "; BODY END",
    }
    result = operation.run(config, read_3mf_toolpaths)
    view = json.loads((root / result["support_preview"]["path"]).read_bytes())
    assert view["provenance"]["selected_section"]["excluded_prefix_lines"] == 2
    assert view["package_sha256"] == hashlib.sha256(archive.getvalue()).hexdigest()
    assert view["layers"][0]["support"]
