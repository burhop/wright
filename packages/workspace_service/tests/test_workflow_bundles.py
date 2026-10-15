import asyncio
import base64
import hashlib
import json
from types import SimpleNamespace

import pytest

from core.process_validation import canonical_digest
from core.workflow_bundle import WorkflowBundle
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_bundles import (
    WorkflowBundleError,
    WorkflowBundleService,
)
from workspace_service.workflow_instruction_settings import (
    materialize_new_workflow_instructions,
)
from workspace_service.workflow_sources import WorkspaceWorkflowSourceStore
from packages.workspace_service.tests.test_workflow_instruction_settings import profile


def source(reference=False, instructions=True):
    text = 'workflow design\n  name: "Design example"\nend\n'
    if reference:
        text += 'input drawing\n  name: "Reference"\n  settings: {"workspace_file":"references/design.png"}\nend\n'
    return (
        materialize_new_workflow_instructions(text, profile("Captured A"))
        if instructions
        else text
    )


@pytest.fixture
def case(tmp_path):
    origin = tmp_path / "origin"
    target = tmp_path / "target"
    origin.mkdir()
    target.mkdir()
    executor = BoundedExecutor(max_workers=1)
    service = WorkflowBundleService(SimpleNamespace(executor=executor))
    yield SimpleNamespace(origin=origin, target=target, service=service)
    asyncio.run(executor.close())


def export(case, text=None, **kwargs):
    text = text or source()
    document = WorkspaceWorkflowSourceStore(case.origin).create(
        "workflows/design.workflow.wflow", text
    )
    return asyncio.run(
        case.service.export(
            "origin", str(case.origin), document.path, document.storage_digest, **kwargs
        )
    )


def inspect(case, raw, destination="workflows/imported.workflow.wflow"):
    return asyncio.run(case.service.inspect(str(case.target), raw, destination))


def test_two_workspace_import_preserves_exact_instructions_and_no_authority(case):
    exported = export(case)
    before = profile("Changed local B")  # Local default changes cannot affect import.
    assert before.assets[0].body != "Captured A"
    report = inspect(case, exported["bundle"])
    assert report.can_import and not report.can_run
    applied = asyncio.run(
        case.service.apply(
            str(case.target),
            exported["bundle"],
            "workflows/imported.workflow.wflow",
            exported["bundle_digest"],
        )
    )
    assert applied["source"]["source"] == exported["bundle"]["source"]
    assert applied["source"]["storage_revision"] == 1
    assert "Captured A" in applied["source"]["source"]
    assert "Changed local B" not in applied["source"]["source"]
    assert not (case.target / "runs").exists()
    assert not inspect(case, exported["bundle"]).can_import


def test_action_intent_snapshot_and_manifest_contract_survive_transfer_without_default_lookup(
    case,
):
    from agent_adapters.workflow_instructions import load_default_workflow_instructions

    text = materialize_new_workflow_instructions(
        'workflow design\n  name: "Design example"\nend\n',
        load_default_workflow_instructions(),
    )
    exported = export(case, text)
    dependency = next(
        item
        for item in exported["bundle"]["dependencies"]
        if item["category"] == "instructions"
    )
    assert (
        dependency["details"]["action_intent_contract"]
        == "wright.workflow-action-intent/1"
    )
    assert inspect(case, exported["bundle"]).can_import
    for action_contract in (None, "wright.workflow-action-intent/999"):
        tampered = json.loads(json.dumps(exported["bundle"]))
        target = next(
            item
            for item in tampered["dependencies"]
            if item["category"] == "instructions"
        )
        if action_contract is None:
            target["details"].pop("action_intent_contract")
        else:
            target["details"]["action_intent_contract"] = action_contract
        assert not inspect(case, tampered).can_import
        assert not (case.target / "workflows").exists()
    applied = asyncio.run(
        case.service.apply(
            str(case.target),
            exported["bundle"],
            "workflows/imported.workflow.wflow",
            exported["bundle_digest"],
        )
    )
    assert applied["source"]["source"] == text


