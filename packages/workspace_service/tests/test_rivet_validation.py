from __future__ import annotations

from importlib.resources import files

import pytest

from workspace_service.rivet_validation import (
    WorkflowIdentityMismatch,
    validate_rivet_project,
)


def _template(name: str) -> str:
    return (
        files("workspace_service.workflow_catalog")
        .joinpath(f"templates/{name}.rivet-project")
        .read_text(encoding="utf-8")
    )


def test_validation_summarizes_graphs_ports_and_main_graph():
    project = _template("ai-agent")
    result = validate_rivet_project(
        project,
        workflow_id="workflow-1",
        revision=2,
        digest="b" * 64,
    )

    assert result.valid
    assert result.workflow_id == "workflow-1"
    assert result.revision == 2
    assert result.main_graph is not None
    assert result.main_graph.id
    assert result.main_graph.name
    assert result.graphs
    assert "ai" in result.requirements


def test_validation_reports_missing_main_and_selected_graph():
    without_main = validate_rivet_project(
        _template("basic-flow"),
        workflow_id="workflow-1",
        revision=1,
        digest="c" * 64,
    )
    assert not without_main.valid
    assert {issue.code for issue in without_main.errors} == {"RIVET_MAIN_GRAPH_MISSING"}

    selected = validate_rivet_project(
        _template("basic-flow"),
        workflow_id="workflow-1",
        revision=1,
        digest="c" * 64,
        selected_graph="Passthrough",
    )
    assert selected.valid
    assert selected.main_graph.name == "Passthrough"
    assert [port.id for port in selected.main_graph.inputs] == ["input"]
    assert [port.id for port in selected.main_graph.outputs] == ["output"]


def test_validation_handles_malformed_projects_and_bounds_issues():
    malformed = validate_rivet_project(
        "not: [valid",
        workflow_id="workflow-1",
        revision=1,
        digest="d" * 64,
    )
    assert not malformed.valid
    assert malformed.errors[0].code == "RIVET_PROJECT_PARSE_FAILED"
    assert len(malformed.errors[0].message) <= 256


def test_validation_rejects_stale_identity_before_parse():
    with pytest.raises(WorkflowIdentityMismatch):
        validate_rivet_project(
            _template("basic-flow"),
            workflow_id="workflow-1",
            revision=2,
            digest="e" * 64,
            expected_revision=1,
            expected_digest="e" * 64,
        )
