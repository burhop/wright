"""Resolve workspace presentation intents through existing source/result authorities."""

from __future__ import annotations

import hashlib

from core.process_interactions import NavigationResolution, NavigationTarget
from core.tracing import traced

from ..workflow_source_execution import _parse
from .errors import ProcessInterfaceError
from .owners import recorded_run_facts
from .projection import project_output, project_previous_output


def _denied():
    return ProcessInterfaceError(
        "SCOPE_DENIED",
        "This navigation target does not belong to the selected process and run.",
        "Open the exact step, output or assessment from its working view.",
    )


class ProcessNavigation:
    def __init__(self, application):
        self.application = application

    @traced("process.interface.navigation.resolve")
    async def resolve(self, scope, process, target, *, gateway=None, session_id=""):
        app = self.application
        resolved = await app.resolve_process(
            scope, process, operation="process.navigate"
        )
        fields = target.model_dump(exclude_none=True)
        permitted = {
            "process": {"run_id"},
            "run": {"run_id"},
            "block": {"block_id", "run_id", "result_id", "assessment_id"},
            "result": {"block_id", "run_id", "result_id"},
            "assessment": {"block_id", "run_id", "result_id", "assessment_id"},
            "evidence": {
                "block_id",
                "run_id",
                "result_id",
                "assessment_id",
                "artifact_ref",
            },
        }[target.kind]
        if set(fields) - {"kind"} - permitted:
            raise _denied()
        if target.block_id and not any(
            block["id"] == target.block_id and block["kind"] in {"input", "task"}
            for block in _parse(resolved.document.source)
        ):
            raise _denied()
        needs_output = target.kind in {"result", "assessment", "evidence"} or bool(
            target.result_id or target.assessment_id
        )
        if needs_output and not target.run_id:
            raise _denied()
        if not target.run_id:
            return NavigationResolution(process=process, target=target)
        facts = await recorded_run_facts(
            app, resolved, target.run_id, gateway=gateway, session_id=session_id
        )
        if (
            facts.run is None
            or facts.run.process.source_digest != process.source_digest
        ):
            raise _denied()
        if not needs_output:
            return NavigationResolution(process=process, target=target)
        outputs = tuple(
            project_output(result, facts.reports) for result in facts.run.results
        ) + tuple(
            project_previous_output(attempt, original_id, result, facts.reports)
            for attempt, original_id, result in facts.run.previous_results
        )
        selected = [
            output
            for output in outputs
            if (not target.result_id or output.result_id == target.result_id)
            and (not target.block_id or output.step_id == target.block_id)
            and (
                not target.assessment_id
                or any(
                    assessment.assessment_id == target.assessment_id
                    for assessment in output.assessments
                )
            )
            and (
                not target.artifact_ref
                or any(
                    ref.artifact_ref == target.artifact_ref
                    for ref in output.representations
                )
            )
        ]
        if not selected and facts.run.results_truncated:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "This output cannot be resolved within the recorded run's read bound.",
                "Inspect the canonical run log for the exact retained output.",
            )
        if len(selected) != 1:
            raise _denied()
        output = selected[0]
        representation = None
        if target.kind == "evidence":
            representations = [
                ref
                for ref in output.representations
                if ref.artifact_ref == target.artifact_ref
            ]
            if len(representations) != 1:
                raise _denied()
            representation = representations[0]
        elif target.kind == "assessment":
            # The validator's recorded JSON is an ordinary canonical result.
            # Locate it by exact content identity, never an invented filename.
            report = next(
                report
                for report in facts.reports
                if report.assessment.id == target.assessment_id
            )
            digest = hashlib.sha256(
                report.assessment.model_dump_json(indent=2).encode("utf-8")
            ).hexdigest()
            representations = [
                ref
                for candidate in outputs
                for ref in candidate.representations
                if ref.sha256 == digest
            ]
            if len(representations) == 1:
                representation = representations[0]
            else:
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "This assessment has no unambiguous recorded file in the selected run.",
                    "Inspect the assessment through its canonical validation result reader.",
                )
        pinned = NavigationTarget.model_validate(
            {**fields, "result_id": output.result_id, "block_id": output.step_id}
        )
        return NavigationResolution(
            process=process, target=pinned, representation=representation
        )