def test_selected_reference_is_required_hashed_confined_and_not_overwritten(case):
    (case.origin / "references").mkdir()
    (case.origin / "references/design.png").write_bytes(b"image-reference")
    exported = export(
        case,
        source(reference=True),
        mode="bundle",
        selected_reference_paths=["references/design.png"],
    )
    assert inspect(case, exported["bundle"]).can_import
    raw = json.loads(json.dumps(exported["bundle"]))
    raw["assets"] = []
    assert not inspect(case, raw).can_import
    asyncio.run(
        case.service.apply(
            str(case.target),
            exported["bundle"],
            "workflows/imported.workflow.wflow",
            exported["bundle_digest"],
        )
    )
    assert (case.target / "references/design.png").read_bytes() == b"image-reference"
    assert not inspect(
        case, exported["bundle"], "workflows/another.workflow.wflow"
    ).can_import
    assert (case.target / "references/design.png").read_bytes() == b"image-reference"


def test_failed_first_asset_retains_reservation_and_blocks_restart_replay(
    case, monkeypatch
):
    (case.origin / "references").mkdir()
    (case.origin / "references/design.png").write_bytes(b"private-reference")
    exported = export(
        case,
        source(reference=True),
        mode="bundle",
        selected_reference_paths=["references/design.png"],
    )
    original = WorkspaceWorkflowSourceStore._write_once
    writes = []

    def fail_asset(store, path, content):
        writes.append(path)
        if path == case.target / "references/design.png":
            raise OSError("controlled first-asset failure")
        return original(store, path, content)

    monkeypatch.setattr(WorkspaceWorkflowSourceStore, "_write_once", fail_asset)
    with pytest.raises(OSError, match="controlled first-asset failure"):
        asyncio.run(
            case.service.apply(
                str(case.target),
                exported["bundle"],
                "workflows/imported.workflow.wflow",
                exported["bundle_digest"],
            )
        )
    receipt = case.target / "imported-assets/imported/manifest.json"
    assert receipt.is_file()
    assert writes[0] == receipt
    assert json.loads(receipt.read_text())["bundle_digest"] == exported["bundle_digest"]
    assert not (case.target / "references/design.png").exists()
    assert not (case.target / "workflows/imported.workflow.wflow").exists()
    # A newly constructed owner has no in-memory knowledge of the first attempt.
    restarted = WorkflowBundleService(case.service.workspace)
    report = asyncio.run(
        restarted.inspect(
            str(case.target), exported["bundle"], "workflows/imported.workflow.wflow"
        )
    )
    assert not report.can_import and not report.can_run
    count = len(writes)
    with pytest.raises(WorkflowBundleError):
        asyncio.run(
            restarted.apply(
                str(case.target),
                exported["bundle"],
                "workflows/imported.workflow.wflow",
                exported["bundle_digest"],
            )
        )
    assert len(writes) == count


def test_manifest_omissions_and_undeclared_assets_are_not_trusted(case):
    exported = export(case, source(reference=True))
    assert inspect(case, exported["bundle"]).can_import
    assert any(
        d.code == "external_dependency"
        for d in inspect(case, exported["bundle"]).diagnostics
    )
    raw = json.loads(json.dumps(exported["bundle"]))
    raw["dependencies"] = []
    assert not inspect(case, raw).can_import
    raw = exported["bundle"] | {
        "assets": [
            {
                "path": "references/extra.txt",
                "sha256": hashlib.sha256(b"extra").hexdigest(),
                "data_base64": base64.b64encode(b"extra").decode(),
            }
        ],
        "mode": "bundle",
    }
    assert not inspect(case, raw).can_import


def test_legacy_source_exports_explicit_dependency_without_default_migration(case):
    exported = export(case, source(instructions=False))
    report = inspect(case, exported["bundle"])
    assert report.can_import
    assert exported["bundle"]["source"] == source(instructions=False)
    assert any(
        d.identity == "legacy-local-defaults" for d in report.external_dependencies
    )
    asyncio.run(
        case.service.apply(
            str(case.target),
            exported["bundle"],
            "workflows/imported.workflow.wflow",
            exported["bundle_digest"],
        )
    )
    assert WorkspaceWorkflowSourceStore(case.target).read(
        "workflows/imported.workflow.wflow"
    ).source == source(instructions=False)


def test_credentials_tampered_defaults_and_forged_metadata_rejected(case):
    text = source() + 'input auth\n  settings: {"api_key":"private"}\nend\n'
    with pytest.raises(WorkflowBundleError, match="Credential"):
        export(case, text)
    raw = WorkflowBundle(
        mode="source",
        source=source(),
        source_digest=hashlib.sha256(source().encode()).hexdigest(),
        dependencies=[],
    ).model_dump(mode="json")
    assert not inspect(case, raw).can_import


