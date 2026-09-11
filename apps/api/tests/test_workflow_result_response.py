from api.schemas.workspace import WorkflowSourceRunResponse


def test_headless_preserves_resource_results_and_allows_no_local_file():
    result = {
        "schema_version": 1,
        "kind": "cad_model",
        "representations": [{"kind": "cloud_resource", "resource_id": "123"}],
    }
    response = WorkflowSourceRunResponse(
        workspace_id="w",
        workflow_path="workflows/cad.workflow.wflow",
        workflow_title="CAD",
        task_id="cad",
        task_title="CAD",
        output_path="",
        output_bytes=0,
        results=[result],
        run_id="r",
    )
    assert response.model_dump()["results"] == [result]
    response.output_bytes = 5 * 1024 * 1024
    assert response.model_dump()["run_id"] == "r"
