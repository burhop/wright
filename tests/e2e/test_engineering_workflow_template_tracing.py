"""Feature operations retain explicit stable span names for trace review."""

from api.routers import workspace
from workspace_service.workflow_engineering_assertions import evaluate_assertion


def test_engineering_template_and_external_action_endpoints_declare_trace_spans():
    expected = {
        workspace.list_engineering_workflow_templates_endpoint: "workspace.workflow_source_templates.list",
        workspace.engineering_workflow_template_detail_endpoint: "workspace.workflow_source_templates.detail",
        workspace.engineering_workflow_template_readiness_endpoint: "workspace.workflow_source_templates.readiness",
        workspace.instantiate_engineering_workflow_template_endpoint: "workspace.workflow_source_templates.instantiate",
        workspace.run_workflow_source_endpoint: "workspace.workflow_sources.run",
        workspace.get_workflow_approval_checkpoint_endpoint: "workspace.workflow_approval.get",
        workspace.decide_workflow_approval_checkpoint_endpoint: "workspace.workflow_approval.decide",
        workspace.resume_workflow_approval_checkpoint_endpoint: "workspace.workflow_approval.resume",
        workspace.reconcile_workflow_external_action_endpoint: "workspace.workflow_external_action.reconcile",
        workspace.create_workflow_demo_capture_endpoint: "workspace.workflow_demo_capture.create",
        evaluate_assertion: "workspace.workflow_engineering_assertion.evaluate",
    }
    assert {
        function.__name__: getattr(function, "__wright_span_name__", None)
        for function in expected
    } == {function.__name__: span for function, span in expected.items()}
