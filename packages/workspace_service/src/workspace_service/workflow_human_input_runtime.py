"""Input barrier descriptors/results for the existing source executor."""

from core.process_validation import canonical_digest, canonical_json

from .workflow_execution_continuation import encode_value, input_identities
from .workflow_references import WorkflowReference
from .workflow_results import EngineeringResult, Provenance, Representation


def input_runtime_owner(service, plan):
    """Require frozen persisted inputs before any unattended work begins."""
    from .workflow_source_execution import _error

    try:
        frozen = plan.input_snapshot
        owner = service.process_interfaces.human_inputs
        retained = owner.inputs.get_snapshot(
            frozen.process.workspace_id, frozen.snapshot_id
        )
        if retained != frozen or frozen.process.source_digest != plan.definition_digest:
            raise ValueError("Frozen inputs do not match the accepted definition")
        return owner
    except (AttributeError, KeyError, ValueError, TypeError) as error:
        raise _error(
            "WORKFLOW_HUMAN_INPUT_UNAVAILABLE",
            "This workflow requires a durable input checkpoint and its frozen run inputs.",
            "Start the saved workflow through the authorized process run service.",
        ) from error


def input_checkpoint_request(
    *,
    plan,
    step,
    run_id,
    cursor,
    execution_context,
    input_values,
    responses,
    records,
    engineering_results,
    artifacts_by_output,
    attempts,
    revision_counts,
    feedback,
):
    from .workflow_source_execution import _execution_snapshot

    frozen = plan.input_snapshot
    representations = [
        rep
        for result in engineering_results
        for rep in (
            *result.representations,
            *(r for exported in result.exports for r in exported.representations),
        )
    ]
    subject = {
        "definition_digest": plan.definition_digest,
        "input_snapshot_id": frozen.snapshot_id,
        "input_digest": frozen.digest,
        "input_digests": sorted(input_identities(input_values).values()),
        "artifact_digests": sorted(
            {rep.sha256 for rep in representations if rep.sha256}
        ),
        "step_id": step.id,
        "declaration": step.human_interaction,
        "upstream_digests": {
            source: canonical_digest(encode_value(responses[source]))
            for _, source in step.references
        },
    }
    return {
        "step_id": step.id,
        "step_title": step.title,
        "instructions": step.human_interaction["instructions"],
        "subject": subject,
        "continuation": {
            "schema_version": 3,
            "checkpoint_kind": "input",
            "run_id": run_id,
            "definition_digest": plan.definition_digest,
            "execution_context": execution_context,
            "input_snapshot_id": frozen.snapshot_id,
            "input_digest": frozen.digest,
            "response_id": None,
            "response_digest": None,
            "next_step_index": cursor,
            "completed_step_ids": [record["task_id"] for record in records],
            "result_ids": [result.id for result in engineering_results],
            "input_files": sorted(
                (
                    {"path": value.path, "sha256": value.sha256}
                    for value in input_values.values()
                    if isinstance(value, WorkflowReference)
                ),
                key=lambda item: item["path"],
            ),
            "artifact_files": sorted(
                (
                    {"path": rep.location, "sha256": rep.sha256}
                    for rep in representations
                    if rep.kind == "workspace_file" and rep.sha256
                ),
                key=lambda item: item["path"],
            ),
            **_execution_snapshot(
                input_values=input_values,
                responses=responses,
                records=records,
                engineering_results=engineering_results,
                artifacts_by_output=artifacts_by_output,
                attempts=attempts,
                revision_counts=revision_counts,
                feedback=feedback,
            ),
        },
    }


def input_response_result(*, step, plan, response, checkpoint):
    """Publish the actual typed answer at its port, with immutable provenance."""
    port = step.human_interaction["output_port"]
    value = canonical_json(response.value)
    result = EngineeringResult(
        f"{response.run_id}:{step.id}:{port}",
        "structured",
        step.title,
        (
            Representation(
                "value", value, format="json", sha256=canonical_digest(response.value)
            ),
        ),
        Provenance(
            response.run_id,
            step.id,
            port,
            input_revisions=tuple(
                sorted(checkpoint["subject"]["upstream_digests"].items())
            ),
            definition_digest=plan.definition_digest,
            binding_digest=canonical_digest(step.human_interaction),
        ),
        artifact_role="intermediate",
    )
    record = {
        "task_id": step.id,
        "task_title": step.title,
        "execution_kind": "human_input",
        "output_format": "json",
        "output_path": None,
        "output_bytes": len(value.encode()),
        "response": value,
        "checkpoint_id": response.checkpoint_id,
        "subject_digest": response.subject_digest,
        "response_id": response.response_id,
        "response_digest": response.digest,
        "actor": response.actor,
        "reason": response.reason,
        "integration_test": response.integration_test,
        "produced_files": [],
    }
    return result, record
