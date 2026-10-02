"""JSON-safe canonical execution snapshots, never a second workflow executor.

The caller obtains a one-shot durable continuation claim before restoring this
state. All effects before the checkpoint are retained; an unknown action outcome
cannot release any later step.
"""

from dataclasses import asdict
import hashlib
import json

from .workflow_references import WorkflowReference, accepts_supplied_artifacts
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
    return approval_input_files(step, input_values)


def approval_input_files(step, input_values):
    """Bind only connected, frozen file references to fixed artifact approvals."""
    if not accepts_supplied_artifacts(step):
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
    return await _validate_continuation(
        state=state,
        checkpoint=checkpoint,
        plan=plan,
        input_values=input_values,
        service=service,
        workspace_dir=workspace_dir,
        input_inspection=False,
    )


async def inspect_input_continuation(
    *, state, checkpoint, plan, input_values, service, workspace_dir
):
    """Read-only validation of an input barrier before any answer is accepted."""
    if (
        not isinstance(state, dict)
        or state.get("schema_version") != 3
        or state.get("checkpoint_kind") != "input"
    ):
        from .workflow_source_execution import _error

        raise _error(
            "WORKFLOW_CONTINUATION_STALE",
            "This is not a declared input checkpoint.",
            "Inspect the exact run's input reference.",
        )
    return await _validate_continuation(
        state=state,
        checkpoint=checkpoint,
        plan=plan,
        input_values=input_values,
        service=service,
        workspace_dir=workspace_dir,
        input_inspection=True,
    )


