"""Input identity unit checks for an authored recipe; no native CAD claim."""

import ast
import hashlib
from pathlib import Path

import pytest


ASSET = Path(__file__).parents[1] / "examples/process-interfaces/printed-replacement-part/wheel-inspection-operation.py"


def identity_prefix(config):
    tree = ast.parse(ASSET.read_text(encoding="utf-8"))
    names = {node.targets[0].id: index for index, node in enumerate(tree.body)
             if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
    body = tree.body[names["inputs"]:names["native"]]
    namespace = {"CONFIG": config, "Path": Path, "hashlib": hashlib}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(ASSET), "exec"), namespace)
    return namespace["inputs"]


@pytest.fixture
def pinned(tmp_path):
    inputs = {}
    for role in ("native", "step", "mesh"):
        path = tmp_path / role
        path.write_bytes(("fixture " + role).encode())
        inputs[role] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {"inputs": inputs}


def test_default_inspection_still_requires_original_pinned_hashes(pinned):
    recorded = identity_prefix(pinned)
    assert all(item["reference_mode"] == "pinned" for item in recorded.values())
    Path(pinned["inputs"]["step"]["path"]).write_bytes(b"different revision")
    with pytest.raises(AssertionError, match="Exact upstream input changed: step"):
        identity_prefix(pinned)


def test_same_run_mode_records_actual_consumed_hashes(pinned):
    config = {"input_reference_mode": "workflow_dependencies", "inputs": {
        role: {"path": ref["path"]} for role, ref in pinned["inputs"].items()}}
    recorded = identity_prefix(config)
    assert all(item["reference_mode"] == "workflow_dependencies" for item in recorded.values())
    assert {role: item["sha256"] for role, item in recorded.items()} == {
        role: ref["sha256"] for role, ref in pinned["inputs"].items()}


@pytest.mark.parametrize("mode", [None, "automatic", "", False])
def test_unknown_identity_mode_fails(pinned, mode):
    with pytest.raises(AssertionError, match="Unknown input identity mode"):
        identity_prefix({**pinned, "input_reference_mode": mode})


def test_identity_mode_cannot_silently_ignore_hash_or_missing_role(pinned):
    with pytest.raises(AssertionError, match="selected input identity contract"):
        identity_prefix({**pinned, "input_reference_mode": "workflow_dependencies"})
    pinned["inputs"].pop("mesh")
    with pytest.raises(AssertionError, match="all three exact upstream inputs"):
        identity_prefix(pinned)
