from __future__ import annotations

import hashlib
import platform
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .catalog_signing import canonical_json
from .windows_qualification_executor import (
    QualificationExecutionContext,
    QualificationOperationOutcome,
    WindowsQualificationExecutor,
)
from .windows_qualification_models import (
    EMPTY_DIGEST,
    QUALIFICATION_STAGES,
    SafetyPreflight,
    ServerQualificationEvidence,
    StageEvidence,
    WindowsQualificationRecipe,
    empty_stage_evidence,
)
from .windows_qualification_recipes import (
    assert_allowlisted,
    get_windows_qualification_recipe,
    recipe_digest,
)


class QualificationExecutor(Protocol):
    def execute_operation(
        self,
        recipe: WindowsQualificationRecipe,
        operation,
        context: QualificationExecutionContext,
    ) -> QualificationOperationOutcome: ...


_RESULT_PRIORITY = {
    "not_tested": 0,
    "not_applicable": 1,
    "passed": 2,
    "partial": 3,
    "obsolete_or_unavailable": 4,
    "safety_blocked": 5,
    "failed": 6,
}


def _machine_digest() -> str:
    payload = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _merge_stage(stages: dict[str, StageEvidence], incoming: StageEvidence) -> None:
    current = stages[incoming.stage]
    if _RESULT_PRIORITY[incoming.result] >= _RESULT_PRIORITY[current.result]:
        stages[incoming.stage] = incoming


def _terminal_classification(
    stages: dict[str, StageEvidence], preflight: SafetyPreflight
) -> str:
    if preflight.decision != "approved":
        return preflight.decision
    results = {stage.result for stage in stages.values()}
    if "failed" in results:
        return "failed"
    if "safety_blocked" in results:
        return "safety_blocked"
    if "obsolete_or_unavailable" in results:
        return "obsolete_or_unavailable"
    if results <= {"passed", "not_applicable"}:
        return "passed"
    return "partial"