async def _validate_continuation(
    *, state, checkpoint, plan, input_values, service, workspace_dir, input_inspection
):
    """Validate the immutable checkpoint before restoring prior engineering work.

    The repository-backed caller is responsible for claiming this continuation
    once. The engine additionally rejects stale source/inputs/files and any
    approval whose action has not been definitively reconciled as dispatched.
    """
    from .workflow_source_execution import _resolved_approval_settings, _error

    def stale(message):
        return _error(
            "WORKFLOW_CONTINUATION_STALE",
            message,
            "Inspect the saved run and approval evidence before starting another attempt.",
        )

    if (
        not isinstance(state, dict)
        or type(state.get("schema_version")) is not int
        or state["schema_version"] not in {2, 3}
    ):
        raise stale("This run has no executable continuation snapshot.")
    state = json.loads(json.dumps(state, allow_nan=False))
    kind = state.get("checkpoint_kind") if state["schema_version"] == 3 else "approval"
    if kind not in {"approval", "input"}:
        raise stale("The continuation checkpoint kind is unsupported.")
    if not isinstance(checkpoint, dict) or (
        checkpoint.get("state")
        not in ({"pending", "consumed"} if input_inspection else {"consumed"})
        or checkpoint.get("run_id") != state.get("run_id")
        or (
            kind == "approval"
            and (checkpoint.get("external_action") or {}).get("outcome") != "dispatched"
        )
    ):
        raise stale("The checkpoint does not have confirmed continuation authority.")
    cursor = state.get("next_step_index")
    if type(cursor) is not int or not 0 <= cursor < len(plan.steps):
        raise stale("The continuation cursor is invalid.")
    step = plan.steps[cursor]
    if checkpoint.get("step_id") != step.id or (
        (kind == "approval" and not step.external_action)
        or (kind == "input" and (not step.human_interaction or step.external_action))
    ):
        raise stale("The continuation does not match its declared canonical step.")
    subject = checkpoint.get("subject", {})
    from .workflow_external_actions import approval_subject_digest
    from .process_interfaces.interactions import input_subject_digest

    try:
        subject_digest = (
            input_subject_digest(subject)
            if kind == "input"
            else approval_subject_digest(subject)
        )
    except (ValueError, RuntimeError) as error:
        raise stale("The checkpoint subject is invalid.") from error
    if subject_digest != checkpoint.get("subject_digest"):
        raise stale("The checkpoint subject digest does not match its evidence.")
    if (
        not plan.definition_digest
        or state.get("definition_digest") != plan.definition_digest
        or subject.get("definition_digest") != plan.definition_digest
        or state.get("input_identities") != input_identities(input_values)
        or subject.get("input_digests")
        != sorted(input_identities(input_values).values())
    ):
        raise stale("The saved definition or inputs changed.")
    if kind == "approval" and (
        subject.get("binding") != step.external_action["binding"]
        or subject.get("destination") != step.external_action["destination"]
        or subject.get("settings")
        != await _resolved_approval_settings(
            pending_action=step,
            plan=plan,
            workspace_dir=workspace_dir,
            service=service,
            continuation=state,
        )
        or subject.get("action") != step.external_action["action"]
    ):
        raise stale("The approved action changed.")
    if kind == "approval" and step.external_action["action_kind"] == "mcp-operation":
        evidence = (checkpoint.get("external_action") or {}).get("evidence", {})
        policy = subject["settings"]["operation_policy"]
        if not evidence.get("delivery_completed") or (
            policy["mode"] == "observe"
            and evidence.get("observed_outcome") != "completed"
        ):
            raise stale(
                "The accepted operation has no confirmed required observation or receipt delivery."
            )
    if state["schema_version"] == 3:
        from core.process_interactions import InputSnapshot

        try:
            frozen = InputSnapshot.model_validate_json(
                plan.input_snapshot.model_dump_json()
            )
            retained_inputs = service.process_interfaces.inputs.get_snapshot(
                frozen.process.workspace_id, frozen.snapshot_id
            )
            if (
                frozen.snapshot_id != state.get("input_snapshot_id")
                or frozen.digest != state.get("input_digest")
                or frozen.process.source_digest != plan.definition_digest
                or retained_inputs != frozen
                or (
                    kind == "approval"
                    and (
                        state.get("response_id") is not None
                        or state.get("response_digest") is not None
                    )
                )
            ):
                raise ValueError("The frozen inputs changed")
        except (AttributeError, KeyError, ValueError, TypeError) as error:
            raise stale(
                "The continuation's immutable input snapshot changed."
            ) from error
    human_response = None
    if kind == "input":
        from core.process_validation import canonical_digest
        from .process_interfaces.errors import ProcessInterfaceError

        try:
            owner = service.process_interfaces.human_inputs
            current = owner.get(
                checkpoint["checkpoint_id"],
                workspace_id=checkpoint["workspace_id"],
                run_id=state["run_id"],
            )
            if asdict(current) != checkpoint or current.continuation != state:
                raise ValueError(
                    "The continuation differs from its retained checkpoint"
                )
            if (
                (current.state != "consumed" and not input_inspection)
                or subject.get("step_id") != step.id
                or subject.get("declaration") != step.human_interaction
                or subject.get("input_snapshot_id") != frozen.snapshot_id
                or subject.get("input_digest") != frozen.digest
                or subject.get("upstream_digests")
                != {
                    source: canonical_digest(state["responses"][source])
                    if source in state["responses"]
                    else canonical_digest(
                        encode_value(input_values[source.split(".", 1)[0]])
                    )
                    for _, source in step.references
                }
            ):
                raise ValueError("The declared input or its upstream evidence changed")
            if (
                current.continuation.get("response_id") is not None
                or not input_inspection
            ):
                human_response = owner.response(current)
        except (
            AttributeError,
            ValueError,
            TypeError,
            KeyError,
            ProcessInterfaceError,
        ) as error:
            raise stale(
                "The input continuation has no matching immutable response."
            ) from error
    expected_ids = [candidate.id for candidate in plan.steps[:cursor]]
    if state.get("completed_step_ids") != expected_ids:
        raise stale("The continuation omits or repeats completed canonical steps.")
    if [record.get("task_id") for record in state.get("records", [])] != expected_ids:
        raise stale("The continuation step evidence is incomplete.")
    results = [restore_result(item) for item in state["results"]]
    if kind == "input":
        expected_inputs = sorted(
            (
                {"path": value.path, "sha256": value.sha256}
                for value in input_values.values()
                if isinstance(value, WorkflowReference)
            ),
            key=lambda item: item["path"],
        )
        expected_files = sorted(
            (
                {"path": rep.location, "sha256": rep.sha256}
                for result in results
                for rep in (
                    *result.representations,
                    *(
                        r
                        for exported in result.exports
                        for r in exported.representations
                    ),
                )
                if rep.kind == "workspace_file" and rep.sha256
            ),
            key=lambda item: item["path"],
        )
        if (
            state.get("input_files") != expected_inputs
            or state.get("artifact_files") != expected_files
            or state.get("result_ids") != [item.id for item in results]
        ):
            raise stale(
                "The input checkpoint omits or changes retained result/file identities."
            )
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
        set(artifact_digests) | set(approval_input_files(step, input_values).values())
    )
    if subject.get("artifact_digests") != artifact_digests:
        raise stale("The approved artifact identities do not match the continuation.")
    restored = {
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
    if human_response is not None:
        restored["human_response"] = human_response
    return restored
