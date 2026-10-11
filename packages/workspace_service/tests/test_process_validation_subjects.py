"""Real files and packaged profiles: confinement, provenance and staleness."""

import hashlib
from threading import Event

import pytest

from core.process_validation import (
    ProducerIdentity,
    ResourceBudget,
    SubjectBinding,
    ValidationRequest,
    canonical_digest,
)
from workspace_service.process_validation.profiles import load_profile
from workspace_service.process_validation.readers.base import (
    ReaderContext,
    ReaderRegistry,
    ValidationIssue,
)
from workspace_service.process_validation.subjects import SubjectResolver


def make_request(subject, *, canonical=False):
    profile = load_profile("structured-demo")
    return ValidationRequest(
        trace_id="trace",
        workspace_id="workspace",
        invocation_id="invocation",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key="key",
        run_id="run" if canonical else None,
        check_step_id="check" if canonical else None,
    )


def file_subject(content, locator="result.json"):
    return SubjectBinding(
        id="subject",
        role="result",
        result_id="run:producer:result",
        kind="file",
        format="json",
        locator=locator,
        encoding="raw-bytes",
        sha256=hashlib.sha256(content).hexdigest(),
        producer=ProducerIdentity(
            run_id="run", step_id="producer", attempt=1, output_port="result"
        ),
    )


def test_packaged_profile_loads_without_test_tree_and_keeps_source_digest():
    from importlib.resources import files

    profile = load_profile("structured-demo")
    baseline = (
        files("workspace_service.process_validation")
        .joinpath("profiles", "structured-demo-requirements.md")
        .read_bytes()
    )
    assert all(
        r.sources[0].sha256 == hashlib.sha256(baseline).hexdigest()
        for r in profile.baseline.requirements
    )
    assert load_profile("structured-demo", expected=profile.reference()) == profile
    assert profile.checks[0].constraint.tolerance == 0.2


def test_altered_profile_or_executable_check_cannot_match_pinned_identity(tmp_path):
    import json

    profile = load_profile("structured-demo")
    data = profile.model_dump(mode="json")
    data["checks"][0]["constraint"]["tolerance"] = 20
    (tmp_path / "profile.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="pinned"):
        load_profile(
            "profile.json", workspace_root=str(tmp_path), expected=profile.reference()
        )
    data["checks"][0]["code"] = "return True"
    (tmp_path / "profile.json").write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_profile("profile.json", workspace_root=str(tmp_path))


@pytest.mark.parametrize(
    "name", ["../structured-demo", "C:/profile", "structured-demo.json", "../../secret"]
)
def test_packaged_profile_name_is_confined(name):
    with pytest.raises(ValueError):
        load_profile(name)


def test_file_snapshot_is_exact_and_source_is_unchanged(tmp_path):
    content = b'{"length_mm":98,"part_id":"demo-plate"}'
    path = tmp_path / "result.json"
    path.write_bytes(content)
    req = make_request(file_subject(content))
    context = ReaderContext.create(req.budget, req.trace_id)
    resolver = SubjectResolver("workspace", str(tmp_path))
    snapshot = resolver.snapshot(req, req.subjects[0], context)
    resolver.assert_unchanged(req, snapshot, context)
    assert snapshot.content == path.read_bytes() == content
    path.write_bytes(b'{"length_mm":100,"part_id":"demo-plate"}')
    with pytest.raises(ValidationIssue) as error:
        resolver.assert_unchanged(req, snapshot, context)
    assert error.value.category == "stale_subject"


def test_missing_file_is_held_not_passed(tmp_path):
    req = make_request(file_subject(b"{}"))
    with pytest.raises(ValidationIssue) as error:
        SubjectResolver("workspace", str(tmp_path)).snapshot(
            req, req.subjects[0], ReaderContext.create(req.budget, req.trace_id)
        )
    assert error.value.code == "subject.missing" and error.value.state == "blocked"


def test_file_size_and_cancellation_are_bounded(tmp_path):
    content = b"123456789"
    (tmp_path / "result.json").write_bytes(content)
    req = make_request(file_subject(content))
    resolver = SubjectResolver("workspace", str(tmp_path))
    with pytest.raises(ValidationIssue):
        resolver.snapshot(
            req,
            req.subjects[0],
            ReaderContext.create(ResourceBudget(max_bytes=4), req.trace_id),
        )
    cancel = Event()
    cancel.set()
    with pytest.raises(ValidationIssue) as error:
        resolver.snapshot(
            req, req.subjects[0], ReaderContext.create(req.budget, req.trace_id, cancel)
        )
    assert error.value.code == "validation.cancelled"
    assert (tmp_path / "result.json").read_bytes() == content


def test_canonical_producer_claim_requires_runtime_receipt_verification(tmp_path):
    value = {"length_mm": 98}
    subject = SubjectBinding(
        id="s",
        role="result",
        result_id="run:producer:result",
        kind="value",
        value=value,
        sha256=canonical_digest(value),
        producer=ProducerIdentity(
            run_id="run", step_id="producer", attempt=1, output_port="result"
        ),
    )
    req = make_request(subject, canonical=True)
    context = ReaderContext.create(req.budget, req.trace_id)
    with pytest.raises(ValidationIssue) as error:
        SubjectResolver("workspace", str(tmp_path)).snapshot(req, subject, context)
    assert error.value.code == "subject.provenance"
    snapshot = SubjectResolver(
        "workspace", str(tmp_path), verify_binding=lambda bound: bound == subject
    ).snapshot(req, subject, context)
    assert snapshot.content == b'{"length_mm":98}'


def test_cross_workspace_binding_is_rejected(tmp_path):
    req = make_request(file_subject(b"{}"))
    with pytest.raises(PermissionError):
        SubjectResolver("different", str(tmp_path)).snapshot(
            req, req.subjects[0], ReaderContext.create(req.budget, req.trace_id)
        )


def test_missing_reader_is_named_and_never_substituted(tmp_path):
    from workspace_service.process_validation.readers.base import SubjectSnapshot

    req = make_request(file_subject(b"{}"))
    with pytest.raises(ValidationIssue) as error:
        ReaderRegistry().measure(
            SubjectSnapshot(req.subjects[0], b"{}"),
            load_profile("structured-demo").checks[0],
            ReaderContext.create(req.budget, req.trace_id),
        )
    assert error.value.code == "reader.unavailable"
    assert "structured" in str(error.value)


def test_reader_deadline_and_entity_limit_are_enforced():
    context = ReaderContext(ResourceBudget(), 0, Event(), "trace")
    with pytest.raises(ValidationIssue, match="time budget"):
        context.checkpoint()
    with pytest.raises(ValidationIssue, match="entity limit"):
        ReaderContext.create(ResourceBudget(max_entities=1), "trace").checkpoint(
            entities=2
        )
