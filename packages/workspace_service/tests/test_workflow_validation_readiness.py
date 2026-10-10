"""Known missing validation readers must not consume a workflow's design work."""

from unittest.mock import AsyncMock

import pytest

from core.process_validation import SourceReference
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_validation.configuration import ValidatorConfiguration
from workspace_service.process_validation.profiles import load_profile
from workspace_service.workflow_source_execution import _parse
from .test_process_input_readiness import process, source
from .test_process_preparation_service import owner, scope
from .test_process_validation_reporting import _profile, _request, _service
from .test_workflow_artifact_review import port, section


def validation_source(root, profile):
    (root / "profile.json").write_text(profile.model_dump_json(), encoding="utf-8")
    config = ValidatorConfiguration.model_validate(
        {
            "profile": {
                "source": "workspace",
                "name": "profile.json",
                "reference": profile.reference(),
            },
            "baseline": profile.baseline.reference(),
            "subjects": {"result": "inspect_subject"},
        }
    )
    blocks = _parse(source(default="Declared fixture input", later=True))
    first = next(block["fields"] for block in blocks if block["id"] == "first")
    first["settings"].update(output_format="json", output_filename="first.json")
    text = "".join(
        section(block["kind"], block["id"], **block["fields"]) for block in blocks
    )
    text += section(
        "task",
        "inspect",
        name="Inspect required length",
        purpose="Check the exact produced file",
        group=None,
        step_type="work",
        performed_by="configured_tool",
        tool=None,
        reusable_step=None,
        inputs=[port("inspect_subject", True)],
        outputs=[port("inspect_assessment")],
        prompt="",
        settings={
            "authoring_template": "process-validator",
            "validation": config.model_dump(mode="json"),
        },
    )
    text += section(
        "connection",
        "subject",
        type="item",
        **{"from": "first.first_out", "to": "inspect.inspect_subject"},
        label="Inspect output",
        when=None,
    )
    text += section(
        "connection",
        "gate",
        type="approval",
        **{"from": "inspect", "to": "later"},
        label="Required checks pass",
        when="pass",
    )
    return text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fault,expected",
    [
        ({"reader": "missing-measurement-reader"}, "missing-measurement-reader"),
        ({"evidence_method": "native_inspection"}, "required evidence method"),
    ],
)
async def test_missing_or_incompatible_required_reader_blocks_readiness_and_start(
    tmp_path, fault, expected
):
    profile = _profile()
    profile = profile.model_copy(
        update={"checks": (profile.checks[0].model_copy(update=fault),)}
    )
    text = validation_source(tmp_path, profile)
    app = owner(tmp_path, text)
    calls = AsyncMock(side_effect=AssertionError("No model or tool work may start"))
    try:
        prepared = await app.set_inputs(scope(), process(text))
        ready = await app.check_readiness(
            scope(), process(text), prepared.snapshot.snapshot_id
        )
        assert ready.state == "blocked"
        assert ready.reasons[0].code == "CAPABILITY_UNAVAILABLE"
        assert expected in ready.reasons[0].message
        assert "Inspect required length" in ready.reasons[0].message
        with pytest.raises(ProcessInterfaceError) as denied:
            await app.runs.start(
                scope(),
                process(text),
                prepared.snapshot.snapshot_id,
                "missing-reader",
                expected_input_digest=prepared.snapshot.digest,
                response_generator=calls,
                gateway=calls,
            )
        assert denied.value.reason.code == "CAPABILITY_UNAVAILABLE"
        calls.assert_not_called()
        assert app.runs._owned == {}
        with pytest.raises(KeyError):
            app.inputs.start_receipt("user", process(text), "missing-reader")
        assert not (tmp_path / "runs").exists()
        assert not (tmp_path / "first.json").exists()
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["available", "optional", "not_applicable", "review"])
async def test_ready_without_producing_upstream_outputs_or_answering_reviews(
    tmp_path, case
):
    profile = _profile(review=case == "review")
    if case in {"optional", "not_applicable"}:
        check = profile.checks[0].model_copy(update={"reader": "unavailable-optional"})
        if case == "optional":
            requirement = profile.baseline.requirements[0].model_copy(
                update={"mandatory": False}
            )
            profile = profile.model_copy(
                update={
                    "baseline": profile.baseline.model_copy(
                        update={"requirements": (requirement,)}
                    )
                }
            )
        else:
            check = check.model_copy(
                update={
                    "applicability_reason": SourceReference(
                        artifact_ref="fixture-exclusion.json",
                        sha256="e" * 64,
                        locator="explicit-exclusion",
                    )
                }
            )
        profile = profile.model_copy(update={"checks": (check,)})
    text = validation_source(tmp_path, profile)
    app = owner(tmp_path, text)
    try:
        prepared = await app.set_inputs(scope(), process(text))
        ready = await app.check_readiness(
            scope(), process(text), prepared.snapshot.snapshot_id
        )
        assert ready.state == "ready"
        assert not (tmp_path / "first.json").exists()
        assert not (tmp_path / "runs").exists()
        assert not (tmp_path / "validation").exists()
    finally:
        await app.close()


def test_reader_disappearing_after_preflight_still_produces_a_runtime_hold(tmp_path):
    service = _service(tmp_path)
    profile = _profile()
    service.registry.qualify_required_readers(profile)
    service.registry._readers.clear()  # Controlled capability loss after readiness.
    outcome = service.evaluate(_request(profile, length=100), profile)
    assert outcome.assessment.summary.release_eligible is False
    assert outcome.assessment.checks[0].state == "blocked"
    assert outcome.assessment.findings[0].code == "reader.unavailable"
    assert not outcome.assessment.measurements


def test_all_packaged_profiles_use_registered_methods_for_required_checks():
    from pathlib import Path
    from workspace_service.process_validation.service import default_reader_registry

    root = (
        Path(__file__).parents[1] / "src/workspace_service/process_validation/profiles"
    )
    # Profile package discovery below must cover actual shipped profile files.
    profiles = sorted(
        path for path in root.glob("*.json") if path.name != "coverage.json"
    )
    assert profiles
    for path in profiles:
        default_reader_registry().qualify_required_readers(load_profile(path.stem))
