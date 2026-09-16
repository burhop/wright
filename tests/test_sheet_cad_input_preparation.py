"""Fresh sheet setup binds additive human decisions without changing prior input bytes."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff"


@pytest.fixture
def preparer():
    spec = importlib.util.spec_from_file_location("sheet_r3_preparer", ROOT / "scripts/prepare-sheet-metal-dataset-campaign.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("directory", sorted(SCENARIOS.iterdir()), ids=lambda path: path.name)
def test_fresh_graph_binds_revised_inputs_and_runtime_output_contract(tmp_path, preparer, directory):
    binding = json.loads(preparer.BINDING.read_text(encoding="utf-8"))
    available = [{"server_id": server, "tool_name": tool, "name": server + "__" + tool, "schema_digest": "a" * 64}
                 for server, names in binding["allowed_tools"].items() for tool in names]
    args = SimpleNamespace(workspace_root=str(tmp_path / "workspace"), draft_root=str(tmp_path / "draft"),
                           attempt="attempt-test", campaign_id="fixture-campaign", instance_source=None)
    result = preparer.prepare(args, directory, available)
    text = Path(result["draft"]).read_text(encoding="utf-8")
    plan = compile_prompt_workflow(text)
    report = json.loads(Path(result["draft"]).with_name("staging-manifest.json").read_text(encoding="utf-8"))
    assert len(plan.steps) == (13 if directory.name.startswith("03") else 10)
    assert len(report["preserved_original_stages"]) == len(report["preserved_original_edges"]) == 6
    assert set(report["preserved_original_stages"]).issubset({step.id for step in plan.steps})
    workspace = Path(args.workspace_root)
    for item in report["input_manifest"]:
        assert hashlib.sha256((workspace / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    assembled = next(item for item in report["input_manifest"] if item["path"].endswith("/assembled-context.md"))
    context = (workspace / assembled["path"]).read_text(encoding="utf-8")
    assert (directory / "cad-design-choices-revision-r3.md").read_text(encoding="utf-8") in context
    assert any(path.endswith("/cad-design-choices-revision-r3.md") for path in assembled["derived_from"])
    capabilities = "company-fabrication-capabilities-r4.md"
    has_company_policy = (directory / capabilities).is_file()
    if has_company_policy:
        assert (directory / capabilities).read_text(encoding="utf-8") in context
        assert any(path.endswith("/" + capabilities) for path in assembled["derived_from"])
    intent = next(step for step in plan.steps if step.id.startswith("intent_document_"))
    if has_company_policy:
        for requirement in [
            "part-specific forming sequence", "Evaluate all company inequalities numerically",
            "Known supplier hard-limit conflicts still block",
            "company limits cannot override them or establish supplier-compatible holes/webs",
            "pending post-CAD verification, not missing human inputs",
            "no unobserved check passes", "physical_fabrication=not_performed",
            "Use only permissions supplied in that document",
            "a separately published deduction difference remains",
            "not agreement between sources or a new dimensional tolerance",
        ]:
            assert requirement in intent.prompt
        creators = [step for step in plan.steps if step.cad and step.cad.get("source") == "new"]
        assert len(creators) == (2 if directory.name.startswith("03") else 1)
        assert all("ready_for_geometry_verification" in step.prompt for step in creators)
        assert all("override an explicit needs_input" in step.prompt for step in creators)
        checks = [step for step in plan.steps if step.design_check]
        assert all("missing observations cannot pass" in step.prompt for step in checks)
        assert all("known supplier hard-limit conflict" in step.prompt for step in checks)
        assert all("development discrepancy and die-width cautions" in step.prompt for step in checks)
    else:
        assert capabilities not in intent.prompt
        assert "company limits cannot override" not in intent.prompt
    for part in binding["scenarios"][report["scenario_id"]]["parts"]:
        assert report["output_root"] + "/" + part + ".psm" in intent.prompt
    research = next(step for step in plan.steps if step.id.startswith("supplier_research_"))
    assert len(research.expected_files) == 16  # All eight raw HTML/text pairs; retained manifest is hash-bound by each read.
    assert "what-are-your-bend-relief-requirements" in research.prompt
    assert "what-are-your-channel-bend-requirements" in research.prompt
    assert "read_reference_text" in research.prompt
    assert "ordinary channel ratio before its optional thin-sheet exceptions" in research.prompt
    assert "A passing channel ratio alone does not verify full box-forming tool access" in research.prompt
    final = next(step for step in plan.steps if step.id.startswith("collect_handoff_"))
    assert report["output_root"] + "/supplier-evidence.json" in final.prompt
    actions = [step.external_action for step in plan.steps if step.external_action]
    assert len(actions) == 3
    for action in actions:
        if action["action_kind"] != "local_review":
            assert action["destination"]["id"].startswith("test://fixture-campaign/")
            assert action["settings"]["manufacturing_release"] == "HOLD"
    assert not (workspace / report["output_root"]).exists()
    assert [section for section in _parse(text) if section["kind"] == "task"]


def test_unrevised_inputs_fail_before_staging(tmp_path, preparer, monkeypatch):
    original_loads = preparer.json.loads

    def without_revision(raw, *args, **kwargs):
        value = original_loads(raw, *args, **kwargs)
        if isinstance(value, dict) and "files" in value:
            value["files"]["context"] = [name for name in value["files"]["context"] if name != "cad-design-choices-revision-r3.md"]
        return value

    monkeypatch.setattr(preparer.json, "loads", without_revision)
    with pytest.raises(ValueError, match="Publish the explicit R3"):
        preparer.prepare(SimpleNamespace(), sorted(SCENARIOS.iterdir())[0], [])
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("directory,material_page", [
    (directory, "https://sendcutsend.com/materials/" +
     ("mild-steel/" if directory.name.startswith("02") else "5052-aluminum/"))
    for directory in sorted(SCENARIOS.iterdir())
], ids=lambda value: value.name if isinstance(value, Path) else value.rsplit("/", 2)[-2])
def test_fresh_research_retains_material_identity_and_complete_table_contract(
    tmp_path, preparer, directory, material_page,
):
    binding_before = preparer.BINDING.read_bytes()
    binding = json.loads(binding_before)
    available = [{"server_id": server, "tool_name": tool, "name": server + "__" + tool, "schema_digest": "a" * 64}
                 for server, names in binding["allowed_tools"].items() for tool in names]
    args = SimpleNamespace(workspace_root=str(tmp_path / "workspace"), draft_root=str(tmp_path / "draft"),
                           attempt="attempt-research-repair", campaign_id="fixture-campaign", instance_source=None)
    result = preparer.prepare(args, directory, available)
    plan = compile_prompt_workflow(Path(result["draft"]).read_text(encoding="utf-8"))
    research = next(step for step in plan.steps if step.id.startswith("supplier_research_"))
    urls = json.loads(research.prompt.split("cart: ", 1)[1].split(". Call retrieve_public_references", 1)[0])
    assert urls == [material_page, *binding["supplier_sources"][1:]]
    assert len(urls) == 8
    assert f"urls={urls!r}" in research.prompt  # The actual operation request matches the stated references.
    assert {Path(path).name for path in research.expected_files} == {
        f"supplier-source-{index}.{extension}" for index in range(1, 9) for extension in ("html", "txt")
    }
    for requirement in [
        "column header plus the complete matching thickness row",
        "literal material query from the returned next_offset",
        "Do not repeatedly reset offset to zero",
        "exact displayed thickness spelling",
        ".059 rather than 0.059",
        "this example is not a stock selection",
        "keep selection unresolved",
    ]:
        assert requirement in research.prompt
    intent = next(step for step in plan.steps if step.id.startswith("intent_document_"))
    for requirement in [
        "existing R1/R3 permission for bare-sheet CAD",
        "not prerequisites for bare-sheet CAD",
        "Do not claim a finish is available or that coated fit has passed without evidence",
        "does not waive material identity or mandatory forming constraints",
        "actual complete forming sequence",
        "do not impose another scenario's four-bend sequence",
        "Unsupported or unresolved mandatory tooling remains a CAD blocker",
        "manufacturing_release=HOLD",
        "supplier_acceptance=unverified",
    ]:
        assert requirement in intent.prompt
    assert len([step for step in plan.steps if step.external_action]) == 3
    assert preparer.BINDING.read_bytes() == binding_before
