"""The closed setup inventory is included by every supported package route."""

import ast
import json
import shlex
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.handle_setup_resources import inventory

ROOT = Path(__file__).resolve().parents[2]


def test_canonical_handle_recipe_inventory_ships_in_public_and_private_distributions():
    package = ROOT / "packages/workspace_service"
    manifest = json.loads(
        (package / "src/workspace_service/handle_setup_resources.json").read_bytes()
    )
    public = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["hatch"][
        "build"
    ]["targets"]
    private = tomllib.loads((package / "pyproject.toml").read_text())["tool"]["hatch"][
        "build"
    ]["targets"]
    targets = set()
    for item in manifest["files"]:
        source, target = item["source"], item["target"]
        assert (ROOT / source).is_file()
        assert target not in targets
        targets.add(target)
        assert not source.startswith(("tests/", "artifacts/"))
        assert item["license"] == "MIT"
        installed = (
            "workspace_service/engineering_workflow_templates/setup_resources/" + target
        )
        assert public["wheel"]["force-include"][source] == installed
        assert source in public["sdist"]["only-include"]
        assert (
            private["sdist"]["force-include"]["../../" + source] == "src/" + installed
        )
    assert len(targets) == 20
    assert {
        "definition.py",
        "printed-replacement-part/prepare.py",
        "printed-replacement-part/handle-geometry/construction.json",
        "printed-replacement-part/handle-geometry/repair.json",
    } <= targets
    resources = inventory()
    assert any(row["license"] == "CC0-1.0" for row in resources)
    assert all(row["sha256"] and row["size_bytes"] > 0 for row in resources)


def test_docker_copy_closes_the_actual_setup_build_hook_inputs(tmp_path):
    manifest_path = Path(
        "packages/workspace_service/src/workspace_service/handle_setup_resources.json"
    )
    manifest = json.loads((ROOT / manifest_path).read_bytes())
    expected = {item["source"] for item in manifest["files"]}
    dockerfile = (ROOT / "docker/Dockerfile").read_text()
    before_install = dockerfile.split("# Install the workspace packages.", 1)[0]
    copied = set()
    for line in before_install.replace("\\\n", " ").splitlines():
        words = shlex.split(line, comments=True)
        if not words or words[0] != "COPY":
            continue
        if any(word.startswith("--from=") for word in words):
            continue
        paths = [word for word in words[1:] if not word.startswith("--")]
        for source in paths[:-1]:
            if not source.startswith("examples/"):
                continue
            # Preserve Docker's destination semantics, not just source presence.
            target = paths[-1]
            if target.endswith("/"):
                target += Path(source).name
            assert source in expected, "Only the closed recipe inventory is copied"
            assert target == source
            destination = tmp_path / target
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / source).read_bytes())
            copied.add(source)
    assert copied == expected

    # Exercise the actual hook against the Docker-staged paths without installing
    # a build backend or building a distribution. Its unrelated frontend inputs
    # are supplied locally; no source fallback exists for missing recipe files.
    package = tmp_path / "packages/workspace_service"
    mapping = tmp_path / manifest_path
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_bytes((ROOT / manifest_path).read_bytes())
    for name in ("process_client", "ui_kit"):
        public = tmp_path / "packages" / name
        (public / "src").mkdir(parents=True)
        for member in ("package.json", "README.md"):
            (public / member).write_bytes(
                (ROOT / "packages" / name / member).read_bytes()
            )
    tree = ast.parse((ROOT / "packages/workspace_service/hatch_build.py").read_text())
    hook = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    initialize = next(node for node in hook.body if isinstance(node, ast.FunctionDef))
    scope = {"Path": Path, "json": json}
    exec(
        compile(ast.Module(body=[initialize], type_ignores=[]), "<build-hook>", "exec"),
        scope,
    )
    build_data = {"force_include": {}}
    scope["initialize"](SimpleNamespace(root=str(package)), "standard", build_data)
    for item in manifest["files"]:
        assert build_data["force_include"][str(tmp_path / item["source"])] == (
            "workspace_service/engineering_workflow_templates/setup_resources/"
            + item["target"]
        )
    missing = manifest["files"][-1]
    (tmp_path / missing["source"]).unlink()
    with pytest.raises(FileNotFoundError, match="Missing packaged setup resource"):
        scope["initialize"](
            SimpleNamespace(root=str(package)), "standard", {"force_include": {}}
        )
