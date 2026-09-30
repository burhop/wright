"""A presentation folds owner facts without granting engineering authority."""

from dataclasses import replace

import pytest

from core.process_interactions import (
    Action,
    InputSnapshot,
    Observation,
    PendingInteraction,
    ProcessRef,
    Readiness,
    Reason,
)
from core.process_validation import canonical_digest
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.projection import (
    ProjectionFacts,
    RecordedRun,
    project_interactions,
    project_output,
)
from workspace_service.process_interfaces.service import ProcessScope
from workspace_service.workflow_results import (
    EngineeringResult,
    Provenance,
    Representation,
)

NOW = "2026-09-30T12:00:00Z"
DIGEST = "a" * 64


def process(workspace="workspace", digest=DIGEST):
    return ProcessRef(
        workspace_id=workspace,
        source_path="workflows/analysis.wflow",
        source_digest=digest,
    )


def scope(capabilities=None):
    return ProcessScope(
        principal_id="user",
        workspace_id="workspace",
        capabilities=frozenset(
            capabilities
            or {
                "process.read",
                "process.start",
                "process.action",
                "process.cancel",
                "process.review",
                "process.respond",
            }
        ),
    )


def facts(**changes):
    snap = InputSnapshot.create(snapshot_id="inputs", process=process(), created_at=NOW)
    ready = Readiness(
        state="ready",
        assessment_id="readiness",
        process=process(),
        input_digest=snap.digest,
        assessed_at=NOW,
    )
    return ProjectionFacts(
        **{
            "process": process(),
            "generated_at": NOW,
            "input_snapshot": snap,
            "readiness": ready,
            **changes,
        }
    )


def run(status="running", **changes):
    return RecordedRun(
        **{
            "process": process(),
            "run_id": "run",
            "status": status,
            "cursor": 3,
            "observed_at": NOW,
            **changes,
        }
    )


def result(location="outputs/model.stl", digest=DIGEST):
    return EngineeringResult(
        "run:model:part",
        "cad_model",
        "Measured part",
        (Representation("workspace_file", location, "stl", sha256=digest),),
        Provenance("run", "model", "part"),
    )


def test_preparation_and_recorded_run_use_same_snapshot_identity():
    prepared = project_interactions(facts(), scope())
    assert prepared.state == "ready" and prepared.context.run_id is None
    live = project_interactions(
        facts(run=run(input_snapshot=facts().input_snapshot)), scope()
    )
    assert live.state == "running" and live.context.run_id == "run"
    assert live.context.input_digest == prepared.context.input_digest
    assert live.context.cursor == 3


@pytest.mark.parametrize(
    "recorded,expected",
    [
        ("awaiting_approval", "waiting_human"),
        ("pending_review", "waiting_human"),
        ("awaiting_external_outcome", "waiting_external"),
        ("external_action_outcome_unknown", "reconciliation_required"),
        ("interrupted", "reconciliation_required"),
        ("unknown", "reconciliation_required"),
        ("cancellation_requested", "cancellation_requested"),
        ("cancelled", "cancelled"),
        ("completed", "completed"),
        ("failed", "failed"),
    ],
)
def test_run_states_have_distinct_honest_meanings(recorded, expected):
    assert project_interactions(facts(run=run(recorded)), scope()).state == expected


def test_unknown_external_outcome_disables_repeat_action_with_reason():
    action = Action(
        action_id="dispatch",
        operation="action",
        title="Send",
        enabled=True,
        subject_digest=DIGEST,
    )
    projected = project_interactions(
        facts(run=run("external_action_outcome_unknown"), actions=(action,)), scope()
    )
    assert not projected.actions[0].enabled
    assert projected.actions[0].reasons[0].code == "OUTCOME_UNKNOWN"


def test_history_remains_visible_but_changed_source_does_not_grant_mutation():
    action = Action(
        action_id="dispatch",
        operation="action",
        title="Send",
        enabled=True,
        subject_digest=DIGEST,
    )
    old = run(process=process(digest="b" * 64), results=(result(),))
    projected = project_interactions(facts(run=old, actions=(action,)), scope())
    assert projected.outputs[0].result_id == "run:model:part"
    assert not projected.actions[0].enabled
    assert projected.actions[0].reasons[0].code == "SOURCE_CHANGED"


def test_scope_cannot_widen_owner_permitted_actions():
    action = Action(
        action_id="dispatch",
        operation="action",
        title="Send",
        enabled=True,
        subject_digest=DIGEST,
    )
    projected = project_interactions(facts(actions=(action,)), scope({"process.read"}))
    assert not projected.actions[0].enabled
    assert projected.actions[0].reasons[0].code == "SCOPE_DENIED"


def test_blocking_owner_evidence_reasons_are_preserved_without_ai_override():
    reason = Reason(
        code="CAPABILITY_UNAVAILABLE",
        message="The required measurement is missing.",
        correction="Run the declared measurement stage.",
    )
    action = Action(
        action_id="approve",
        operation="review",
        title="Approve",
        enabled=False,
        subject_digest=DIGEST,
        reasons=(reason,),
    )
    projected = project_interactions(facts(actions=(action,)), scope())
    assert projected.actions[0] == action
    assert not projected.outputs


def test_foreign_run_or_result_is_rejected_instead_of_silently_rebound():
    for candidate in (
        run(process=process("foreign")),
        run(
            results=(
                replace(result(), provenance=Provenance("other-run", "model", "part")),
            )
        ),
    ):
        with pytest.raises(ProcessInterfaceError) as exc:
            project_interactions(facts(run=candidate), scope())
        assert exc.value.reason.code == "SCOPE_DENIED"


