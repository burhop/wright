"""Resolve workspace presentation intents through existing source/result authorities."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import PurePosixPath

from core.process_interactions import NavigationResolution, NavigationTarget
from core.tracing import traced

from ..workflow_source_execution import _parse
from ..errors import WorkspaceTimeoutError
from .errors import ProcessInterfaceError
from .artifacts import assessment_content_matches
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
            # Find the immutable assessment in byte-pinned recorded JSON files.
            # A ledger reload can reorder dictionaries; its serialization is not
            # the original file's byte identity. Never invent a filename or SHA.
            report = next(
                report
                for report in facts.reports
                if report.assessment.id == target.assessment_id
            )
            legacy_digest = hashlib.sha256(
                report.assessment.model_dump_json(indent=2).encode("utf-8")
            ).hexdigest()
            evidence_files = {
                (
                    result.id,
                    result.provenance.output_port.removeprefix("diagnostic:"),
                )
                for result in facts.run.results
                + tuple(row[2] for row in facts.run.previous_results)
                if result.artifact_role in {"diagnostic", "verification"}
                and result.provenance.output_port.startswith("diagnostic:")
            }
            # Preserve legacy exact-byte candidates from any output role. The
            # formatting-independent path applies to explicitly recorded diagnostic
            # evidence, not arbitrary JSON deliverables or guessed filenames.
            candidates = [
                ref
                for candidate in outputs
                for ref in candidate.representations
                if ref.sha256 == legacy_digest
                or (
                    PurePosixPath(ref.artifact_ref).suffix.lower() == ".json"
                    and (candidate.result_id, ref.artifact_ref) in evidence_files
                )
            ]
            representations = []
            remaining = app.limits.maximum_representation_bytes
            if len(candidates) > app.limits.maximum_diagnostics:
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "The recorded assessment candidates exceed the supported read bound.",
                    "Inspect the canonical validation result for this run.",
                )
            try:
                async with asyncio.timeout(app.limits.representation_timeout_seconds):
                    for ref in candidates:
                        if remaining <= 0:
                            raise TimeoutError("Assessment candidate byte bound")
                        artifact = await app.artifacts.read(
                            scope,
                            process,
                            ref,
                            run_id=target.run_id,
                            _maximum_bytes=min(remaining, 16 * 1024 * 1024),
                        )
                        remaining -= len(artifact.content)
                        matches = await app.workspace.executor.run(
                            "process.assessment.identify",
                            lambda: assessment_content_matches(
                                artifact.content, report.assessment
                            ),
                            timeout_seconds=app.limits.representation_timeout_seconds,
                        )
                        if matches:
                            representations.append(ref)
            except (TimeoutError, WorkspaceTimeoutError) as error:
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "The recorded assessment candidates exceed the supported read bound.",
                    "Inspect the canonical validation result for this run.",
                ) from error
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
