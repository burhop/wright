"""Adapter for the existing canonical scheduler, not a second executor."""

import asyncio
import hashlib
from pathlib import PurePosixPath

from core.process_validation import (
    ProducerIdentity,
    SubjectBinding,
    ValidationRequest,
    canonical_digest,
    canonical_json,
)

from .application import ValidationApplication, assessment_reference
from .configuration import ValidatorConfiguration


def _correction_explanations(findings):
    """Bound the run summary without repeating a cause shared by many checks."""
    # Keep every per-check finding in the assessment. Collapse only exact text
    # duplicates here, before the summary limit, preserving first-seen order.
    return list(dict.fromkeys(finding.explanation for finding in findings))[:20]


def application_for_workspace(service, workspace_dir):
    from ..workflow_source_execution import _invalid

    workspace = service.repository.get_by_path(workspace_dir)
    if not workspace:
        raise _invalid("Validation requires a registered workspace.")
    return ValidationApplication(
        service.db_path, workspace["workspace_id"], workspace_dir
    )


def output_id(run_id, step_id, attempt, port):
    return "output-" + canonical_digest([run_id, step_id, attempt, port])


def register_outputs(
    application,
    step,
    record,
    run_id,
    responses,
    artifacts_by_output,
    engineering_results,
):
    """Retain the producer's exact bytes/receipt before any downstream inspection."""
    from ..workflow_results import EngineeringResult
    from ..workflow_source_execution import _invalid

    attempt = record["producer_attempt"]
    for port, kind in step.output_ports:
        address = f"{step.id}.{port}"
        if address not in responses:
            continue
        result = next(
            (
                r
                for r in engineering_results
                if r.provenance.task_id == step.id and r.provenance.output_port == port
            ),
            None,
        )
        value = responses[address]
        if isinstance(value, EngineeringResult):
            result = value
        identity = dict(
            id=output_id(run_id, step.id, attempt, port),
            role="output",
            result_id=result.id if result else f"{run_id}:{step.id}:{port}",
            input_digests=tuple(record.get("verified_file_input_digests", ())),
            producer=ProducerIdentity(
                run_id=run_id, step_id=step.id, attempt=attempt, output_port=port
            ),
        )
        files = artifacts_by_output.get(address, [])
        receipt = next((f for f in files if f.get("output_port") == port), None)
        if kind == "workspace_file" and receipt is None and len(files) == 1:
            receipt = files[0]
        representation = (
            next(
                (r for r in result.representations if r.kind == "workspace_file"), None
            )
            if result
            else None
        )
        if kind in {"workspace_file", "cad_model", "analysis_result"} or isinstance(
            value, EngineeringResult
        ):
            if representation and representation.sha256:
                path, digest, fmt = (
                    representation.location,
                    representation.sha256,
                    representation.format,
                )
            elif receipt and receipt.get("sha256"):
                path, digest = receipt["output_path"], receipt["sha256"]
                fmt = receipt.get("output_format") or PurePosixPath(path).suffix.lstrip(
                    "."
                )
            else:
                # No guessed file or model-authored summary can stand in for a
                # native output. A provider reader is wired in the CAD slice.
                continue
            subject = SubjectBinding(
                **identity,
                kind="file",
                locator=path,
                format=fmt,
                sha256=digest,
                encoding="raw-bytes",
            )
        elif isinstance(value, str):
            subject = SubjectBinding(
                **identity,
                kind="value",
                value=value,
                format=step.output_format,
                sha256=hashlib.sha256(value.encode("utf-8")).hexdigest(),
                encoding="raw-bytes",
            )
        else:
            raise _invalid(
                f"{step.title}: no exact validation representation is available for {port}."
            )
        application.repository.register_output(application.workspace_id, subject)


