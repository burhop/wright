"""Retirement scope only; historical data is inert and remains inspectable."""
import ast
import hashlib
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
RETIRED = (
    "scripts/engineering_dataset_slice.py",
    "scripts/engineering_dataset_slice_mcp.py",
    "scripts/engineering_jig_slice_mcp.py",
)


@pytest.mark.parametrize("path", RETIRED)
def test_embedded_vendor_slice_implementation_is_absent(path):
    assert not (ROOT / path).exists()


@pytest.mark.parametrize("path", (
    "scripts/prepare-printed-dataset-campaign.py",
    "scripts/prepare-drill-jig-dataset-campaign.py",
))
def test_preparers_only_declare_the_external_slice_pipeline(path):
    source = (ROOT / path).read_text(encoding="utf-8")
    assert "external_slice.preflight" in source and "external_slice.bind" in source
    assert not any(Path(name).stem in source for name in RETIRED)


def test_diagnostic_has_no_native_slicer_invocation_or_vendor_profile_derivation():
    source = (ROOT / "scripts/probe_printed_blender_binding.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    probe = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "external_slice_probe")
    assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                   and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"
                   for node in ast.walk(probe))
    assert "BAMBU_" not in source
    assert "profiles_root" not in source
    assert "outcome_unknown" in source and "do not replay" in source


@pytest.mark.parametrize("path", (
    "tests/datasets/engineering-workflows/bindings/printed-replacement-part.json",
    "tests/datasets/engineering-workflows/bindings/parametric-drill-jig.json",
))
def test_original_campaign_binding_data_remains_unchanged(path):
    original = subprocess.check_output(["git", "show", "369993be:" + path], cwd=ROOT)
    assert hashlib.sha256(original.replace(b"\r\n", b"\n")).hexdigest() == hashlib.sha256(
        (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
