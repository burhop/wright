import json
import pytest

from workspace_service.process_interfaces.legacy_results import read_legacy_result
from workspace_service.workflow_run_record import WorkflowRunReadError


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
