from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from tool_registry.windows_qualification_executor import (
    QualificationOperationOutcome,
)
from tool_registry.windows_qualification_models import SafetyPreflight, StageEvidence
from tool_registry.windows_qualification_service import (
    WindowsQualificationService,
)

NOW = datetime(2026, 8, 13, 14, 0, tzinfo=UTC)


def _stage(stage: str, result: str = "passed") -> StageEvidence:
    return StageEvidence(
        stage=stage,
        result=result,
        reason_code=f"fixture_{result}",
        summary="Fixture evidence",
        started_at=NOW,
        finished_at=NOW,
        duration_ms=0,
    )


class FakeExecutor:
    def __init__(self, outcomes=None, failure: str | None = None) -> None:
        self.outcomes = outcomes or {}
        self.failure = failure
        self.calls: list[str] = []

    def execute_operation(self, recipe, operation, context):
        self.calls.append(operation.operation_id)
        if operation.operation_id == self.failure:
            raise RuntimeError("fixture execution failure")
        return self.outcomes.get(
            operation.operation_id,
            QualificationOperationOutcome((_stage(operation.stage),)),
        )


def _decision(value: str = "approved") -> SafetyPreflight:
    return SafetyPreflight(
        decision=value,
        reason_code=f"fixture_{value}",
        reviewed_at=NOW,
    )


def _root(tmp_path: Path) -> Path:
    path = tmp_path / "windows-mcp-qualification"
    path.mkdir()
    return path


def test_nonallowlisted_identity_reaches_no_recipe_or_executor_seam(
    tmp_path: Path,
) -> None:
    loaded: list[str] = []
    executor = FakeExecutor()

    def loader(server_id: str):
        loaded.append(server_id)
        raise AssertionError("loader must not run")

    service = WindowsQualificationService(executor=executor, recipe_loader=loader)

    with pytest.raises(ValueError, match="allowlist"):
        service.qualify("unreviewed-mcp", _decision(), _root(tmp_path))

    assert loaded == []
    assert executor.calls == []


def test_safety_refusal_records_terminal_evidence_without_side_effects(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor()
    service = WindowsQualificationService(executor=executor, clock=lambda: NOW)

    evidence = service.qualify("brep-mcp", _decision("safety_blocked"), _root(tmp_path))

    assert executor.calls == []
    assert evidence.terminal_classification == "safety_blocked"
    assert evidence.stages[0].result == "safety_blocked"
    assert evidence.stages[-1].result == "passed"


def test_obsolete_source_continues_to_factual_checkpoint(tmp_path: Path) -> None:
    executor = FakeExecutor()
    service = WindowsQualificationService(executor=executor, clock=lambda: NOW)

    evidence = service.qualify(
        "aps-mcp-server-nodejs",
        _decision("obsolete_or_unavailable"),
        _root(tmp_path),
    )

    assert executor.calls == []
    assert evidence.terminal_classification == "obsolete_or_unavailable"
    assert evidence.stages[1].result == "not_applicable"


def test_cleanup_runs_after_execution_failure_and_evidence_is_complete(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor(failure="install-local-package")
    checkpoints = []
    service = WindowsQualificationService(
        executor=executor,
        clock=lambda: NOW,
        checkpoint=checkpoints.append,
    )

    evidence = service.qualify("brep-mcp", _decision(), _root(tmp_path))

    assert "stop-owned-processes" in executor.calls
    assert "remove-work-root" in executor.calls
    assert evidence.terminal_classification == "failed"
    assert len(evidence.stages) == 8
    assert checkpoints[-1] == evidence


def test_protocol_and_host_results_remain_independent(tmp_path: Path) -> None:
    executor = FakeExecutor(
        outcomes={
            "launch-stdio": QualificationOperationOutcome(
                (
                    _stage("mcp_started"),
                    _stage("protocol_passed"),
                    _stage("safe_probe_passed"),
                )
            )
        }
    )
    service = WindowsQualificationService(executor=executor, clock=lambda: NOW)

    evidence = service.qualify("brep-mcp", _decision(), _root(tmp_path))
    stages = {item.stage: item for item in evidence.stages}

    assert stages["protocol_passed"].result == "passed"
    assert stages["safe_probe_passed"].result == "passed"
    assert stages["wright_gateway_passed"].result == "passed"
    assert evidence.attempted_server_ids == ["brep-mcp"]
    assert evidence.non_allowlist_actions == []


def test_protocol_metadata_is_promoted_to_bounded_top_level_fields(
    tmp_path: Path,
) -> None:
    executor = FakeExecutor(
        outcomes={
            "launch-stdio": QualificationOperationOutcome(
                (
                    StageEvidence(
                        stage="mcp_started",
                        result="passed",
                        reason_code="mcp_initialized",
                        observations={
                            "server_identity": "fixture-server",
                            "server_version": "1.2.3",
                            "protocol_version": "2025-11-25",
                            "tool_count": 4,
                            "tool_schema_digest": "a" * 64,
                        },
                    ),
                    _stage("protocol_passed"),
                    _stage("safe_probe_passed"),
                )
            )
        }
    )
    evidence = WindowsQualificationService(
        executor=executor, clock=lambda: NOW
    ).qualify("brep-mcp", _decision(), _root(tmp_path))

    assert evidence.server_identity == "fixture-server"
    assert evidence.server_version == "1.2.3"
    assert evidence.protocol_version == "2025-11-25"
    assert evidence.tool_count == 4
    assert evidence.tool_schema_digest == "a" * 64


def test_remote_mcp_has_no_local_windows_package_stage(tmp_path: Path) -> None:
    evidence = WindowsQualificationService(
        executor=FakeExecutor(), clock=lambda: NOW
    ).qualify("autodesk-product-help-mcp", _decision(), _root(tmp_path))

    package = next(
        stage for stage in evidence.stages if stage.stage == "windows_install_passed"
    )
    assert package.result == "not_applicable"
    assert package.reason_code == "no_local_package"
