"""Read-only campaign audit; save a new evidence snapshot without rewriting runs."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import urllib.parse
import urllib.request

import psutil

from engineering_dataset_campaign import check_outputs


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            return {"available": True, "data": json.load(response)}
    except (OSError, ValueError) as error:
        return {"available": False, "error_type": type(error).__name__}


def audit(root: Path):
    state = root / "artifacts/engineering-workflow-datasets"
    with sqlite3.connect((state / "campaign.sqlite3").as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        datasets = [json.loads(row[0]) for row in db.execute("SELECT document FROM datasets ORDER BY id")]
        receipts = [json.loads(row[0]) for row in db.execute("SELECT document FROM attempts")]
    accepted = {r["run_id"]: r for r in receipts if r.get("accepted_by_runtime") is True and r.get("run_id")}
    completed, families = [], {}
    for dataset in datasets:
        scenario = dataset["scenario_id"]
        history = [r for r in accepted.values() if r["scenario_id"] == scenario]
        current = [r for r in history if r.get("dataset_digest") == dataset["digest"]
                   and r.get("template_digest") == dataset["template_digest"]]
        verified = []
        for receipt in current:
            if receipt.get("status") != "completed":
                continue
            files = state / "output" / scenario / receipt["attempt_id"] / "artifacts"
            check = check_outputs(dataset, receipt, files)
            nonempty = all((files / item["path"]).stat().st_size > 0 for item in receipt["produced_files"]) if check["passed"] else False
            all_steps = (receipt.get("all_required_steps_succeeded") is True
                         and receipt.get("terminal_step_reached") is True)
            row = {"scenario_id": scenario, "attempt_id": receipt["attempt_id"], "run_id": receipt["run_id"],
                   "output_check": check, "all_nonempty": nonempty, "full_run": all_steps}
            verified.append(row)
            if check["passed"] and nonempty and all_steps:
                completed.append(row)
        latest = max(history, key=lambda r: r.get("started_at") or "") if history else {}
        family = families.setdefault(dataset["template_id"], {"completed": 0, "scenarios": []})
        family["completed"] += bool(verified and any(v in completed for v in verified))
        family["scenarios"].append({"scenario_id": scenario, "accepted_attempts": len(history),
            "latest_attempt": latest.get("attempt_id"), "latest_status": latest.get("status", "not_run"),
            "error_code": latest.get("error_code"), "error": str(latest.get("error") or "")[:1000]})
    native, workers, inspection_errors = [], [], []
    for process in psutil.process_iter(["pid", "name"]):
        try:
            name = (process.info["name"] or "").lower()
            if name in {"edge.exe", "blender.exe"}:
                native.append({"pid": process.pid, "creation_time": datetime.fromtimestamp(process.create_time(), timezone.utc).isoformat(),
                    "executable": process.exe(), "parent_pid": process.ppid(), "ownership": "unknown"})
            elif name in {"python.exe", "python"}:
                command = process.cmdline()
                if any(Path(arg).name == "run_engineering_dataset_campaign.py" for arg in command):
                    workers.append({"pid": process.pid, "creation_time": process.create_time(), "executable": process.exe()})
        except (psutil.AccessDenied, psutil.NoSuchProcess) as error:
            if name in {"edge.exe", "blender.exe"}:
                inspection_errors.append({"pid": process.pid, "error_type": type(error).__name__})
    orphan_path = root / ".local-run/feature-081-live/campaign-runner-state/sheet-metal-supplier-handoff-01/attempt-004.json"
    orphan_bytes = orphan_path.read_bytes()
    orphan = json.loads(orphan_bytes)
    query = urllib.parse.urlencode({"session_id": "wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a",
        "path": "workflows/campaign-sheet-metal-supplier-handoff-01-attempt-004.workflow.wflow", "latest_only": "true"})
    lifecycle = fetch("http://127.0.0.1:8000/api/workspace/workflow-sources/runs?" + query)
    models = fetch("http://127.0.0.1:8000/api/agent/models")
    selected = {key: models.get("data", {}).get(key) for key in ("current_value", "current_provider", "current_model")}
    return {"schema_version": 1, "observed_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {"datasets_created": len(datasets), "combinations_run": len({r["scenario_id"] for r in accepted.values()}),
                    "processes_with_outputs": len({r["scenario_id"] for r in completed}), "valid_data": 0},
        "accepted_runs": len(accepted), "accepted_statuses": dict(Counter(r["status"] for r in accepted.values())),
        "completed_rechecked": completed, "families": families, "native_applications": native,
        "native_inspection_errors": inspection_errors, "campaign_workers": workers,
        "workflow_model": {"available": models["available"], **selected},
        "historical_orphan": {"run_id": orphan["run_id"], "original_checkpoint_sha256": hashlib.sha256(orphan_bytes).hexdigest(),
            "original_phase": orphan["phase"], "latest_api_observation": lifecycle,
            "disposition": "No replay; historical engineering outcome remains unresolved; no completion credit."},
        "content_validation_enabled": False, "historical_records_modified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(Path(__file__).resolve().parents[1])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"evidence": str(args.output), "metrics": report["metrics"],
        "accepted_runs": report["accepted_runs"], "native_apps": len(report["native_applications"]),
        "workers": len(report["campaign_workers"]), "workflow_model": report["workflow_model"]}))