class WindowsQualificationService:
    def __init__(
        self,
        *,
        executor: QualificationExecutor | None = None,
        recipe_loader: Callable[[str], WindowsQualificationRecipe] = (
            get_windows_qualification_recipe
        ),
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        checkpoint: Callable[[ServerQualificationEvidence], None] | None = None,
    ) -> None:
        self.executor = executor or WindowsQualificationExecutor()
        self.recipe_loader = recipe_loader
        self.clock = clock
        self.checkpoint = checkpoint

    def qualify(
        self,
        server_id: str,
        safety_preflight: SafetyPreflight,
        work_root: Path,
    ) -> ServerQualificationEvidence:
        assert_allowlisted(server_id)
        recipe = self.recipe_loader(server_id)
        if recipe.server_id != server_id:
            raise ValueError("qualification recipe identity changed")
        context = QualificationExecutionContext(
            work_root=work_root,
            server_id=server_id,
        )
        stages = {
            item.stage: item
            for item in empty_stage_evidence(reason_code="stage_not_run")
        }
        installed_items: list[str] = []
        cleanup_events: list[str] = []
        limitations: list[str] = []

        def build_evidence() -> ServerQualificationEvidence:
            observed_at = self.clock()
            mcp_observations = stages["mcp_started"].observations
            schema_digest = mcp_observations.get("tool_schema_digest")
            tool_count = mcp_observations.get("tool_count")
            evidence = ServerQualificationEvidence(
                evidence_id=(
                    f"{server_id}-windows-{observed_at.strftime('%Y%m%dT%H%M%SZ')}"
                ),
                server_id=server_id,
                policy_version="windows-allowlist-v1",
                recipe_digest=recipe_digest(recipe),
                source_revision=recipe.source.immutable_revision,
                package_version=recipe.source.package_version,
                package_digest=None,
                tool_schema_digest=(
                    str(schema_digest) if isinstance(schema_digest, str) else None
                ),
                machine_digest=_machine_digest(),
                credential_binding_digest=EMPTY_DIGEST,
                observed_at=observed_at,
                safety_preflight=safety_preflight,
                stages=[stages[stage] for stage in QUALIFICATION_STAGES],
                server_identity=(
                    str(mcp_observations["server_identity"])
                    if mcp_observations.get("server_identity")
                    else None
                ),
                server_version=(
                    str(mcp_observations["server_version"])
                    if mcp_observations.get("server_version")
                    else None
                ),
                protocol_version=(
                    str(mcp_observations["protocol_version"])
                    if mcp_observations.get("protocol_version")
                    else None
                ),
                tool_count=(int(tool_count) if isinstance(tool_count, int) else None),
                installed_items=installed_items,
                cleanup_events=cleanup_events,
                attempted_server_ids=[server_id],
                non_allowlist_actions=[],
                limitations=limitations,
                terminal_classification=_terminal_classification(
                    stages, safety_preflight
                ),
            )
            return evidence

        if safety_preflight.decision != "approved":
            refused_result = safety_preflight.decision
            stages["source_current"] = StageEvidence(
                stage="source_current",
                result=refused_result,
                reason_code=safety_preflight.reason_code,
                summary="Executable qualification stopped at the reviewed safety boundary.",
            )
            for stage in QUALIFICATION_STAGES[1:-1]:
                stages[stage] = StageEvidence(
                    stage=stage,
                    result=(
                        "not_applicable"
                        if refused_result == "obsolete_or_unavailable"
                        else "safety_blocked"
                    ),
                    reason_code=safety_preflight.reason_code,
                    summary="No executable action was attempted.",
                )
            stages["cleanup_passed"] = StageEvidence(
                stage="cleanup_passed",
                result="passed",
                reason_code="no_executable_action",
                summary="No qualification-owned executable state was created.",
            )
            evidence = build_evidence()
            if self.checkpoint:
                self.checkpoint(evidence)
            return evidence

        if recipe.locality in {"remote", "built_in_host"}:
            stages["windows_install_passed"] = StageEvidence(
                stage="windows_install_passed",
                result="not_applicable",
                reason_code="no_local_package",
                summary="This MCP has no separate local Windows package to install.",
            )

        stop_regular_operations = False
        try:
            for operation in recipe.operations:
                if stop_regular_operations:
                    break
                try:
                    outcome = self.executor.execute_operation(
                        recipe, operation, context
                    )
                except Exception:
                    stages[operation.stage] = StageEvidence(
                        stage=operation.stage,
                        result="failed",
                        reason_code="qualification_execution_failed",
                        summary="The bounded native operation failed.",
                        recovery="Review the redacted evidence and retry from a clean root.",
                    )
                    limitations.append(
                        f"{operation.operation_id} ended before completion"
                    )
                    stop_regular_operations = True
                else:
                    for stage in outcome.evidence:
                        _merge_stage(stages, stage)
                    installed_items.extend(outcome.installed_items)
                    cleanup_events.extend(outcome.cleanup_events)
                    if any(
                        stage.result
                        in {
                            "partial",
                            "failed",
                            "safety_blocked",
                            "obsolete_or_unavailable",
                        }
                        for stage in outcome.evidence
                    ):
                        stop_regular_operations = True
                if self.checkpoint:
                    self.checkpoint(build_evidence())
        finally:
            for operation in recipe.cleanup:
                try:
                    outcome = self.executor.execute_operation(
                        recipe, operation, context
                    )
                except Exception:
                    _merge_stage(
                        stages,
                        StageEvidence(
                            stage="cleanup_passed",
                            result="failed",
                            reason_code="qualification_cleanup_failed",
                            summary="Qualification-owned state could not be fully cleaned.",
                            recovery="Inspect only the declared disposable root and owned processes.",
                        ),
                    )
                    limitations.append(
                        f"cleanup {operation.operation_id} ended before completion"
                    )
                else:
                    for stage in outcome.evidence:
                        _merge_stage(stages, stage)
                    installed_items.extend(outcome.installed_items)
                    cleanup_events.extend(outcome.cleanup_events)
                if self.checkpoint:
                    self.checkpoint(build_evidence())

        evidence = build_evidence()
        if self.checkpoint:
            self.checkpoint(evidence)
        return evidence
