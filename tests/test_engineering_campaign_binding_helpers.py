"""Shared preparation helpers retain declarations without importing a vendor demo."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "neutral_campaign_binding_helpers_test",
    ROOT / "scripts/engineering_campaign_binding_helpers.py",
)
helpers = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helpers)


def test_helpers_digest_and_write_preserve_exact_bytes(tmp_path):
    payload = b"original engineering input\r\n"
    path = helpers.confined(tmp_path, "inputs/requirements.md")
    helpers.write_once(path, payload)
    helpers.write_once(path, payload)
    assert path.read_bytes() == payload
    assert helpers.digest(payload) == hashlib.sha256(payload).hexdigest()
    with pytest.raises(ValueError, match="different staged file"):
        helpers.write_once(path, b"replacement")
    assert path.read_bytes() == payload


@pytest.mark.parametrize("relative", ["../outside.txt", "inputs/../../outside.txt"])
def test_helpers_reject_escape(tmp_path, relative):
    with pytest.raises(ValueError, match="escapes"):
        helpers.confined(tmp_path, relative)


def test_helpers_keep_exact_declared_input_connection():
    sections = []
    producer = helpers.add_file_input(sections, "proof", "requirements", "inputs/original.md")
    target = {"id": "analyse", "fields": {"inputs": []}}
    helpers.add_reference(sections, producer, target, "requirements")
    rendered = helpers.render(sections)
    assert '"inputs/original.md"' in rendered
    assert '"campaign_requirements_proof.campaign_requirements_proof_document"' in rendered
    assert '"analyse.analyse_requirements"' in rendered
    assert target["fields"]["inputs"][0]["required"] is True


def test_new_draft_captures_complete_instructions_and_preserves_strict_policy():
    from core.workflow_instructions import WorkflowInstructionSet
    from workspace_service.workflow_source_execution import _parse

    sections = [{"kind": "workflow", "id": "example", "fields": {"name": "Example"}}]
    legacy = helpers.render(sections)
    assert "instructions:" not in legacy
    source = helpers.render_new_draft(sections)
    snapshot = WorkflowInstructionSet.model_validate(_parse(source)[0]["fields"]["instructions"])
    assert snapshot.action_intent_contract == "wright.workflow-action-intent/1"
    assert snapshot.policy.assumption_policy == "require_specified"
    assert any(asset.id == "protocol.action-intent" and asset.body for asset in snapshot.assets)
    assert all(asset.body_digest for asset in snapshot.assets)
    assert helpers.render(sections) == legacy


def test_new_draft_preserves_existing_accepted_instructions():
    from agent_adapters.workflow_instructions import load_default_workflow_instructions

    saved = load_default_workflow_instructions().model_dump(mode="json")
    saved["profile_version"] = "retained-test-revision"
    saved["policy"]["assumption_policy"] = "document_reasonable"
    sections = [{"kind": "workflow", "id": "example", "fields": {"instructions": saved}}]
    assert helpers.render_new_draft(sections) == helpers.render(sections)


def test_new_draft_rejects_invalid_saved_instructions_instead_of_replacing():
    sections = [{"kind": "workflow", "id": "example", "fields": {"instructions": {}}}]
    with pytest.raises(ValueError):
        helpers.render_new_draft(sections)


def test_printed_preparer_launches_without_scripts_namespace(tmp_path):
    collision = tmp_path / "scripts"
    collision.mkdir()
    (collision / "__init__.py").write_text("# unrelated installed namespace\n", encoding="utf-8")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/prepare-printed-dataset-campaign.py"), "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--instance-source" in result.stdout


def test_other_examples_load_neutral_helper_file():
    names = ["bracket", "drill-jig", "harness", "heat", "modelica", "pcb", "pi",
             "pi-fixed", "pi-visual", "robot", "sheet-metal"]
    for name in names:
        source = (ROOT / f"scripts/prepare-{name}-dataset-campaign.py").read_text(encoding="utf-8")
        assert "engineering_campaign_binding_helpers.py" in source
        assert "prepare-printed-dataset-campaign.py" not in source
