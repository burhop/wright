"""Durable idempotency, terminal immutability and latest-attempt semantics."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from core.process_validation import (
    Assessment,
    Baseline,
    CheckDefinition,
    CheckResult,
    Constraint,
    ProducerIdentity,
    Requirement,
    SourceReference,
    SubjectBinding,
    ValidationProfile,
    ValidationRequest,
    canonical_digest,
    summarize,
)
from data_vault.process_validation_repository import (
    ProcessValidationRepository,
    ValidationConflict,
)


def request(key="request-1", value="demo", workspace="workspace-1"):
    profile = ValidationProfile(
        id="profile",
        version="1",
        baseline=Baseline(
            id="basis",
            version="1",
            requirements=(
                Requirement(
                    id="identity",
                    text="Part identity is demo",
                    scope="content",
                    sources=(
                        SourceReference(
                            artifact_ref="requirements",
                            sha256="a" * 64,
                            locator="identity",
                        ),
                    ),
                ),
            ),
        ),
        checks=(
            CheckDefinition(
                id="identity",
                requirement_ids=("identity",),
                subject_role="result",
                reader="structured",
                selector="",
                constraint=Constraint(operator="equals", expected="demo"),
            ),
        ),
    )
    req = ValidationRequest(
        trace_id="trace",
        workspace_id=workspace,
        invocation_id="check-invocation",
        run_id="run",
        check_step_id="check",
        subjects=(
            SubjectBinding(
                id="subject",
                role="result",
                result_id="run:producer:result",
                kind="value",
                value=value,
                sha256=canonical_digest(value),
                producer=ProducerIdentity(
                    run_id="run", step_id="producer", attempt=1, output_port="result"
                ),
            ),
        ),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=key,
    )
    return req, profile


def passed(attempt, profile):
    checks = (
        CheckResult(
            check_id="identity",
            requirement_ids=("identity",),
            state="pass",
            evidence_refs=("measured-inline-value",),
        ),
    )
    return Assessment(
        id="assessment-" + attempt.id,
        attempt_id=attempt.id,
        request=attempt.request,
        profile=profile,
        created_at="2026-09-16T00:00:00Z",
        checks=checks,
        summary=summarize(profile, checks),
    )


def test_same_idempotency_returns_same_attempt_but_changed_request_conflicts(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    req, _ = request()
    first, created = repo.create(req)
    duplicate, repeated = repo.create(req)
    assert created and not repeated and duplicate == first
    with pytest.raises(ValidationConflict, match="Idempotency"):
        repo.create(request(value="changed")[0])


def test_terminal_retry_uses_new_attempt_and_latest_includes_unfinished(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    req, profile = request()
    first, _ = repo.create(req)
    first = repo.start(req.workspace_id, first.id)
    assessment = passed(first, profile)
    repo.finalize(assessment)
    assert (
        repo.current(req.workspace_id, first.stream_key).assessment_id == assessment.id
    )
    second, _ = repo.create(request(key="retry-2")[0])
    current = repo.current(req.workspace_id, first.stream_key)
    assert (
        current.id == second.id
        and current.state == "queued"
        and current.assessment_id is None
    )
    assert repo.assessment(req.workspace_id, assessment.id) == assessment


def test_terminal_evidence_is_immutable_and_cross_workspace_reads_fail(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    req, profile = request()
    attempt, _ = repo.create(req)
    attempt = repo.start(req.workspace_id, attempt.id)
    assessment = passed(attempt, profile)
    repo.finalize(assessment)
    repo.finalize(assessment)  # exact repeated finalization is idempotent
    with pytest.raises(ValidationConflict):
        repo.start(req.workspace_id, attempt.id)
    with pytest.raises(ValidationConflict):
        repo.finalize(assessment.model_copy(update={"id": "replacement"}))
    with pytest.raises(KeyError):
        repo.assessment("other-workspace", assessment.id)
    with pytest.raises(KeyError):
        repo.get("other-workspace", attempt.id)


def test_concurrent_duplicate_request_has_one_winner(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    req, _ = request()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: repo.create(req), range(8)))
    assert len({attempt.id for attempt, _ in results}) == 1
    assert sum(created for _, created in results) == 1


def test_cancel_is_terminal_and_does_not_reveal_other_workspaces(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    req, _ = request()
    attempt, _ = repo.create(req)
    with pytest.raises(KeyError):
        repo.stop("foreign", attempt.id, "cancelled", "cancel")
    repo.stop(req.workspace_id, attempt.id, "cancelled", "User cancelled")
    assert repo.get(req.workspace_id, attempt.id).state == "cancelled"
    with pytest.raises(ValidationConflict):
        repo.start(req.workspace_id, attempt.id)


def test_resume_only_returns_same_running_identity(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    req, _ = request()
    attempt, _ = repo.create(req)
    running = repo.start(req.workspace_id, attempt.id)
    assert repo.resume(req, attempt.id) == running
    with pytest.raises(ValidationConflict):
        repo.resume(request(value="changed")[0], attempt.id)


def test_migration_is_additive_and_reopen_preserves_rows(tmp_path):
    import sqlite3

    path = tmp_path / "state.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE existing_user_data (value TEXT)")
        db.execute("INSERT INTO existing_user_data VALUES ('keep')")
    repo = ProcessValidationRepository(path)
    req, _ = request()
    attempt, _ = repo.create(req)
    assert (
        ProcessValidationRepository(path).get(req.workspace_id, attempt.id) == attempt
    )
    with sqlite3.connect(path) as db:
        assert (
            db.execute("SELECT value FROM existing_user_data").fetchone()[0] == "keep"
        )
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def pending_review(repo):
    from core.process_validation import Correction, Finding, ReviewDecision

    req, original_profile = request()
    raw = original_profile.model_dump()
    raw["baseline"]["requirements"][0]["review_required"] = True
    raw["checks"] = list(raw["checks"]) + [
        {
            "id": "human-review",
            "requirement_ids": ["identity"],
            "subject_role": "result",
            "reader": "review",
            "constraint": {"operator": "review"},
            "evidence_method": "human_review",
        }
    ]
    profile = ValidationProfile(**raw)
    req = ValidationRequest(
        **{
            **req.model_dump(),
            "profile_ref": profile.reference(),
            "baseline_ref": profile.baseline.reference(),
        }
    )
    attempt, _ = repo.create(req)
    attempt = repo.start(req.workspace_id, attempt.id)
    finding = Finding(
        id="pending",
        code="review.required",
        check_id="human-review",
        requirement_ids=("identity",),
        state="blocked",
        category="review_required",
        expected=Constraint(operator="review"),
        source_refs=profile.baseline.requirements[0].sources,
        summary="Review required",
        explanation="Awaiting an authenticated reviewer",
        correction=Correction(
            action="request_review", target="Review the output identity"
        ),
    )
    checks = (
        CheckResult(
            check_id="identity",
            requirement_ids=("identity",),
            state="pass",
            evidence_refs=("measurement",),
        ),
        CheckResult(
            check_id="human-review",
            requirement_ids=("identity",),
            state="blocked",
            finding_ids=("pending",),
        ),
    )
    original = Assessment(
        id="original",
        attempt_id=attempt.id,
        request=req,
        profile=profile,
        created_at="2026-09-16T00:00:00Z",
        checks=checks,
        findings=(finding,),
        summary=summarize(profile, checks),
    )
    repo.finalize(original)
    decision = ReviewDecision(
        id="decision",
        workspace_id=req.workspace_id,
        assessment_id=original.id,
        assessment_digest=canonical_digest(original),
        requirement_id="identity",
        actor_id="reviewer",
        actor_type="authenticated_human",
        authority_ref="authenticated-request",
        decision="approved",
        rationale="Identity verified",
        evidence_refs=("subject",),
        created_at=original.created_at,
    )
    revised_checks = (
        checks[0],
        CheckResult(
            check_id="human-review",
            requirement_ids=("identity",),
            state="pass",
            evidence_refs=(decision.id,),
        ),
    )
    revised = Assessment(
        **{
            **original.model_dump(),
            "id": "reviewed",
            "supersedes": original.id,
            "checks": revised_checks,
            "findings": (),
            "review_ids": (decision.id,),
            "summary": summarize(profile, revised_checks),
        }
    )
    return original, decision, revised, attempt


def test_late_review_appends_without_rewriting_original(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    original, decision, revised, attempt = pending_review(repo)
    repo.append_review(decision, revised)
    assert repo.assessment(decision.workspace_id, original.id) == original
    assert repo.assessment(decision.workspace_id, revised.id).summary.release_eligible
    assert (
        repo.current(decision.workspace_id, attempt.stream_key).assessment_id
        == revised.id
    )
    assert repo.get(decision.workspace_id, attempt.id).assessment_id == original.id


def test_late_review_rejects_superseded_attempt(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    original, decision, revised, _ = pending_review(repo)
    repo.create(
        ValidationRequest(
            **{**original.request.model_dump(), "idempotency_key": "newer"}
        )
    )
    with pytest.raises(ValidationConflict, match="current"):
        repo.append_review(decision, revised)


def test_review_cannot_remove_a_measured_check(tmp_path):
    repo = ProcessValidationRepository(tmp_path / "validation.sqlite3")
    original, decision, revised, _ = pending_review(repo)
    checks = revised.checks[1:]
    forged = Assessment(
        **{
            **revised.model_dump(),
            "checks": checks,
            "summary": summarize(original.profile, checks),
        }
    )
    with pytest.raises(ValidationConflict, match="remove"):
        repo.append_review(decision, forged)