async def execute_validator(
    application, step, *, records, run_id, revision, service, workspace_dir, emit
):
    from ..workflow_source_execution import _error

    config = ValidatorConfiguration.model_validate(step.validation)
    try:
        profile = config.load(workspace_dir)
    except (OSError, ValueError) as exc:
        raise _error(
            "PROCESS_VALIDATION_PROFILE_CHANGED",
            "The validation profile or requirement baseline changed.",
            "Restore the pinned profile or explicitly save a new approved baseline before a new run.",
        ) from exc
    subjects = []
    for role, address in step.validation_sources:
        producer_id, port = address.split(".", 1)
        record = next((r for r in records if r["task_id"] == producer_id), None)
        if record is None:
            continue  # Service persists an explicit missing-subject finding.
        try:
            subject = application.repository.output(
                application.workspace_id,
                output_id(run_id, producer_id, record["producer_attempt"], port),
            )
        except KeyError:
            continue
        subjects.append(subject.model_copy(update={"role": role}))
    request = ValidationRequest(
        trace_id=run_id,
        workspace_id=application.workspace_id,
        invocation_id=f"{step.id}:{revision + 1}",
        run_id=run_id,
        check_step_id=step.id,
        subjects=tuple(subjects),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        # A step/revision repeats in each durable run. Its validation request
        # binds run-specific output identities and must not collide with a
        # different run in the same workspace. Exact retries remain stable.
        idempotency_key="run:" + canonical_digest([run_id, step.id, revision]),
        budget=config.budget,
    )
    await emit(
        "step_started",
        task_id=step.id,
        task_title=step.title,
        execution_kind="validator",
        output_format="json",
    )
    from threading import Event

    cancelled = Event()
    work = asyncio.create_task(
        asyncio.to_thread(
            application.service.evaluate, request, profile, cancelled=cancelled
        )
    )
    try:
        outcome = await asyncio.shield(work)
    except asyncio.CancelledError:
        cancelled.set()
        await asyncio.shield(work)
        raise
    assessment = outcome.assessment
    if assessment is None:
        raise _error(
            "PROCESS_VALIDATION_INCOMPLETE",
            "Validation did not produce a terminal assessment.",
            "Inspect the saved validation attempt before retrying.",
        )
    review_requirement_ids = {
        requirement.id
        for requirement in profile.baseline.requirements
        if requirement.review_required
    }
    for record in reversed(records):
        authority = record.get("review_authority") or {}
        configured = (authority.get("settings") or {}).get("validation_review")
        if (
            authority.get("action_kind") != "local_review"
            or not isinstance(configured, dict)
            or not configured
        ):
            continue
        configured_ids = configured.get("requirement_ids")
        if (
            set(configured) != {"profile_ref", "requirement_ids"}
            or not isinstance(configured_ids, list)
            or any(not isinstance(item, str) for item in configured_ids)
            or configured.get("profile_ref")
            != profile.reference().model_dump(mode="json")
            or set(configured_ids) != review_requirement_ids
            or not isinstance(authority.get("actor"), str)
            or not authority["actor"].strip()
            or authority["actor"].startswith("integration_test:")
            or not isinstance(authority.get("checkpoint_id"), str)
            or not isinstance(authority.get("subject_digest"), str)
        ):
            continue
        approved = (authority.get("subject") or {}).get("artifact_digests")
        if not isinstance(approved, list) or any(
            not isinstance(item, str) for item in approved
        ):
            continue
        approved_digests = set(approved)
        review_roles = {
            check.subject_role
            for check in profile.checks
            if check.constraint.operator == "review"
        }
        if not {
            subject.sha256
            for subject in assessment.request.subjects
            if subject.role in review_roles
        }.issubset(approved_digests):
            continue
        rationale = authority.get("reason")
        if not isinstance(rationale, str) or not rationale.strip():
            rationale = (
                "Approved the exact validator subjects under the declared "
                "local-review criteria."
            )
        for requirement_id in sorted(review_requirement_ids):
            assessment = application.service.record_review(
                assessment.id,
                requirement_id=requirement_id,
                actor_id=authority["actor"],
                authority_ref=(
                    "workflow-approval:"
                    + authority["checkpoint_id"]
                    + ":"
                    + authority["subject_digest"]
                ),
                decision="approved",
                rationale=rationale,
                evidence_refs=(
                    authority["checkpoint_id"],
                    authority["subject_digest"],
                ),
            )
        from .service import EvaluationOutcome

        outcome = EvaluationOutcome(
            outcome.attempt,
            assessment,
            application.service.currentness(assessment).is_current,
        )
        break
    raw = assessment.model_dump_json(indent=2)
    path = await service.files.write_generated(
        workspace_dir, f"validation/{assessment.id}.json", raw, "indexed"
    )
    artifact_role = "verification" if outcome.release_eligible else "diagnostic"
    output = dict(
        task_id=step.id,
        task_title=step.title,
        output_path=path,
        output_bytes=len(raw.encode("utf-8")),
        output_format="json",
        sha256=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        artifact_role=artifact_role,
        artifact_title=f"{step.title} — validation evidence",
    )
    await emit("output_saved", **output)
    errors = any(f.state == "error" for f in assessment.findings)
    correctable = any(
        f.correction.action == "revise_output" for f in assessment.findings
    )
    verdict = (
        "pass"
        if outcome.release_eligible
        else "error"
        if errors
        else "revise"
        if correctable and assessment.subject_current
        else "needs_input"
    )
    report = {
        **assessment_reference(assessment, outcome.is_current),
        "verdict": verdict,
        "assessment_path": path,
        "corrections": _correction_explanations(assessment.findings),
    }
    await emit(
        "design_check",
        task_id=step.id,
        task_title=step.title,
        report=report,
        revision=revision,
        status=verdict,
        message="Validation passed."
        if verdict == "pass"
        else "Validation is holding downstream work; inspect the saved findings.",
        assessment_id=assessment.id,
        assessment_path=path,
        release_eligible=outcome.release_eligible,
    )
    return canonical_json(report), report, output
