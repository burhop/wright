"""Bounded declaration/readiness and passive-byte controls; no native dispatch."""
import ast
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


binding = module("external_mesh", "scripts/engineering_external_mesh_binding.py")
fixture = module("external_mesh_fixture", "tests/fixtures/external_mesh_binding.py")
inspection = module("passive_mesh", "scripts/engineering/inspect_repaired_mesh.py")
POLICY = ROOT / "examples/process-interfaces/printed-replacement-part/original-repair-policy.json"


@pytest.fixture
def prepared(tmp_path):
    machine = tmp_path / "machine.json"
    machine.write_bytes(b'{"name":"synthetic selected profile"}')
    tool = {"server_id": "independent-geometry", "tool_name": "execute_blender_code",
            "schema_digest": "a" * 64, "name": "independent-geometry__execute_blender_code"}
    workspace = tmp_path / "workspace"
    path = fixture.make_binding(tmp_path / "binding", "printed-replacement-part-01", workspace, "fresh", POLICY, machine, tool)
    value = json.loads(path.read_bytes())
    return path, value, tool, {
        "workspace": workspace, "output_root": value["output_root"], "policy": value["policy"],
        "machine_profile_sha256": hashlib.sha256(machine.read_bytes()).hexdigest(),
    }


@pytest.mark.parametrize("problem", ["missing", "scenario", "workspace", "attempt", "policy", "profile",
                                      "provider", "schema", "ambiguous", "retired", "arguments", "argument-shape", "nonfinite", "duplicate"])
def test_invalid_bindings_fail_before_any_workspace_staging(prepared, problem):
    path, value, tool, options = prepared
    tools = [tool]
    if problem == "missing":
        path = None
    elif problem == "scenario":
        value["scenario_id"] = "different"
    elif problem == "workspace":
        value["workspace_root"] += "/other"
    elif problem == "attempt":
        value["output_root"] = "another/attempt"
    elif problem == "policy":
        value["policy"]["triangle_limit"] += 1
        options["policy"] = {**value["policy"], "triangle_limit": value["policy"]["triangle_limit"] - 1}
    elif problem == "profile":
        value["machine_profile_sha256"] = "b" * 64
    elif problem == "provider":
        tools = []
    elif problem == "schema":
        value["provider"]["schema_digest"] = "b" * 64
    elif problem == "ambiguous":
        tools = [tool, dict(tool)]
    elif problem == "retired":
        value["provider"]["server"] = "wright-printed-part-mesh-repair"
    elif problem in {"arguments", "argument-shape", "nonfinite"}:
        argument = Path(value["arguments"]["path"])
        raw = {"arguments": b'{"code":"changed"}', "argument-shape": b'[]', "nonfinite": b'{"value":NaN}'}[problem]
        argument.write_bytes(raw)
        if problem != "arguments":
            value["arguments"]["sha256"] = hashlib.sha256(raw).hexdigest()
    if path:
        path.write_text(json.dumps(value), encoding="utf-8")
        if problem == "duplicate":
            path.write_bytes(b'{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError):
        binding.preflight(path, "printed-replacement-part-01", tools, **options)
    assert not options["workspace"].exists()


def test_pinned_arguments_are_never_interpreted_or_rewritten(prepared):
    path, value, tool, options = prepared
    actual = binding.preflight(path, "printed-replacement-part-01", [tool], **options)
    assert actual["arguments"] == Path(value["arguments"]["path"]).read_bytes()
    assert actual["selected_tool"] == tool
    assert not options["workspace"].exists()
    tree = ast.parse((ROOT / "scripts/engineering_external_mesh_binding.py").read_text())
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) and "blender_mcp" in ast.unparse(node) for node in ast.walk(tree))
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval"} for node in ast.walk(tree))


@pytest.mark.parametrize("defect", ["version-bool", "policy-bool-as-zero", "policy-zero-as-bool", "policy-float-limit"])
def test_pinned_policy_identity_preserves_json_types(prepared, defect):
    path, value, tool, options = prepared
    original = json.loads(json.dumps(options["policy"]))
    if defect == "version-bool":
        value["schema_version"] = True
    elif defect == "policy-bool-as-zero":
        value["policy"]["force_voxel_remesh"] = 0
    elif defect == "policy-zero-as-bool":
        value["policy"]["envelope_margin_mm"] = False
    else:
        value["policy"]["triangle_limit"] = float(value["policy"]["triangle_limit"])
    options["policy"] = original
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        binding.preflight(path, "printed-replacement-part-01", [tool], **options)
    assert not options["workspace"].exists()


def tetrahedron(*, offset=0, reverse=False):
    a, b, c, d = [(x + offset, y, z) for x, y, z in ((0,0,0),(1,0,0),(0,2,0),(0,0,3))]
    triangles = [(a,c,b),(a,b,d),(b,c,d),(c,a,d)]
    if reverse:
        triangles = [(a,c,b) for a,b,c in triangles]
    return triangles


