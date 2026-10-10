"""Exact assessment presentation uses the validator owner, never JSON claims."""

from contextlib import asynccontextmanager
from dataclasses import asdict
import hashlib
from types import SimpleNamespace

import pytest

from core.process_interactions import ArtifactRef
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_validation.reporting import render_readable_markdown
from workspace_service.process_validation.service import ProcessValidationService
from workspace_service.process_validation.subjects import SubjectResolver
from workspace_service.workflow_results import (
    EngineeringResult,
    Representation,
    Provenance,
)
from .test_process_artifact_access import case, CAPABILITIES, scope, source
from .test_process_validation_reporting import _profile, _request, _service


@asynccontextmanager
async def assessment_case(
    root, monkeypatch, *, workspace="workspace", owner_run="report-check"
):
    async with case(root, text=source(default="Assessment fixture")) as c:
        service = ProcessValidationService(
            ProcessValidationRepository(c.app.db_path),
            SubjectResolver(workspace, str(root)),
        )
        profile = _profile(review=True)
        request = _request(profile, length=100, workspace=workspace)
        subject = request.subjects[0]
        request = request.model_copy(
            update={
                "subjects": (
                    subject.model_copy(
                        update={
                            "producer": subject.producer.model_copy(
                                update={"run_id": owner_run}
                            )
                        }
                    ),
                )
            }
        )
        assessment = service.evaluate(request, profile).assessment
        content = assessment.model_dump_json(indent=2).encode()
        path = root / "assessment.json"
        path.write_bytes(content)
        reference = ArtifactRef(
            artifact_ref=path.name,
            sha256=hashlib.sha256(content).hexdigest(),
            result_id="recorded-assessment",
        )
        result = EngineeringResult(
            reference.result_id,
            "structured",
            "Assessment",
            (
                Representation(
                    "workspace_file", path.name, "json", sha256=reference.sha256
                ),
            ),
            Provenance("report-check", "validate", "report"),
        )
        view = {"source_digest": c.process.source_digest, "results": [asdict(result)]}
        monkeypatch.setattr(
            "workspace_service.process_interfaces.artifacts.read_workflow_run",
            lambda *a, **k: view,
        )
        yield SimpleNamespace(
            **vars(c),
            service=service,
            assessment=assessment,
            reference=reference,
            path=path,
            content=content,
            view=view,
        )


async def preview(c, **changes):
    return await c.app.artifacts.preview(
        scope(*CAPABILITIES),
        c.process,
        c.reference,
        **{"run_id": "report-check", "preview": "validation-report", **changes},
    )


@pytest.mark.asyncio
async def test_exact_report_preserves_hold_and_original_bytes_without_dispatch(
    tmp_path, monkeypatch
):
    async with assessment_case(tmp_path, monkeypatch) as c:
        report = await preview(c)
        assert report.reference == c.reference and report.media_type == "text/markdown"
        text = report.content.decode()
        assert (
            "Recorded outcome: HOLD" in text and "Findings requiring attention" in text
        )
        assert "Drawing has been reviewed" in text and "100.0 ± 0.2 mm" in text
        assert (
            "**Observed:** 100 mm" in text
            and "Physical validation:** not assessed" in text
        )
        assert text.index("Findings requiring attention") < text.index(
            "Record identity"
        )
        assert c.path.read_bytes() == c.content
        assert (
            c.app.inputs.receipt_for_run(
                "workspace", c.process.source_path, "report-check"
            )
            is None
        )
        assert c.service.repository.assessment_ids_for_run(
            "workspace", "report-check"
        ) == ((1, c.assessment.id),)


@pytest.mark.asyncio
@pytest.mark.parametrize("owner", [{"workspace": "foreign"}, {"owner_run": "foreign"}])
async def test_a_recorded_json_cannot_impersonate_another_workspace_or_run_report(
    tmp_path, monkeypatch, owner
):
    async with assessment_case(tmp_path, monkeypatch, **owner) as c:
        with pytest.raises(ProcessInterfaceError) as error:
            await preview(c)
        assert error.value.reason.code == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_actual_result_membership_and_hash_are_checked_before_report_lookup(
    tmp_path, monkeypatch
):
    async with assessment_case(tmp_path, monkeypatch) as c:
        for field, value in [
            ("result_id", "foreign"),
            ("sha256", "b" * 64),
            ("artifact_ref", "foreign.json"),
        ]:
            with pytest.raises(ProcessInterfaceError) as error:
                await c.app.artifacts.preview(
                    scope(*CAPABILITIES),
                    c.process,
                    c.reference.model_copy(update={field: value}),
                    run_id="report-check",
                    preview="validation-report",
                )
            assert error.value.reason.code == "SCOPE_DENIED"
        c.path.write_bytes(b"changed")
        with pytest.raises(ProcessInterfaceError) as error:
            await preview(c)
        assert error.value.reason.code == "SUBJECT_STALE"


