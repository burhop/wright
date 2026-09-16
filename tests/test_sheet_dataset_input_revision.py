"""Human revision publication retains historical evidence and changes identity."""
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_revision_preserves_original_files_and_registers_both_identities(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    import engineering_dataset_campaign as campaign
    spec = importlib.util.spec_from_file_location("sheet_revision", ROOT / "scripts/revise_sheet_metal_dataset_inputs.py")
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)
    inputs = tmp_path / "inputs"
    folder = inputs / "scenarios/sheet-metal-supplier-handoff/01-fixture"
    folder.mkdir(parents=True)
    (inputs / "campaign.json").write_text(json.dumps({"campaign_id": "revision-test", "target": 30, "approval_mode": "auto", "template_ids": ["sheet-metal-supplier-handoff"]}))
    original = {
        "schema_version": 1, "scenario_id": "sheet-metal-supplier-handoff-01",
        "template_id": "sheet-metal-supplier-handoff", "title": "Revision fixture", "difficulty": "basic",
        "provenance": {"kind": "synthetic"},
        "files": {"user_profile": "user.md", "prompt": "prompt.txt", "context": ["context.md"], "images": ["image.png"]},
        "expected_outputs": [{"role": "native", "patterns": ["**/*.psm"]}],
    }
    original_bytes = (json.dumps(original, indent=3) + "\n").encode()
    (folder / "scenario.json").write_bytes(original_bytes)
    retained = {"user.md": b"Fictional user", "prompt.txt": b"Original request", "context.md": b"Original policy", "image.png": b"original binary", "dimensions.csv": b"x,y\n1,2\n"}
    for name, raw in retained.items():
        (folder / name).write_bytes(raw)
    (folder / revision.ADDENDUM).write_text("Explicit fictional bounded revision")
    state = campaign.Campaign(inputs, tmp_path / "state")
    state.scan()
    before = campaign.load_dataset(folder / "scenario.json", inputs, state.config)
    result = revision.publish(inputs)
    assert result[0]["prior_dataset_digest"] == before["digest"]
    assert result[0]["dataset_digest"] != before["digest"]
    assert result[0]["execution_started"] is False
    assert (inputs / "revisions" / revision.REVISION / original["scenario_id"] / "scenario.before.json").read_bytes() == original_bytes
    assert all((folder / name).read_bytes() == raw for name, raw in retained.items())
    assert revision.publish(inputs) == result
    state.scan()
    with state.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM dataset_revisions").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
    r1_manifest = (folder / "scenario.json").read_bytes()
    (folder / "native-r2.md").write_text("Explicit observed native geometry-label mapping")
    later = revision.publish(inputs, addendum_name="native-r2.md", revision_name="revision-r2", scenario_id=original["scenario_id"], reason="Explicit later human design choice")
    assert later[0]["reason"] == "Explicit later human design choice"
    assert later[0]["prior_dataset_digest"] == result[0]["dataset_digest"]
    assert later[0]["retained_original_files"][revision.ADDENDUM] == result[0]["addendum_sha256"]
    assert (inputs / "revisions/revision-r2" / original["scenario_id"] / "scenario.before.json").read_bytes() == r1_manifest
    state.scan()
    with state.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM dataset_revisions").fetchone()[0] == 3
        assert db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
    (folder / "context.md").write_text("Changed original")
    with pytest.raises(ValueError, match="Original human file changed"):
        revision.publish(inputs, addendum_name="native-r2.md", revision_name="revision-r2", scenario_id=original["scenario_id"])
