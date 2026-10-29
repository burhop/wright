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
        ("plate", True),
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


@pytest.mark.parametrize(
    "preview", ["valid", "missing", "invalid", "duplicate", "existing"]
)
def test_legacy_preview_uses_actual_package_and_same_passive_paths(handoff, preview):
    root, config, _ = handoff
    source_package = root / config["slice_package"]
    with zipfile.ZipFile(source_package) as archive:
        gcode = archive.read(config["gcode_entry"])
    archive_bytes = io.BytesIO()
    png = b"\x89PNG\r\n\x1a\n" + b"fixture bytes; not a render qualification"
    with zipfile.ZipFile(archive_bytes, "w") as archive:
        archive.writestr(config["gcode_entry"], gcode)
        if preview != "missing":
            archive.writestr(
                "Metadata/plate_1.png", b"invalid!" if preview == "invalid" else png
            )
        if preview == "duplicate":
            with pytest.warns(UserWarning, match="Duplicate"):
                archive.writestr("Metadata/plate_1.png", png)
    source_package.write_bytes(archive_bytes.getvalue())
    config["legacy_previews"] = True
    if preview == "existing":
        (root / "outputs/support-preview.svg").write_bytes(b"retained")
    if preview != "valid":
        with pytest.raises(ValueError):
            operation.run(config, read_3mf_toolpaths)
        assert {path.name for path in (root / "outputs").iterdir()} == (
            {"support-preview.svg"} if preview == "existing" else set()
        )
        return
    result = operation.run(config, read_3mf_toolpaths)
    assert (root / "outputs/slice-preview.png").read_bytes() == png
    assert result["engineering_acceptance"] is False
    svg = (root / "outputs/support-preview.svg").read_text()
    view = json.loads((root / "outputs/support-preview.json").read_bytes())
    segment = view["layers"][0]["support"][0]
    a, b, c, d = segment
    assert f"M{a:.3f},{-b:.3f}L{c:.3f},{-d:.3f}" in svg
    assert "256" not in svg and "<script" not in svg


def observed_response(root, config, response, *, calls=None):
    from workspace_service.workflow_tool_observations import response_from_observations

    selector = {
        "server_id": "fixture-slicer",
        "tool": "fixture-slicer__slice",
        "schema_digest": "a" * 64,
        "arguments": {
            "source": response["source"],
            "output": response["output"],
            "plate": 1,
        },
    }
    config["provider_observation"] = selector
    if calls is None:
        calls = [
            {
                "tool": selector["tool"],
                "schema_digest": selector["schema_digest"],
                "arguments": selector["arguments"],
                "status": "succeeded",
                "result": response,
                "text": json.dumps(response),
            }
        ]
    envelope = json.loads(response_from_observations(selector["server_id"], calls))
    (root / config["provider_response"]).write_text(json.dumps(envelope))
    return envelope


def test_recorded_observation_to_passive_package_inspection(handoff):
    root, config, response = handoff
    envelope = observed_response(root, config, response)
    result = operation.run(config, read_3mf_toolpaths)
    evidence = json.loads((root / result["slice_evidence"]["path"]).read_text())
    assert evidence["provider_observation"]["call_number"] == 1
    assert (
        evidence["provider_observation"]["projection_sha256"]
        == envelope["observations"]["digest"]
    )
    assert (
        evidence["package_sha256"]
        == hashlib.sha256((root / config["slice_package"]).read_bytes()).hexdigest()
    )
    assert evidence["engineering_acceptance"] is False


@pytest.mark.parametrize(
    "change",
    [
        "server",
        "tool",
        "arguments",
        "schema",
        "incomplete",
        "redacted",
        "digest",
        "count",
        "missing",
    ],
)
def test_observation_mismatch_never_publishes(handoff, change):
    root, config, response = handoff
    envelope = observed_response(root, config, response)
    if change == "server":
        config["provider_observation"]["server_id"] = "different"
    elif change == "tool":
        config["provider_observation"]["tool"] = "different"
    elif change == "arguments":
        config["provider_observation"]["arguments"]["output"] = "different"
    elif change == "schema":
        config["provider_observation"]["schema_digest"] = "b" * 64
    elif change == "incomplete":
        envelope["observations"]["complete"] = False
    elif change == "redacted":
        envelope["observations"]["redaction_count"] = 1
    elif change == "digest":
        envelope["observations"]["digest"] = "b" * 64
    elif change == "count":
        envelope["call_count"] += 1
    elif change == "missing":
        envelope = response
    (root / config["provider_response"]).write_text(json.dumps(envelope))
    with pytest.raises(ValueError):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())


@pytest.mark.parametrize("kind", ["duplicate", "failed", "warning"])
def test_ambiguous_failed_or_qualified_observation_blocks_inspection(handoff, kind):
    root, config, response = handoff
    envelope = observed_response(root, config, response)
    call = envelope["observations"]["value"][0]
    if kind == "failed":
        call["status"] = "failed"
    if kind == "warning":
        call["text"] = "Warning: support geometry incomplete"
    observed_response(
        root, config, response, calls=[call, call] if kind == "duplicate" else [call]
    )
    with pytest.raises(ValueError):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())


def test_selects_exact_orientation_among_multiple_calls(handoff):
    root, config, response = handoff
    envelope = observed_response(root, config, response)
    selected = envelope["observations"]["value"][0]
    alternate = json.loads(json.dumps(selected))
    alternate["arguments"]["source"] = "configured-host/side.stl"
    alternate["arguments"]["output"] = "configured-host/side.3mf"
    alternate["result"].update(alternate["arguments"])
    observed_response(root, config, response, calls=[alternate, selected])
    result = operation.run(config, read_3mf_toolpaths)
    evidence = json.loads((root / result["slice_evidence"]["path"]).read_text())
    assert evidence["provider_observation"]["call_number"] == 2


def test_argument_identity_does_not_equate_boolean_with_integer(handoff):
    root, config, response = handoff
    observed_response(root, config, response)
    config["provider_observation"]["arguments"]["plate"] = True
    with pytest.raises(ValueError, match="unambiguous"):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())


def test_supplementary_response_equality_is_type_exact(handoff):
    root, config, response = handoff
    envelope = observed_response(root, config, response)
    call = envelope["observations"]["value"][0]
    call["text"] = json.dumps({**response, "ok": 1, "plate": True})
    observed_response(root, config, response, calls=[call])
    with pytest.raises(ValueError):
        operation.run(config, read_3mf_toolpaths)
    assert not list((root / "outputs").iterdir())