def test_output_link_retains_exact_port_and_hashed_representation():
    projected = project_output(result())
    assert projected.result_id == "run:model:part"
    assert (projected.step_id, projected.port_id) == ("model", "part")
    assert projected.representations[0].sha256 == DIGEST
    assert projected.representations[0].artifact_ref == "outputs/model.stl"
    assert projected.supported_viewers == ("stl",)


def test_unhashed_or_unknown_representation_is_not_claimed_as_verified_preview():
    projected = project_output(result(digest=None))
    assert projected.representations == () and projected.supported_viewers == ()
    native = replace(
        result(),
        representations=(
            Representation(
                "application_document",
                "model",
                "native",
                provider_id="cad",
                resource_id="doc",
            ),
        ),
    )
    assert project_output(native).supported_viewers == ()


def test_observation_preserves_unavailable_metrics_and_freshness():
    observed = Observation(
        observation_id="solver",
        provider_binding="solver-mcp",
        state="waiting_external",
        observed_at=NOW,
        stale_after="2026-09-30T12:01:00Z",
    )
    projected = project_interactions(
        facts(run=run(), observations=(observed,)), scope()
    )
    assert projected.observations[0] == observed
    assert projected.observations[0].progress_percent is None


def test_declared_interaction_and_navigation_keep_exact_subject():
    pending = PendingInteraction(
        checkpoint_id="checkpoint",
        step_id="selection",
        kind="input",
        subject_digest=DIGEST,
        instructions="Select a candidate.",
        response_schema={"type": "string", "enum": ["a", "b"]},
    )
    projected = project_interactions(
        facts(run=run("awaiting_approval"), interactions=(pending,)), scope()
    )
    assert projected.interactions[0] == pending
    assert any(
        item.kind == "block" and item.block_id == "selection"
        for item in projected.navigation
    )
    assert canonical_digest(projected) == canonical_digest(
        project_interactions(
            facts(run=run("awaiting_approval"), interactions=(pending,)), scope()
        )
    )


def test_attached_run_does_not_inherit_another_preparation_or_legacy_unknown_inputs():
    from core.process_interactions import ValueBinding

    actual = InputSnapshot.create(
        snapshot_id="actual",
        process=process(),
        created_at=NOW,
        bindings=(ValueBinding(input_id="width", value=40),),
    )
    attached = project_interactions(facts(run=run(input_snapshot=actual)), scope())
    assert attached.context.input_digest == actual.digest
    assert attached.readiness is None
    legacy = project_interactions(facts(run=run()), scope())
    assert (
        legacy.context.input_digest is None and legacy.context.input_snapshot_id is None
    )


def validation_report(tmp_path, *, revision=False):
    from core.process_validation import (
        ProducerIdentity,
        SubjectBinding,
        ValidationRequest,
    )
    from data_vault.process_validation_repository import ProcessValidationRepository
    from workspace_service.process_validation.profiles import load_profile
    from workspace_service.process_validation.service import ProcessValidationService
    from workspace_service.process_validation.subjects import SubjectResolver

    value = {"length_mm": 100, "part_id": "demo-plate"}
    subject = SubjectBinding(
        id="subject",
        role="result",
        result_id="run:producer:result",
        producer=ProducerIdentity(
            run_id="run", step_id="producer", attempt=1, output_port="result"
        ),
        kind="value",
        value=value,
        sha256=canonical_digest(value),
    )
    profile = load_profile("structured-demo")
    request = ValidationRequest(
        trace_id="trace",
        workspace_id="workspace",
        invocation_id="check",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key="first",
    )
    owner = ProcessValidationService(
        ProcessValidationRepository(tmp_path / "validation.db"),
        SubjectResolver("workspace", str(tmp_path)),
    )
    first = owner.evaluate(request, profile)
    if revision:
        owner.evaluate(
            ValidationRequest.model_validate(
                {**request.model_dump(), "idempotency_key": "second"}
            ),
            profile,
        )
    report = owner.get_result(first.assessment.id)
    native = EngineeringResult(
        subject.result_id,
        "structured",
        "Measured dimensions",
        (
            Representation(
                "value", "steps/producer/response", "json", sha256=subject.sha256
            ),
        ),
        Provenance("run", "producer", "result"),
    )
    return report, native, subject


@pytest.mark.parametrize("revision,expected", [(False, "current"), (True, "stale")])
def test_assessment_reference_uses_actual_082_currentness_and_exact_subject(
    tmp_path, revision, expected
):
    report, native, subject = validation_report(tmp_path, revision=revision)
    projected = project_output(native, (report,))
    reference = projected.assessments[0]
    assert reference.assessment_id == report.assessment.id
    assert reference.subject_digest == canonical_digest(subject)
    assert reference.currentness == expected and reference.outcome == "pass"
    changed = replace(
        native, representations=(replace(native.representations[0], sha256="b" * 64),)
    )
    assert project_output(changed, (report,)).assessments == ()


def test_projected_assessment_cannot_approve_an_action_without_owner_permission(
    tmp_path,
):
    report, native, _ = validation_report(tmp_path)
    reason = Reason(
        code="ACTION_NOT_PERMITTED",
        message="A declared engineering review is still required.",
        correction="Review the exact subject at its checkpoint.",
    )
    blocked = Action(
        action_id="dispatch",
        operation="action",
        title="Send",
        enabled=False,
        subject_digest=DIGEST,
        reasons=(reason,),
    )
    projected = project_interactions(
        facts(run=run(results=(native,)), reports=(report,), actions=(blocked,)),
        scope(),
    )
    assert projected.outputs[0].assessments[0].outcome == "pass"
    assert projected.actions[0] == blocked
