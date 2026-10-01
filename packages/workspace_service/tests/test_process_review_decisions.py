"""Exact scoped reviews use real source, run, SQLite and artifact authorities.

Model documents and decisions are synthetic test inputs, not engineering approval.
"""

import json
from dataclasses import replace

import pytest

from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import ProcessInterfaceService
from workspace_service.workflow_integration_policy import (
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
)
from workspace_service.workflow_sources import WorkspaceWorkflowSourceStore
from packages.workspace_service.tests.test_process_input_readiness import (
    process,
    source,
)
from packages.workspace_service.tests.test_process_preparation_service import (
    owner,
    scope,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section, port


def review_scope(actor="reviewer"):
    return replace(
        scope("process.read", "process.start", "process.inputs", "process.review"),
        principal_id=actor,
    )


def review_source(*, artifact=False):
    text = source(default="Synthetic review requirements")
    text += section(
        "task",
        "review",
        name="Review prepared document",
        purpose="Declared exact evidence review",
        step_type="work" if artifact else "review",
        group=None,
        performed_by="engineer",
        inputs=[port("evidence", True)],
        outputs=[],
        instructions="Review the prepared test document before continuing.",
        tool=None,
        reusable_step=None,
        settings={"authoring_template": "manual-review"}
        if artifact
        else {
            "authoring_template": "external-action-approval",
            "action_kind": "local_review",
            "approval_binding": LOCAL_REVIEW_BINDING,
            "approval_destination": LOCAL_REVIEW_DESTINATION,
            "approval_settings": {"review_task_id": "review"},
            "approval_action": {"kind": "local_review", "mode": "review_only"},
        },
    )
    return text + section(
        "connection",
        "review_evidence",
        type="item",
        **{"from": "first.first_out", "to": "review.evidence"},
        label="Actual reviewed document",
        when=None,
    )


async def waiting_review_case(root, *, artifact=False):
    text = review_source(artifact=artifact)
    reference = process(text)
    (root / "workflows").mkdir(parents=True, exist_ok=True)
    store = WorkspaceWorkflowSourceStore(str(root))
    store.create(reference.source_path, text)
    app = owner(root, text)
    app.workspace.process_interfaces = app
    from workspace_service.workflow_artifact_review import WorkflowArtifactReviewService
    from workspace_service.workflow_external_actions import (
        WorkflowExternalActionService,
    )
    from data_vault.workflow_continuation_repository import (
        WorkflowContinuationRepository,
    )
    from workspace_service.workspace_file_identity import workspace_file_sha256

    app.workspace.workflow_external_actions = WorkflowExternalActionService(
        WorkflowContinuationRepository(str(root / "state.db"))
    )
    app.workspace.workflow_artifact_reviews = WorkflowArtifactReviewService(
        str(root / "state.db")
    )

    async def read(workspace_dir, path):
        return store.read(path)

    async def hash_reference(workspace_dir, path):
        return workspace_file_sha256(workspace_dir, path)

    app.workspace.workflow_sources.read = read
    app.workspace.files.hash_reference = hash_reference
    frozen = (await app.set_inputs(review_scope(), reference)).snapshot
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Synthetic test document for declared review"

    receipt = await app.runs.start(
        review_scope(),
        reference,
        frozen.snapshot_id,
        "start-review",
        expected_input_digest=frozen.digest,
        response_generator=generate,
    )
    view = await app.runs.wait(review_scope(), reference, receipt.run_id)
    assert view["status"] == ("pending_review" if artifact else "awaiting_approval"), (
        view
    )
    ref = view["review"] if artifact else view["approval"]
    checkpoint_id = ref["review_id"] if artifact else ref["checkpoint_id"]
    subject_digest = ref["package_digest"] if artifact else ref["subject_digest"]
    return app, reference, receipt, checkpoint_id, subject_digest, calls, generate


async def decide(case, **changes):
    app, reference, _, checkpoint, digest, *_ = case
    arguments = dict(
        expected_subject_digest=digest,
        decision="approved",
        reason="Synthetic test review",
    )
    actor = changes.pop("actor", "reviewer")
    request = changes.pop("request_id", "review-one")
    arguments.update(changes)
    return await app.reviews.decide(
        review_scope(actor), reference, checkpoint, request, **arguments
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("artifact", [False, True])
async def test_review_is_scoped_durable_and_does_not_dispatch(tmp_path, artifact):
    case = await waiting_review_case(tmp_path, artifact=artifact)
    app, reference, receipt, cp, digest, calls, _ = case
    try:
        result = await decide(case)
        assert result.context.run_id == receipt.run_id
        assert result.interactions[0].subject_digest == digest
        assert result.interactions[0].decision.request_id == "review-one"
        assert result.state == ("completed" if artifact else "waiting_human")
        assert len(calls) == 1 and not app.runs.is_live(receipt.run_id)
        if artifact:
            reviewed = await app.workspace.workflow_artifact_reviews.get(
                "workspace", cp, str(tmp_path)
            )
            assert reviewed["actor"] == "reviewer"
            assert reviewed["request_id"] == "review-one"
            assert reviewed["state"] == "approved"
        else:
            reviewed = app.workspace.workflow_external_actions.lookup(cp)
            assert reviewed.actor == "reviewer" and reviewed.state == "approved"
            assert reviewed.external_action is None
            assert (
                reviewed.continuation["decision_receipt"]["request_id"] == "review-one"
            )
        await app.close()
        recreated = ProcessInterfaceService(app.workspace)
        app.workspace.process_interfaces = recreated
        case = (recreated, *case[1:])
        retried = await decide(case)
        assert retried.context.run_id == receipt.run_id
        assert len(calls) == 1
        record = json.loads(
            (tmp_path / receipt.run_log_path).read_text(encoding="utf-8")
        )
        assert (
            len(
                [
                    event
                    for event in record["events"]
                    if event["kind"]
                    == ("review_decided" if artifact else "approval_decided")
                ]
            )
            == 1
        )
        await recreated.close()
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("artifact", [False, True])
@pytest.mark.parametrize("change", ["actor", "request_id", "decision", "reason"])
async def test_review_request_identity_cannot_be_replaced(tmp_path, artifact, change):
    case = await waiting_review_case(tmp_path, artifact=artifact)
    try:
        await decide(case)
        with pytest.raises(ProcessInterfaceError) as failed:
            await decide(
                case,
                **{
                    change: {
                        "actor": "another-user",
                        "request_id": "other-request",
                        "decision": "changes_requested",
                        "reason": "Different test review",
                    }[change]
                },
            )
        assert failed.value.reason.code == "REQUEST_CONFLICT"
        assert len(case[5]) == 1
    finally:
        await case[0].close()


@pytest.mark.asyncio
@pytest.mark.parametrize("artifact", [False, True])
@pytest.mark.parametrize(
    "change", ["artifact", "source", "subject", "scope", "blank_reason"]
)
async def test_invalid_or_changed_review_does_not_record_decision(
    tmp_path, artifact, change
):
    case = await waiting_review_case(tmp_path, artifact=artifact)
    app, reference, _, cp, digest, calls, _ = case
    try:
        if change == "artifact":
            (tmp_path / "first.txt").write_text(
                "Changed actual evidence", encoding="utf-8"
            )
        elif change == "source":
            path = tmp_path / reference.source_path
            path.write_text(
                path.read_text().replace("Prepared input fixture", "Changed inputs")
            )
        arguments = dict(
            expected_subject_digest=digest, decision="approved", reason="Test review"
        )
        if change == "subject":
            arguments["expected_subject_digest"] = "0" * 64
        if change == "blank_reason":
            arguments.update(decision="changes_requested", reason="   ")
        with pytest.raises(ProcessInterfaceError):
            await app.reviews.decide(
                scope("process.read") if change == "scope" else review_scope(),
                reference,
                cp,
                "review-one",
                **arguments,
            )
        if artifact:
            reviewed = await app.workspace.workflow_artifact_reviews.get(
                "workspace", cp
            )
            assert reviewed["state"] == "pending" and reviewed["actor"] is None
        else:
            reviewed = app.workspace.workflow_external_actions.lookup(cp)
            assert reviewed.state == "pending" and reviewed.actor is None
        assert len(calls) == 1
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("artifact", [False, True])
async def test_lost_run_projection_can_be_reconciled_without_another_decision(
    tmp_path, artifact, monkeypatch
):
    case = await waiting_review_case(tmp_path, artifact=artifact)
    app, _, receipt, cp, _, calls, _ = case
    write = app.workspace.files.write_generated
    failed_once = False

    async def fail_projection(workspace_dir, path, *args, **kwargs):
        nonlocal failed_once
        if path == receipt.run_log_path and not failed_once:
            failed_once = True
            raise OSError("Synthetic lost run projection write")
        return await write(workspace_dir, path, *args, **kwargs)

    monkeypatch.setattr(app.workspace.files, "write_generated", fail_projection)
    try:
        with pytest.raises((ProcessInterfaceError, OSError)):
            await decide(case)
        if artifact:
            stored = await app.workspace.workflow_artifact_reviews.get("workspace", cp)
            assert (
                stored["request_id"] == "review-one" and stored["state"] == "approved"
            )
        else:
            stored = app.workspace.workflow_external_actions.lookup(cp)
            assert stored.continuation["decision_receipt"]["request_id"] == "review-one"
            assert stored.state == "approved" and stored.external_action is None
        recovered = await decide(case)
        assert recovered.interactions[0].decision.request_id == "review-one"
        assert len(calls) == 1
        record = json.loads(
            (tmp_path / receipt.run_log_path).read_text(encoding="utf-8")
        )
        assert (
            len(
                [
                    event
                    for event in record["events"]
                    if event["kind"] in {"approval_decided", "review_decided"}
                ]
            )
            == 1
        )
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_declared_input_cannot_be_decided_as_an_approval(tmp_path):
    from packages.workspace_service.tests.test_process_input_supervision import (
        waiting_case,
    )
    from workspace_service.workflow_external_actions import (
        WorkflowExternalActionService,
    )

    app, reference, _, checkpoint, calls, _ = await waiting_case(tmp_path)
    app.workspace.workflow_external_actions = WorkflowExternalActionService(
        app.human_inputs.repository
    )
    try:
        with pytest.raises(ProcessInterfaceError) as denied:
            await app.reviews.decide(
                review_scope(),
                reference,
                checkpoint.checkpoint_id,
                "review-input",
                expected_subject_digest=checkpoint.subject_digest,
                decision="approved",
                reason="Synthetic invalid cross-kind review",
            )
        assert denied.value.reason.code == "SCOPE_DENIED"
        assert (
            app.human_inputs.repository.get(checkpoint.checkpoint_id).state == "pending"
        )
        assert len(calls) == 1
    finally:
        await app.close()
