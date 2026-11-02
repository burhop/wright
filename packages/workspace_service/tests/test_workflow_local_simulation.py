"""Ordinary local artifact simulation uses manual, exact, one-shot authority."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from packages.workspace_service.tests.test_workflow_approval_execution import (
    setup_case,
    reopen_case,
)
from workspace_service.workflow_approval_execution import (
    decide_workflow_approval,
    qualify_workflow_action_dispatch,
    resume_workflow_approval,
)
from workspace_service.workflow_external_actions import (
    LOCAL_SIMULATION_BINDING,
    LOCAL_SIMULATION_DESTINATION,
    WorkflowExternalActionError,
)
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
)


async def case_at(root, kind="printer_transfer"):
    return await setup_case(root, integration=False, local_simulation_kind=kind)


def receipt_path(case):
    return case.root / case.checkpoint.subject["settings"]["receipt_path"]


async def approve(case):
    return await decide_workflow_approval(
        **case.args, decision="approved", actor="local_workspace_user"
    )


async def resume(case, request="manual-local-handoff"):
    return await resume_workflow_approval(
        **case.args, request_id=request, response_generator=case.generate
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["printer_transfer", "supplier_upload_preview"])
async def test_manual_simulation_preserves_exact_receipt_and_durable_single_dispatch(
    tmp_path, kind
):
    if kind == "supplier_upload_preview":
        # Reuse the accepted sheet-metal wall-dock handoff shape. This is a
        # controlled dispatcher proof, not a new CAD or campaign-validation run.
        profile = json.loads(
            (
                Path(__file__).resolve().parents[3]
                / "examples/process-interfaces/sheet-metal-wall-dock/validation-profile-r5-native-inventory.json"
            ).read_text()
        )
        original = next(
            check
            for check in profile["checks"]
            if check["id"] == "supplier-preview-simulation"
        )
        assert original["parameters"]["action_kind"] == kind
        assert original["parameters"]["destination"].startswith("test://")
    case = await case_at(tmp_path, kind)
    assert case.context is None
    assert case.checkpoint.subject["binding"] == LOCAL_SIMULATION_BINDING
    assert case.checkpoint.subject["destination"] == LOCAL_SIMULATION_DESTINATION
    assert not receipt_path(case).exists()
    await approve(case)
    checkpoint, result = await resume(case)
    raw = receipt_path(case).read_bytes()
    receipt = json.loads(raw)
    assert receipt["authority_mode"] == "manual_local_simulation"
    assert receipt["approval_actor"] == "local_workspace_user"
    assert receipt["integration_test"] is True
    assert receipt["simulated_handoff"] is True
    assert receipt["network_dispatch"] is False
    assert receipt["destination"] == LOCAL_SIMULATION_DESTINATION
    assert (
        not {"campaign_id", "dataset_id", "integration_policy_digest"} & receipt.keys()
    )
    package = next(
        item
        for item in case.checkpoint.continuation["artifact_files"]
        if item["path"].endswith("package.json")
    )
    assert (
        hashlib.sha256((tmp_path / package["path"]).read_bytes()).hexdigest()
        in receipt["artifact_digests"]
    )
    if kind == "printer_transfer":
        # Check the unchanged Printed02 receipt reader against actual receipt
        # bytes and the exact controlled package. No slicing claim is made.
        from core.process_validation import (
            CheckDefinition,
            Constraint,
            ProducerIdentity,
            ResourceBudget,
            SubjectBinding,
        )
        from workspace_service.process_validation.readers.base import (
            ReaderContext,
            SubjectSnapshot,
        )

        def subject(role, content, fmt):
            return SubjectSnapshot(
                SubjectBinding(
                    id=role,
                    role=role,
                    result_id=f"run:package:{role}",
                    producer=ProducerIdentity(
                        run_id="run", step_id="package", attempt=1, output_port=role
                    ),
                    kind="file",
                    locator=f"{role}.{fmt}",
                    format=fmt,
                    encoding="raw-bytes",
                    sha256=hashlib.sha256(content).hexdigest(),
                ),
                content,
            )

        receipt_check = CheckDefinition(
            id="transfer-identity",
            requirement_ids=("PRINTED02-HANDOFF",),
            subject_role="transfer_receipt",
            reader="printing",
            selector="printing/transfer",
            constraint=Constraint(operator="equals", expected=True),
            evidence_method="independent_measurement",
            parameters={
                "operation": "transfer_binding",
                "related_roles": ["slice_package"],
            },
        )
        from workspace_service.process_validation.readers.printing import (
            PrintingArtifactReader,
        )

        package_snapshot = subject(
            "slice_package", (tmp_path / package["path"]).read_bytes(), "3mf"
        )
        context = replace(
            ReaderContext.create(ResourceBudget(), "local-simulation"),
            related_snapshots=(package_snapshot,),
        )
        assert (
            PrintingArtifactReader()
            .measure(
                subject("transfer_receipt", raw, "json"),
                receipt_check,
                context,
            )
            .value
            is True
        )
    assert (
        checkpoint.state == "consumed"
        and checkpoint.external_action["outcome"] == "dispatched"
    )
    assert result["status"] == "completed" and result["run_id"] == case.result["run_id"]
    # Reopen persisted owners and recover the same completed run without replay.
    reopen_case(case)
    _, recovered = await resume(case, "another-request")
    assert recovered["status"] == "completed"
    assert receipt_path(case).read_bytes() == raw
    assert len(list(receipt_path(case).parent.glob("receipt*.json"))) == 1


@pytest.mark.asyncio
async def test_no_auto_or_enrollment_authority_for_manual_simulation(tmp_path):
    case = await case_at(tmp_path)
    with pytest.raises(WorkflowSourceExecutionError, match="manual decision"):
        await decide_workflow_approval(**case.args, decision="approved", auto=True)
    assert not receipt_path(case).exists()
    with pytest.raises(WorkflowSourceExecutionError, match="unsupported"):
        qualify_workflow_action_dispatch(
            case.plan, {"integration_policy_digest": "a" * 64}
        )
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "pending"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("when", ["before_decision", "after_decision"])
async def test_changed_exact_package_stops_simulation(tmp_path, when):
    case = await case_at(tmp_path)
    if when == "after_decision":
        await approve(case)
    package = case.checkpoint.continuation["artifact_files"][0]["path"]
    (tmp_path / package).write_bytes(b"changed package")
    with pytest.raises((WorkflowSourceExecutionError, WorkflowExternalActionError)):
        if when == "before_decision":
            await approve(case)
        else:
            await resume(case)
    assert not receipt_path(case).exists()


@pytest.mark.asyncio
async def test_existing_receipt_rejected_before_consumption(tmp_path):
    case = await case_at(tmp_path)
    await approve(case)
    path = receipt_path(case)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"previous output")
    with pytest.raises(WorkflowSourceExecutionError, match="already exists"):
        await resume(case)
    assert path.read_bytes() == b"previous output"
    assert (
        case.services.workflow_external_actions.lookup(
            case.checkpoint.checkpoint_id
        ).state
        == "approved"
    )
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.asyncio
async def test_publication_race_consumed_failure_has_no_sibling_or_replay(
    tmp_path, monkeypatch
):
    case = await case_at(tmp_path)
    await approve(case)
    path = receipt_path(case)
    original = case.services.files.write_generated
    calls = []

    async def race(workspace, relative, content, policy):
        if relative == case.checkpoint.subject["settings"]["receipt_path"]:
            calls.append(policy)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"concurrent output")
        return await original(workspace, relative, content, policy)

    monkeypatch.setattr(case.services.files, "write_generated", race)
    with pytest.raises(FileExistsError):
        await resume(case)
    checkpoint = case.services.workflow_external_actions.lookup(
        case.checkpoint.checkpoint_id
    )
    assert checkpoint.state == "consumed"
    assert checkpoint.external_action["outcome"] == "outcome_unknown"
    assert checkpoint.external_action["evidence"]["replay_permitted"] is False
    with pytest.raises(
        WorkflowSourceExecutionError, match="no confirmed completed outcome"
    ):
        await resume(case, "do-not-replay")
    assert calls == ["exclusive"]
    assert path.read_bytes() == b"concurrent output"
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "alteration",
    [
        "uri",
        "query",
        "setting",
        "authority",
        "mode",
        "simulation",
        "missing_file",
        "missing_run_path",
        "direct_input",
    ],
)
async def test_source_contract_rejects_ambiguous_or_unconfined_simulation(
    tmp_path, alteration
):
    from workspace_service.workflow_source_execution import _parse
    from packages.workspace_service.tests.test_workflow_artifact_review import section

    case = await case_at(tmp_path)
    blocks = _parse((tmp_path / case.checkpoint.workflow_id).read_text())
    block = next(b for b in blocks if b["id"] == "approve")
    fields, settings = block["fields"], block["fields"]["settings"]
    if alteration == "uri":
        settings["approval_destination"]["id"] = "https://printer.example/upload"
    elif alteration == "query":
        settings["approval_destination"]["id"] += "?device=printer"
    elif alteration == "setting":
        settings["approval_settings"]["network_dispatch"] = True
    elif alteration == "authority":
        settings["approval_settings"]["campaign_id"] = "invented"
    elif alteration == "mode":
        settings["approval_action"]["mode"] = "transfer_only"
    elif alteration == "simulation":
        settings["approval_action"]["simulation"] = 1
    elif alteration == "missing_file":
        fields["inputs"] = []
        blocks = [b for b in blocks if b["id"] != "package_to_approval"]
    elif alteration == "direct_input":
        package = next(b for b in blocks if b["id"] == "package")
        package["kind"] = "input"
        package["fields"]["settings"] = {
            "input_mode": "workspace-file",
            "workspace_file": "brief.md",
        }
    else:
        settings.pop("run_path_template")
    text = "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)
    with pytest.raises(WorkflowSourceExecutionError) as captured:
        compile_prompt_workflow(text)
    if alteration == "direct_input":
        assert "produced by upstream tasks" in str(captured.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("handoff", [False, True])
async def test_normal_readiness_rejects_unsupported_handoff_before_model_resolution(
    tmp_path, monkeypatch, handoff
):
    from workspace_service.workflow_run_preparation import (
        prepare_authorized_workflow_run,
    )

    case = await setup_case(tmp_path, integration=False, handoff=handoff)
    if not handoff:
        # Ordinary local review remains supported.
        qualify_workflow_action_dispatch(case.plan, None)
        return
    case.services.workflow_sources.read_template_origin = AsyncMock(return_value=None)
    freeze = AsyncMock(
        side_effect=AssertionError("No model resolution for unsupported action")
    )
    monkeypatch.setattr(
        "workspace_service.workflow_run_preparation.freeze_workflow_model_routing",
        freeze,
    )
    with pytest.raises(
        WorkflowSourceExecutionError, match="no supported authorized dispatcher"
    ):
        await prepare_authorized_workflow_run(
            service=case.services,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            session_id="s",
            source_path=case.checkpoint.workflow_id,
            source_digest=case.plan.definition_digest,
            gateway=None,
        )
    freeze.assert_not_awaited()


@pytest.mark.asyncio
async def test_existing_enrolled_dispatch_stays_distinct(tmp_path):
    case = await setup_case(tmp_path, integration=True, handoff=True)
    qualify_workflow_action_dispatch(case.plan, case.context)
    await decide_workflow_approval(**case.args, decision="approved", auto=True)
    await resume(case)
    receipt = json.loads((tmp_path / "outputs/attempt/receipt.json").read_bytes())
    assert receipt["campaign_id"] == "campaign"
    assert "authority_mode" not in receipt


@pytest.mark.asyncio
async def test_ordinary_simulation_is_ready_without_enrollment_or_execution(tmp_path):
    from workspace_service.workflow_run_preparation import (
        prepare_authorized_workflow_run,
    )

    case = await case_at(tmp_path)
    case.services.workflow_sources.read_template_origin = AsyncMock(return_value=None)
    prior_calls = len(case.calls)
    prepared = await prepare_authorized_workflow_run(
        service=case.services,
        workspace_dir=str(tmp_path),
        workspace_id="ws",
        session_id="s",
        source_path=case.checkpoint.workflow_id,
        source_digest=case.plan.definition_digest,
        gateway=None,
    )
    assert prepared.execution_context is None and prepared.runtime is None
    assert len(case.calls) == prior_calls
    assert not receipt_path(case).exists()


@pytest.mark.asyncio
async def test_missing_connected_output_identity_cannot_be_approved(
    tmp_path, monkeypatch
):
    case = await case_at(tmp_path)
    broken = replace(
        case.checkpoint,
        continuation={**case.checkpoint.continuation, "artifacts_by_output": {}},
    )
    monkeypatch.setattr(
        case.services.workflow_external_actions, "get", lambda *args, **kwargs: broken
    )
    with pytest.raises(
        WorkflowSourceExecutionError, match="connected, sealed artifacts"
    ):
        await approve(case)
    assert not receipt_path(case).exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("change_profile", [False, True])
async def test_static_profile_can_accompany_produced_package_and_stays_hash_bound(
    tmp_path, change_profile
):
    case = await setup_case(
        tmp_path,
        integration=False,
        local_simulation_kind="printer_transfer",
        local_simulation_static_input=True,
    )
    assert any(
        item["path"] == "brief.md"
        for item in case.checkpoint.continuation["input_files"]
    )
    await approve(case)
    if change_profile:
        (tmp_path / "brief.md").write_bytes(b"changed static profile")
        with pytest.raises(WorkflowExternalActionError, match="changed"):
            await resume(case)
        assert not receipt_path(case).exists()
    else:
        checkpoint, result = await resume(case)
        assert checkpoint.external_action["outcome"] == "dispatched"
        assert result["status"] == "completed"
        assert (
            hashlib.sha256((tmp_path / "brief.md").read_bytes()).hexdigest()
            in case.checkpoint.subject["input_digests"]
        )