def test_stale_export_and_import_digest_write_nothing(case):
    document = WorkspaceWorkflowSourceStore(case.origin).create(
        "workflows/design.workflow.wflow", source()
    )
    with pytest.raises(WorkflowBundleError, match="changed"):
        asyncio.run(
            case.service.export("origin", str(case.origin), document.path, "0" * 64)
        )
    exported = asyncio.run(
        case.service.export(
            "origin", str(case.origin), document.path, document.storage_digest
        )
    )
    with pytest.raises(WorkflowBundleError, match="changed"):
        asyncio.run(
            case.service.apply(
                str(case.target),
                exported["bundle"],
                "workflows/imported.workflow.wflow",
                "0" * 64,
            )
        )
    assert list(case.target.iterdir()) == []


def test_symlink_in_target_never_followed(case, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (case.target / "references").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Host does not permit creating a symlink")
    (case.origin / "references").mkdir()
    (case.origin / "references/design.png").write_bytes(b"picture")
    exported = export(
        case,
        source(reference=True),
        mode="bundle",
        selected_reference_paths=["references/design.png"],
    )
    assert not inspect(case, exported["bundle"]).can_import
    assert list(outside.iterdir()) == []


def test_invalid_source_and_invalid_destination_report_diagnostics(case):
    exported = export(case)
    assert not inspect(case, exported["bundle"], "../outside").can_import
    text = "invalid syntax"
    raw = exported["bundle"] | {
        "source": text,
        "source_digest": hashlib.sha256(text.encode()).hexdigest(),
    }
    assert not inspect(case, raw).can_import


def test_ui_candidate_keeps_binding_versions_and_source_but_not_build_trust(case):
    from core.process_interfaces import InterfaceManifest, SourceEnvelope

    exported = export(case, mode="bundle")
    envelope = SourceEnvelope(
        files={"App.tsx": "export default function App(){return <div>View</div>}"}
    )
    manifest = InterfaceManifest(
        ui_id="portable-ui",
        revision_id="original-revision",
        title="View",
        process={
            "workspace_id": "origin",
            "source_path": "workflows/design.workflow.wflow",
            "source_digest": exported["bundle"]["source_digest"],
        },
        client_version="1.0.0",
        kit_version="1.0.0",
    )
    raw = exported["bundle"] | {
        "interfaces": [
            {
                "manifest": manifest.model_dump(mode="json"),
                "source": envelope.model_dump(mode="json"),
                "source_digest": canonical_digest(envelope),
            }
        ],
        "dependencies": [
            *exported["bundle"]["dependencies"],
            {
                "category": "ui",
                "identity": "portable-ui",
                "disposition": "embedded",
                "sha256": canonical_digest(envelope),
                "details": {"activation": "local-rebuild-and-review-required"},
            },
        ],
    }
    report = inspect(case, raw)
    assert report.can_import and any(
        d.code == "ui_rebuild_required" for d in report.diagnostics
    )
    result = asyncio.run(
        case.service.apply(
            str(case.target),
            raw,
            "workflows/imported.workflow.wflow",
            report.bundle_digest,
        )
    )
    candidate_path = next(
        path for path in result["imported_paths"] if path.endswith("portable-ui.json")
    )
    candidate = json.loads((case.target / candidate_path).read_text())
    assert candidate["manifest"]["client_version"] == "1.0.0"
    assert candidate["source"] == envelope.model_dump(mode="json")
    assert "build" not in candidate and "role_resolution" not in candidate
    assert not (case.target / "state.db").exists()


@pytest.mark.parametrize("location", ["packaged", "workspace"])
def test_validation_profile_and_baseline_snapshots_are_pinned_and_complete(
    case, location
):
    from workspace_service.process_validation.profiles import load_profile

    selected = load_profile("printed-replacement-part-01")
    roles = {check.subject_role for check in selected.checks}
    for check in selected.checks:
        roles.update(check.parameters.get("related_roles", []))
    name = (
        "printed-replacement-part-01"
        if location == "packaged"
        else "profiles/requirements.json"
    )
    config = {
        "profile": {
            "source": location,
            "name": name,
            "reference": selected.reference().model_dump(mode="json"),
        },
        "baseline": selected.baseline.reference().model_dump(mode="json"),
        "subjects": {
            role: "port-" + str(index) for index, role in enumerate(sorted(roles))
        },
    }
    if location == "workspace":
        (case.origin / "profiles").mkdir()
        (case.origin / name).write_text(selected.model_dump_json(), encoding="utf-8")
    text = (
        source()
        + "task verify\n  settings: "
        + json.dumps({"validation": config})
        + "\nend\n"
    )
    exported = export(case, text, mode="bundle")
    profile_dependency = next(
        d
        for d in exported["bundle"]["dependencies"]
        if d["category"] == "validation_profile"
    )
    assert profile_dependency["details"]["profile"] == selected.model_dump(mode="json")
    report = inspect(case, exported["bundle"])
    assert report.can_import
    raw = json.loads(json.dumps(exported["bundle"]))
    dependency = next(
        d for d in raw["dependencies"] if d["category"] == "validation_profile"
    )
    dependency["details"]["profile"]["version"] = "different-version"
    assert not inspect(case, raw).can_import
    applied = asyncio.run(
        case.service.apply(
            str(case.target),
            exported["bundle"],
            "workflows/imported.workflow.wflow",
            exported["bundle_digest"],
        )
    )
    if location == "workspace":
        assert name in applied["imported_paths"]
        assert json.loads(
            (case.target / name).read_text(encoding="utf-8")
        ) == selected.model_dump(mode="json")


def test_provider_schema_requirements_and_model_requirements_do_not_claim_uuid_equivalence(
    case,
):
    text = (
        source()
        + 'task cad\n  performed_by: ai_assisted\n  settings: {"mcp_server":"same-uuid","mcp_tool":"local-name","mcp_schema_digest":"'
        + "a" * 64
        + '","model":"requested-model"}\nend\n'
    )
    catalog = [
        {
            "server_id": "same-uuid",
            "name": "local-name",
            "tool_name": "create_shape",
            "schema_digest": "a" * 64,
        }
    ]
    exported = export(case, text, catalog=catalog)
    report = inspect(case, exported["bundle"])
    provider = next(d for d in report.requirements if d.category == "provider")
    assert provider.details["qualified_operations"] == [
        {"tool_name": "create_shape", "schema_digest": "a" * 64}
    ]
    assert report.can_import and not report.can_run
    assert any(
        d.category == "model" and d.details["requested_model"] == "requested-model"
        for d in report.requirements
    )
    assert any(d.code == "local_qualification_required" for d in report.diagnostics)
    raw = json.loads(json.dumps(exported["bundle"]))
    next(d for d in raw["dependencies"] if d["category"] == "provider")["details"][
        "schema_digest"
    ] = "b" * 64
    assert not inspect(case, raw).can_import


def test_valid_layout_retained_and_forged_authority_metadata_rejected(case):
    layout = {
        "documentKind": "workflow-layout",
        "schemaVersion": "1.0.0-recovery.1",
        "workflowId": "workflow-design",
        "semanticRevision": 1,
        "layoutRevision": 1,
        "positions": {"task-cad": {"x": 100, "y": 200}},
        "viewport": {"x": 0, "y": 0, "zoom": 1},
    }
    document = WorkspaceWorkflowSourceStore(case.origin).create(
        "workflows/design.workflow.wflow", source(), layout=layout
    )
    exported = asyncio.run(
        case.service.export(
            "origin", str(case.origin), document.path, document.storage_digest
        )
    )
    assert exported["bundle"]["layout"] == layout
    raw = json.loads(json.dumps(exported["bundle"]))
    raw["dependencies"][0]["details"]["approval"] = {"granted": True}
    assert not inspect(case, raw).can_import
    result = asyncio.run(
        case.service.apply(
            str(case.target),
            exported["bundle"],
            "workflows/imported.workflow.wflow",
            exported["bundle_digest"],
        )
    )
    assert result["source"]["layout"] == layout


def test_dynamic_input_choice_provider_dependency_cannot_disappear(case):
    text = (
        source()
        + "input choice\n  settings: "
        + json.dumps(
            {
                "interaction_input": {
                    "option_source": {
                        "binding_id": "material-options",
                        "server_id": "external-machine",
                        "tool_name": "material_catalog",
                        "schema_digest": "c" * 64,
                    }
                }
            }
        )
        + "\nend\n"
    )
    exported = export(case, text)
    dependency = next(
        d for d in exported["bundle"]["dependencies"] if d["category"] == "provider"
    )
    assert dependency["identity"] == "choice:options"
    assert dependency["details"]["schema_digest"] == "c" * 64
    assert inspect(case, exported["bundle"]).can_import
    raw = exported["bundle"] | {
        "dependencies": [
            d for d in exported["bundle"]["dependencies"] if d["category"] != "provider"
        ]
    }
    assert not inspect(case, raw).can_import
