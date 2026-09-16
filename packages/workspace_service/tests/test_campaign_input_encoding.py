"""Human context survives a Windows legacy default text encoding."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "short,family,ordinal",
    [("bracket", "lightweight-equipment-bracket", n) for n in (1, 2, 3)]
    + [("harness", "sensor-fan-harness", n) for n in (1, 2, 3)]
    + [("robot", "robot-tracking-diagnosis", 2)],
)
def test_normalized_context_keeps_original_unicode(
    tmp_path, monkeypatch, short, family, ordinal
):
    spec = importlib.util.spec_from_file_location(
        "utf8_" + short, ROOT / f"scripts/prepare-{short}-dataset-campaign.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    read_text = Path.read_text

    def legacy_default(path, encoding=None, errors=None):
        return read_text(path, encoding=encoding or "cp1252", errors=errors)

    monkeypatch.setattr(Path, "read_text", legacy_default)
    directory = next(
        p
        for p in (
            ROOT / "tests/datasets/engineering-workflows/scenarios" / family
        ).iterdir()
        if p.name.startswith(f"{ordinal:02d}")
    )
    manifest = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))
    config = json.loads(module.BINDING.read_text(encoding="utf-8"))
    if short == "robot":
        allowed = config["allowed_tools"]
    elif short == "harness":
        allowed = {"harness": config["allowed_tools"]}
    else:
        allowed = {
            "agentcad": ["context", "docs", "run", "inspect", "measure"],
            "wright-workspace-files": ["write_text_document", "inspect_file"],
            "solver": [
                "calculix_mesh_preflight",
                "calculix_solve_static_recorded",
                "calculix_run_get",
            ],
            "fields": ["export_recorded_fields_and_reactions"],
        }
    tools = [
        {"server_id": server, "tool_name": name, "schema_digest": "a" * 64}
        for server, names in allowed.items()
        for name in names
    ]
    args = SimpleNamespace(
        workspace_root=str(tmp_path / "workspace"),
        draft_root=str(tmp_path / "draft"),
        instance_source=None,
        attempt="encoding-test",
        server_id="harness",
        initialize_agentcad=False,
        solver_server_id="solver",
        field_server_id="fields",
    )
    module.prepare(args, directory, tools)
    assembled = next((tmp_path / "workspace").rglob("assembled-context.md")).read_text(
        encoding="utf-8"
    )
    names = [
        manifest["files"]["user_profile"],
        manifest["files"]["prompt"],
        *manifest["files"]["context"],
    ]
    saw_unicode = False
    for name in names:
        original = (directory / name).read_text(encoding="utf-8")
        assert original in assembled
        saw_unicode |= any(ord(char) > 127 for char in original)
        copied = next((tmp_path / "workspace").rglob(name))
        assert copied.read_bytes() == (directory / name).read_bytes()
    assert saw_unicode, "Regression needs actual non-ASCII user input"