def stl(triangles, header=b"fixture"):
    raw = header.ljust(80, b"\0") + struct.pack("<I", len(triangles))
    return raw + b"".join(struct.pack("<12fH",0,0,0,*(number for point in triangle for number in point),0) for triangle in triangles)


@pytest.fixture
def files(tmp_path):
    source = tmp_path / "source.stl"
    repaired = tmp_path / "repaired.stl"
    preview = tmp_path / "preview.png"
    source.write_bytes(stl(tetrahedron(), b"source"))
    repaired.write_bytes(stl(tetrahedron(), b"repaired"))
    preview.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="))
    return {"workspace_root": str(tmp_path), "source": source.name, "repaired": repaired.name,
            "preview": preview.name, "output": "evidence.json", "measure_handle_features": False,
            "policy": {"build_volume_mm": [1,2,3], "build_volume_tolerance_mm": 0.000001, "triangle_limit": 4}}


def test_actual_final_bytes_and_explicit_noncubic_envelope(files):
    report = inspection.run(files)
    assert report["after"]["dimensions_mm"] == [1,2,3]
    assert report["after"]["signed_volume_mm3"] == 1
    assert all(report["checks"].values())
    assert report["engineering_acceptance"] is False
    assert report["physical_verification"] is False
    assert report["after"]["source_sha256"] == hashlib.sha256((Path(files["workspace_root"]) / files["repaired"]).read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="new evidence output"):
        inspection.run(files)


@pytest.mark.parametrize("defect", ["boolean-tolerance", "float-limit", "oversized-preview"])
def test_passive_inspection_rejects_invalid_types_and_unbounded_preview(files, defect):
    root = Path(files["workspace_root"])
    if defect == "boolean-tolerance":
        files["policy"]["build_volume_tolerance_mm"] = False
    elif defect == "float-limit":
        files["policy"]["triangle_limit"] = 4.0
    else:
        preview = root / files["preview"]
        with preview.open("ab") as stream:
            stream.write(b"\0" * (16 * 1024 * 1024))
    with pytest.raises(ValueError):
        inspection.run(files)
    assert not (root / files["output"]).exists()


@pytest.mark.parametrize("defect", ["inward", "disconnected", "degenerate", "oversize", "over-limit", "nonfinite", "truncated", "preview", "escape"])
def test_invalid_or_mandatory_failed_output_never_releases_the_inspection(files, defect):
    root = Path(files["workspace_root"])
    before = (root / files["source"]).read_bytes()
    repaired = root / files["repaired"]
    if defect == "inward":
        repaired.write_bytes(stl(tetrahedron(reverse=True)))
    elif defect == "disconnected":
        repaired.write_bytes(stl(tetrahedron() + tetrahedron(offset=5)))
        files["policy"]["triangle_limit"] = 8
        files["policy"]["build_volume_mm"] = [10,10,10]
    elif defect == "degenerate":
        repaired.write_bytes(stl(tetrahedron() + [((0,0,0),(0,0,0),(0,0,0))]))
        files["policy"]["triangle_limit"] = 5
    elif defect == "oversize":
        files["policy"]["build_volume_mm"] = [0.5,2,3]
    elif defect == "over-limit":
        repaired.write_bytes(stl(tetrahedron() + tetrahedron(offset=5)))
    elif defect == "nonfinite":
        raw = bytearray(repaired.read_bytes())
        struct.pack_into("<f", raw, 96, float("nan"))
        repaired.write_bytes(raw)
    elif defect == "truncated":
        repaired.write_bytes(repaired.read_bytes()[:-1])
    elif defect == "preview":
        (root / files["preview"]).write_bytes(b"not an image")
    else:
        files["output"] = "../outside.json"
    with pytest.raises(ValueError):
        inspection.run(files)
    assert (root / files["source"]).read_bytes() == before
    if (root / "evidence.json").exists():
        report = json.loads((root / "evidence.json").read_bytes())
        assert not all(report["checks"].values())


def test_original_handle_measurement_functions_are_unchanged():
    archive = ROOT / "artifacts/process-interfaces/083/20261003-mesh-repair-retirement/archive-engineering_dataset_mesh_repair.py.txt"
    old = ast.parse(archive.read_text())
    new = ast.parse((ROOT / "scripts/engineering/inspect_repaired_mesh.py").read_text())
    for name in ("_clip_x", "measure_handle_features"):
        before = next(node for node in old.body if isinstance(node, ast.FunctionDef) and node.name == name)
        after = next(node for node in new.body if isinstance(node, ast.FunctionDef) and node.name == name)
        assert ast.dump(before) == ast.dump(after)
