"""JSON-safe canonical execution snapshots, never a second workflow executor.

The caller obtains a one-shot durable continuation claim before restoring this
state. All effects before the checkpoint are retained; an unknown action outcome
cannot release any later step.
"""

from dataclasses import asdict
import hashlib
import json

from .workflow_references import WorkflowReference
from .workflow_results import EngineeringResult, Provenance, Representation


def input_identities(values):
    return {
        key: value.sha256
        if isinstance(value, WorkflowReference)
        else hashlib.sha256(str(value).encode("utf-8")).hexdigest()
        for key, value in sorted(values.items())
    }


def local_review_input_files(step, input_values):
    """Only explicitly connected uploads can serve as initial local review artifacts."""
    if (step.external_action or {}).get("action_kind") != "local_review":
        return {}
    return {
        value.path: value.sha256
        for _, source_id in step.references
        if isinstance(
            value := input_values.get(source_id.split(".", 1)[0]), WorkflowReference
        )
    }


def encode_value(value):
    from .workflow_cad import CadDocument

    if isinstance(value, WorkflowReference):
        return {"type": "reference", "value": asdict(value)}
    if isinstance(value, EngineeringResult):
        return {"type": "engineering_result", "value": value.to_dict()}
    if isinstance(value, CadDocument):
        return {
            "type": "cad_document",
            "server_id": value.server_id,
            "document": value.document,
            "result": encode_value(value.result),
        }
    if value is None or isinstance(value, (str, bool, int, float, dict, list)):
        # Each entry is wrapped so arbitrary tool JSON cannot masquerade as a
        # typed runtime value when restored.
        json.dumps(value, allow_nan=False)
        return {"type": "json", "value": value}
    raise ValueError("Unsupported workflow continuation value")


def restore_result(value):
    return EngineeringResult(
        value["id"],
        value["kind"],
        value["name"],
        tuple(Representation(**rep) for rep in value["representations"]),
        Provenance(
            **{
                **value["provenance"],
                "input_revisions": tuple(
                    tuple(pair)
                    for pair in value["provenance"].get("input_revisions", [])
                ),
            }
        ),
        tuple(restore_result(item) for item in value.get("exports", [])),
        value.get("artifact_role", "deliverable"),
    )


def decode_value(value):
    from .workflow_cad import CadDocument

    kind = value["type"]
    if kind == "reference":
        return WorkflowReference(**value["value"])
    if kind == "engineering_result":
        return restore_result(value["value"])
    if kind == "cad_document":
        return CadDocument(
            value["server_id"], value["document"], decode_value(value["result"])
        )
    if kind == "json":
        return value["value"]
    raise ValueError("Unknown workflow continuation value")


async def restore_continuation(
    *, state, checkpoint, plan, input_values, service, workspace_dir
):
    """Validate the immutable checkpoint before restoring prior engineering work.

    The repository-backed caller is responsible for claiming this continuation
    once. The engine additionally rejects stale source/inputs/files and any
    approval whose action has not been definitively reconciled as dispatched.
    """
    from .workflow_source_execution import _error

    def stale(message):
        return _error(
            "WORKFLOW_CONTINUATION_STALE",
            message,
            "Inspect the saved run and approval evidence before starting another attempt.",
        )

    if not isinstance(state, dict) or state.get("schema_version") != 2:
        raise stale("This run has no executable continuation snapshot.")
    state = json.loads(json.dumps(state, allow_nan=False))
    if not isinstance(checkpoint, dict) or (
        checkpoint.get("state") != "consumed"
        or checkpoint.get("run_id") != state.get("run_id")
        or (checkpoint.get("external_action") or {}).get("outcome") != "dispatched"
    ):
        raise stale("The checkpoint does not have a confirmed completed action.")
    cursor = state.get("next_step_index")
    if type(cursor) is not int or not 0 <= cursor < len(plan.steps):
        raise stale("The continuation cursor is invalid.")
    step = plan.steps[cursor]
    if not step.external_action or checkpoint.get("step_id") != step.id:
        raise stale("The continuation does not match the approved canonical step.")
    subject = checkpoint.get("subject", {})
    from .workflow_external_actions import approval_subject_digest

    if approval_subject_digest(subject) != checkpoint.get("subject_digest"):
        raise stale("The approval subject digest does not match its evidence.")
    if (
        not plan.definition_digest
        or state.get("definition_digest") != plan.definition_digest
        or subject.get("definition_digest") != plan.definition_digest
        or state.get("input_identities") != input_identities(input_values)
        or subject.get("input_digests")
        != sorted(input_identities(input_values).values())
        or any(
            subject.get(key) != step.external_action[key]
            for key in ("binding", "destination", "settings", "action")
        )
    ):
        raise stale("The saved definition, inputs, or approved action changed.")
    expected_ids = [candidate.id for candidate in plan.steps[:cursor]]
    if state.get("completed_step_ids") != expected_ids:
        raise stale("The continuation omits or repeats completed canonical steps.")
    if [record.get("task_id") for record in state.get("records", [])] != expected_ids:
        raise stale("The continuation step evidence is incomplete.")
    files = state.get("input_files", []) + state.get("artifact_files", [])
    for evidence in files:
        try:
            identity = await service.files.hash_reference(
                workspace_dir, evidence["path"]
            )
        except (OSError, ValueError) as error:
            raise stale(
                "A checkpoint input or generated artifact is unavailable."
            ) from error
        if identity != evidence["sha256"]:
            raise stale("A checkpoint input or generated artifact changed.")
    results = [restore_result(item) for item in state["results"]]
    if any(item.provenance.run_id != state["run_id"] for item in results):
        raise stale("The continuation includes an artifact from another run.")
    artifact_digests = sorted(
        {
            representation.sha256
            for item in results
            for representation in (
                *item.representations,
                *(rep for exported in item.exports for rep in exported.representations),
            )
            if representation.sha256
        }
    )
    artifact_digests = sorted(
        set(artifact_digests)
        | set(local_review_input_files(step, input_values).values())
    )
    if subject.get("artifact_digests") != artifact_digests:
        raise stale("The approved artifact identities do not match the continuation.")
    return {
        "run_id": state["run_id"],
        "cursor": cursor,
        "responses": {
            key: decode_value(value) for key, value in state["responses"].items()
        },
        "artifacts_by_output": state["artifacts_by_output"],
        "records": state["records"],
        "engineering_results": results,
        "attempts": state["revision_attempts"],
        "revision_counts": state["revision_counts"],
        "feedback": state["feedback"],
    }
