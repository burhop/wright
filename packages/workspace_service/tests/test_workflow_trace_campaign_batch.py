import hashlib
import importlib.util
import json
import sqlite3
import zipfile
from pathlib import Path

from workspace_service.workflow_trace.campaign_batch import (
    build_campaign_inventory,
    export_prepared_campaign,
)


ROOT = Path(__file__).resolve().parents[3]
VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_trace_campaign", ROOT / "scripts" / "verify-workflow-trace-campaign.py"
)
assert VERIFY_SPEC and VERIFY_SPEC.loader
VERIFY = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(VERIFY)


def _run(case: str, attempt: str, status: str, artifact: bytes = b"result") -> dict:
    task = f"produce_{case.replace('-', '_')}"
    return {
        "schema_version": 1,
        "scenario_id": case,
        "attempt_id": attempt,
        "run_id": f"run-{case}",
        "status": status,
        "dataset_digest": hashlib.sha256(case.encode()).hexdigest(),
        "template_digest": hashlib.sha256(case.rsplit("-", 1)[0].encode()).hexdigest(),
        "definition_digest": "d" * 64,
        "started_at": "2026-09-12T10:00:00+00:00",
        "finished_at": "2026-09-12T10:01:00+00:00" if status == "completed" else None,
        "required_step_ids": [task],
        "completed_step_ids": [task] if status == "completed" else [],
        "all_required_steps_succeeded": status == "completed",
        "error_code": None if status == "completed" else "TASK_BLOCKED",
        "error": None
        if status == "completed"
        else "The approved dimensions do not define the final bend.",
        "step_events": [
            {
                "kind": "step_started",
                "at": "2026-09-12T10:00:00+00:00",
                "task_id": task,
            },
            *(
                [
                    {
                        "kind": "step_completed",
                        "at": "2026-09-12T10:01:00+00:00",
                        "task_id": task,
                    }
                ]
                if status == "completed"
                else []
            ),
        ],
        "produced_files": [
            {
                "artifact_id": f"artifact-{case}",
                "path": "result.json",
                "sha256": hashlib.sha256(artifact).hexdigest(),
                "size_bytes": len(artifact),
                "task_id": task,
                "artifact_role": "engineering_report",
            }
        ],
    }


def _write_bundle_run(bundle: Path, record: dict, artifact: bytes = b"result") -> str:
    attempt = bundle / "output" / record["scenario_id"] / record["attempt_id"]
    (attempt / "artifacts").mkdir(parents=True)
    (attempt / "artifacts" / "result.json").write_bytes(artifact)
    (attempt / "run.json").write_text(json.dumps(record))
    return (attempt / "run.json").relative_to(bundle).as_posix()


def test_inventory_pins_reviewed_completed_and_latest_incomplete_attempt(
    tmp_path: Path,
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    completed = _run("family-a-01", "attempt-002", "completed")
    completed_path = _write_bundle_run(bundle, completed)
    _write_bundle_run(bundle, _run("family-b-01", "attempt-003", "failed"))
    latest = _run("family-b-01", "attempt-011", "failed")
    latest_path = _write_bundle_run(bundle, latest)
    datasets = []
    revisions = []
    for record in (completed, latest):
        datasets.append(
            {
                "scenario_id": record["scenario_id"],
                "title": record["scenario_id"],
                "summary": "Test case",
                "digest": record["dataset_digest"],
                "template_digest": record["template_digest"],
                "path": record["scenario_id"],
            }
        )
        revisions.append(
            (
                f"{record['dataset_digest']}/{record['template_digest']}",
                json.dumps(
                    {
                        "scenario_id": record["scenario_id"],
                        "path": record["scenario_id"],
                    }
                ),
            )
        )
    (bundle / "status.json").write_text(
        json.dumps({"campaign_id": "campaign", "datasets": datasets})
    )
    with sqlite3.connect(bundle / "campaign.sqlite3") as database:
        database.execute(
            "CREATE TABLE dataset_revisions (fingerprint TEXT, document TEXT)"
        )
        database.executemany("INSERT INTO dataset_revisions VALUES (?, ?)", revisions)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "selection": [
                    {
                        "case_id": completed["scenario_id"],
                        "attempt_id": completed["attempt_id"],
                        "run_path": completed_path,
                    }
                ]
            }
        )
    )

    inventory = build_campaign_inventory(bundle, manifest)

    assert inventory["case_count"] == 2
    assert inventory["status_counts"] == {"completed": 1, "failed": 1}
    by_case = {item["case_id"]: item for item in inventory["cases"]}
    assert by_case["family-a-01"]["run_path"] == completed_path
    assert by_case["family-b-01"]["run_path"] == latest_path
    assert by_case["family-b-01"]["attempt_id"] == "attempt-011"
    assert "run did not complete" in by_case["family-b-01"]["known_gaps"]
    assert by_case["family-b-01"]["stopping_reason"].startswith(
        "The approved dimensions"
    )


def test_batch_export_writes_one_zip_per_case_and_offline_catalog(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    records = [
        _run("heat-spreader-sizing-01", "attempt-002", "completed"),
        _run("sheet-metal-supplier-handoff-01", "attempt-011", "failed"),
    ]
    indexed = []
    cases = []
    for record in records:
        run_dir = workspace / "runs" / record["scenario_id"]
        (run_dir / "artifacts").mkdir(parents=True)
        (run_dir / "artifacts" / "result.json").write_bytes(b"result")
        run_path = run_dir / f"{record['attempt_id']}.json"
        run_path.write_text(json.dumps(record))
        indexed.append(
            {
                "case_id": record["scenario_id"],
                "run_path": run_path.relative_to(workspace).as_posix(),
            }
        )
        cases.append(
            {
                "case_id": record["scenario_id"],
                "family": record["scenario_id"].rsplit("-", 1)[0],
                "title": record["scenario_id"],
                "summary": "Recorded test case",
                "attempt_id": record["attempt_id"],
                "run_id": record["run_id"],
                "status": record["status"],
                "produced_artifacts": 1,
            }
        )
    (workspace / "trace-review-index.json").write_text(json.dumps({"runs": indexed}))
    inventory = {"cases": cases, "status_counts": {"completed": 1, "failed": 1}}

    output = tmp_path / "reports"
    catalog = export_prepared_campaign(workspace, inventory, output, mode="full_data")

    assert len(catalog["reports"]) == 2
    assert (output / "index.html").is_file()
    assert "Open engineering review" in (output / "index.html").read_text()
    for entry in catalog["reports"]:
        archive_path = output / entry["archive_path"]
        report_path = output / entry["report_path"]
        assert archive_path.is_file()
        assert report_path.is_file()
        with zipfile.ZipFile(archive_path) as archive:
            assert "index.html" in archive.namelist()
            assert any(name.startswith("outputs/") for name in archive.namelist())
            report = archive.read("index.html").decode()
            if entry["status"] == "completed":
                assert "Conduction heat-spreader sizing" in report
                assert "Thermal sizing decision produced" in report
            else:
                assert "Sheet-metal supplier handoff" in report
                assert "Stopped / Task blocked" in report
                assert "approved dimensions do not define the final bend" in report
            manifest = json.loads(archive.read("manifest.json"))
            assert manifest["mode"] == "full_data"
            assert all(
                item["package_path"] in archive.namelist()
                for item in manifest["entries"]
                if item["package_path"]
            )
    assert VERIFY.verify(output, expected=2)["failures"] == []
