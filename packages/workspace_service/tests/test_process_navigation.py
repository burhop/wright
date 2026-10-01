"""Presentation navigation resolves exact subjects without starting or replaying work."""

from dataclasses import replace
import hashlib

import pytest

from core.process_interactions import NavigationTarget
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.projection import RecordedRun, ProjectionFacts
from workspace_service.workflow_results import (
    EngineeringResult,
    Representation,
    Provenance,
)
from packages.workspace_service.tests.test_process_artifact_access import case
from packages.workspace_service.tests.test_process_input_readiness import source
from packages.workspace_service.tests.test_process_preparation_service import scope
from packages.workspace_service.tests.test_process_run_supervisor import start
from packages.workspace_service.tests.test_process_interaction_projection import (
    validation_report,
)


CAPABILITIES = (
    "process.read",
    "process.inputs",
    "process.start",
    "process.results",
    "process.navigate",
)


@pytest.mark.asyncio
async def test_source_navigation_reads_exact_declarations_without_preparation(tmp_path):
    async with case(tmp_path, text=source(default="Exact requirements")) as c:
        for target in (
            NavigationTarget(kind="process"),
            NavigationTarget(kind="block", block_id="brief"),
            NavigationTarget(kind="block", block_id="first"),
        ):
            resolved = await c.app.navigation.resolve(
                scope(*CAPABILITIES), c.process, target
            )
            assert resolved.process == c.process
            assert resolved.target == target
            assert resolved.representation is None
        assert not (tmp_path / "state.db").exists()
        assert not (tmp_path / "runs").exists()
        assert not (tmp_path / "first.txt").exists()
        for target in (
            NavigationTarget(kind="block", block_id="other"),
            NavigationTarget(kind="process", result_id="unrelated"),
        ):
            with pytest.raises(ProcessInterfaceError) as failure:
                await c.app.navigation.resolve(scope(*CAPABILITIES), c.process, target)
            assert failure.value.reason.code == "SCOPE_DENIED"


@pytest.mark.asyncio
async def test_navigation_keeps_scope_source_and_run_authority(tmp_path):
    async with case(tmp_path, text=source(default="Exact requirements")) as c:
        target = NavigationTarget(kind="block", block_id="first")
        for supplied_scope, supplied_process in (
            (scope("process.read"), c.process),
            (
                scope(*CAPABILITIES),
                c.process.model_copy(update={"workspace_id": "other"}),
            ),
        ):
            with pytest.raises(ProcessInterfaceError) as failure:
                await c.app.navigation.resolve(supplied_scope, supplied_process, target)
            assert failure.value.reason.code == "SCOPE_DENIED"
        with pytest.raises(ProcessInterfaceError) as failure:
            await c.app.navigation.resolve(
                scope(*CAPABILITIES),
                c.process.model_copy(update={"source_digest": "0" * 64}),
                target,
            )
        assert failure.value.reason.code == "SOURCE_CHANGED"
        for target in (
            NavigationTarget(kind="result", result_id="result"),
            NavigationTarget(kind="assessment", assessment_id="assessment"),
            NavigationTarget(kind="evidence", artifact_ref="private.txt"),
        ):
            with pytest.raises(ProcessInterfaceError) as failure:
                await c.app.navigation.resolve(scope(*CAPABILITIES), c.process, target)
            assert failure.value.reason.code == "SCOPE_DENIED"


