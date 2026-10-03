"""Inert history remains byte-exact; active native wrapper/launcher paths are absent."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "artifacts/process-interfaces/083/20261003-mesh-repair-retirement"
RETIRED = (
    "scripts/engineering_dataset_mesh_repair.py",
    "scripts/engineering_dataset_mesh_repair_mcp.py",
    "scripts/run_printed_validator_campaign.py",
    "tests/test_printed_validator_campaign_wrapper.py",
)


@pytest.mark.parametrize("name", RETIRED)
def test_retired_native_implementation_and_launcher_are_absent(name):
    assert not (ROOT / name).exists()
    retained = json.loads((ARCHIVE / "retained-originals.json").read_bytes())
    item = retained["files"][name]
    raw = (ARCHIVE / ("archive-" + Path(name).name + ".txt")).read_bytes()
    assert len(raw) == item["bytes"]
    assert hashlib.sha256(raw).hexdigest() == item["sha256"]
    original = subprocess.check_output(["git", "show", retained["source_head"] + ":" + name], cwd=ROOT)
    assert original.replace(b"\r\n", b"\n") == raw.replace(b"\r\n", b"\n")


def test_preparation_declares_existing_capabilities_and_never_starts_a_private_lifecycle():
    source = (ROOT / "scripts/prepare-printed-dataset-campaign.py").read_text()
    assert "external_mesh.preflight" in source and "external_mesh.bind" in source
    assert all(Path(name).stem not in source for name in RETIRED)
    assert "fixed_mesh_repair_wrapper" not in source
    for name in ("scripts/engineering_external_mesh_binding.py", "scripts/engineering/inspect_repaired_mesh.py"):
        tree = ast.parse((ROOT / name).read_text())
        imports = [ast.unparse(node) for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        assert not any(word in item for item in imports for word in ("blender_mcp", "bpy", "bmesh", "FastMCP", "subprocess", "socket"))


def test_original_operation_policy_and_campaign_binding_history_remain_preserved():
    policy = json.loads((ROOT / "examples/process-interfaces/printed-replacement-part/original-repair-policy.json").read_bytes())
    retained = json.loads((ARCHIVE / "retained-originals.json").read_bytes())
    assert policy["archived_operation_sha256"] == retained["files"][RETIRED[0]]["sha256"]
    assert policy["build_volume_mm"] == [256,256,256]
    assert policy["triangle_limit"] == 80000 and policy["handle_triangle_limit"] == 24000
    assert policy["force_voxel_remesh"] is False and policy["envelope_margin_mm"] == 0
    name = "tests/datasets/engineering-workflows/bindings/printed-replacement-part.json"
    original = subprocess.check_output(["git","show","369993be:" + name],cwd=ROOT)
    assert original.replace(b"\r\n",b"\n") == (ROOT/name).read_bytes().replace(b"\r\n",b"\n")
