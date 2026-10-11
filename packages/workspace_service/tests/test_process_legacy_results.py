import hashlib
import json
import pytest

from workspace_service.process_interfaces.legacy_results import read_legacy_result
from workspace_service.workflow_run_record import WorkflowRunReadError
from workspace_service.workflow_results import Provenance, file_result


def history(root):
    source = "workflows/saved.workflow.wflow"
    relative = "runs/saved/retained.json"
    (root / source).parent.mkdir()
    (root / source).write_text("workflow saved\nend\n")
    (root / relative).parent.mkdir(parents=True)
    (root / relative).write_text(
        json.dumps(
            {
                "workflow_path": source,
                "run_id": "recorded-run",
                "status": "failed",
                "events": [],
                "error": "Original retained failure",
                "result": {"run_id": "recorded-run", "results": []},
            }
        )
    )
    return source, relative


def test_historical_read_is_exact_read_only_and_preserves_files(tmp_path):
    source, relative = history(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = read_legacy_result(str(tmp_path), source, relative)
    assert result["read_only"] and result["permitted_actions"] == []
    assert result["run"]["run_id"] == "recorded-run"
    assert result["run"]["status"] == "failed"
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize(
    "locator",
    ["../outside.json", "runs/other/retained.json", "runs/saved/retained.txt"],
)
def test_historical_locator_cannot_escape_or_select_other_source(tmp_path, locator):
    source, _ = history(tmp_path)
    with pytest.raises(WorkflowRunReadError):
        read_legacy_result(str(tmp_path), source, locator)


def test_historical_record_cannot_claim_another_source(tmp_path):
    source, relative = history(tmp_path)
    path = tmp_path / relative
    value = json.loads(path.read_text())
    value["workflow_path"] = "workflows/other.workflow.wflow"
    path.write_text(json.dumps(value))
    with pytest.raises(WorkflowRunReadError):
        read_legacy_result(str(tmp_path), source, relative)


@pytest.mark.parametrize(
    "status,count,top_level_identity",
    [("failed", 3, True), ("completed", 16, True), ("completed", 16, False)],
)
def test_original_recorder_shapes_preserve_exact_results_without_actions(
    tmp_path, status, count, top_level_identity
):
    """Controlled shape checks complement the real original-history browser proof."""
    source, relative = history(tmp_path)
    rows = [
        file_result(
            {
                "output_path": f"artifacts/output-{index}.json",
                "output_format": "json",
                "output_bytes": 2,
            },
            Provenance("recorded-run", f"step-{index}", "result"),
        ).to_dict()
        for index in range(count)
    ]
    record = {
        "workflow_path": source,
        "source_digest": hashlib.sha256((tmp_path / source).read_bytes()).hexdigest(),
        "status": status,
        "events": [],
        "partial_results": {row["id"]: row for row in rows},
    }
    if top_level_identity:
        record["run_id"] = "recorded-run"
    if status == "completed":
        record["result"] = {"run_id": "recorded-run", "results": rows}
    else:
        record["error"] = "Original mesh operation failed"
        assert "result" not in record
    (tmp_path / relative).write_text(json.dumps(record), encoding="utf-8")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    response = read_legacy_result(str(tmp_path), source, relative)

    assert response["read_only"] is True and response["permitted_actions"] == []
    run = response["run"]
    assert run["run_id"] == "recorded-run" and run["status"] == status
    assert run["source_matches_current"] is True
    assert {row["id"] for row in run["results"]} == {row["id"] for row in rows}
    assert all(row["provenance"]["run_id"] == "recorded-run" for row in run["results"])
    assert {
        path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()
    } == before
