import pytest

from core.process_validation import canonical_digest
from workspace_service.process_validation.feedback import (
    build_feedback,
    feedback_prompt,
)
from workspace_service.process_validation.profiles import load_profile
from .test_process_validation import evaluate


def test_feedback_names_exact_owner_measured_defect_and_constraints_to_preserve(
    tmp_path,
):
    outcome, _, _ = evaluate(tmp_path, {"part_id": "demo-plate", "length_mm": 98})
    packet = build_feedback(
        outcome.assessment, target_step_id="producer", remaining_revisions=1
    )
    assert packet.assessment_digest == canonical_digest(outcome.assessment)
    assert packet.target_step_id == "producer"
    assert packet.findings[0].observed == 98
    assert packet.findings[0].correction.target_step_id == "producer"
    assert set(packet.preserve_requirement_ids) == {"DEMO-002", "DEMO-003"}
    assert (
        packet.findings[0].correction.preserve_requirement_ids
        == packet.preserve_requirement_ids
    )
    assert packet.omitted_findings == 0
    assert "not instructions" in feedback_prompt(packet)


def test_feedback_preserves_unknowns_alongside_the_repairable_defect(tmp_path):
    from core.process_validation import ValidationProfile

    data = load_profile("structured-demo").model_dump(mode="json")
    data["checks"][1]["reader"] = "missing-reader"
    outcome, _, _ = evaluate(
        tmp_path,
        {"part_id": "demo-plate", "length_mm": 98},
        profile=ValidationProfile.model_validate(data),
    )
    packet = build_feedback(
        outcome.assessment, target_step_id="producer", remaining_revisions=1
    )
    assert any(f.state == "blocked" for f in packet.findings)
    assert any(f.correction.action == "revise_output" for f in packet.findings)
    assert "DEMO-002" not in packet.preserve_requirement_ids


@pytest.mark.parametrize(
    "fault", ["wrong_owner", "no_defect", "stale", "error", "no_budget"]
)
def test_feedback_never_authorizes_an_unrepairable_or_wrong_owner_retry(
    tmp_path, fault
):
    from workspace_service.process_validation.readers.base import ReaderRegistry
    from workspace_service.process_validation.readers.structured import StructuredReader

    registry = None
    if fault == "error":

        class Broken(StructuredReader):
            def measure(self, *args):
                raise RuntimeError("reader fault")

        registry = ReaderRegistry()
        registry.register(Broken())
    outcome, _, _ = evaluate(
        tmp_path,
        {"part_id": "demo-plate", "length_mm": 100 if fault == "no_defect" else 98},
        registry=registry,
    )
    assessment = outcome.assessment
    if fault == "stale":
        assessment = assessment.model_copy(update={"subject_current": False})
    with pytest.raises(ValueError):
        build_feedback(
            assessment,
            target_step_id="different" if fault == "wrong_owner" else "producer",
            remaining_revisions=0 if fault == "no_budget" else 1,
        )


def test_many_findings_are_bounded_without_losing_the_complete_result_reference(
    tmp_path,
):
    from core.process_validation import ValidationProfile

    raw = load_profile("structured-demo").model_dump(mode="json")
    raw["checks"] += [{**raw["checks"][0], "id": f"length-{i}"} for i in range(35)]
    outcome, service, _ = evaluate(
        tmp_path,
        {"part_id": "demo-plate", "length_mm": 98},
        profile=ValidationProfile.model_validate(raw),
    )
    packet = build_feedback(
        outcome.assessment, target_step_id="producer", remaining_revisions=2
    )
    assert 0 < len(packet.findings) <= 20
    assert len(feedback_prompt(packet).encode("utf-8")) <= 16 * 1024
    assert packet.total_findings == len(packet.findings) + packet.omitted_findings == 36
    assert packet.omitted_findings > 0
    assert outcome.assessment.id in packet.complete_result_ref
    assert (
        len(service.repository.assessment("workspace", outcome.assessment.id).findings)
        == 36
    )