@pytest.mark.asyncio
@pytest.mark.parametrize("extra", [{"page": 1}, {"archive_entry": "other"}])
async def test_report_rejects_unrelated_preview_options(tmp_path, monkeypatch, extra):
    async with assessment_case(tmp_path, monkeypatch) as c:
        with pytest.raises(ProcessInterfaceError) as error:
            await preview(c, **extra)
        assert error.value.reason.code == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
async def test_report_respects_bound_and_worker_timeout(tmp_path, monkeypatch):
    from workspace_service.errors import WorkspaceTimeoutError

    async with assessment_case(tmp_path, monkeypatch) as c:
        original_run = c.app.workspace.executor.run

        async def timeout(operation, *args, **kwargs):
            if operation == "process.representation.preview":
                raise WorkspaceTimeoutError("preview timed out")
            return await original_run(operation, *args, **kwargs)

        monkeypatch.setattr(c.app.workspace.executor, "run", timeout)
        with pytest.raises(ProcessInterfaceError) as error:
            await preview(c)
        assert error.value.reason.code == "CAPABILITY_UNAVAILABLE"
        assert "readable assessment" in error.value.reason.message


def test_readable_report_uses_currentness_and_escapes_untrusted_requirements(tmp_path):
    profile = _profile(
        requirement_text="Length | <script>bad</script> [open](https://invalid)"
    )
    service = _service(tmp_path)
    first = service.evaluate(_request(profile, length=100), profile).assessment
    current = render_readable_markdown(service.get_result(first.id))
    assert "Recorded outcome: PASS" in current
    assert "<script>" not in current and "\\[open\\]" in current
    service.evaluate(_request(profile, length=100, key="second"), profile)
    stale = render_readable_markdown(service.get_result(first.id))
    assert "Recorded outcome: HOLD" in stale and "Evidence current:** No" in stale


@pytest.mark.parametrize(
    "rule,expected",
    [
        (
            {"operator": "range", "minimum": 0, "maximum": 100, "inclusive": False},
            "> 0.0 and < 100.0 mm",
        ),
        ({"operator": "equals", "expected": 100}, "Equals 100 mm"),
    ],
)
def test_expected_values_keep_bounds_units_and_meaning(tmp_path, rule, expected):
    from core.process_validation import Constraint

    profile = _profile()
    profile = profile.model_copy(
        update={
            "checks": (
                profile.checks[0].model_copy(update={"constraint": Constraint(**rule)}),
            )
        }
    )
    service = _service(tmp_path)
    result = service.evaluate(_request(profile, length=100), profile)
    text = render_readable_markdown(service.get_result(result.assessment.id))
    from workspace_service.process_validation.reporting import _markdown

    assert _markdown(expected) in text


@pytest.mark.parametrize(
    "rule,observed,unit,expected",
    [
        (
            {"operator": "within", "target": 100, "tolerance": 0.2},
            0.1,
            "mm",
            "100.0 ± 0.2 mm",
        ),
        (
            {"operator": "equals", "expected": "Sheet-metal fabrication"},
            "Polymer material extrusion",
            None,
            "Equals Sheet-metal fabrication",
        ),
        ({"operator": "equals", "expected": True}, False, None, "Equals Yes"),
        (
            {
                "operator": "equals",
                "expected": "<script>bad</script> [link](https://invalid)",
            },
            "other",
            None,
            "Equals <script>bad</script> [link](https://invalid)",
        ),
    ],
)
def test_readable_failure_summary_uses_typed_values_without_rule_syntax(
    tmp_path, rule, observed, unit, expected
):
    from core.process_validation import Constraint
    from workspace_service.process_validation.reporting import _markdown

    profile = _profile()
    profile = profile.model_copy(
        update={
            "checks": (
                profile.checks[0].model_copy(
                    update={"constraint": Constraint(**rule), "unit": unit}
                ),
            )
        }
    )
    service = _service(tmp_path)
    assessment = service.evaluate(
        _request(profile, length=observed), profile
    ).assessment
    original = assessment.model_dump_json()
    report = service.get_result(assessment.id)
    text = render_readable_markdown(report)
    summary = text.split("## Findings requiring attention", 1)[1].split(
        "## Requirements and observations", 1
    )[0]
    assert _markdown(expected) in summary
    observed_label = "No" if observed is False else str(observed)
    assert _markdown(observed_label + (" " + unit if unit else "")) in summary
    assert "operator" not in summary and "inclusive" not in summary
    assert "/length" not in summary and "<script>" not in text
    assert "Revise the assessed output and rerun the required checks." in text
    assert assessment.model_dump_json() == original
    assert report.assessment.model_dump_json() == original