@pytest.mark.asyncio
async def test_recorded_navigation_pins_producer_and_representation_without_replay(
    tmp_path,
):
    async with case(tmp_path, text=source(default="Exact requirements")) as c:
        prepared = await c.app.set_inputs(scope(*CAPABILITIES), c.process)
        calls = []

        async def generate(prompt, fmt):
            calls.append(prompt)
            return "Controlled actual output"

        receipt = await start(c.app, c.process, prepared.snapshot, generate)
        await c.app.runs.wait(scope(*CAPABILITIES), c.process, receipt.run_id)
        snapshot = await c.app.get_snapshot(
            scope(*CAPABILITIES), c.process, run_id=receipt.run_id
        )
        output = snapshot.outputs[0]
        ref = output.representations[0]
        for target in (
            NavigationTarget(kind="run", run_id=receipt.run_id),
            NavigationTarget(
                kind="result", run_id=receipt.run_id, result_id=output.result_id
            ),
            NavigationTarget(
                kind="block",
                run_id=receipt.run_id,
                block_id=output.step_id,
                result_id=output.result_id,
            ),
            NavigationTarget(
                kind="evidence", run_id=receipt.run_id, artifact_ref=ref.artifact_ref
            ),
        ):
            resolved = await c.app.navigation.resolve(
                scope(*CAPABILITIES), c.process, target
            )
            assert resolved.target.run_id == receipt.run_id
            if target.kind == "evidence":
                assert resolved.representation == ref
                assert resolved.target.result_id == output.result_id
                assert resolved.target.block_id == output.step_id
                artifact = await c.app.artifacts.read(
                    scope(*CAPABILITIES),
                    c.process,
                    resolved.representation,
                    run_id=receipt.run_id,
                )
                assert artifact.content == b"Controlled actual output"
        assert len(calls) == 1
        for target in (
            NavigationTarget(kind="result", run_id=receipt.run_id, result_id="foreign"),
            NavigationTarget(
                kind="evidence", run_id=receipt.run_id, artifact_ref="private.txt"
            ),
            NavigationTarget(
                kind="block",
                run_id=receipt.run_id,
                block_id="brief",
                result_id=output.result_id,
            ),
            NavigationTarget(
                kind="result",
                run_id=receipt.run_id,
                result_id=output.result_id,
                artifact_ref=ref.artifact_ref,
            ),
        ):
            with pytest.raises(ProcessInterfaceError) as failure:
                await c.app.navigation.resolve(scope(*CAPABILITIES), c.process, target)
            assert failure.value.reason.code == "SCOPE_DENIED"
        assert len(calls) == 1


@pytest.mark.asyncio
async def test_assessment_subject_and_recorded_evidence_are_separate_identities(
    tmp_path, monkeypatch
):
    report, subject_result, _ = validation_report(tmp_path)
    async with case(tmp_path, text=source(default="Exact requirements")) as c:
        raw = report.assessment.model_dump_json(indent=2).encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        evidence = EngineeringResult(
            "run:validator:evidence",
            "structured",
            "Recorded assessment",
            (
                Representation(
                    "workspace_file", "outputs/check.json", "json", sha256=digest
                ),
            ),
            Provenance("run", "validator", "evidence"),
            artifact_role="verification",
        )
        facts = ProjectionFacts(
            process=c.process,
            generated_at="2026-10-01T05:00:00Z",
            reports=(report,),
            run=RecordedRun(
                process=c.process,
                run_id="run",
                status="completed",
                cursor=1,
                observed_at="2026-10-01T05:00:00Z",
                results=(subject_result, evidence),
            ),
        )

        async def read_facts(*args, **kwargs):
            return facts

        monkeypatch.setattr(
            "workspace_service.process_interfaces.navigation.recorded_run_facts",
            read_facts,
        )
        target = NavigationTarget(
            kind="assessment",
            run_id="run",
            assessment_id=report.assessment.id,
            result_id=subject_result.id,
        )
        resolved = await c.app.navigation.resolve(
            scope(*CAPABILITIES), c.process, target
        )
        assert resolved.target.result_id == subject_result.id
        assert resolved.representation.result_id == evidence.id
        assert resolved.representation.artifact_ref == "outputs/check.json"
        assert resolved.representation.sha256 == digest
        with pytest.raises(ProcessInterfaceError) as failure:
            await c.app.navigation.resolve(
                scope(*CAPABILITIES),
                c.process,
                target.model_copy(update={"result_id": evidence.id}),
            )
        assert failure.value.reason.code == "SCOPE_DENIED"
        facts = replace(facts, run=replace(facts.run, results=(subject_result,)))
        with pytest.raises(ProcessInterfaceError) as failure:
            await c.app.navigation.resolve(scope(*CAPABILITIES), c.process, target)
        assert failure.value.reason.code == "CAPABILITY_UNAVAILABLE"
        facts = replace(facts, run=replace(facts.run, results=(), results_truncated=True))
        with pytest.raises(ProcessInterfaceError) as failure:
            await c.app.navigation.resolve(scope(*CAPABILITIES), c.process, target)
        assert failure.value.reason.code == "CAPABILITY_UNAVAILABLE"
        assert "read bound" in failure.value.reason.message
        facts = replace(facts, run=replace(facts.run, results_truncated=False))
        with pytest.raises(ProcessInterfaceError) as failure:
            await c.app.navigation.resolve(scope(*CAPABILITIES), c.process, target)
        assert failure.value.reason.code == "SCOPE_DENIED"
